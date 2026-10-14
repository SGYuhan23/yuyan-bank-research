"""Snapshot completed real run; compare after operator restarts Gateway."""
import hashlib,json,sys
from pathlib import Path
from client import client,ROOT
base=ROOT/'agent-ops/evidence'
passed=[json.loads(p.read_text()) for p in base.glob('live-*.json') if json.loads(p.read_text()).get('checks',{}).get('second_total')]
r=passed[-1];c=client();tid=r['thread_id']
state=c.get(f'/api/threads/{tid}/state');state.raise_for_status()
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/r['output_paths'][0]).parent.iterdir() if p.is_file()}
snapshot={'thread':tid,'checkpoint_id':state.json()['checkpoint_id'],'files':files,'artifacts':state.json()['values'].get('artifacts',[])}
p=base/'restart-before.json'
if sys.argv[-1]=='before':
 p.write_text(json.dumps(snapshot,indent=2));print('Saved restart baseline',len(files),'files')
else:
 checks={'checkpoint_unchanged':snapshot['checkpoint_id']==json.loads(p.read_text())['checkpoint_id'],'files_unchanged':snapshot['files']==json.loads(p.read_text())['files'],'artifacts_unchanged':snapshot['artifacts']==json.loads(p.read_text())['artifacts']}
 (base/'restart-result.json').write_text(json.dumps(checks,indent=2));print(checks);assert all(checks.values())
