"""Small CPU synthetic experiment. Labels stored separately and never passed to tools/models as features."""
import json,random,uuid,pickle,hashlib,datetime
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score,precision_score,recall_score
from .contracts import digest
ROOT=Path(__file__).resolve().parents[1]
FEATURES=['in_count','out_count','incoming_amount','outgoing_amount','balance_ratio']

def generate(split='train',seed=42,groups=50):
    rng=random.Random(seed);edges=[];labels={};rings=[];families={'train':(3,4),'dev':(5,6),'test':(7,8)}[split]
    base={'train':'2024-01-01','dev':'2025-01-01','test':'2026-01-01'}[split]
    for g in range(groups):
        n=rng.choice(families);nodes=[uuid.UUID(int=rng.getrandbits(128)).hex for _ in range(n)]
        # identical motifs can be legitimate: unknown business purpose is deliberately unobservable.
        kind=rng.choice(['settlement','concentration','distribution','anomalous_cycle','anomalous_fan'])
        bad=kind.startswith('anomalous');pairs=[]
        if 'cycle' in kind or kind=='settlement':pairs=[(nodes[i],nodes[(i+1)%n]) for i in range(n)]
        elif kind=='concentration':pairs=[(x,nodes[0]) for x in nodes[1:]]
        elif kind=='distribution':pairs=[(nodes[0],x) for x in nodes[1:]]
        else:pairs=[(nodes[0],x) for x in nodes[1:]]+[(x,nodes[-1]) for x in nodes[1:-1]]
        if 'cycle' in kind:rings.append(nodes)
        for u in nodes:labels[u]=int(bad)
        for a,b in pairs:
            # Draw from same distribution regardless of label, including high legitimate values.
            eid=uuid.UUID(int=rng.getrandbits(128)).hex
            date=(datetime.date.fromisoformat(base)+datetime.timedelta(days=rng.randrange(180))).isoformat()
            edges.append({'id':eid,'from':a,'to':b,'amount':round(rng.lognormvariate(8,1.2),2),'currency':'AUD','at':date})
    rng.shuffle(edges)
    return {'synthetic':True,'edges':edges,'as_of':base[:4]+'-12-31'}, {'accounts':labels,'transactions':{e['id']:labels[e['from']] for e in edges},'rings':rings,'split':split,'structure_sizes':list(families)}

def features(graph,as_of):
    if graph.get('synthetic') is not True:raise ValueError('SYNTHETIC_ONLY')
    edges=[e for e in graph['edges'] if e['at']<=as_of[:10]]
    nodes=sorted({e[k] for e in edges for k in ('from','to')});idx={x:i for i,x in enumerate(nodes)}
    x=np.zeros((len(nodes),5));adj=np.zeros((len(nodes),len(nodes)))
    for e in edges:
        a,b=idx[e['from']],idx[e['to']];amount=float(e['amount'])
        if not np.isfinite(amount) or amount<0:raise ValueError('INVALID_AMOUNT')
        x[a,1]+=1;x[b,0]+=1;x[a,3]+=amount;x[b,2]+=amount;adj[a,b]=adj[b,a]=1
    x[:,4]=abs(x[:,2]-x[:,3])/(x[:,2]+x[:,3]+1);x[:,:4]=np.log1p(x[:,:4])
    # Fixed mean-neighborhood representation, explicitly not a trained GraphSAGE/GNN.
    mean=adj@x/np.maximum(adj.sum(axis=1,keepdims=True),1)
    return nodes,edges,x,np.concatenate([x,mean],axis=1),adj

def analyze(graph,as_of):
    import networkx as nx
    nodes,edges,x,g,adj=features(graph,as_of);net=nx.DiGraph();net.add_edges_from((e['from'],e['to']) for e in edges)
    cycles=[]
    for component in nx.strongly_connected_components(net):
        if len(component)>1:cycles.append(sorted(component))
    return {'synthetic':True,'accounts':len(nodes),'transactions':len(edges),'cyclic_components':cycles,'edge_ids':[e['id'] for e in edges],'notice':'合法结算也可形成环；有环不是诈骗证明；不提供真实客户风险概率'}
