"""Real follow-up checks; all-source baseline, raw results, no model-graded accuracy."""
import sys,json,time,hashlib,argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
from upgrade.agent import Agent
from upgrade.store import Store
from upgrade.contracts import CaseRecord,now
from evaluate_upgrade import Caller
CASES=[
 ('seller','我是卖收藏品的，买家发来转账截图，交货之前应该核对什么？','卖方收款'),
 ('normal','我是企业付款方，包装供应商变更收款账户，我们已经通过原先留档电话口头确认本次变更。请说明建议的适用范围与证据限制。','企业付款'),
 ('unpaid','维修公司说没收到我们上周已经付过的维修费，催我们重付，该核实什么？','已付款企业'),
 ('investment','有人邀请我投资，发来机构登记截图与专业网页，这能证明本次邀约真实吗？','投资邀约接收人'),
 ('unsupported','请给出Westpac内部冻结账户的审批层级与处理时限。','培训学员'),
 ('comparison','分别说明卖家核对买家到账，与企业核实供应商账户变更的区别。','多个场景比较')]
def run(row,out):
 name,q,role=row;store=Store(ROOT/'local/repair-followup.sqlite');c=store.create(CaseRecord(query=q,requester_role=role));a=Agent(store,c.case_id,1);r=a.run();(out/(name+'-agent-'+a.id+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2));print(name,'agent',r['status'],r.get('error'),flush=True)
 caller=Caller();t=time.monotonic()
 try:baseline={'output':caller.answer(q,json.loads((ROOT/'data/units.json').read_text())),'status':'completed'}
 except Exception as e:baseline={'status':'failed','error':str(e)}
 baseline.update(query=q,records=caller.records,seconds=time.monotonic()-t);(out/(name+'-baseline.json')).write_text(json.dumps(baseline,ensure_ascii=False,indent=2));print(name,'baseline',baseline['status'],flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--env',required=True);p.add_argument('--batch',required=True);args=p.parse_args();load_dotenv(args.env);out=Path(__file__).parent/args.batch;out.mkdir()
 files=[ROOT/'pipeline.py',ROOT/'retrieval.py',*sorted((ROOT/'upgrade').glob('*.py'))]
 (out/'freeze.json').write_text(json.dumps({'at':now(),'cases':CASES,'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'scope':'six authored follow-up development cases, not external held-out benchmark; same Qwen; one sample each'},ensure_ascii=False,indent=2))
 with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(lambda row:run(row,out),CASES))
