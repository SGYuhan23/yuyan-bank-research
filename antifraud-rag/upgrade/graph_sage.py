"""Two learned mean-GraphSAGE layers. Torch training, small JSON/numpy inference.
Equation follows SAGEConv mean/root operator; no PyG/NVIDIA code copied.
"""
import argparse,hashlib,json,time,platform
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score
from .graph_lab import ROOT,FEATURES,generate,features,metrics
from .contracts import digest

def prepare(graph):
    nodes,edges,x,g,adj=features(graph,graph['as_of'])
    mean=adj/np.maximum(adj.sum(1,keepdims=True),1)
    return nodes,x.astype('float32'),g,mean.astype('float32')

def predict(checkpoint,x,adj):
    z=(x-np.array(checkpoint['mean']))/np.array(checkpoint['scale'])
    if checkpoint['model']=='sage_no_messages':adj=np.zeros_like(adj)
    for i in range(2):
        layer=checkpoint['layers'][i]
        z=z@np.array(layer['self']).T+(adj@z)@np.array(layer['neighbor']).T+np.array(layer['bias'])
        if i==0:z=np.maximum(z,0)
    return 1/(1+np.exp(-np.clip(z[:,0],-80,80)))

def train(train_data,dev_data,seed,no_messages=False,epochs=200):
    import torch
    from torch import nn
    torch.set_num_threads(1);torch.manual_seed(seed);torch.use_deterministic_algorithms(True)
    class Layer(nn.Module):
        def __init__(self,a,b):
            super().__init__();self.root=nn.Linear(a,b);self.neighbor=nn.Linear(a,b,bias=False)
        def forward(self,x,adj):return self.root(x)+self.neighbor(adj@x)
    class SAGE(nn.Module):
        def __init__(self):super().__init__();self.layers=nn.ModuleList([Layer(5,16),Layer(16,1)])
        def forward(self,x,adj):return self.layers[1](torch.relu(self.layers[0](x,adj)),adj).flatten()
    _,x,_,adj,y=train_data;_,dx,_,da,dy=dev_data
    mean=x.mean(0);scale=np.maximum(x.std(0),1e-6)
    tx=torch.tensor((x-mean)/scale);td=torch.tensor((dx-mean)/scale)
    ta=torch.tensor(np.zeros_like(adj) if no_messages else adj);tda=torch.tensor(np.zeros_like(da) if no_messages else da)
    ty=torch.tensor(y,dtype=torch.float32);model=SAGE();opt=torch.optim.Adam(model.parameters(),lr=.01,weight_decay=.001)
    loss_fn=nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float((len(y)-y.sum())/y.sum())))
    best=-1;checkpoint=None;history=[];start=time.monotonic()
    for epoch in range(1,epochs+1):
        model.train();opt.zero_grad();loss=loss_fn(model(tx,ta),ty);loss.backward();opt.step()
        model.eval()
        with torch.no_grad():dev_scores=torch.sigmoid(model(td,tda)).numpy()
        ap=float(average_precision_score(dy,dev_scores));history.append({'epoch':epoch,'train_loss':float(loss.detach()),'dev_ap':ap})
        if ap>best:
            best=ap;checkpoint={'model':'sage_no_messages' if no_messages else 'graphsage','seed':seed,'epoch':epoch,'dev_ap':best,'mean':mean.tolist(),'scale':scale.tolist(),'layers':[{'self':l.root.weight.detach().numpy().tolist(),'neighbor':l.neighbor.weight.detach().numpy().tolist(),'bias':l.root.bias.detach().numpy().tolist()} for l in model.layers]}
            # Export inference must reproduce the actual selected torch checkpoint.
            if not np.allclose(predict(checkpoint,dx,da),dev_scores,atol=1e-6):raise ValueError('EXPORT_PARITY_FAILED')
    return checkpoint,history,round(time.monotonic()-start,4)

def evaluate(y,s):
    r=metrics(y,s);r['average_precision']=r.pop('pr_auc')
    k=r['review_budget_k'];top=np.argsort(-np.asarray(s),kind='stable')[:k]
    r['precision_at_k']=float(np.asarray(y)[top].mean());return r

