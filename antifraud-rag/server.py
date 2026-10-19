"""Local single-user server. No bank operations, no deployment claim."""
import argparse,json,re,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from dotenv import load_dotenv
from pipeline import ROOT,RagRun
BUSY=threading.Semaphore(1)
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,obj,code=200,ctype='application/json; charset=utf-8'):
  raw=obj if isinstance(obj,bytes) else json.dumps(obj,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  if self.path.startswith(('/api/cases/','/api/jobs/','/api/scenarios')):
   from upgrade.api import get
   try:return self.send(get(self.path))
   except (ValueError,KeyError):return self.send({'error':'NOT_FOUND'},404)
  if self.path.startswith('/api/run/'):
   rid=self.path.removeprefix('/api/run/')
   if not re.fullmatch('[a-f0-9]{16}',rid):return self.send({'error':'INVALID_RUN'},400)
   p=ROOT/'runs'/rid/'run.json'
   if not p.exists():return self.send({'error':'NOT_FOUND'},404)
   return self.send(json.loads(p.read_text()))
  files={'/':'upgrade.html','/upgrade.js':'upgrade.js','/upgrade.css':'upgrade.css','/legacy':'index.html','/app.js':'app.js','/style.css':'style.css'}
  if self.path not in files:return self.send({'error':'NOT_FOUND'},404)
  p=ROOT/'web'/files[self.path];return self.send(p.read_bytes(),ctype={'.html':'text/html','.js':'text/javascript','.css':'text/css'}[p.suffix]+'; charset=utf-8')
 def do_POST(self):
  if self.headers.get('Origin') not in [None,'http://'+self.headers.get('Host','')]:return self.send({'error':'ORIGIN_REJECTED'},403)
  if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send({'error':'JSON_REQUIRED'},415)
  try:
   length=int(self.headers.get('Content-Length',0))
   if not 0<length<4500000:raise ValueError('INVALID_SIZE')
   d=json.loads(self.rfile.read(length))
   if self.path!='/api/run':
    from upgrade.api import post
    return self.send(post(self.path,d))
   if not BUSY.acquire(False):return self.send({'error':'已有研究正在执行，请等待结束。'},409)
   try:run=RagRun(d['query'],d['task'],d.get('retriever','auto'))
   except Exception:BUSY.release();raise
   def work():
    try:run.run()
    finally:BUSY.release()
   threading.Thread(target=work,daemon=True).start();return self.send({'run_id':run.id},202)
  except (ValueError,KeyError,TypeError) as e:return self.send({'error':str(e)},400)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--env');p.add_argument('--port',type=int,default=8770);a=p.parse_args()
 if a.env:load_dotenv(a.env)
 print(f'反诈知识与培训辅助 http://127.0.0.1:{a.port}',flush=True);ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
