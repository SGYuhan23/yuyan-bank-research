"""Real model edit within an existing authenticated image conversation."""
import json,time,hashlib
from client import client,ROOT
c=client()
source=json.loads((ROOT/'agent-ops/evidence/media-0a42c926-7c8d-4d8e-b9b5-f6cfbc54bb82.json').read_text())
tid=source['thread'];path=next(p for p in source['state']['values']['artifacts'] if p.endswith('.png'))
url=f'/api/threads/{tid}/artifacts/{path.lstrip("/")}'
before=c.get(url);before.raise_for_status()
prompt=f'请使用 edit_image 编辑这张已有图片 {path}，保留橘猫与窗边水彩构图，将窗外改为蓝紫色夜空与月亮。请展示编辑后的图片。'
r=c.post(f'/api/threads/{tid}/runs',json={'input':{'messages':[{'type':'human','content':prompt}]},'context':{'model_name':'qwen-plus','thinking_enabled':False,'subagent_enabled':False},'on_disconnect':'continue'});r.raise_for_status();rid=r.json()['run_id'];print('started',tid,flush=True)
for _ in range(110):
 run=c.get(f'/api/threads/{tid}/runs/{rid}').json()
 if run['status'] not in ('running','pending','queued'):break
 time.sleep(2)
else:c.post(f'/api/threads/{tid}/runs/{rid}/cancel')
state=c.get(f'/api/threads/{tid}/state').json();v=state['values'];edits=[p for p in v.get('artifacts',[]) if '/edit-' in p and p.endswith('.png')]
checks={'finished':run['status']=='success','edit_tool':any(m.get('name')=='edit_image' and '"status": "success"' in str(m.get('content')) for m in v['messages']),'new_image':bool(edits),'original_unchanged':hashlib.sha256(c.get(url).content).digest()==hashlib.sha256(before.content).digest()}
if edits:
 out=c.get(f'/api/threads/{tid}/artifacts/{edits[-1].lstrip("/")}');out.raise_for_status();(ROOT/'agent-ops/evidence/edited-night.png').write_bytes(out.content)
(ROOT/'agent-ops/evidence/image-edit-live.json').write_text(json.dumps({'thread':tid,'run':run,'checks':checks,'state':state,'mock':False},ensure_ascii=False,indent=2));print(checks);assert all(checks.values())