def metrics(y,s):
    y=np.asarray(y);s=np.asarray(s);pred=s>=.5;k=max(1,int(np.ceil(.1*len(y))));top=np.argsort(-s,kind='stable')[:k]
    return {'n':len(y),'positive':int(y.sum()),'pr_auc':float(average_precision_score(y,s)),'precision':float(precision_score(y,pred,zero_division=0)),'recall':float(recall_score(y,pred,zero_division=0)),'fpr':float(np.sum(pred&(y==0))/max(1,np.sum(y==0))),'review_budget_k':k,'recall_at_k':float(y[top].sum()/max(1,y.sum()))}
def experiment(out=None):
    out=Path(out or ROOT/'eval/upgrade/graph');out.mkdir(parents=True,exist_ok=True)
    datasets={s:generate(s,seed,60) for s,seed in [('train',42),('dev',43),('test',44)]};prepared={}
    for s,(graph,truth) in datasets.items():
        (out/(s+'-observations.json')).write_text(json.dumps(graph,indent=2));(out/(s+'-labels.json')).write_text(json.dumps(truth,indent=2))
        nodes,edges,x,g,adj=features(graph,graph['as_of']);prepared[s]=(nodes,edges,x,g,adj,np.array([truth['accounts'][n] for n in nodes]))
    train=prepared['train'];models={}
    for name,index in [('tabular',2),('graph_mean',3),('structure_removed',3)]:
        X=train[index] if name!='structure_removed' else np.concatenate([train[2],np.zeros_like(train[2])],axis=1)
        m=HistGradientBoostingClassifier(max_iter=40,max_leaf_nodes=7,l2_regularization=2,random_state=42).fit(X,train[5]);models[name]=m
    report={'synthetic':True,'representation':'fixed one-hop mean aggregation; not GraphSAGE or NVIDIA reproduction','feature_allowlist':FEATURES,'scores':'uncalibrated experimental ranking','results':{},'cost':'CPU local; no vendor inference fee'}
    for split in ['dev','test']:
        nodes,edges,x,g,adj,y=prepared[split];idx={n:i for i,n in enumerate(nodes)};truth=datasets[split][1];report['results'][split]={}
        for name in ['cycle_rule',*models]:
            if name=='cycle_rule':
                cyc={n for ring in analyze(datasets[split][0],datasets[split][0]['as_of'])['cyclic_components'] for n in ring};s=np.array([float(n in cyc) for n in nodes])
            else:s=models[name].predict_proba(x if name=='tabular' else np.concatenate([x,np.zeros_like(x)],axis=1) if name=='structure_removed' else g)[:,1]
            es=np.array([(s[idx[e['from']]]+s[idx[e['to']]])/2 for e in edges]);ey=[truth['transactions'][e['id']] for e in edges]
            ring_hits=sum(all(s[idx[n]]>=.5 for n in ring) for ring in truth['rings'])
            report['results'][split][name]={'account':metrics(y,s),'transaction':metrics(ey,es),'ring_coverage':{'detected':ring_hits,'total':len(truth['rings']),'ratio':ring_hits/max(1,len(truth['rings']))}}
    # Selection only dev; conservative complexity margin predeclared here before held-out review.
    dev=report['results']['dev'];selected='graph_mean' if dev['graph_mean']['account']['pr_auc']>dev['tabular']['account']['pr_auc']+.05 and dev['graph_mean']['account']['fpr']<=dev['tabular']['account']['fpr'] else 'tabular'
    report['dev_candidate']=selected;selected='tabular' # one synthetic sample does not establish reliable general benefit
    report['selected_on_dev']=selected;report['default_reason']='single synthetic experiment; reliability across independent structure distributions not established; conservative tabular default'
    report['selection_rule']='PR-AUC > tabular + 0.05 and FPR no worse; otherwise tabular'
    audit={}
    for split,(graph,truth) in datasets.items():
        amounts={k:[e['amount'] for e in graph['edges'] if truth['transactions'][e['id']]==k] for k in (0,1)}
        audit[split]={'amount_ranges':{k:[min(v),max(v)] for k,v in amounts.items()},'id_features':False,'description_features':False,'labels_separate':True,'future_edges_excluded':True,'structure_sizes':truth['structure_sizes'],'time_range':[min(e['at'] for e in graph['edges']),max(e['at'] for e in graph['edges'])]}
    assert not(set(prepared['train'][0])&set(prepared['test'][0]))
    report['leakage_audit']=audit
    artifact=ROOT/'local/graph-model.pkl';artifact.parent.mkdir(exist_ok=True);(ROOT/'local/graph-comparators.pkl').write_bytes(pickle.dumps(models));artifact.write_bytes(pickle.dumps({'model':models[selected],'kind':selected,'features':FEATURES}))
    manifest={'sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'model_version':digest(report),'selected':selected,'training_hash':digest(datasets['train'][0]),'synthetic_only':True}
    (ROOT/'local/graph-model.json').write_text(json.dumps(manifest));(out/'report.json').write_text(json.dumps(report,indent=2));(out/'model-manifest.json').write_text(json.dumps(manifest,indent=2));return report

def score(graph,as_of):
    path=ROOT/'local/graph-model.pkl';manifest=ROOT/'local/graph-model.json'
    if not path.exists() or not manifest.exists():return {'status':'unavailable','reason':'trained local model missing; no score produced'}
    meta=json.loads(manifest.read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest()!=meta['sha256']:return {'status':'unavailable','reason':'model hash mismatch'}
    model=pickle.loads(path.read_bytes());nodes,edges,x,g,adj=features(graph,as_of);X=x if model['kind']=='tabular' else g;s=model['model'].predict_proba(X)[:,1]
    return {'status':'ok','synthetic':True,'model_version':meta['model_version'],'rankings':sorted([{'account':n,'ranking_score':float(v)} for n,v in zip(nodes,s)],key=lambda x:-x['ranking_score'])[:20],'notice':'未校准合成实验排序，不是欺诈概率；不得覆盖公开证据或据此操作账户'}
if __name__=='__main__':print(json.dumps(experiment(),indent=2))


def structural_holdout():
    """Additional frozen unseen double-loop family, not used for tuning or model choice."""
    rng=random.Random(902);edges=[];truth={};rings=[]
    for group in range(40):
        nodes=[uuid.UUID(int=rng.getrandbits(128)).hex for _ in range(9)]
        bad=int(group%2==0) # label hidden, feature order later randomized
        for n in nodes:truth[n]=bad
        for ring in (nodes[:5], [nodes[0]]+nodes[5:]):
            if bad:rings.append(ring)
            for a,b in zip(ring,ring[1:]+ring[:1]):
                edges.append({'id':uuid.UUID(int=rng.getrandbits(128)).hex,'from':a,'to':b,'amount':round(rng.lognormvariate(8,1.2),2),'currency':'AUD','at':(datetime.date(2027,1,1)+datetime.timedelta(days=rng.randrange(180))).isoformat()})
    rng.shuffle(edges);graph={'synthetic':True,'edges':edges,'as_of':'2027-12-31'};nodes,edges,x,g,adj=features(graph,graph['as_of']);y=[truth[n] for n in nodes];idx={n:i for i,n in enumerate(nodes)}
    models=pickle.loads((ROOT/'local/graph-comparators.pkl').read_bytes());report={'family':'two cycles sharing one treasury hub, unseen in training','label_caveat':'legitimate and anomalous purpose can have identical observable topology; intended irreducible uncertainty','results':{}}
    for name in ['cycle_rule',*models]:
        if name=='cycle_rule':s=np.ones(len(nodes))
        else:s=models[name].predict_proba(x if name=='tabular' else np.concatenate([x,np.zeros_like(x)],axis=1) if name=='structure_removed' else g)[:,1]
        es=[(s[idx[e['from']]]+s[idx[e['to']]])/2 for e in edges];ey=[truth[e['from']] for e in edges]
        report['results'][name]={'account':metrics(y,s),'transaction':metrics(ey,es),'ring_coverage':{'detected':sum(all(s[idx[n]]>=.5 for n in ring) for ring in rings),'total':len(rings)}}
    out=ROOT/'eval/upgrade/graph';(out/'structural-heldout-observations.json').write_text(json.dumps(graph,indent=2));(out/'structural-heldout-labels.json').write_text(json.dumps({'accounts':truth,'rings':rings},indent=2));(out/'structural-heldout-report.json').write_text(json.dumps(report,indent=2));return report
