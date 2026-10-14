"""Offline search transport tests, with explicitly synthetic provider responses."""
import httpx,pytest
from web_research import search_qwen

def test_no_sources_is_failure_even_if_model_claims_answer():
 def handle(r):return httpx.Response(200,json={'output':{'choices':[{'message':{'content':'confident invented answer'}}]}})
 out=search_qwen('query',endpoint='https://dashscope.aliyuncs.com/test',model='qwen-plus',key='test',transport=httpx.MockTransport(handle))
 assert out['status']=='unavailable' and 'confident' not in str(out)

def test_sources_preserved_synthesis_not_used_as_fact():
 def handle(r):return httpx.Response(200,json={'output':{'search_info':{'search_results':[{'title':'Official','url':'https://example.org/news'}]},'choices':[{'message':{'content':'invented synthesis'}}]},'usage':{'plugins':{'search':{'count':1}}}})
 out=search_qwen('query',endpoint='https://dashscope.aliyuncs.com/test',model='qwen-plus',key='test',transport=httpx.MockTransport(handle))
 assert out['results'][0]['url']=='https://example.org/news'
 assert 'invented synthesis' not in str(out)
 assert out['provider']=='qwen-search'

def test_error_does_not_leak_secret():
 out=search_qwen('query',endpoint='https://dashscope.aliyuncs.com/test',model='qwen-plus',key='secret',transport=httpx.MockTransport(lambda r:httpx.Response(401,text='secret')))
 assert out['status']=='unavailable' and 'secret' not in str(out)

def test_tool_boundary_preserves_first_query(monkeypatch):
 from types import SimpleNamespace
 from langchain_core.messages import HumanMessage
 import web_research
 seen=[]
 def search(query,**kwargs):
  seen.append(query)
  return {'status':'success','results':[]}
 monkeypatch.setattr(web_research,'search_qwen',search)
 monkeypatch.setattr(web_research,'english_query',lambda *a,**k:None)
 web_research.web_search_tool.func(runtime=SimpleNamespace(state={'messages':[HumanMessage('你知道 Zeta-X9 吗')]}),query='old product')
 assert seen==['你知道 Zeta-X9 吗']
