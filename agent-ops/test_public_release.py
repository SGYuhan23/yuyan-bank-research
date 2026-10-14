"""Publication boundary regressions; no financial model changes."""
import json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'agent-ops/research'))
from export_trace import FORBIDDEN,pick,proposal,metrics
WEB=ROOT/'agent-platform/frontend/public/research'

def test_public_trace_nested_allowlist_and_actual_semantics():
 trace=json.loads((WEB/'trace.json').read_text())
 assert not FORBIDDEN.search(json.dumps(trace,ensure_ascii=False))
 assert trace['parameters_prespecified'] is True
 assert trace['original_model_proposal']['request']['discount'] is None
 assert trace['confirmed_request']['request']['customer_id']=='C1'
 assert trace['confirmed_request']['request']['delay_days']==14
 assert trace['harness_corrected_proposal'] is True
 injected={**trace['original_model_proposal'],'system_message':'private','request':{**trace['original_model_proposal']['request'],'skill_system':'private'}}
 assert proposal(injected)==trace['original_model_proposal']
 original=trace['result']['baseline'];injected={**original,'working_directory':'/mnt/private','concentration':{**original['concentration'],'provider_system':'private'}}
 assert metrics(injected)==original
 with pytest.raises(ValueError):pick({'customer_id':{'system_message':'secret'}},['customer_id'])

def test_public_inventory_and_stale_customer_field():
 expected={'v2.json','trace.json','sources.json','fuling_public_facts.json','fuling-v2-customers.csv','fuling-v2-actions.csv','deposit-sensitivity.csv','fuling-research.pdf','supplier-research.pdf','deposit-research.pdf'}
 assert {p.name for p in WEB.iterdir()}==expected
 data=json.loads((WEB/'v2.json').read_text())
 assert all('service_hours' not in row for row in data['fuling']['customers'])
 assert all('service_hours' in row for row in data['fuling']['actions'])
 assert 'service_hours' not in (WEB/'fuling-v2-customers.csv').read_text().splitlines()[0]
