"""Frozen small held-out comparisons. References never enter generation; raw failures retained."""
import argparse,json,time,hashlib,random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pipeline import RagRun,SYSTEM,ROOT
from retrieval import retrieve
from upgrade.contracts import CaseRecord,now,digest,uid
from upgrade.store import Store
from upgrade.agent import Agent
class Caller:
 model=RagRun.model
 def __init__(self):self.records=[]
 def log(self,kind,**data):self.records.append({'kind':kind,**data})
 def answer(self,q,docs):return self.model([{'role':'system','content':SYSTEM+'\n简明回答当前任务，只输出JSON {"answer":str,"sources":[str],"unknowns":[str]}。'},{'role':'user','content':json.dumps({'question':q,'untrusted_materials':docs},ensure_ascii=False)}],'baseline_answer')
def freeze(out):
 paths=[ROOT/'pipeline.py',ROOT/'retrieval.py',*sorted((ROOT/'upgrade').glob('*.py')),ROOT/'eval/upgrade/cases.json']
 f={'at':now(),'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'temperature':0,'max_tokens':6500,'model_source':'QWEN_MODEL same environment for all','price':'unknown; no cost estimate','repetitions':1}
 p=out/'freeze.json'
 if p.exists():
  if json.loads(p.read_text())['files']!=f['files']:raise ValueError('FROZEN_CODE_CHANGED_USE_NEW_BATCH')
 else:p.write_text(json.dumps(f,indent=2))
def run_case(case,out):
 store=Store(ROOT/'local/evaluation.sqlite');q=case['query'];rows=[];observations=[]
 for system in ['direct','all','retrieved','fixed','tools','same_observations']:
  dest=out/(case['id']+'-'+system+'.json')
  if dest.exists():rows.append(json.loads(dest.read_text()));continue
  row={'id':uid(),'case_id':case['id'],'family':case['family'],'system':system,'query':q,'started_at':now(),'cost':None,'cost_reason':'dated model prices not verified'};start=time.monotonic();caller=Caller()
  try:
   if system=='tools':
    c=store.create(CaseRecord(query=q,requester_role=case['role']));agent=Agent(store,c.case_id,1);r=agent.run();observations=r['tool_results'];row.update(status=r['status'],output={k:r.get(k) for k in ('summary','recommendations','unresolved_questions','limitations','error')},trace=r,records=r['records'])
   elif system=='fixed':
    r=RagRun(q).run();row.update(status=r['status'],output=r.get('result'),run_id=r['run_id'],records=r['records'])
   else:
    if system=='all':docs=json.loads((ROOT/'data/units.json').read_text())
    elif system=='retrieved':docs=[x['unit'] for x in retrieve(q,'auto',log=caller.log)]
    elif system=='same_observations':
     if not observations:
      prior=json.loads((out/(case['id']+'-tools.json')).read_text());observations=prior['trace']['tool_results']
     docs=observations
    else:docs=[]
    answer=caller.answer(q,docs);row.update(status='completed',output=answer,records=caller.records)
  except Exception as e:row.update(status='failed',error=type(e).__name__+': '+str(e)[:250],records=caller.records)
  row['seconds']=round(time.monotonic()-start,3);dest.write_text(json.dumps(row,ensure_ascii=False,indent=2));rows.append(row);print(case['id'],system,row['status'],flush=True)
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--env');p.add_argument('--batch',default='heldout-v1');a=p.parse_args()
 if a.env:load_dotenv(a.env)
 out=ROOT/'eval/upgrade'/a.batch;out.mkdir(exist_ok=True);freeze(out)
 cases=json.loads((ROOT/'eval/upgrade/cases.json').read_text())
 with ThreadPoolExecutor(max_workers=2) as pool: rows=[r for group in pool.map(lambda c:run_case(c,out),cases) for r in group]
 random.Random(914).shuffle(rows)
 (out/'blind.json').write_text(json.dumps([{'id':r['id'],'query':r['query'],'output':r.get('output'),'status':r['status']} for r in rows],ensure_ascii=False,indent=2))
 (out/'key.json').write_text(json.dumps([{'id':r['id'],'case_id':r['case_id'],'system':r['system']} for r in rows],indent=2))
 summary={}
 for r in rows:
  s=summary.setdefault(r['system'],{'n':0,'completed':0,'seconds':0,'model_calls':0,'input_tokens':0,'output_tokens':0,'cost':None});s['n']+=1;s['completed']+=r['status'] in ('completed','pending_review');s['seconds']+=r['seconds']
  for rec in r['records']:
   if rec['kind']=='model_call':
    s['model_calls']+=1;u=rec.get('usage') or {};s['input_tokens']+=u.get('prompt_tokens',0);s['output_tokens']+=u.get('completion_tokens',0)
 (out/'execution-summary.json').write_text(json.dumps(summary,indent=2))
