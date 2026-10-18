from pathlib import Path
import json,datetime
from dotenv import load_dotenv
from retrieval import retrieve,ROOT
load_dotenv(ROOT.parents[1]/'yuqi-core/.env')
cases=json.loads((ROOT/'eval/cases.json').read_text());out=[]
for mode in ['bm25','semantic']:
 for c in cases:
  try:
   results=retrieve(c['query'],mode);ids=[r['unit']['unit_id'] for r in results];expected=c['relevant'];out.append(dict(id=c['id'],mode=mode,ids=ids,scores=[r['score'] for r in results],recall_at_3=len(set(ids)&set(expected))/len(expected) if expected else None,error=None))
  except Exception as e:out.append(dict(id=c['id'],mode=mode,error=str(e)));break
 (ROOT/'eval/retrieval-results.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'results':out},ensure_ascii=False,indent=2))
 print(mode,[(x['id'],x.get('recall_at_3'),x['error']) for x in out if x['mode']==mode],flush=True)
