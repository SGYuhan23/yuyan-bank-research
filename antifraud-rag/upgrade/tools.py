"""Trusted read-only adapters. No arbitrary URL visits or executable model arguments."""
import base64,io,json,re,time,os,ipaddress
from decimal import Decimal,InvalidOperation
from urllib.parse import urlsplit
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from .contracts import *
from retrieval import retrieve,ROOT

def material(c):return c.query+'\n'+'\n'.join(e.statement for e in c.evidence if e.kind=='reported_claim')+'\n'+'\n'.join(s.text for a in c.artifacts for s in a.spans if s.method in ('user_text','human_correction','ocr'))
def allowed(c):
    result=['guidance']
    if re.search(r'\d{4}-\d{2}-\d{2}|上周|昨天|今天|明天|前天',material(c)):result.append('timeline')
    if c.artifacts:result.append('extract')
    if re.search(r'https?://[^\s<>]+',material(c)):result.append('links')
    if c.fields.get('old') and c.fields.get('new'):result.append('compare')
    if c.mode=='graph_lab' and c.fields.get('synthetic_graph'): result+=['graph','score']
    return result

def invoke(c,call,log=lambda *a,**k:None):
    start=time.monotonic();name=call.tool_name;args=call.args
    if name not in allowed(c):raise ValueError('TOOL_NOT_APPLICABLE:'+name)
    valid={'extract':set(),'guidance':{'query','mode'},'links':set(),'compare':set(),'timeline':set(),'graph':set(),'score':set()}
    if set(args)-valid[name]:raise ValueError('UNEXPECTED_TOOL_ARGUMENT')
    t=ToolResult(case_id=c.case_id,case_version=c.version,tool_name=name,validated_args=args,args_hash=digest(args),input_evidence=[{'id':'case-input:'+c.case_id,'hash':digest({'query':c.query,'fields':c.fields,'artifacts':[a.model_dump() for a in c.artifacts]})}]+[{'id':e.evidence_id,'hash':e.source_hash} for e in c.evidence],status='ok',observations=[],limitations=[],latency_seconds=0,data_origin='user_supplied')
    evidence=[]
    def add(kind,statement,origin,span,limitations,hash_value=None,extra=None):
        e=Evidence(case_id=c.case_id,case_version=c.version,kind=kind,origin_id=origin,span=span,source_hash=hash_value or digest(statement),jurisdiction=c.jurisdiction,statement=statement,limitations=limitations)
        evidence.append(e);t.observations.append({'evidence_id':e.evidence_id,'statement':statement,**(extra or {})})
    try:
        if name=='extract':
            for a in c.artifacts:
                spans=a.spans
                if a.mime.startswith('image/') and not any(s.method=='human_correction' for s in spans):
                    try:
                        from PIL import Image
                        from .ocr import extract
                        raw=base64.b64decode(a.content,validate=True)
                        im=Image.open(io.BytesIO(raw))
                        if im.width*im.height>12000000:raise ValueError('IMAGE_TOO_LARGE')
                        d=extract(raw)
                        spans=[Span(method='ocr',text=x['text'],region=[int(x['region_normalized_bottom_left'][0]*im.width),int((1-x['region_normalized_bottom_left'][1]-x['region_normalized_bottom_left'][3])*im.height),int(x['region_normalized_bottom_left'][2]*im.width),int(x['region_normalized_bottom_left'][3]*im.height)]) for x in d]
                    except Exception as exc:
                        t.status='partial';t.limitations.append('OCR unavailable: '+type(exc).__name__+'; 请人工转录核对，未读取图片内容');continue
                for s in spans:add('reported_claim',s.text,a.artifact_id,s.model_dump(),['材料陈述，不证明真实到账；OCR/人工转录可能有误'],a.sha256)
        elif name=='guidance':
            query=args.get('query',c.query)
            if not isinstance(query,str) or len(query)>12000:raise ValueError('INVALID_QUERY')
            if c.jurisdiction!='Australia':
                t.status='unavailable';t.limitations=['当前只有澳大利亚公开资料，不能当作本地区流程'];return t,evidence
            units=json.loads((ROOT/'data/units.json').read_text())
            # Retrieval date is not a publication date; unknown dates remain explicit.
            units=[u for u in units if not u.get('published_or_updated_at') or u['published_or_updated_at']<=c.as_of[:10]]
            found=retrieve(query,args.get('mode','auto'),units=units,log=log)
            for row in found:
                u=row['unit'];add('public_guidance',u['text'],u['source_id'],{'section':u['section'],'url':u['url'],'unit_id':u['unit_id'],'published_at':u.get('published_or_updated_at')},[u['limitations'],'未知发布日期不能证明在案件时点已生效'],u['unit_sha256'],{'unit':u})
            t.data_origin='public_sources'
        elif name=='links':
            for url in set(re.findall(r'https?://[^\s<>]+',material(c))):
                p=urlsplit(url);host=(p.hostname or '').encode('idna').decode();private=False
                try:private=ipaddress.ip_address(host).is_private
                except ValueError:private=host in ('localhost','') or host.endswith('.local')
                obs={'hostname':host,'scheme':p.scheme,'private_or_local':private,'credentials_present':bool(p.username),'query_and_path_not_sent':True,'reputation':'unavailable','visited':False}
                # Optional fixed-endpoint provider. Only origin sent; never follow suspect URL.
                key=os.getenv('SAFEBROWSING_API_KEY')
                if key and not private:
                    import httpx
                    try:
                        r=httpx.post('https://safebrowsing.googleapis.com/v4/threatMatches:find',params={'key':key},json={'client':{'clientId':'antifraud-local','clientVersion':'1'},'threatInfo':{'threatTypes':['MALWARE','SOCIAL_ENGINEERING'],'platformTypes':['ANY_PLATFORM'],'threatEntryTypes':['URL'],'threatEntries':[{'url':p.scheme+'://'+host+'/'}]}},timeout=8,follow_redirects=False)
                        if r.status_code==200:obs['reputation']='flagged' if r.json().get('matches') else 'not_flagged'
                    except Exception:pass
                if obs['reputation']=='unavailable':t.status='partial'
                add('tool_observation',json.dumps(obs,ensure_ascii=False),t.call_id,{'material':'URL origin only'},['not_flagged不代表安全；未访问网址；未检查路径和查询参数；域名不是邀约真实性证明'])
        elif name=='compare':
            old,new=c.fields['old'],c.fields['new']
            for key in ('account','name','amount','currency','date'):
                if key not in old or key not in new:continue
                a,b=str(old[key]),str(new[key]);equal=a==b
                if key=='amount':
                    if old.get('currency')!=new.get('currency') or not old.get('currency'):equal=None
                    else:equal=Decimal(a)==Decimal(b)
                add('tool_observation',json.dumps({'field':key,'old':a,'new':b,'equal':equal},ensure_ascii=False),t.call_id,{'field':key},['仅比较用户输入，未验证银行账户、身份或实际交易'])
        elif name=='timeline':
            text=material(c);dates=[{'date':m.group(),'start':m.start(),'end':m.end(),'certainty':'literal_date_not_verified'} for m in re.finditer(r'\d{4}-\d{2}-\d{2}',text)]
            relative=[m.group() for m in re.finditer('上周|昨天|今天|明天|前天',text)]
            add('tool_observation',json.dumps({'dated_mentions':dates,'relative_unresolved':relative,'order':'按原材料位置，不推定事件先后','conflicts':'不同陈述同时保留，日期本身不判真实性'},ensure_ascii=False),t.call_id,{'start':0,'end':len(text)},['材料可能有矛盾；相对日期须由用户核对'])
        elif name in ('graph','score'):
            from .graph_lab import analyze,score
            graph=c.fields['synthetic_graph'];result=analyze(graph,c.as_of) if name=='graph' else score(graph,c.as_of)
            if result.get('status')=='unavailable':t.status='unavailable'
            add('synthetic_observation',json.dumps(result,ensure_ascii=False),t.call_id,{'edges':result.get('edge_ids',[])},['仅合成实验；分数非诈骗概率；结构/归因不证明违法']);t.data_origin='project_synthetic'
    except Exception as exc:
        t.status='unavailable' if name in ('guidance','score') else 'failed';t.limitations.append(type(exc).__name__+': service or input failed; cannot infer absence of evidence')
    finally:t.latency_seconds=round(time.monotonic()-start,3)
    return t,evidence