def experiment(out):
    import torch,networkx as nx
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    data={};split_manifest={}
    for split,seed in [('train',42),('dev',43),('test',44)]:
        graph,truth=generate(split,seed,60);nodes,x,g,a=prepare(graph);y=np.array([truth['accounts'][n] for n in nodes]);data[split]=(nodes,x,g,a,y)
        net=nx.Graph();net.add_edges_from((e['from'],e['to']) for e in graph['edges']);components=list(nx.connected_components(net))
        split_manifest[split]={'groups':len(components),'nodes':len(nodes),'positives':int(y.sum()),'edges':len(graph['edges']),'account_ids':nodes,'group_hashes':[digest(sorted(c)) for c in components],'observations_hash':digest(graph),'labels_hash':digest(truth)}
        (out/(split+'-observations.json')).write_text(json.dumps(graph));(out/(split+'-labels.json')).write_text(json.dumps(truth))
    for a,b in [('train','dev'),('train','test'),('dev','test')]:
        if set(data[a][0])&set(data[b][0]):raise ValueError('SPLIT_ACCOUNT_OVERLAP')
    challenge=ROOT/'eval/upgrade/graph';graph=json.loads((challenge/'structural-heldout-observations.json').read_text());truth=json.loads((challenge/'structural-heldout-labels.json').read_text());nodes,x,g,a=prepare(graph);data['structural_challenge']=(nodes,x,g,a,np.array([truth['accounts'][n] for n in nodes]))
    report={'task':'synthetic account ranking at 10% review budget','metric':'average_precision_score; not accuracy or trapezoidal PR-AUC','split_manifest':split_manifest,'seeds':[11,22,33],'seed_scope':'initialization variability on fixed data; not independent data draws','torch':torch.__version__,'python':platform.python_version(),'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),ROOT/'upgrade/graph_lab.py']},'challenge_hash':digest(graph),'results':{},'training':{},'default':'tabular','demo_sage_seed':11,'selection':'checkpoint by dev AP only; fixed seed11 demo; test never used for selection'}
    for model_name,index in [('tabular',1),('fixed_mean',2)]:
        model=HistGradientBoostingClassifier(max_iter=40,max_leaf_nodes=7,l2_regularization=2,random_state=42).fit(data['train'][index],data['train'][4]);report['results'][model_name]={}
        for split in ('test','structural_challenge'):
            s=model.predict_proba(data[split][index])[:,1];report['results'][model_name][split]=evaluate(data[split][4],s)
            (out/f'{model_name}-{split}-predictions.json').write_text(json.dumps(dict(zip(data[split][0],map(float,s)))))
    for name in ('graphsage','sage_no_messages'):
        report['results'][name]={};report['training'][name]={}
        for seed in report['seeds']:
            checkpoint,history,seconds=train(data['train'],data['dev'],seed,no_messages=name=='sage_no_messages')
            (out/f'{name}-{seed}-checkpoint.json').write_text(json.dumps(checkpoint));(out/f'{name}-{seed}-history.json').write_text(json.dumps(history))
            report['training'][name][seed]={'seconds':seconds,'selected_epoch':checkpoint['epoch'],'dev_ap':checkpoint['dev_ap']}
            for split in ('test','structural_challenge'):
                nodes,x,g,a,y=data[split];s=predict(checkpoint,x,a);report['results'][name].setdefault(split,[]).append({'seed':seed,**evaluate(y,s)})
                (out/f'{name}-{seed}-{split}-predictions.json').write_text(json.dumps(dict(zip(nodes,map(float,s)))))
        report['results'][name]['summary']={split:{key:{'mean':float(np.mean([r[key] for r in report['results'][name][split]])),'std':float(np.std([r[key] for r in report['results'][name][split]],ddof=1))} for key in ('average_precision','recall_at_k','precision_at_k')} for split in ('test','structural_challenge')}
    cp=out/'graphsage-11-checkpoint.json';(out/'demo-manifest.json').write_text(json.dumps({'sha256':hashlib.sha256(cp.read_bytes()).hexdigest(),'checkpoint':cp.name,'training_hash':split_manifest['train']['observations_hash'],'synthetic_only':True}))
    (out/'report.json').write_text(json.dumps(report,indent=2));return report

def score(graph,as_of,artifact_dir=None):
    path=Path(artifact_dir or ROOT/'eval/graphsage-v1/actual');manifest=path/'demo-manifest.json'
    if not manifest.exists():return {'status':'unavailable','reason':'GraphSAGE checkpoint missing; run experiment first'}
    meta=json.loads(manifest.read_text());cp=path/meta['checkpoint']
    if not cp.is_file() or hashlib.sha256(cp.read_bytes()).hexdigest()!=meta['sha256']:return {'status':'unavailable','reason':'GraphSAGE checkpoint hash mismatch'}
    nodes,edges,x,g,a=features(graph,as_of);a=a/np.maximum(a.sum(1,keepdims=True),1);s=predict(json.loads(cp.read_text()),x,a)
    return {'status':'ok','synthetic':True,'model':'graphsage','model_version':meta['sha256'],'rankings':sorted([{'account':n,'ranking_score':float(v)} for n,v in zip(nodes,s)],key=lambda r:(-r['ranking_score'],r['account'])),'notice':'训练型两层GraphSAGE；仅合成演练排序，不是诈骗概率或违法结论'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args();r=experiment(args.out);print(json.dumps({k:v.get('summary',v) for k,v in r['results'].items()},indent=2))
