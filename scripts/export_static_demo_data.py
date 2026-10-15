"""Export browser inputs and independent Python parity fixtures; never exports credentials."""
from pathlib import Path
import sys,json,hashlib,re
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
def select(row, fields):
 return {k:row[k] for k in fields if k in row}
customer_fields=('id','sector','deposit_fen','annual_transaction_count','payroll_employee_count','eligible_supply_chain_links','relationship_contribution_fen','attrition_scenario')
action_fields=('id','customer_id','sector','action_type','service_hours','expected_benefit_fen','implementation_cost_fen','benefit_fen','value_formula','business_drivers','stop_condition','evidence_requirement')
case=select(data['supplier']['initial_case'],('version','opening_fen','opening_date','as_of','necessary_expenses_complete','orders','events','history'))
case['orders']=[select(o,('order_id','customer_id','name','order_amount_fen','payment_terms')) for o in case['orders']]
case['events']=[select(e,('event_id','order_id','event_type','planned_date','confirmed_date','posted_date','amount_fen','status','evidence','prediction_confidence')) for e in case['events']]
payload={'source_sha256':hashlib.sha256(raw).hexdigest(),'fuling':{'customers':[select(c,customer_fields) for c in data['fuling']['customers']],'actions':[select(a,action_fields) for a in data['fuling']['actions']],'comparisons':[select(c,customer_fields) for c in comparisons],'assumptions':'单价、采用率、成本、工时、25%行业工时约束均为研究假设，不是银行内部参数或监管限额。'},'supplier':{'initial_case':case},'trace_path':'data/traces/supplier.json'}
def public_ids(value):
 if isinstance(value,str):return re.sub(r'SYN-V2-(\d+)',r'CUST-\1',value)
 if isinstance(value,list):return [public_ids(v) for v in value]
 if isinstance(value,dict):return {k:public_ids(v) for k,v in value.items()}
 return value
payload=public_ids(payload)
(out/'demo-data.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
# The canonical recorded call is a separately reviewed public evidence artifact.
# Never overwrite it with the older research trace during a data rebuild.
trace_path=out/'traces/supplier.json'
if not trace_path.exists():raise RuntimeError('Canonical supplier trace missing')
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
