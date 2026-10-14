import importlib.util,itertools
from pathlib import Path
from decimal import Decimal
spec=importlib.util.spec_from_file_location('fuling_v2',Path(__file__).parent/'examples/fuling.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

def test_prototypes_are_experiment_not_market_share():
 a=f.prototypes();assert a==f.prototypes() and len(a)==120
 assert len({x['sector'] for x in a})==5
 assert all(x['source_fact_ids']=='FL-CLUSTERS' for x in a if x['sector']=='新能源汽车及零部件')
 assert all('并非重庆农商行或涪陵真实客户分布' in x['disclosure'] for x in a)
 assert len([r for r in f.prototypes(weights=(2,1,1,1,1)) if r['sector']==f.SECTORS_V2[0]])==40

def test_exact_optimizer_independent_enumeration():
 actions=[dict(id=str(i),customer_id=c,sector=s,service_hours=h,benefit_fen=v) for i,(c,s,h,v) in enumerate([('a','x',5,10),('a','x',10,22),('b','x',5,9),('c','y',10,12),('d','y',5,6)])]
 for cap,ratio in [(15,None),(20,'.5'),(0,None)]:
  valid=[]
  for bits in itertools.product([False,True],repeat=len(actions)):
   chosen=[a for a,b in zip(actions,bits) if b];h=sum(a['service_hours'] for a in chosen)
   if h>cap or len({a['customer_id'] for a in chosen})!=len(chosen):continue
   if ratio and h and any(sum(a['service_hours'] for a in chosen if a['sector']==s)>Decimal(ratio)*h for s in ['x','y']):continue
   valid.append(sum(a['benefit_fen'] for a in chosen))
  result=f.optimize_resources(actions,cap,ratio)
  assert result['benefit_fen']==max(valid) and result['hours']<=cap

def test_capacity_and_concentration_really_change_decisions():
 actions=f.candidate_actions(f.prototypes())
 normal=f.optimize_resources(actions,600);restricted=f.optimize_resources(actions,150)
 capped=f.optimize_resources(actions,150,'.25')
 assert len(restricted['selected'])<len(normal['selected'])
 assert restricted['benefit_fen']>capped['benefit_fen']
 assert restricted['selected']!=capped['selected']
 assert Decimal(capped['max_sector_share'])<=Decimal('.25')
 assert any(x['benefit_fen']>0 and x['customer_id'] not in {a['customer_id'] for a in actions if a['id'] in restricted['selected']} for x in restricted['rejected'])

def test_equal_balances_different_business_drivers_choose_different_actions():
 base=f.prototypes(count=1)[0]
 low={**base,'deposit_fen':10000000,'annual_transaction_count':0,'payroll_employee_count':0,'eligible_supply_chain_links':0,'relationship_contribution_fen':0,'attrition_scenario':'0'}
 examples=[({**low,'annual_transaction_count':10000},'结算深化',600000),({**low,'payroll_employee_count':500},'代发/支付场景',600000),({**low,'eligible_supply_chain_links':30},'供应链上下游连接',840000),({**low,'relationship_contribution_fen':3000000,'attrition_scenario':'.5'},'客户经营维护',600000)]
 for customer,kind,gross in examples:
  actions=f.candidate_actions([customer]);winner=max(actions,key=lambda a:a['benefit_fen'])
  assert winner['action_type']==kind and winner['expected_benefit_fen']==gross
  assert f.optimize_resources(actions,25)['selected']==[winner['id']]
  assert all(a['business_drivers'] and a['value_formula'] and a['evidence_requirement'] and a['stop_condition'] and a['evidence_type']=='ASSUMPTION' for a in actions)
 assert len({e[0]['deposit_fen'] for e in examples})==1
