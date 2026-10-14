"""Render authoritative financial answers only from successful tool output.
The LLM chooses arguments; this deterministic renderer owns amounts and state claims.
"""
import json
from decimal import Decimal
from langchain_core.messages import ToolMessage, AIMessage
from scenario_request import ScenarioRequest

def financial_result(messages):
 calls={c["id"]:c for m in messages if isinstance(m,AIMessage) for c in m.tool_calls}
 for message in reversed(messages):
  if isinstance(message,ToolMessage) and (message.name or calls.get(message.tool_call_id,{}).get('name','')).startswith('ext_yuyan_research_supplier_cash_scenario_'):
   if getattr(message,'status',None)=='error':return None
   try:
    data=json.loads(message.content)
    if 'result' in data:data=data['result']
    if not isinstance(data.get('baseline'),dict) or not isinstance(data.get('scenario'),dict):return None
    request=ScenarioRequest(**data['request'])
    call=calls.get(message.tool_call_id,{})
    if call.get('args')!={'request_id':request.request_id}:return None
    if request.confirmation_status!='CONFIRMED' or data['parameter_hash']!=request.parameter_hash():return None
    if data['base_version']!=request.base_version or data['scenario']['base_version']!=request.base_version:return None
    for x in (data['baseline'],data['scenario']):
     for key in ('peak_gap_fen','negative_days','actual_balance_fen'):
      if type(x.get(key)) is not int:return None
    return data
   except (ValueError,TypeError,AttributeError,KeyError):return None
 return None

def render_result(data):
 b,s=data['baseline'],data['scenario']
 def yuan(v):return format(Decimal(v)/100,',.2f')+'元'
 change=s['peak_gap_fen']-b['peak_gap_fen']
 r=data['request']
 return ('**确定性工具结果｜合成案例**\n\n'
  f"请求 {r['request_id']} / 案例 {r['case_id']} / 版本 {r['base_version']}：客户 {r['customer_id']}，延期 {r['delay_days']} 天，折扣 {r['discount']}，费用 {yuan(r['fee_fen'])}，每单追加预付 {yuan(r['advance_fen'])}。已确认参数快照；账本或输入变化后须重新确认。\n\n"
  f"|指标|当前基线|待协商情景|\n|---|---:|---:|\n|峰值缺口|{yuan(b['peak_gap_fen'])}|{yuan(s['peak_gap_fen'])}|\n|负余额天数|{b['negative_days']}天|{s['negative_days']}天|\n\n"
  f"峰值缺口变化：{yuan(change)}；负余额天数变化：{s['negative_days']-b['negative_days']}天。"
  +('峰值没有增加，但资金占用可能持续更久。' if change==0 and s['negative_days']>b['negative_days'] else '缺口变化与持续时间需要一起比较。')
  +f"\n\n折扣代价{yuan(s.get('discount_cost_fen',0))}，费用{yuan(s.get('fee_fen',0))}。账本事实余额{yuan(b['actual_balance_fen'])}。"
  +'\n\n来源：已授权合成订单事件账本；情景不保存为正式基线，不代表对方接受或实际到账。'
  +('存在逾期或争议未解决，不能据此判断整体资金安全。' if not s.get('complete') else '')
  +'资金缺口不等于授信额度，仍需用途、还款来源与风险审核。'
  +'\n\n金额和解释由实际工具输出生成；模型负责理解请求与选取工具，不改写金融结果。')


def proposal_result(messages):
 for m in reversed(messages):
  if isinstance(m,ToolMessage) and (m.name or '').startswith('ext_yuyan_research_supplier_cash_scenario_'):return None
  if isinstance(m,ToolMessage) and (m.name or '').startswith('ext_yuyan_research_supplier_scenario_proposal_'):
   try:
    data=json.loads(m.content);data=data.get('result',data)
    r=ScenarioRequest(**data['request'])
    if r.confirmation_status!='PROPOSED':return None
    return '参数提案（尚未确认，未计算）\n'+json.dumps(r.snapshot(),ensure_ascii=False,indent=2)+'\n缺失字段：'+str(data['missing_fields'])+'\n'+data['message']
   except (ValueError,KeyError,TypeError):return None
 return None
