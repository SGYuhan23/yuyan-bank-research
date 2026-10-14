# coding: utf-8
import json,time,uuid
from client import client,ROOT
c=client(); tid=c.post('/api/threads',json={}).json()['thread_id']
body={'input':{'messages':[{'type':'human','content':'请查阅 Python 官方文档并写一段简短说明。'}]},'context':{'thinking_enabled':False,'subagent_enabled':False},'on_disconnect':'continue'}
headers={'Idempotency-Key':uuid.uuid4().hex}
a=c.post(f'/api/threads/{tid}/runs',json=body,headers=headers);a.raise_for_status()
b=c.post(f'/api/threads/{tid}/runs',json=body,headers=headers);b.raise_for_status()
rid=a.json()['run_id'];checks={'same_run_after_retry':rid==b.json()['run_id']}
conflict=dict(body,input={'messages':[{'type':'human','content':'different request'}]})
resp=c.post(f'/api/threads/{tid}/runs',json=conflict,headers=headers)
checks['changed_payload_conflicts']=resp.status_code==409
cancel=c.post(f'/api/threads/{tid}/runs/{rid}/cancel');cancel.raise_for_status()
for _ in range(20):
 s=c.get(f'/api/threads/{tid}/runs/{rid}').json()
 if s['status'] not in ('running','pending','queued'): break
 time.sleep(.5)
checks['cancel_terminal']=s['status'] in ('interrupted','cancelled')
result={'checks':checks,'status':s['status'],'run_id':rid,'thread_id':tid}
(ROOT/'agent-ops/evidence/run-control.json').write_text(json.dumps(result,indent=2));print(result);assert all(checks.values())
