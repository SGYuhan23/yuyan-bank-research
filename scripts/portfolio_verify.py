"""Verify frozen core and exported public files without models, network or databases."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
for manifest in ['docs/FROZEN_CORE_SHA256.json','PUBLIC_RELEASE_INVENTORY.json']:
 p=ROOT/manifest
 if not p.exists():raise SystemExit('Missing '+manifest+'; run against exported portfolio')
 values=json.loads(p.read_text())
 files=values.get('files',values)
 for name,meta in files.items():
  expected=meta['sha256'] if isinstance(meta,dict) else meta
  assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
 assert all('.git' not in Path(n).parts for n in files)
 print(manifest+': all hashes verified')
assert len(list((ROOT/'docs/screenshots').glob('*.png')))==11
for name in ['overview.mp4','fuling.mp4','supplier-ai.mp4','overview-preview.gif']:assert (ROOT/'docs/media'/name).stat().st_size>0
print('11 screenshots, 3 recordings, preview and frozen files present')
