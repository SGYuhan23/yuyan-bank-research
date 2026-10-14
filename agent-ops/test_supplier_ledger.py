import sys
from pathlib import Path
from copy import deepcopy
import pytest
sys.path.insert(0,str(Path(__file__).parent/'research'))
from supplier_ledger import fixture,evaluate,apply_command,simulate

def test_facts_and_forecasts_are_separate():
 c=fixture();assert evaluate(c)['actual_balance_fen']==20000000
 e=next(e for e in c['events'] if e['event_id']=='O1-receivable');e.update(status='CONFIRMED',confirmed_date='2027-01-01',evidence='synthetic contract')
 assert evaluate(c)['actual_balance_fen']==20000000
 # Independent prefix sum, never use evaluate for reference.
 values=[20000000];amount=20000000
 for d in sorted({e['planned_date'] for e in c['events'] if e['status'] in {'CONFIRMED','PROJECTED'} and e['planned_date']>=c['as_of']}):
  amount+=sum(e['amount_fen'] for e in c['events'] if e['planned_date']==d and e['status'] in {'CONFIRMED','PROJECTED'});values.append(amount)
 assert evaluate(c)['peak_gap_fen']==max(0,-min(values))

def test_posted_immutable_and_duplicate_rejected():
 c=fixture()
 for op in ['reschedule','post','cancel']:
  with pytest.raises(ValueError):apply_command(c,dict(event_id='O1-prepayment',operation=op,reason='test',planned_date='2027-01-10'))
 c['events'].append(deepcopy(c['events'][0]))
 with pytest.raises(ValueError):evaluate(c)

def test_transition_history_and_exactly_once_cash():
 c=fixture();c['as_of']='2027-03-01'
 with pytest.raises(ValueError):apply_command(c,dict(event_id='O1-receivable',operation='post',reason='test',posted_date='2027-02-15'))
 confirmed=apply_command(c,dict(event_id='O1-receivable',operation='confirm',reason='合同核对',confirmed_date='2027-02-01',evidence='合成合同'))
 posted=apply_command(confirmed,dict(event_id='O1-receivable',operation='post',reason='流水核对',posted_date='2027-02-15',evidence='合成流水'))
 assert evaluate(posted)['actual_balance_fen']==68000000
 assert len(posted['history'])==2 and c['version']==1
 assert posted['history'][1]['before']['status']=='CONFIRMED'
 with pytest.raises(ValueError):apply_command(posted,dict(event_id='O1-receivable',operation='post',reason='重试'))
 confirmed['orders'][0]['payment_terms']={'type':'FIXED_DATE'}
 revised=apply_command(confirmed,dict(event_id='O1-receivable',operation='reschedule',reason='重新协商',planned_date='2027-02-28'))
 assert revised['events'][-1]!=posted['events'][0]
 assert next(e for e in revised['events'] if e['event_id']=='O1-receivable')['status']=='PROJECTED'

def test_scenarios_cost_concentration_and_no_mutation():
 c=fixture();before=deepcopy(c);base=evaluate(c);late=simulate(c,14);all_late=simulate(c,14,'ALL');discount=simulate(c,discount='.02',fee_fen=100000)
 assert c==before
 assert late['negative_days']>base['negative_days']
 assert all_late['peak_gap_fen']>=late['peak_gap_fen']
 assert discount['discount_cost_fen']==960000
 assert discount['closing_fen']==base['closing_fen']-1060000
 assert base['concentration']['top1']=='0.625' and base['concentration']['top3']=='0.875'
 assert base['evidence_completeness']['supported']==4

def test_overdue_not_moved_and_window_not_truncated():
 c=fixture();c['as_of']='2027-04-01'
 assert not evaluate(c)['complete'] and evaluate(c)['overdue_unresolved']
 c['events'][-1]['planned_date']='2029-01-01'
 with pytest.raises(ValueError):evaluate(c)

def test_quality_deduction_is_separate_cash_event_with_audit():
 c=fixture();base=evaluate(c)
 command={'operation':'add','event_id':'O1-quality-1','order_id':'O1','event_type':'quality_deduction','planned_date':'2027-02-15','amount_fen':-100000,'source':'合成补充协议','reason':'合成验收质量扣款'}
 updated=apply_command(c,command)
 assert evaluate(updated)['actual_balance_fen']==base['actual_balance_fen']
 assert evaluate(updated)['closing_fen']==base['closing_fen']-100000
 assert updated['history'][-1]['before'] is None
 with pytest.raises(ValueError):apply_command(updated,command)
 with pytest.raises(ValueError):apply_command(c,{**command,'order_id':'unknown'})

def test_dispute_requires_evidence_and_cancel_requires_cash_event():
 c=fixture()
 with pytest.raises(ValueError):apply_command(c,{'operation':'dispute','event_id':'O1-receivable','reason':'x','evidence':''})
 # Cancelling a purchase-order milestone alone would leave its cash forecast alive.
 with pytest.raises(ValueError):apply_command(c,{'operation':'cancel','event_id':'O1-purchase_order','reason':'x'})

