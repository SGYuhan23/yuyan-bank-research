"""BM25 baseline and optional real embedding cosine search, without a vector DB."""
from pathlib import Path
from collections import Counter
import re,math,json,hashlib,os,httpx
ROOT=Path(__file__).resolve().parent

def tokenize(s):
 s=s.lower();return re.findall(r'[a-z0-9]+',s)+[s[i:i+2] for i in range(len(s)-1) if all('\u4e00'<=c<='\u9fff' for c in s[i:i+2])]
def bm25(query,units):
 docs=[Counter(tokenize(u['search_labels']+' '+u['text'])) for u in units];q=set(tokenize(query));avg=sum(map(lambda d:sum(d.values()),docs))/max(len(docs),1);scores=[]
 for u,d in zip(units,docs):
  score=0
  for t in q:
   n=sum(t in x for x in docs);f=d[t]
   score+=math.log(1+(len(docs)-n+.5)/(n+.5))*f*2.5/(f+1.5*(.25+.75*sum(d.values())/avg)) if f else 0
  scores.append((u,score))
 return sorted(scores,key=lambda x:-x[1])
def embed(texts):
 endpoint=os.getenv('RAG_EMBEDDING_ENDPOINT',os.getenv('QWEN_ENDPOINT','')).rstrip('/')
 key=os.getenv('RAG_EMBEDDING_KEY',os.getenv('QWEN_API_KEY',''))
 r=httpx.post(endpoint+'/embeddings',headers={'Authorization':'Bearer '+key},json={'model':os.getenv('RAG_EMBEDDING_MODEL','text-embedding-v4'),'input':texts},timeout=60)
 if r.status_code!=200:raise RuntimeError(f'EMBEDDING_UNAVAILABLE_HTTP_{r.status_code}')
 data=r.json();return [x['embedding'] for x in sorted(data['data'],key=lambda x:x['index'])]
def semantic(query,units):
 texts=[u['search_labels']+'\n'+u['text'] for u in units];fingerprint=hashlib.sha256(json.dumps([os.getenv('RAG_EMBEDDING_MODEL','text-embedding-v4'),texts],ensure_ascii=False).encode()).hexdigest()
 path=ROOT/'data'/f'embeddings-{fingerprint}.json'
 if path.exists():vectors=json.loads(path.read_text())
 else:
  vectors=embed(texts);path.write_text(json.dumps(vectors))
 q=embed([query])[0]
 def cosine(v):return sum(a*b for a,b in zip(q,v))/(math.sqrt(sum(a*a for a in q))*math.sqrt(sum(a*a for a in v)))
 return sorted(zip(units,map(cosine,vectors)),key=lambda x:-x[1])
def retrieve(query,mode='auto',units=None,k=3,log=None):
 if mode not in ('auto','bm25','semantic'):raise ValueError('INVALID_RETRIEVER')
 if units is None:units=json.loads((ROOT/'data/units.json').read_text())
 def emit(kind,**data):
  if log:log(kind,**data)
 def search(method):
  emit('retrieval_started',method=method)
  try:ranked=bm25(query,units) if method=='bm25' else semantic(query,units)
  except Exception:
   emit('retrieval_failed',method=method,reason='semantic_service_unavailable' if method=='semantic' else 'retrieval_error',source_ids=[])
   raise RuntimeError('语义检索不可用，本次检索失败；不能据此判断知识库没有相关资料。' if method=='semantic' else 'BM25检索失败') from None
  hits=[{'unit':u,'score':round(score,6)} for u,score in ranked[:k] if method!='bm25' or score>0]
  emit('retrieval_attempt_completed',method=method,unit_ids=[x['unit']['unit_id'] for x in hits],source_ids=[x['unit']['source_id'] for x in hits])
  return hits
 if mode=='semantic':return search('semantic')
 hits=search('bm25')
 if mode=='auto' and not hits:
  emit('retrieval_fallback',from_method='bm25',to_method='semantic',reason='bm25_no_positive_score')
  return search('semantic')
 return hits
