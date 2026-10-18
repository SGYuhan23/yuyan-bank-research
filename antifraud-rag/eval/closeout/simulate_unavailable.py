"""Explicit fault injection, never evidence of a real provider outage."""
import sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from pipeline import RagRun,ROOT
with tempfile.TemporaryDirectory() as d,patch('pipeline.ROOT',Path(d)),patch('retrieval.embed',side_effect=RuntimeError('simulated provider unavailable')):
 r=RagRun('老合作方说换了卡号，让我们今天打钱，先做什么？').run()
 assert r['status']=='failed' and r['result'] is None
 assert '语义检索不可用' in r['error']
 assert any(e['kind']=='retrieval_failed' and e['method']=='semantic' for e in r['records'])
 assert not any(e['kind']=='adequacy_checked' for e in r['records'])
 (ROOT/'eval/closeout/mock-unavailable.json').write_text(json.dumps({'method':'mock embed network fault; not real provider outage','status':r['status'],'error':r['error'],'records':r['records']},ensure_ascii=False,indent=2))
print('simulated embedding failure: explicit failure and no adequacy claim')