def test_invalid_command_fields_cannot_bypass_validation():
 with pytest.raises(ValueError):apply_command(fixture(),{'operation':'confirm','event_id':'O1-receivable','reason':'x','confirmed_date':'2027-01-01','evidence':'x','status':'POSTED'})

def test_missing_order_milestones_count_as_missing_evidence():
 c=fixture();r=evaluate(c)
 assert r['evidence_completeness']['required']==len(c['orders'])*4
 assert r['evidence_completeness']['supported']==4
 c['events']=[e for e in c['events'] if e['event_type']!='invoice']
 assert evaluate(c)['evidence_completeness']['required']==16

def event(case,eid):return next(e for e in case['events'] if e['event_id']==eid)
def command(case,eid,op,**args):return apply_command(case,{'event_id':eid,'operation':op,'reason':'合成验证',**args})

def test_contract_dependency_dates_and_confirmed_boundaries():
 c=fixture();r=command(c,'O1-acceptance','reschedule',planned_date='2027-02-10')
 assert event(r,'O1-invoice')['planned_date']=='2027-02-12'
 assert event(r,'O1-receivable')['planned_date']=='2027-02-19'
 assert event(r,'O1-receivable')['status']=='PROJECTED'
 assert event(r,'O2-receivable')==event(c,'O2-receivable')
 r=command(r,'O1-invoice','reschedule',planned_date='2027-02-15')
 assert event(r,'O1-receivable')['planned_date']=='2027-02-22'
 confirmed=command(c,'O1-receivable','confirm',confirmed_date='2027-01-01',evidence='合成合同')
 changed=command(confirmed,'O1-acceptance','reschedule',planned_date='2027-02-10')
 assert event(changed,'O1-receivable')['planned_date']==event(confirmed,'O1-receivable')['planned_date']
 assert event(changed,'O1-receivable')['status']=='CONFIRMED'
 posted=apply_command(confirmed,{'operation':'record_actuals_and_reconcile','event_id':'batch','reason':'合成流水','as_of':'2027-02-16','observed_balance_fen':68000000,'postings':[{'event_id':'O1-receivable','posted_date':'2027-02-15','evidence':'合成到账'}]})
 changed=command(posted,'O1-acceptance','reschedule',planned_date='2027-02-20')
 assert event(changed,'O1-receivable')==event(posted,'O1-receivable')
 assert r['history'][-1]['derived_changes']
 fixed=fixture();fixed['orders'][0]['payment_terms']={'type':'FIXED_DATE'}
 changed=command(fixed,'O1-acceptance','reschedule',planned_date='2027-02-20')
 assert event(changed,'O1-receivable')==event(fixed,'O1-receivable')

def test_disputes_propagate_without_upgrading_cash_state():
 c=fixture();r=command(c,'O1-acceptance','dispute',evidence='合成质量争议')
 for eid in ('O1-invoice','O1-receivable'):
  assert event(r,eid)['prediction_confidence']=='BLOCKED_BY_DISPUTE'
  assert event(r,eid)['status']=='PROJECTED'
 out=evaluate(r)
 assert not out['complete'] and 'O1-receivable' in out['disputed_events']
 assert all('O1-receivable' not in [x['event_id'] for x in p['events']] for p in out['series'])
 assert out['actual_balance_fen']==evaluate(c)['actual_balance_fen']

def test_atomic_actuals_reconcile_rollback_and_exact_cash():
 from supplier_ledger import ReconciliationMismatch
 c=command(fixture(),'O1-receivable','confirm',confirmed_date='2027-01-01',evidence='合成确认')
 before=deepcopy(c)
 cmd={'operation':'record_actuals_and_reconcile','event_id':'batch','reason':'核对合成流水','as_of':'2027-02-16','observed_balance_fen':67999000,
      'postings':[{'event_id':'O1-receivable','posted_date':'2027-02-15','evidence':'合成到账48万'}, {'event_id':'new-fee','posted_date':'2027-02-15','evidence':'合成支付10元','new_event':{'order_id':'O1','event_type':'fee','amount_fen':-1000,'source':'合成银行流水'}}]}
 with pytest.raises(ReconciliationMismatch) as ex:apply_command(c,{**cmd,'observed_balance_fen':0})
 assert ex.value.difference_fen==-67999000 and c==before
 result=apply_command(c,cmd)
 assert result['version']==c['version']+1 and evaluate(result)['actual_balance_fen']==67999000
 assert result['as_of']=='2027-02-16' and event(result,'O1-receivable')['status']=='POSTED'
 assert result['history'][-1]['before']['events'][0]['status']=='CONFIRMED'
 assert c==before
 with pytest.raises(ValueError):apply_command(result,cmd)
 with pytest.raises(ValueError):apply_command(c,{**cmd,'postings':[cmd['postings'][0],cmd['postings'][0]]})
 with pytest.raises(ValueError):apply_command(c,{**cmd,'postings':[{**cmd['postings'][0],'amount_fen':1}]})
