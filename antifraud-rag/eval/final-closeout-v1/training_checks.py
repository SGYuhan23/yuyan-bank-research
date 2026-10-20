"""Final training dataflow verification, real Qwen reviewer; no answer scoring."""
import sys,json,tempfile,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
from dotenv import load_dotenv
load_dotenv(sys.argv[1])
from upgrade import training
from upgrade.store import Store
out=Path(sys.argv[2]);out.mkdir(exist_ok=False,parents=True)
with tempfile.TemporaryDirectory() as tmp:
 store=Store(Path(tmp)/'db');rows=[]
 for s in training.scenarios().values():
  info=training.start(store,s.scenario_id);rows.append({'public':info['scenario'],'authored_truth_for_review_only':s.latent_truth,'debrief_before_turn':training.debrief(store,info['session_id'])})
 (out/'all18.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 for name,normal,text in [('normal',True,'我会依据已通过留档电话确认的本次变更处理，不把无关付款一并暂停。'),('negated',False,'不用电话，不必核对账户，本次直接付款。')]:
  s=next(s for s in training.scenarios().values() if s.family_id=='account_change' and s.legitimate==normal and s.clue_level==1)
  start=training.start(store,s.scenario_id);sid=start['session_id'];training.turn(store,sid,text)
  semantic=training.semantic_debrief(store,sid)
  result={'session_id':sid,'scenario':start['scenario'],'learner_context':training.learner_context(store,sid),'debrief':training.debrief(store,sid),'semantic':semantic,'training_code_hash':hashlib.sha256((root/'upgrade/training.py').read_bytes()).hexdigest()}
  (out/(name+'-'+sid+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(name,sid,semantic['status'],flush=True)
