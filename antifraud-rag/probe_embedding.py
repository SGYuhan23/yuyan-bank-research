import os,json,datetime,httpx
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2]/'yuqi-core/.env')
r=httpx.post(os.environ['QWEN_ENDPOINT'].rstrip('/')+'/embeddings',headers={'Authorization':'Bearer '+os.environ['QWEN_API_KEY']},json={'model':'text-embedding-v4','input':['供应商更换收款账户','verify supplier bank details']},timeout=40)
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':r.status_code,'model':'text-embedding-v4'}
if r.status_code==200:result['dimensions']=len(r.json()['data'][0]['embedding'])
else:result['error']='embedding endpoint did not accept request'
Path(__file__).with_name('docs').joinpath('embedding-probe.json').write_text(json.dumps(result,indent=2));print(result)
