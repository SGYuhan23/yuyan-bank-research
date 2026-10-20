import sys,json,time
from pathlib import Path
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'antifraud-rag'))
from dotenv import load_dotenv
import argparse
p=argparse.ArgumentParser();p.add_argument('--env',required=True);p.add_argument('--output',required=True);args=p.parse_args();load_dotenv(args.env)
from retrieval import retrieve
out=Path(args.output)
if out.exists():raise ValueError('OUTPUT_ALREADY_EXISTS')
out.parent.mkdir(parents=True,exist_ok=True)
cases=[('老合作方说换了卡号，让我们今天打钱，先做什么？','bec-guidance'),('对方发来转账凭证，货可以给他了吗？','receipt-guidance'),('买家给了打款截图，现在能发货吗？','receipt-guidance'),('一直合作的厂家突然通知用新银行卡收钱，如何确认？','bec-guidance'),('我是卖二手机床的，对方给我银行转款图片但我还没查自己的账户，能装车交付吗？','receipt-guidance'),('供应商说上周的货款没收到，现在催我再付一次，该核实什么？','bec-guidance')]
rows=[]
for q,expected in cases:
 for mode in ['bm25','auto','semantic']:
  logs=[];t=time.monotonic();r={'query':q,'expected':expected,'mode':mode}
  try:
   hits=retrieve(q,mode,log=lambda kind,**kw:logs.append({'kind':kind,**kw}));ids=[h['unit']['unit_id'] for h in hits];r.update(ids=ids,hit=expected in ids,status='completed')
  except Exception as e:r.update(status='failed',error=str(e))
  r.update(logs=logs,seconds=time.monotonic()-t);rows.append(r)
out.write_text(json.dumps({'scope':'6 development queries; 18 searches; real query embeddings; document embeddings cache may be reused; recall is not answer accuracy','rows':rows},ensure_ascii=False,indent=2));print([(m,sum(x.get('hit',False) for x in rows if x['mode']==m)) for m in ['bm25','auto','semantic']])
