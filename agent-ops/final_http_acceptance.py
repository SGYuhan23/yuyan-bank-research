"""HTTP semantic binding and atomic rollback; no model call; authentic local principal."""
import json,uuid
from client import client,ROOT
c=client();base='/api/plugins/yuyan.research/actions/'
def action(name,p):
 r=c.post(base+name,json=p);r.raise_for_status();return r.json()
case=action('create',{'key':'final-http-'+uuid.uuid4().hex});cid=case['case_id']
p=action('propose_scenario',dict(request_id=uuid.uuid4().hex,case_id=cid,base_version=1,customer_id='C1',delay_days=14,discount='0',fee_fen=0,advance_fen=0));rid=p['request']['request_id']
assert c.post(base+'simulate',json={'request_id':rid}).status_code==422
action('confirm_scenario',{'request_id':rid,'snapshot':p['request']});r=action('simulate',{'request_id':rid});assert r['scenario']['negative_days']==52 and r['request']['customer_id']=='C1'
action('invalidate_scenario',{'request_id':rid});assert c.post(base+'simulate',json={'request_id':rid}).status_code==422
cmd={'case_id':cid,'version':1,'key':uuid.uuid4().hex,'command':{'operation':'record_actuals_and_reconcile','event_id':'batch','reason':'合成实际收付验收','as_of':'2027-01-09','observed_balance_fen':0,'postings':[{'event_id':'HTTP-actual-fee','posted_date':'2027-01-08','evidence':'合成付款凭证','new_event':{'order_id':'O1','event_type':'fee','amount_fen':-1000,'source':'合成流水'}}]}}
failed=action('change',cmd);assert failed['committed'] is False and failed['error']['difference_fen']==-19999000
assert action('get',{'case_id':cid})==case
cmd['command']['observed_balance_fen']=19999000
result=action('change',cmd);assert result['case']['version']==2 and result['calculation']['actual_balance_fen']==19999000
assert action('change',cmd)==result
assert c.post(base+'change',json={**cmd,'version':2,'key':uuid.uuid4().hex}).status_code==422
out={'unconfirmed_rejected':True,'confirmed_snapshot_bound':True,'input_invalidation_rejected':True,'mismatch_difference_fen':failed['error']['difference_fen'],'mismatch_fully_rolled_back':True,'atomic_success':True,'idempotent_repeat':True,'duplicate_posted_rejected':True}
(ROOT/'agent-ops/research/evidence-final/http.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
