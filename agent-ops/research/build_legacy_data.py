"""Build a shared evidence/computation bundle for reports and interactive pages."""
import csv,json,sys,math
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'agent-ops/examples'))
from fuling import customers,calculate,STRATEGIES,STRESSES
from models import supplier_case,deposit_case,deposit_grid,allocate_actions,cents,rounded
OUT=ROOT/'output/archive/research-v1'
OUT.mkdir(parents=True,exist_ok=True)
rows=customers();base=calculate(rows,STRATEGIES[0],STRESSES[0],3)
actions=[]
for row in rows:
    extra_deposit=Decimal(str(row['deposit']))*Decimal('.15')
    # No new loans. Settlement/deposit relationship action; gross benefit then fixed delivery cost.
    benefit=extra_deposit*(Decimal('.02')-Decimal(str(row['deposit_rate'])))+Decimal(str(row['fee']))*Decimal('.25')-Decimal('.05')
    actions.append({'id':row['id'],'sector':row['sector'],'hours':max(4,math.ceil(row['hours']*.30)),'benefit_fen':rounded(benefit*1000000),'incremental_deposit_wan':float(extra_deposit),'delivery_cost_wan':.05})
capacity=math.floor(3000-base['hours']);allocation=allocate_actions(actions,capacity)
allocation.update(capacity_hours=capacity,base_hours=base['hours'],base_contribution_wan=base['contribution'],total_contribution_wan=round(base['contribution']+allocation['benefit_fen']/1000000,2),assumption='15%新增存款、25%手续费增长、额外服务成本500元/户、30%新增工时；不增加授信')
scenarios=[calculate(rows,s,t,3) for s in STRATEGIES for t in STRESSES]
supplier=[]
for pre in ['.2','.3','.4','.5']:
 for delay in [0,14,30]:
  for discount in ['0','.01','.02']:
   for fee in ['0','1000']:
    supplier.append(supplier_case(pre,delay,discount,fee))
data={'version':'2026-10-13.research-v1','sources':json.loads((Path(__file__).parent/'sources.json').read_text()),'fuling':{'base':base,'scenarios':scenarios,'allocation':allocation,'actions':actions,'customers':rows},'supplier':{'base':supplier_case(),'cases':supplier},'deposit':{'base':deposit_case(),'grid':deposit_grid()}}
(OUT/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
for name,items in [('fuling-customers',rows),('fuling-strategies',scenarios),('fuling-actions',actions),('deposit-sensitivity',data['deposit']['grid']),('supplier-scenarios',[{k:v for k,v in x.items() if k!='series'} for x in supplier])]:
 with (OUT/(name+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=items[0].keys());w.writeheader();w.writerows(items)
(OUT/'models.py').write_text((Path(__file__).parent/'models.py').read_text())
(OUT/'sources.json').write_text((Path(__file__).parent/'sources.json').read_text())
print(json.dumps({'allocation':allocation,'supplier_cases':len(supplier),'deposit_cases':len(data['deposit']['grid'])},ensure_ascii=False))

