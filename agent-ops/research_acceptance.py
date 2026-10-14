# coding: utf-8
"""General web research smoke test, distinct from bank examples."""
import json,time
from client import client,ROOT
c=client();thread=c.post('/api/threads',json={'metadata':{'title':'联网检索与引用验收'}}).json()['thread_id']
prompt='请搜索 Python 官方资料，比较 CSV 与 JSON 交换表格数据的差异，写一份中文简短说明，至少引用两个实际访问成功的官方页面。保存为 formats.md 并展示。说明来源无法访问的情况，不要凭记忆假装已检索。无需银行案例。'
r=c.post(f'/api/threads/{thread}/runs',json={'input':{'messages':[{'type':'human','content':prompt}]},'context':{'model_name':'qwen-plus','thinking_enabled':False,'is_plan_mode':True,'subagent_enabled':False},'on_disconnect':'continue'});r.raise_for_status();rid=r.json()['run_id'];print('Started research',thread,flush=True)
deadline=time.monotonic()+360
while time.monotonic()<deadline:
 status=c.get(f'/api/threads/{thread}/runs/{rid}').json()
 if status['status'] not in ('pending','running','queued'): break
 time.sleep(3)
if status['status'] in ('pending','running','queued'):
 c.post(f'/api/threads/{thread}/runs/{rid}/cancel')
state=c.get(f'/api/threads/{thread}/state').json()
result={'thread':thread,'run':status,'state':state,'mock':False}
(ROOT/f'agent-ops/evidence/research-{thread}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('Research result',status['status'],flush=True)
