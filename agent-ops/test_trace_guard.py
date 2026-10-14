import sys,json
from pathlib import Path
from langchain_core.messages import ToolMessage,HumanMessage,AIMessage
sys.path.insert(0,str(Path(__file__).parent/'research'))
from trace_guard import financial_result,render_result
from supplier_ledger import fixture,evaluate,simulate

def test_financial_units_are_not_recomputed_by_model():
 data,call=trace_data()
 tool=ToolMessage(content=json.dumps(data),name='ext_yuyan_research_supplier_cash_scenario_test',tool_call_id='x')
 text=render_result(financial_result([call,tool]))
 assert '490,000.00元' in text and '490万元' not in text
 assert '38天' in text and '52天' in text and '0.00元' in text
 assert financial_result([HumanMessage(content=json.dumps(data))]) is None
 assert financial_result([ToolMessage(content='invalid',name=tool.name,tool_call_id='y')]) is None

def test_final_provider_amount_cannot_override_tool_result():
 from research_policy import ResearchPolicy
 from langchain_core.messages import AIMessage
 data,call=trace_data()
 tool=ToolMessage(content=json.dumps(data),name='ext_yuyan_research_supplier_cash_scenario_test',tool_call_id='x')
 hallucination=AIMessage(content='缺口490万元，建议直接授信490万元',id='final')
 update=ResearchPolicy().after_model({'messages':[HumanMessage('延期14天'),call,tool,hallucination]},None)
 actual=update['messages'][0]
 assert actual.id=='final' and actual.content==render_result(data)
 assert actual.additional_kwargs['financial_result_source']=='deterministic_tool'
 assert '建议直接授信' not in actual.content
 # A subsequent user request must not accidentally reuse a previous turn's numbers.
 assert ResearchPolicy().after_model({'messages':[tool,hallucination,HumanMessage('你好'),AIMessage('你好')]},None) is None

def test_tool_failure_gets_explicit_unavailable_final():
 from research_policy import ResearchPolicy
 from langchain_core.messages import AIMessage
 call=AIMessage('',tool_calls=[{'name':'ext_yuyan_research_supplier_cash_scenario_test','id':'x','args':{}}])
 error=ToolMessage(content='case unavailable',name='ext_yuyan_research_supplier_cash_scenario_test',status='error',tool_call_id='x')
 update=ResearchPolicy().after_model({'messages':[HumanMessage('计算'),call,error,AIMessage('估计50万元')]},None)
 final=update['messages'][0]
 assert final.additional_kwargs['financial_result_source']=='unavailable'
 assert '无法给出缺口金额' in final.content and '50万元' not in final.content


def trace_data():
 from scenario_request import ScenarioRequest,envelope
 request=ScenarioRequest('r1','case1',1,'C1',14,'0',0,0,'CONFIRMED')
 data={**envelope(request),'base_version':1,'baseline':evaluate(fixture()),'scenario':simulate(fixture(),14)}
 call=AIMessage('',tool_calls=[{'name':'ext_yuyan_research_supplier_cash_scenario_test','id':'x','args':{'request_id':'r1'}}])
 return data,call
