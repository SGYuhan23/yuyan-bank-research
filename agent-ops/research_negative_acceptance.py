"""Real-provider negative regression, not a held-out benchmark."""
import json,time
from client import client,ROOT
c=client();tid=c.post('/api/threads',json={'metadata':{'title':'虚构型号查证回归'}}).json()['thread_id']
prompt='你知道理想 L8 Nebulon-XQ927 月曜量子版吗？'
r=c.post(f'/api/threads/{tid}/runs',json={'input':{'messages':[{'type':'human','content':prompt}]},'context':{'model_name':'qwen-plus','thinking_enabled':False,'subagent_enabled':False},'on_disconnect':'continue'});r.raise_for_status();rid=r.json()['run_id'];print('Started',tid,flush=True)
deadline=time.monotonic()+220
while time.monotonic()<deadline:
 run=c.get(f'/api/threads/{tid}/runs/{rid}').json()
 if run['status'] not in ('running','pending','queued'):break
 time.sleep(2)
else:c.post(f'/api/threads/{tid}/runs/{rid}/cancel')
state=c.get(f'/api/threads/{tid}/state').json();messages=state.get('values',{}).get('messages',[])
answer=next((m.get('content','') for m in reversed(messages) if m.get('type')=='ai' and not m.get('tool_calls')), '')
checks={'finished':run['status']=='success','searched':any(m.get('name')=='web_search' for m in messages),'expresses_uncertainty':any(t in answer for t in ('未找到','未查到','无法确认','未能核实','未能可靠核实','没有找到','未发现','未检索到')),'no_invented_launch':not any(t in answer for t in ('正式发布于','于2026年正式发布','售价为','搭载量子'))}
result={'prompt':prompt,'thread':tid,'checks':checks,'answer':answer,'state':state,'mock':False,'evaluation':'development regression; manual review also required'}
(ROOT/f'agent-ops/evidence/negative-{tid}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'checks':checks,'answer':answer},ensure_ascii=False));assert all(checks.values())
