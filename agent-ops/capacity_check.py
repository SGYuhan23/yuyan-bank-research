"""Read-only HTTP probes + isolated test conversation; mixed-host capacity evidence.
This is NOT a 4GB Linux whole-stack stress test. Credentials are never exported.
"""
import concurrent.futures, datetime, json, re, subprocess, threading, time
from pathlib import Path
import httpx
from client import client, ROOT
OUT = ROOT/'agent-ops/evidence/capacity-20261013'
OUT.mkdir(parents=True, exist_ok=True)
stop = threading.Event()
samples=[]; probes=[]
NAMES=('yuqi-agent-platform-db-1','lottery-replica-')
def cmd(args):
    return subprocess.run(args, capture_output=True,text=True,timeout=20).stdout

def sample():
    while not stop.is_set():
        at=time.time(); containers=[]; host=[]
        for line in cmd(['docker','stats','--no-stream','--format','{{json .}}']).splitlines():
            try: row=json.loads(line)
            except ValueError: continue
            if row['Name'].startswith(NAMES+('yuqi-agent-sandbox',)):
                containers.append({k:row[k] for k in ('Name','MemUsage','CPUPerc','PIDs')})
        for line in cmd(['ps','-axo','pid,rss,command']).splitlines():
            if not any(s in line for s in ('agent-ops/gateway.py','xybjz-app.jar','node scripts/serve.mjs','next-server (')): continue
            if '/bin/bash' in line or 'capacity_check' in line: continue
            parts=line.strip().split(None,2)
            if len(parts)!=3: continue
            pid=int(parts[0]); fp=cmd(['/usr/bin/footprint','-p',str(pid)])
            match=re.search(r'Footprint:\s+([\d.]+)\s+(\w+)', fp)
            host.append({'pid':pid,'rss_kib':int(parts[1]),'process':parts[2], 'footprint':match.group(0) if match else None})
        samples.append({'at':at,'containers':containers,'host':host})
        (OUT/'resources.json').write_text(json.dumps(samples,ensure_ascii=False,indent=2))
        stop.wait(3)

def probe_loop():
    urls=['http://127.0.0.1:3002/','http://127.0.0.1:3002/research/fuling-research.pdf','http://127.0.0.1:18000/','http://127.0.0.1:18000/api/v1/activity/query_sku_product_list_by_activity_id?activityId=1989345533881966594']
    with httpx.Client(timeout=20,follow_redirects=True) as c:
        while not stop.is_set():
            for url in urls:
                t=time.monotonic()
                try:
                    r=c.get(url); good=r.status_code==200
                    if '/api/v1/activity/' in url: good=good and r.json().get('code')==1000
                    if url.endswith('.pdf'): good=good and r.content.startswith(b'%PDF')
                    probes.append({'url':url,'ok':good,'status':r.status_code,'seconds':round(time.monotonic()-t,3),'bytes':len(r.content)})
                except Exception as e: probes.append({'url':url,'ok':False,'error':type(e).__name__})
            (OUT/'probes.json').write_text(json.dumps(probes,indent=2))
            stop.wait(5)

def main():
    workers=[threading.Thread(target=sample),threading.Thread(target=probe_loop)]
    for w in workers:w.start()
    result={'mock':False,'environment':'macOS application processes + Docker Linux dependencies; no whole-stack 4GB cap','started_at':datetime.datetime.now().isoformat()}
    c=client(); t=time.monotonic()
    try:
        r=c.post('/api/threads',json={'metadata':{'title':'低频部署容量验收 · 独立测试会话'}});r.raise_for_status();tid=r.json()['thread_id'];result['thread_id']=tid
        r=c.post(f'/api/threads/{tid}/uploads',files={'files':('capacity.csv',b'item,quantity,unit_price_cents\nA,3,1250\nB,2,800\n','text/csv')});r.raise_for_status()
        prompt='读取本会话上传的 capacity.csv，用 Python 实际计算每项金额和总额，金额为整数分。在 outputs 保存 capacity-result.json，字段 total_cents 和 rows。再生成一个简单中文 capacity-report.html 并用 present_files 展示这两个文件。合成测试数据，无需联网，不要用子Agent。完成后停止。'
        r=c.post(f'/api/threads/{tid}/runs',json={'input':{'messages':[{'type':'human','content':prompt}]},'context':{'model_name':'qwen-plus','thinking_enabled':False,'subagent_enabled':False,'is_plan_mode':True},'on_disconnect':'continue'});r.raise_for_status();rid=r.json()['run_id']; result['run_id']=rid;print('Real Qwen test started',flush=True)
        while time.monotonic()-t<300:
            r=c.get(f'/api/threads/{tid}/runs/{rid}');r.raise_for_status();status=r.json()['status']
            if status not in ('pending','running','queued'):break
            time.sleep(3)
        else:
            c.post(f'/api/threads/{tid}/runs/{rid}/cancel').raise_for_status();status='test_deadline_cancelled'
        result['status']=status
        files=list((ROOT/'agent-platform/.deer-flow').glob(f'users/*/threads/{tid}/user-data/outputs/capacity-result.json'))
        result['independent_reference_cents']=5350
        result['correct_total']=bool(files) and json.loads(files[0].read_text()).get('total_cents')==5350
        result['html_present']=bool(list((ROOT/'agent-platform/.deer-flow').glob(f'users/*/threads/{tid}/user-data/outputs/capacity-report.html')))
    except Exception as e: result['error']=type(e).__name__+': '+str(e)[:200]
    finally:
        result['seconds']=round(time.monotonic()-t,2)
        stop.set()
        for w in workers:w.join()
        result['http_checks']=len(probes);result['http_failures']=sum(not p['ok'] for p in probes)
        (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
