"""Real Agent tool-to-artifact acceptance, no mock responses."""
import json,time
from client import client,ROOT
c=client();tid=c.post('/api/threads',json={'metadata':{'title':'自定义助手图示验收','agent_name':'yuyan'}}).json()['thread_id']
prompt='请用 draw_diagram 画一个简单流程图：上传资料→读取内容→核对来源→交付报告。交付 SVG 预览和可编辑 Draw.io 文件。'
r=c.post(f'/api/threads/{tid}/runs',json={'input':{'messages':[{'type':'human','content':prompt}]},'context':{'agent_name':'yuyan','model_name':'qwen-plus','thinking_enabled':False,'subagent_enabled':False},'on_disconnect':'continue'});r.raise_for_status();rid=r.json()['run_id'];print('Started',tid,flush=True)
deadline=time.monotonic()+200
while time.monotonic()<deadline:
 run=c.get(f'/api/threads/{tid}/runs/{rid}').json()
 if run['status'] not in ('running','pending','queued'):break
 time.sleep(2)
else:c.post(f'/api/threads/{tid}/runs/{rid}/cancel')
state=c.get(f'/api/threads/{tid}/state').json();v=state.get('values',{});messages=v.get('messages',[])
checks={'finished':run['status']=='success','generated':any(m.get('name')=='draw_diagram' and '"status": "success"' in str(m.get('content','')) for m in messages),'presented_svg':any(x.endswith('.svg') for x in v.get('artifacts',[]))}
result={'thread':tid,'run':run,'checks':checks,'state':state,'mock':False}
(ROOT/f'agent-ops/evidence/diagram-{tid}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'thread':tid,'checks':checks},ensure_ascii=False));assert all(checks.values())
