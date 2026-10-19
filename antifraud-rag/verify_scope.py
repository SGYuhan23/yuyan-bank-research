"""Actual existing-provider runs, including historical bad-output audit, never mock."""
import json
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pipeline import ROOT,RagRun,write,Assessment,TaskScene,scope_review_passes
load_dotenv(ROOT.parents[1]/'yuqi-core/.env')
OUT=ROOT/'eval/scope'
old=[('e939b58bd6e64512','seller_receipt'),('4b48fa8dbff54fc4','account_change'),('88a6b108e1604ba6','account_change')]
def audit(item):
 rid,scene=item;d=json.loads((ROOT/'runs'/rid/'run.json').read_text());run=RagRun(d['query'],d['task']);run.units={x['unit_id']:x for x in d['result']['sources']};run.calculations=[];run.assessment=Assessment(sufficient=True,relevant_ids=list(run.units),missing=[],conflicts=[],task_scenes=[TaskScene(scene=scene,question_basis=d['query'])]);run.data['audit_of_historical_run']=rid
 verdict=run.review_scope(d['result']['answer']);run.data['status']='audit_completed';run.data['audit_verdict']=verdict;run.save();return {'old_run':rid,'audit_run':run.id,'verdict':verdict,'accepted_by_runtime':scope_review_passes(verdict,len(d['result']['answer']['steps']),d['result']['answer'],[scene])}
with ThreadPoolExecutor(max_workers=3) as pool:audits=list(pool.map(audit,old))
write(OUT/'historical-audits.json',{'method':'actual current semantic scope reviewer on unchanged historical final answers, no mock','results':audits})
print('historical',[(x['old_run'],x['verdict']['pass']) for x in audits],flush=True)
tasks=[('seller','对方发来转账凭证，货可以给他了吗？','knowledge'),('change','老合作方说换了卡号，让我们今天打钱，先做什么？','knowledge'),('unreceived','供应商说上周的货款没收到，现在催我再付一次，该核实什么？','knowledge'),('training','生成供应商收款账户变更的新员工培训材料。','training'),('compare','分别说明卖家核对买家到账，与企业核实供应商账户变更的区别。','knowledge'),('seller-paraphrase','买家给了汇款截屏，我现在就把货寄走吗？','knowledge'),('change-paraphrase','熟人来信说收钱的卡换了，催着赶紧汇过去，要怎么确认？','knowledge'),('amount','生成供应商收款账户变更培训材料，并说明John案例17,000澳元与超过30,000澳元损失的关系。','training'),('unrelated','火星种土豆的最佳温度是多少？','knowledge')]
def execute(item):
 label,q,task=item;r=RagRun(q,task).run();print(label,r['status'],r.get('error'),flush=True);return {'id':label,'run_id':r['run_id'],'status':r['status'],'error':r.get('error')}
with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(execute,tasks))
write(OUT/'real-results.json',{'method':'actual auto RAG with current Qwen configuration; no mock; human/source review separate','results':results})
