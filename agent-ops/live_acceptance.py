# coding: utf-8
"""Real authenticated Gateway + Qwen + PostgreSQL acceptance. No mocked tools."""
import json, secrets, time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/'agent-platform'/'.deer-flow'/'acceptance'
LOCAL.mkdir(parents=True,exist_ok=True)
account=LOCAL/'account.json'
if not account.exists():
    account.write_text(json.dumps({'email':'local-agent@example.org','password':'Aa9!'+secrets.token_urlsafe(24)}))
    account.chmod(0o600)
credentials=json.loads(account.read_text())
c=httpx.Client(base_url='http://127.0.0.1:8001',timeout=45,headers={'Origin':'http://127.0.0.1:8001'})
def checked(r):
    if r.is_error: raise RuntimeError(f'{r.request.url.path}: {r.status_code} {r.text[:500]}')
    return r.json()
if checked(c.get('/api/v1/auth/setup-status'))['needs_setup']:
    checked(c.post('/api/v1/auth/initialize',json=credentials))
else:
    checked(c.post('/api/v1/auth/login/local',data={'username':credentials['email'],'password':credentials['password']}))
c.get('/api/v1/auth/me')
c.headers['X-CSRF-Token']=c.cookies.get('csrf_token')
thread=checked(c.post('/api/threads',json={'metadata':{'title':'通用 Agent · 文件与迭代验收'}}))['thread_id']
record={'thread_id':thread,'model':'qwen-plus','mock':False,'runs':[]}
evidence=ROOT/'agent-ops'/'evidence'/f'live-{thread}.json'
def save(): evidence.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
save()
record['upload']=checked(c.post(f'/api/threads/{thread}/uploads',files={'files':('sales.csv',b'item,quantity,unit_price_cents\nA,3,1250\nB,2,800\n','text/csv')}))
save()
prompts=[
'这是合成验收数据。读取本会话上传的 sales.csv，使用 Python 计算每项金额和总额（整数分）。在 outputs 生成 result.json（字段 total_cents、rows）、中文 summary.md 和独立 HTML report.html，并用 present_files 展示。不要联网，不要调用子Agent。必须实际读取和计算，不要只给代码。',
'继续修改刚才的产物：B 的数量改成 5，A 不变。保留第一版文件，生成 result-v2.json（total_cents、rows）、summary-v2.md 和 report-v2.html 并展示。请重新运行计算。']
for prompt in prompts:
    run=checked(c.post(f'/api/threads/{thread}/runs',json={'input':{'messages':[{'type':'human','content':prompt}]},'context':{'model_name':'qwen-plus','thinking_enabled':False,'subagent_enabled':False,'is_plan_mode':True},'config':{'recursion_limit':240},'on_disconnect':'continue'}))
    rid=run['run_id']; print('Started',rid,flush=True)
    deadline=time.monotonic()+420
    while time.monotonic()<deadline:
        status=checked(c.get(f'/api/threads/{thread}/runs/{rid}'))
        if status['status'] not in ('pending','running','queued'): break
        time.sleep(3)
    record['runs'].append(status); save()
    print('Finished',status['status'],flush=True)
    if status['status']!='success': raise RuntimeError('Run did not succeed; see evidence')
record['state']=checked(c.get(f'/api/threads/{thread}/state'))
outputs=list((ROOT/'agent-platform'/'.deer-flow').glob(f'users/*/threads/{thread}/user-data/outputs/result*.json'))
record['output_paths']=[str(p.relative_to(ROOT)) for p in outputs]
results={p.name:json.loads(p.read_text()) for p in outputs}
record['checks']={'first_total':results.get('result.json',{}).get('total_cents')==5350,'second_total':results.get('result-v2.json',{}).get('total_cents')==7750}
save()
assert all(record['checks'].values()),record['checks']
print(json.dumps({'evidence':str(evidence),'checks':record['checks']},ensure_ascii=False))
