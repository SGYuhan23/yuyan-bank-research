"""Export browser inputs and independent Python parity fixtures; never exports credentials."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'agent-ops/examples'))
sys.path.insert(0,str(ROOT/'agent-ops/research'))
from fuling import optimize_resources,candidate_actions
from supplier_ledger import simulate,evaluate,apply_command,derive_payment_conditions
raw=(ROOT/'agent-platform/frontend/public/research/v2.json').read_bytes();data=json.loads(raw)
out=ROOT/'site/data';out.mkdir(parents=True,exist_ok=True)
comparisons=[]
for key,value in [('annual_transaction_count',10000),('payroll_employee_count',500),('eligible_supply_chain_links',30),('relationship_contribution_fen',3000000)]:
 c=dict(id='COMPARE',sector='合成对照',deposit_fen=10000000,annual_transaction_count=0,payroll_employee_count=0,eligible_supply_chain_links=0,relationship_contribution_fen=0,attrition_scenario='0.5',source_fact_ids='ASSUMPTION')
 c[key]=value;comparisons.append(c)
payload={'source_sha256':hashlib.sha256(raw).hexdigest(),'fuling':{'customers':data['fuling']['customers'],'actions':data['fuling']['actions'],'comparisons':comparisons,'assumptions':'单价、采用率、成本、工时、25%行业工时约束均为研究假设，不是银行内部参数或监管限额。'},'supplier':{'initial_case':data['supplier']['initial_case']},'trace_path':'data/traces/supplier.json'}
(out/'demo-data.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
trace=json.loads((ROOT/'agent-platform/frontend/public/research/trace.json').read_text())
allow=['mock','status','model','recorded_at','actual_user_prompt','actual_followup_prompt','system_policy_summary','parameters_prespecified','confirmation_actor','original_model_proposal','harness_corrected_proposal','correction_summary','confirmed_request','tool','arguments','result','answer','boundary','redaction_note']
(out/'traces').mkdir(exist_ok=True)
(out/'traces/supplier.json').write_text(json.dumps({k:trace[k] for k in allow if k in trace},ensure_ascii=False,indent=2)+'\n')
# Tests compare current Python execution, not a manually maintained table of answers.
case=data['supplier']['initial_case'];expected={'fuling':[],'supplier':[],'compare':[]}
for hours in [50,150,220,600]:
 for cap in [None,.25]:
  r=optimize_resources(data['fuling']['actions'],hours,cap)
  expected['fuling'].append({'hours':hours,'cap':cap,'result':{k:r[k] for k in ['hours','benefit_fen','selected','sector_hours']}})
for customer,days in [('C1',0),('C1',14),('ALL',30),('C1',7),('C2',12),('ALL',15)]:
 expected['supplier'].append({'customer':customer,'days':days,'result':simulate(case,days,customer)})
expected['cost_scenarios']=[]
for args in [dict(customer_id='C1',delay_days=7,discount='0.025',fee_fen=12345,advance_fen=1234567),dict(customer_id='ALL',delay_days=15,discount='0.1',fee_fen=10000000,advance_fen=10000000)]:
 expected['cost_scenarios'].append({'parameters':args,'result':simulate(case,**args)})
for c in comparisons:expected['compare'].append(candidate_actions([c]))
contract=apply_command(case,dict(operation='reschedule',event_id='O1-acceptance',reason='合成合同演示',planned_date='2027-03-10'))
expected['contract']={e['event_id']:e['planned_date'] for e in contract['events']}
confirmed=apply_command(case,dict(operation='confirm',event_id='O1-materials',reason='合成付款确认',confirmed_date='2027-01-01',evidence='合成凭证'))
expected['reconcile_initial']=confirmed
expected['reconcile']=apply_command(confirmed,dict(operation='record_actuals_and_reconcile',event_id='BATCH',reason='合成付款核对',postings=[dict(event_id='O1-materials',posted_date='2027-01-08',evidence='合成付款凭证')],as_of='2027-01-09',observed_balance_fen=-10000000))
(ROOT/'site/tests/python-expected.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2)+'\n')
print('Exported synthetic browser inputs, allowlisted recorded trace and dynamic Python parity expectations')
