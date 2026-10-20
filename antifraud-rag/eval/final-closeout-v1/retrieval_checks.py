import sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
from dotenv import load_dotenv
load_dotenv(sys.argv[1])
from retrieval import retrieve
rows=[]
for q in ['老合作方说换了卡号，让我们今天打钱，先做什么？','对方发来转账凭证，货可以给他了吗？']:
 logs=[]
 try:
  hits=retrieve(q,'auto',log=lambda kind,**kw:logs.append({'kind':kind,**kw}))
  rows.append({'query':q,'hit_unit_ids':[x['unit']['unit_id'] for x in hits],'records':logs,'execution':'real query embedding API, existing document vector cache allowed'})
 except Exception as e:rows.append({'query':q,'error':str(e),'records':logs})
p=Path(sys.argv[2]);p.open('x').write(json.dumps(rows,ensure_ascii=False,indent=2));print(json.dumps(rows,ensure_ascii=False))
