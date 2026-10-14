"""Shared deterministic V2 bundle, called by the existing build_data pipeline."""
import json,sys,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
from fuling import prototypes,candidate_actions,optimize_resources,DISCLOSURE_V2
from supplier_ledger import fixture,evaluate,simulate
from decimal import Decimal
from models import rounded,deposit_case,deposit_grid

def build_v2(out):
 rows=prototypes();actions=candidate_actions(rows);allocations=[]
 for name,cap,reason in [('正常产能',600,'3人×1000小时，存量维护2100小时、合规/行政300小时，剩余600；均为预算假设'),('受限产能',150,'额外风险排查450小时，新增经营预算由600降至150；人为压力实验，不是预测')]:
  for limit in [None,'.25']:
   a=optimize_resources(actions,cap,limit);a.update(name=name,reason=reason,constraint='不设行业上限' if limit is None else '单行业≤实际分配工时25%（研究假设）');allocations.append(a)
 facts=json.loads(Path(__file__).with_name('fuling_public_facts.json').read_text())
 sensitivity=[]
 for rate in ('1','.75','.5'):
  adjusted=[{**a,'benefit_fen':rounded(Decimal(a['expected_benefit_fen'])*Decimal(rate))-a['implementation_cost_fen']} for a in actions]
  x=optimize_resources(adjusted,150,'.25');x['realization_rate']=rate;sensitivity.append(x)
 case=fixture();base=evaluate(case)
 data={'version':'2026-10-14.final-p0','fuling':{'disclosure':DISCLOSURE_V2,'facts':facts,'customers':rows,'actions':actions,'allocations':allocations,'sensitivity':sensitivity},'supplier':{'initial_case':case,'base':base,'delay14':simulate(case,14),'core_customer_stress':simulate(case,30),'all_customer_stress':simulate(case,30,'ALL')},'deposit':{'base':deposit_case(),'grid':deposit_grid()},'roles':[{'role':'Agent / LLM','work':'资料搜索、信息抽取、来源整理、问题拆解、自然语言解释与文件交付'},{'role':'Deterministic Engine','work':'金额、日期、现金曲线、资源优化、敏感性分析和图表数据'},{'role':'Human Decision','work':'参数确认、经营判断、客户策略、授信与风险审批'}]}
 (out/'v2.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 (out/'fuling_public_facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2))
 for name,items in [('fuling-v2-customers',rows),('fuling-v2-actions',actions)]:
  with (out/(name+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=items[0].keys());w.writeheader();w.writerows(items)
 return data
