from runtime import configure,OPS
configure()
import httpx,os,json
r=httpx.post(os.environ['QWEN_ENDPOINT']+'/chat/completions',headers={'Authorization':'Bearer '+os.environ['QWEN_API_KEY']},json={'model':os.environ['QWEN_MODEL'],'messages':[{'role':'user','content':'理想 L8 Livis 是什么？搜索官方发布消息并给出来源。'}],'enable_thinking':False,'enable_search':True,'search_options':{'forced_search':True,'enable_source':True,'enable_citation':True},'max_tokens':700},timeout=90)
print('status',r.status_code)
if r.status_code==200:
 d=r.json();(OPS/'evidence/search-provider-probe.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));print(json.dumps(d,ensure_ascii=False)[:7000])
