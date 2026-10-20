import sys,json
from pathlib import Path
from types import SimpleNamespace
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'antifraud-rag'))
from dotenv import load_dotenv
import argparse
p=argparse.ArgumentParser();p.add_argument('--env',required=True);p.add_argument('--output',required=True);args=p.parse_args();load_dotenv(args.env)
from pipeline import Assessment
from evaluate_upgrade import Caller
from upgrade.grounding import audit_answer
out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
for name,path in [('normal','normal-demo-bf353905512244e2b33a56b6e06de689.json'),('email','tool-track/email-ced1d61357bb4bd38d71b6929b4e82a8.json')]:
 d=json.loads((root/'antifraud-rag/eval/upgrade'/path).read_text()); units={o['unit']['unit_id']:o['unit'] for t in d['tool_results'] for o in t['observations'] if 'unit' in o}; owner=Caller();legacy=SimpleNamespace(units=units,assessment=Assessment.model_validate(d['assessment']),data={'query':d['query']});r={'historical_run_id':d['run_id'],'historical_file':path,'method':'actual same-provider audit; exact source quote validation; not independent expert'}
 try:r['issues']=audit_answer(legacy,owner,d['answer']);r['rejected']=bool(r['issues'])
 except Exception as e:r.update(error=str(e),rejected=False,check_failed=True)
 r['records']=owner.records;(out/('history-'+name+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2));print(name,r.get('rejected'),r.get('error'),flush=True)
