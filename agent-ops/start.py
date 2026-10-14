"""Start the local platform, retaining logs and stopping only our child processes."""
import os, signal, socket, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLATFORM=ROOT/'agent-platform'
logs=PLATFORM/'logs';logs.mkdir(exist_ok=True)
python=PLATFORM/'backend/.venv/bin/python'
node=os.environ.get('AGENT_NODE','node')
version=subprocess.check_output([node,'--version'],text=True).strip()
if int(version.lstrip('v').split('.')[0])<22:
    raise SystemExit('Node 22+ required. Set AGENT_NODE to the Node executable path.')
for port in (3000,8001):
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',port))==0:
            raise SystemExit(f'Port {port} already in use; existing processes were left unchanged.')
subprocess.run(['docker','compose','-f',str(ROOT/'agent-ops/compose.yaml'),'up','-d','--wait'],check=True)
children=[];handles=[]
def shutdown(*_):
    for p in children:
        if p.poll() is None: p.terminate()
    for p in children:
        try:p.wait(timeout=45)
        except subprocess.TimeoutExpired:p.kill()
    for f in handles:f.close()
    raise SystemExit(0)
signal.signal(signal.SIGINT,shutdown);signal.signal(signal.SIGTERM,shutdown)
commands=[('gateway',[str(python),str(ROOT/'agent-ops/gateway.py')],ROOT),('frontend',[node,'node_modules/next/dist/bin/next','dev','--hostname','127.0.0.1','--port','3000'],PLATFORM/'frontend')]
for name,command,cwd in commands:
    handle=open(logs/f'{name}.log','a',encoding='utf-8');handles.append(handle)
    children.append(subprocess.Popen(command,cwd=cwd,stdout=handle,stderr=subprocess.STDOUT))
print('Starting local platform: http://127.0.0.1:3000/workspace',flush=True)
print('Logs: agent-platform/logs/. Ctrl+C stops these two services, retaining database and files.',flush=True)
while True:
    if any(p.poll() is not None for p in children):
        print('A service stopped. Inspect its log.',flush=True);shutdown()
    time.sleep(1)
