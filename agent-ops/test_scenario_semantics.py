import sys,json
from pathlib import Path
from copy import deepcopy
import pytest
sys.path.insert(0,str(Path(__file__).parent/'research'))
from scenario_request import proposal,confirm_request,assert_consumable,envelope
from supplier_ledger import fixture,evaluate,simulate
from trace_guard import financial_result
from langchain_core.messages import AIMessage,ToolMessage

def payload():return dict(request_id='request1',case_id='case1',base_version=1,customer_id='C1',delay_days=14,discount='0',fee_fen=0,advance_fen=0)

def test_missing_or_ambiguous_request_cannot_run_and_no_defaults():
 c=fixture();p=proposal({**payload(),'customer_id':None,'delay_days':None},c)
 assert envelope(p)['missing_fields']==['customer_id','delay_days']
 with pytest.raises(ValueError):confirm_request(p,p.snapshot(),c)
 with pytest.raises(ValueError):assert_consumable(proposal(payload(),c),c)
 for mutation in [{'delay_days':True},{'fee_fen':1.2},{'discount':'NaN'},{'confirmation_status':'CONFIRMED'}]:
  with pytest.raises(ValueError):proposal({**payload(),**mutation},c)

def test_c1_14_and_all_30_not_the_same_confirmed_request():
 c=fixture();p=proposal(payload(),c);wrong={**p.snapshot(),'customer_id':'ALL','delay_days':30}
 with pytest.raises(ValueError):confirm_request(p,wrong,c)
 confirmed=confirm_request(p,p.snapshot(),c);assert_consumable(confirmed,c)
 other=proposal({**payload(),'customer_id':'ALL','delay_days':30},c)
 assert other.parameter_hash()!=confirmed.parameter_hash()
 with pytest.raises(ValueError):assert_consumable(confirmed,{**c,'version':2})
 result={**envelope(confirmed),'base_version':1,'baseline':evaluate(c),'scenario':simulate(c,14)}
 call=AIMessage('',tool_calls=[{'name':'ext_yuyan_research_supplier_cash_scenario_test','id':'x','args':{'request_id':'request1'}}])
 def check(data):return financial_result([call,ToolMessage(content=json.dumps(data),name=call.tool_calls[0]['name'],tool_call_id='x')])
 assert check(result)
 wrong=deepcopy(result);wrong['request'].update(customer_id='ALL',delay_days=30)
 assert check(wrong) is None
 wrong=deepcopy(result);wrong['request']['request_id']='different'
 assert check(wrong) is None
