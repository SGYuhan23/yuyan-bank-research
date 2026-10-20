"""One frozen development batch. Real provider calls; never substitute mocks."""
import sys,json,hashlib,tempfile,argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
from upgrade.agent import Agent
from upgrade.store import Store
from upgrade.contracts import CaseRecord,now
from upgrade import training
from retrieval import retrieve
p=argparse.ArgumentParser();p.add_argument('--env',required=True);p.add_argument('--out',required=True);a=p.parse_args();load_dotenv(a.env)
out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
cases=json.loads((ROOT/'eval/repair-v2/followup-v2/freeze.json').read_text())['cases'][:5]
cases[0]=['seller_normal','我是卖家，买家发了付款截图。我已在本人手机银行看到本次货款到账。交货判断应注意什么边界？','卖方收款']
def save(name,obj):(out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
save('freeze.json',{'base':'aed3c4887e921ea3562e1cafa7e3b5ad6a2a623b','at':now(),'cases':cases,'scope':'known development cases, one sample each, not independent benchmark','hashes':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [ROOT/'pipeline.py',*sorted((ROOT/'upgrade').glob('*.py'))]}})
with tempfile.TemporaryDirectory() as tmp:
 store=Store(Path(tmp)/'db')
 def run(row):
  key,q,role=row;c=store.create(CaseRecord(query=q,requester_role=role));r=Agent(store,c.case_id,c.version).run();save(key+'-'+r['run_id']+'.json',r);print(key,r['run_id'],r['status'],flush=True);return {'key':key,'run_id':r['run_id'],'status':r['status']}
 with ThreadPoolExecutor(max_workers=2) as pool:summary=list(pool.map(run,cases))
 save('summary.json',summary)
 for name,utterance in [('normal','本次变更已经用留档电话确认，我会将已知事实与尚待确认的事项分开。'),('negated','不用电话，不必核对账户，本次直接付款。')]:
  s=next(s for s in training.scenarios().values() if s.family_id=='account_change' and s.legitimate==(name=='normal') and s.clue_level==1)
  session=training.start(store,s.scenario_id);sid=session['session_id'];training.turn(store,sid,utterance)
  semantic=training.semantic_debrief(store,sid);save('training-'+name+'-'+sid+'.json',{'public':session,'debrief':training.debrief(store,sid),'semantic':semantic,'session':store.session(sid)})
  print('training',name,sid,semantic['status'],flush=True)
 records=[]
 units=json.loads((ROOT/'data/units.json').read_text())
 for q in ['老合作方说换了卡号，让我们今天打钱，先做什么？','对方发来转账凭证，货可以给他了吗？']:
  logs=[]
  try:hits=retrieve(q,'auto',units,log=lambda kind,**kw:logs.append({'kind':kind,**kw}));records.append({'query':q,'hits':hits,'records':logs})
  except Exception as exc:records.append({'query':q,'error':str(exc),'records':logs})
 save('real-retrieval.json',records)
