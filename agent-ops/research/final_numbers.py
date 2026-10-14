"""Small current evidence summary, generated from the canonical output and pure functions."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'agent-ops/examples'))
from fuling import prototypes,candidate_actions
x=json.loads((ROOT/'agent-platform/frontend/public/research/v2.json').read_text())
base={**prototypes(count=1)[0],'deposit_fen':10000000,'annual_transaction_count':0,'payroll_employee_count':0,'eligible_supply_chain_links':0,'relationship_contribution_fen':0,'attrition_scenario':'0'}
changes=[{'annual_transaction_count':10000},{'payroll_employee_count':500},{'eligible_supply_chain_links':30},{'relationship_contribution_fen':3000000,'attrition_scenario':'.5'}]
comparisons=[]
for change in changes:
 c={**base,**change};winner=max(candidate_actions([c]),key=lambda a:a['benefit_fen']);comparisons.append({'same_deposit_fen':c['deposit_fen'],'changed_drivers':change,'priority_action':winner})
r={'version':x['version'],'same_balance_different_business_drivers':comparisons,
 'fuling':[{k:a[k] for k in ['name','constraint','hours','benefit_fen','max_sector_share','sector_hours']}|{'selected_count':len(a['selected'])} for a in x['fuling']['allocations']],
 'supplier':{k:{n:x['supplier'][k][n] for n in ['actual_balance_fen','peak_gap_fen','minimum_date','negative_days','closing_fen','evidence_completeness','concentration']} for k in ['base','delay14','core_customer_stress','all_customer_stress']},'deposit':x['deposit']['base']}
(ROOT/'agent-ops/research/evidence-final/key-numbers.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps({'fuling':r['fuling'],'same_balance_actions':[{'action':c['priority_action']['action_type'],'net_fen':c['priority_action']['benefit_fen']} for c in comparisons]},ensure_ascii=False))
