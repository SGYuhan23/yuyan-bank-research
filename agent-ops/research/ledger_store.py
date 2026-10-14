"""Plugin-owned PostgreSQL transactions. Host principal supplies owner; never model input."""
import hashlib,json,uuid
import psycopg
from psycopg.types.json import Jsonb
from supplier_ledger import fixture,apply_command,evaluate,simulate
from scenario_request import ScenarioRequest,proposal,envelope,confirm_request,assert_consumable,PARAMS

DDL='''CREATE TABLE IF NOT EXISTS public.yuyan_supplier_cases (
 case_id text PRIMARY KEY, owner_id text NOT NULL, version integer NOT NULL,
 payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS yuyan_supplier_owner ON public.yuyan_supplier_cases(owner_id);
CREATE TABLE IF NOT EXISTS public.yuyan_supplier_commands (
 owner_id text NOT NULL, idempotency_key text NOT NULL, payload_hash text NOT NULL,
 response jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(owner_id,idempotency_key));
CREATE TABLE IF NOT EXISTS public.yuyan_scenario_requests (
 owner_id text NOT NULL, request_id text NOT NULL, case_id text NOT NULL,
 payload jsonb NOT NULL, PRIMARY KEY(owner_id,request_id));'''
class LedgerStore:
 def __init__(self,url):self.url=url
 def migrate(self):
  with psycopg.connect(self.url) as db:db.execute(DDL)
 def apply(self,action,payload,owner):
  if not owner:raise ValueError('Authentication required')
  allowed={'create':{'key'},'list':set(),'get':{'case_id'},'simulate':{'request_id'},'invalidate_scenario':{'request_id'},'propose_scenario':{'request_id','case_id','base_version',*PARAMS},'confirm_scenario':{'request_id','snapshot'},'scenario_requests':{'case_id'},'change':{'case_id','version','key','command'}}
  if action not in allowed or set(payload)!=allowed[action]:raise ValueError('Invalid request fields')
  mutating=action in {'create','change'};digest=hashlib.sha256(json.dumps({'action':action,**payload},sort_keys=True).encode()).hexdigest()
  with psycopg.connect(self.url) as db:
   if mutating:
    key=payload['key']
    if not isinstance(key,str) or not 1<=len(key)<=128:raise ValueError('Invalid idempotency key')
    # Serialize owner mutations BEFORE read; protects quotas and idempotency across cases.
    db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(owner,))
    old=db.execute('SELECT payload_hash,response FROM public.yuyan_supplier_commands WHERE owner_id=%s AND idempotency_key=%s',(owner,key)).fetchone()
    if old:
     if old[0]!=digest:raise ValueError('幂等键载荷冲突')
     return old[1]
   if action in {'propose_scenario','confirm_scenario','simulate','scenario_requests','invalidate_scenario'}:
    db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(owner,))
    stored=None
    if action in {'confirm_scenario','simulate','invalidate_scenario'}:
     row=db.execute('SELECT payload FROM public.yuyan_scenario_requests WHERE owner_id=%s AND request_id=%s',(owner,payload['request_id'])).fetchone()
     if not row:raise ValueError('请求不可用')
     stored=ScenarioRequest(**row[0]);cid=stored.case_id
    else:cid=payload['case_id']
    row=db.execute('SELECT payload FROM public.yuyan_supplier_cases WHERE owner_id=%s AND case_id=%s FOR SHARE',(owner,cid)).fetchone()
    if not row:raise ValueError('案例不可用')
    case=row[0]
    if action=='scenario_requests':
     return {'requests':[envelope(ScenarioRequest(**r[0])) for r in db.execute('SELECT payload FROM public.yuyan_scenario_requests WHERE owner_id=%s AND case_id=%s',(owner,cid)).fetchall()]}
    if action=='propose_scenario':
     request=proposal(payload,case)
     existing=db.execute('SELECT case_id FROM public.yuyan_scenario_requests WHERE owner_id=%s AND request_id=%s',(owner,request.request_id)).fetchone()
     if existing and existing[0]!=cid:raise ValueError('请求不可跨案例改写')
     count=db.execute('SELECT count(*) FROM public.yuyan_scenario_requests WHERE owner_id=%s',(owner,)).fetchone()[0]
     if not existing and count>=500:raise ValueError('请求数量上限500')
     db.execute('INSERT INTO public.yuyan_scenario_requests(owner_id,request_id,case_id,payload) VALUES(%s,%s,%s,%s) ON CONFLICT(owner_id,request_id) DO UPDATE SET payload=EXCLUDED.payload',(owner,request.request_id,cid,Jsonb(request.snapshot())))
     return envelope(request)
    if action=='invalidate_scenario':
     invalid={**stored.snapshot(),'confirmation_status':'INVALIDATED'}
     db.execute('UPDATE public.yuyan_scenario_requests SET payload=%s WHERE owner_id=%s AND request_id=%s',(Jsonb(invalid),owner,stored.request_id))
     return {'invalidated':True}
    if action=='confirm_scenario':
     request=confirm_request(stored,payload['snapshot'],case)
     db.execute('UPDATE public.yuyan_scenario_requests SET payload=%s WHERE owner_id=%s AND request_id=%s',(Jsonb(request.snapshot()),owner,request.request_id))
     return envelope(request)
    assert_consumable(stored,case)
    return {**envelope(stored),'base_version':case['version'],'baseline':evaluate(case),'scenario':simulate(case,**{k:getattr(stored,k) for k in PARAMS})}
   if action=='create':
    count=db.execute('SELECT count(*) FROM public.yuyan_supplier_cases WHERE owner_id=%s',(owner,)).fetchone()[0]
    if count>=20:raise ValueError('案例数量已达20个')
    case=fixture();cid=str(uuid.uuid4());db.execute('INSERT INTO public.yuyan_supplier_cases(case_id,owner_id,version,payload) VALUES(%s,%s,%s,%s)',(cid,owner,case['version'],Jsonb(case)));result={'case_id':cid,'case':case,'calculation':evaluate(case)}
   elif action=='list':
    return {'cases':[{'case_id':r[0],'version':r[1]} for r in db.execute('SELECT case_id,version FROM public.yuyan_supplier_cases WHERE owner_id=%s ORDER BY created_at DESC',(owner,)).fetchall()]}
   else:
    row=db.execute('SELECT payload FROM public.yuyan_supplier_cases WHERE case_id=%s AND owner_id=%s'+(' FOR UPDATE' if action=='change' else ''),(payload['case_id'],owner)).fetchone()
    if not row:raise ValueError('案例不可用')
    case=row[0]
    if action=='change':
     if type(payload['version']) is not int or payload['version']!=case['version']:raise ValueError('版本冲突，请重新载入')
     case=apply_command(case,payload['command']);db.execute('UPDATE public.yuyan_supplier_cases SET version=%s,payload=%s WHERE case_id=%s AND owner_id=%s',(case['version'],Jsonb(case),payload['case_id'],owner))
    result={'case_id':payload['case_id'],'case':case,'calculation':evaluate(case)}
   if mutating:db.execute('INSERT INTO public.yuyan_supplier_commands(owner_id,idempotency_key,payload_hash,response) VALUES(%s,%s,%s,%s)',(owner,payload['key'],digest,Jsonb(result)))
   return result
