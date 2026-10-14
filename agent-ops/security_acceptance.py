"""Real PostgreSQL/HTTP isolation and idempotency checks; model not mocked."""
import json,secrets,uuid
from client import client,ROOT
import httpx
c=client()
thread=c.post('/api/threads',json={'thread_id':str(uuid.uuid4())}).json()['thread_id']
repeat=c.post('/api/threads',json={'thread_id':thread}); assert repeat.status_code==200
other=httpx.Client(base_url='http://127.0.0.1:8001',headers={'Origin':'http://127.0.0.1:8001'})
r=other.post('/api/v1/auth/register',json={'email':f'test-{uuid.uuid4().hex}@example.org','password':'Aa9!'+secrets.token_urlsafe(24)})
r.raise_for_status();other.get('/api/v1/auth/me');other.headers['X-CSRF-Token']=other.cookies.get('csrf_token')
checks={}
for label,method,path,kwargs in [
 ('foreign_thread','get',f'/api/threads/{thread}',{}),
 ('foreign_checkpoint','get',f'/api/threads/{thread}/state',{}),
 ('foreign_upload','post',f'/api/threads/{thread}/uploads',{'files':{'files':('attack.txt',b'no','text/plain')}}),
 ('foreign_delete','delete',f'/api/threads/{thread}',{}),
]:
 response=getattr(other,method)(path,**kwargs)
 checks[label]={'status':response.status_code,'pass':response.status_code in (403,404)}
anon=httpx.get(f'http://127.0.0.1:8001/api/threads/{thread}')
checks['anonymous_read']={'status':anon.status_code,'pass':anon.status_code==401}
checks['thread_create_idempotent']={'pass':repeat.json()['thread_id']==thread}
(ROOT/'agent-ops/evidence/isolation.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2));assert all(v['pass'] for v in checks.values())
