# coding: utf-8
"""Real-provider regression for the user-reported unsupported denial."""
import json,time,uuid
from client import client,ROOT
c=client();tid=c.post('/api/threads',json={'metadata':{'title':'事实查证回归'}}).json()['thread_id']
prompt='你知道理想l8 livis吗'
r=c.post(f'/api/threads/{tid}/runs',json={'input':{'messages':[{'type':'human','content':prompt}]},'context':{'model_name':'qwen-plus','thinking_enabled':False,'subagent_enabled':False},'on_disconnect':'continue'});r.raise_for_status();rid=r.json()['run_id']
print('Started',tid,flush=True)
deadline=time.monotonic()+240
while time.monotonic()<deadline:
 s=c.get(f'/api/threads/{tid}/runs/{rid}').json()
 if s['status'] not in ('running','pending','queued'):break
 time.sleep(2)
else:c.post(f'/api/threads/{tid}/runs/{rid}/cancel')
state=c.get(f'/api/threads/{tid}/state').json();messages=state.get('values',{}).get('messages',[])
tools=[m.get('name') for m in messages if m.get('type')=='tool']
answer=next((m.get('content','') for m in reversed(messages) if m.get('type')=='ai' and not m.get('tool_calls')), '')
checks={'correct_launch_year':'2026' in answer,'searched':'web_search' in tools,'fetched':'web_fetch' in tools,'cites_official':any(host in answer for host in ('ir.lixiang.com','www.lixiang.com/news/')),'not_unsupported_denial':not any(x in answer for x in ('并非理想汽车的官方','没有名为“Livis”','不是理想汽车官方命名','口误或拼写错误','不是真实存在','自媒体虚构','并不存在','并非官方车型','错误地嫁接'))}
result={'prompt':prompt,'thread':tid,'run':s,'checks':checks,'answer':answer,'state':state,'mock':False}
p=ROOT/f'agent-ops/evidence/freshness-{tid}.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'checks':checks,'answer':answer},ensure_ascii=False),flush=True)
assert all(checks.values())
