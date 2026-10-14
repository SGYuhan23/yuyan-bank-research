"""Real Agent tool-to-artifact acceptance, no mock responses."""
import json,time
from client import client,ROOT
c=client();tid=c.post('/api/threads',json={'metadata':{'title':'真实绘图能力验收'}}).json()['thread_id']
prompt='请用图片生成工具画一张水彩风格的橘猫窗边插画，1024*1024。将生成的图片呈现给我，不要用 SVG 或代码替代图片模型。'
r=c.post(f'/api/threads/{tid}/runs',json={'input':{'messages':[{'type':'human','content':prompt}]},'context':{'model_name':'qwen-plus','thinking_enabled':False,'subagent_enabled':False},'on_disconnect':'continue'});r.raise_for_status();rid=r.json()['run_id'];print('Started',tid,flush=True)
deadline=time.monotonic()+200
while time.monotonic()<deadline:
 run=c.get(f'/api/threads/{tid}/runs/{rid}').json()
 if run['status'] not in ('running','pending','queued'):break
 time.sleep(2)
else:c.post(f'/api/threads/{tid}/runs/{rid}/cancel')
state=c.get(f'/api/threads/{tid}/state').json();v=state.get('values',{});messages=v.get('messages',[])
checks={'finished':run['status']=='success','generated':any(m.get('name')=='generate_image' and '"status": "success"' in str(m.get('content','')) for m in messages),'presented_png':any(x.endswith('.png') for x in v.get('artifacts',[]))}
result={'thread':tid,'run':run,'checks':checks,'state':state,'mock':False}
(ROOT/f'agent-ops/evidence/media-{tid}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'thread':tid,'checks':checks},ensure_ascii=False));assert all(checks.values())
