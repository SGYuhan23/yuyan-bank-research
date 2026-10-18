"""Real embedding/model checks, separate from network-mocked unit tests."""
from pathlib import Path
import json,datetime,hashlib
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pipeline import ROOT,RagRun,write
from retrieval import retrieve
load_dotenv(ROOT.parents[1]/'yuqi-core/.env')
OUT=ROOT/'eval/closeout';OUT.mkdir(exist_ok=True)
checks=[('colloquial-account','老合作方说换了卡号，让我们今天打钱，先做什么？','bec-guidance'),('colloquial-receipt','对方发来转账凭证，货可以给他了吗？','receipt-guidance'),('paraphrase-account','熟人来信说收钱的卡换了，催着赶紧汇过去，要怎么确认？','bec-guidance'),('paraphrase-receipt','买家把汇款截屏给我了，我现在就发货行吗？','receipt-guidance')]
retrieval=[]
for label,q,expected in checks:
 events=[]
 try:
  hits=retrieve(q,log=lambda kind,**d:events.append({'kind':kind,**d}));ids=[h['unit']['unit_id'] for h in hits]
  retrieval.append(dict(id=label,query=q,expected=expected,unit_ids=ids,passed=expected in ids,events=events))
 except Exception as e:retrieval.append(dict(id=label,query=q,error=str(e),passed=False,events=events))
write(OUT/'real-retrieval.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'real existing embedding provider, no mock; auto default','results':retrieval})
tasks=[('colloquial-account',checks[0][1],'knowledge'),('colloquial-receipt',checks[1][1],'knowledge'),('normal','熟悉的供应商发邮件说更换收款账户，应该核实什么？','knowledge'),('training','为新入职客服生成一份收款账户变更场景的培训材料，并说明John公开案例中最初17,000澳元与超过30,000澳元损失的关系。','training'),('unrelated','火星上种土豆的最佳温度是多少？','knowledge')]
def run(t):
 name,q,task=t;r=RagRun(q,task).run();print(name,r['status'],r.get('error'),flush=True)
 return {'id':name,'run_id':r['run_id'],'status':r['status'],'error':r.get('error'),'assessment':r.get('assessment'),'path':[x for x in r['records'] if x['kind'].startswith('retrieval_')]}
with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,tasks))
write(OUT/'real-pipeline.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'actual default auto RagRun; no mock; author review separate','results':results})
