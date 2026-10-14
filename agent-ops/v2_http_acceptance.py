"""Real authenticated HTTP / PostgreSQL lifecycle checks; isolated synthetic case."""
import json,uuid,secrets,httpx
from client import client,ROOT
c=client();base='/api/plugins/yuyan.research/actions/'
checks={}
def call(action,payload):
 r=c.post(base+action,json=payload);r.raise_for_status();return r.json()
create_payload={'key':'v2-http-'+uuid.uuid4().hex}
a=call('create',create_payload);cid=a['case_id']
checks['create_idempotent']=call('create',create_payload)==a
# Mutation requests re-use their exact key to prove no duplicate ledger entry.
def change(cmd):
 global a
 p={'case_id':cid,'version':a['case']['version'],'key':uuid.uuid4().hex,'command':cmd}
 a=call('change',p);again=call('change',p);assert again==a
 return p
change({'operation':'add','event_id':'HTTP-fee','order_id':'O1','event_type':'fee','planned_date':'2027-01-01','amount_fen':-1000,'source':'合成费用凭据','reason':'验收入账'})
change({'operation':'confirm','event_id':'HTTP-fee','confirmed_date':'2027-01-01','evidence':'合成确认单','reason':'核对'})
p=change({'operation':'post','event_id':'HTTP-fee','posted_date':'2027-01-01','evidence':'合成付款流水','reason':'登记事实'})
checks['posting_exactly_once']=a['calculation']['actual_balance_fen']==19999000 and len(a['case']['history'])==3
bad={**p,'key':uuid.uuid4().hex,'version':a['case']['version']}
checks['duplicate_post_rejected']=c.post(base+'change',json=bad).status_code==422
checks['stale_version_rejected']=c.post(base+'change',json={**p,'key':uuid.uuid4().hex}).status_code==422
checks['reload_same']=call('get',{'case_id':cid})==a
other=httpx.Client(base_url='http://127.0.0.1:8001',headers={'Origin':'http://127.0.0.1:8001'})
r=other.post('/api/v1/auth/register',json={'email':f'v2-{uuid.uuid4().hex}@example.org','password':'Aa9!'+secrets.token_urlsafe(24)});r.raise_for_status()
other.get('/api/v1/auth/me').raise_for_status();other.headers['X-CSRF-Token']=other.cookies.get('csrf_token')
checks['foreign_case_unavailable']=other.post(base+'get',json={'case_id':cid}).status_code in (403,404,422)
checks['foreign_case_list_empty']=other.post(base+'list',json={}).json()['cases']==[]
checks['anonymous_rejected']=httpx.post('http://127.0.0.1:8001'+base+'get',json={'case_id':cid}).status_code in (401,403)
c.headers.pop('X-CSRF-Token')
checks['missing_csrf_rejected']=c.post(base+'create',json={'key':'csrf-test'}).status_code==403
out=ROOT/'agent-ops/research/evidence-v2'
(out/'http.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2));assert all(checks.values())
