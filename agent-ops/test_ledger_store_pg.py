"""Real PostgreSQL integration; dedicated synthetic owner IDs, no mocks."""
import sys,uuid,concurrent.futures,os
from pathlib import Path
import psycopg,pytest
sys.path.insert(0,str(Path(__file__).parent/'research'))
from ledger_store import LedgerStore
URL=os.environ.get('AGENT_DATABASE_URL')
pytestmark = pytest.mark.skipif(not URL, reason='AGENT_DATABASE_URL is required for PostgreSQL integration tests')

def test_real_pg_idempotency_isolation_conflicts_and_reopen():
 s=LedgerStore(URL);s.migrate();owner='v2-test-'+uuid.uuid4().hex;other=owner+'-other'
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
   copies=list(pool.map(lambda _:s.apply('create',{'key':'first'},owner),range(4)))
  assert len({c['case_id'] for c in copies})==1
  cid=copies[0]['case_id']
  with pytest.raises(ValueError):s.apply('get',{'case_id':cid},other)
  cmd={'case_id':cid,'version':1,'key':'confirm','command':{'operation':'confirm','event_id':'O1-receivable','reason':'合成合同核对','confirmed_date':'2027-01-01','evidence':'测试合同'}}
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
   replies=list(pool.map(lambda _:s.apply('change',cmd,owner),range(4)))
  assert all(x['case']['version']==2 for x in replies)
  assert len(replies[0]['case']['history'])==1
  with pytest.raises(ValueError):s.apply('change',{**cmd,'key':'different'},owner)
  with pytest.raises(ValueError):s.apply('change',{**cmd,'version':2},owner)
  assert LedgerStore(URL).apply('get',{'case_id':cid},owner)['case']==replies[0]['case']
  assert not s.apply('list',{},other)['cases']
 finally:
  with psycopg.connect(URL) as db:
   db.execute('DELETE FROM public.yuyan_supplier_commands WHERE owner_id=%s',(owner,));db.execute('DELETE FROM public.yuyan_supplier_cases WHERE owner_id=%s',(owner,))

def test_atomic_reconciliation_and_confirmed_scenario_request_real_pg():
 s=LedgerStore(URL);s.migrate();owner='final-p0-'+uuid.uuid4().hex
 try:
  a=s.apply('create',{'key':'create'},owner);cid=a['case_id']
  request={'request_id':'r1','case_id':cid,'base_version':1,'customer_id':'C1','delay_days':14,'discount':'0','fee_fen':0,'advance_fen':0}
  p=s.apply('propose_scenario',request,owner)
  with pytest.raises(ValueError):s.apply('simulate',{'request_id':'r1'},owner)
  with pytest.raises(ValueError):s.apply('confirm_scenario',{'request_id':'r1','snapshot':{**p['request'],'customer_id':'ALL','delay_days':30}},owner)
  confirmed=s.apply('confirm_scenario',{'request_id':'r1','snapshot':p['request']},owner)
  r=s.apply('simulate',{'request_id':'r1'},owner)
  assert r['request']==confirmed['request'] and r['scenario']['negative_days']==52
  with pytest.raises(ValueError):s.apply('simulate',{'request_id':'r1'},owner+'other')
  p=s.apply('propose_scenario',{**request,'customer_id':'ALL','delay_days':30},owner)
  assert p['parameter_hash']!=r['parameter_hash']
  with pytest.raises(ValueError):s.apply('simulate',{'request_id':'r1'},owner)
  s.apply('confirm_scenario',{'request_id':'r1','snapshot':p['request']},owner)
  assert s.apply('simulate',{'request_id':'r1'},owner)['scenario']['peak_gap_fen']==53000000
  change={'case_id':cid,'version':1,'key':'atomic','command':{'operation':'record_actuals_and_reconcile','event_id':'batch','reason':'合成验收','as_of':'2027-01-09','observed_balance_fen':19999000,'postings':[{'event_id':'fee1','posted_date':'2027-01-08','evidence':'合成流水','new_event':{'order_id':'O1','event_type':'fee','amount_fen':-1000,'source':'合成'}}]}}
  with pytest.raises(ValueError):s.apply('change',{**change,'command':{**change['command'],'observed_balance_fen':0}},owner)
  assert s.apply('get',{'case_id':cid},owner)==a
  result=s.apply('change',change,owner)
  assert s.apply('change',change,owner)==result
  assert result['case']['version']==2 and result['calculation']['actual_balance_fen']==19999000
  assert LedgerStore(URL).apply('get',{'case_id':cid},owner)==result
  with pytest.raises(ValueError):s.apply('simulate',{'request_id':'r1'},owner)
  with pytest.raises(ValueError):s.apply('change',{**change,'key':'stale'},owner)
  with pytest.raises(ValueError):s.apply('change',{**change,'key':'dup','version':2},owner)
 finally:
  with psycopg.connect(URL) as db:
   db.execute('DELETE FROM public.yuyan_scenario_requests WHERE owner_id=%s',(owner,))
   db.execute('DELETE FROM public.yuyan_supplier_commands WHERE owner_id=%s',(owner,))
   db.execute('DELETE FROM public.yuyan_supplier_cases WHERE owner_id=%s',(owner,))
