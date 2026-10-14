import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'research'))
from supplier_ledger import fixture,evaluate

def test_sources_are_saved_and_never_calibrate_financial_parameters():
 facts=json.loads((ROOT/'research/fuling_public_facts.json').read_text())
 for f in facts:
  assert f['model_usage'] in {'background_only','scenario_design'}
  raw=(ROOT/'research'/f['source_snapshot']).read_bytes()
  assert hashlib.sha256(raw).hexdigest()==f['source_sha256']
  assert '已直读' in f['verification_status']

def test_full_cash_curve_matches_independent_date_prefix_reference():
 from datetime import date,timedelta
 c=fixture();r=evaluate(c)
 for point in r['series']:
  value=c['opening_fen']+sum(e['amount_fen'] for e in c['events'] if e['status']=='POSTED' and c['opening_date']<=e['posted_date']<c['as_of'])+sum(e['amount_fen'] for e in c['events'] if e['status'] in {'PROJECTED','CONFIRMED'} and c['as_of']<=e['planned_date']<=point['date'])
  assert point['balance_fen']==value
 assert r['peak_gap_fen']==49000000 and r['negative_days']==38
