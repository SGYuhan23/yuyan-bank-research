from runtime import configure,OPS
configure()
import httpx,os,json
r=httpx.post('https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',headers={'Authorization':'Bearer '+os.environ['QWEN_API_KEY']},json={'model':os.environ['QWEN_MODEL'],'input':{'messages':[{'role':'user','content':'理想 L8 Livis 官方上市发布。请简短给出搜索所得信息。'}]},'parameters':{'enable_thinking':False,'enable_search':True,'search_options':{'forced_search':True,'enable_source':True},'result_format':'message','max_tokens':300}},timeout=90)
print('status',r.status_code)
if r.status_code==200:
 d=r.json();(OPS/'evidence/search-native-probe.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));print(json.dumps(d,ensure_ascii=False)[:10000])
