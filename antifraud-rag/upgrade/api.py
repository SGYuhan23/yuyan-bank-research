"""Local HTTP handlers used by existing server; old /api/run remains available."""
import json,threading,base64,hashlib
from .contracts import CaseRecord,Artifact,Span,uid
from .store import Store
from .agent import Agent
from . import training
STORE=Store();RUNS={};LOCK=threading.Lock()
def get(path):
    if path=='/api/scenarios':return [training.public(s) for s in training.scenarios().values()]
    if path.startswith('/api/cases/'):return STORE.export(path.split('/')[-1])
    if path.startswith('/api/jobs/'):
        rid=path.split('/')[-1]
        return RUNS[rid].data if rid in RUNS else STORE.result(rid)
    raise ValueError('NOT_FOUND')
def post(path,d):
    if path=='/api/cases':return STORE.create(CaseRecord(query=d['query'],mode=d.get('mode','case'),requester_role=d.get('requester_role','unknown'),task_scene=d.get('task_scene',[]),fields=d.get('fields',{}),jurisdiction=d.get('jurisdiction','Australia'))).model_dump()
    if path=='/api/case/update':return STORE.update(d['case_id'],d['version'],d['patch']).model_dump()
    if path=='/api/case/upload':
        c=STORE.get(d['case_id'])
        if c.version!=d['version']:raise ValueError('STALE_VERSION')
        mime=d['mime'];content=d['content']
        if mime not in ('text/plain','image/png','image/jpeg'):raise ValueError('UNSUPPORTED_MIME')
        raw=base64.b64decode(content,validate=True) if mime.startswith('image/') else content.encode()
        if len(raw)>3_000_000:raise ValueError('ARTIFACT_TOO_LARGE')
        if mime.startswith('image/'):
            from PIL import Image
            import io
            im=Image.open(io.BytesIO(raw))
            if im.width*im.height>12000000:raise ValueError('IMAGE_TOO_LARGE')
            im.verify()
        a=Artifact(case_id=c.case_id,sha256=hashlib.sha256(raw).hexdigest(),mime=mime,origin='user_supplied',content=content,spans=[] if mime.startswith('image/') else [Span(method='user_text',start=0,end=len(content),text=content)])
        return STORE.update(c.case_id,c.version,{'artifacts':[x.model_dump() for x in c.artifacts]+[a.model_dump()]}).model_dump()
    if path=='/api/case/correct':
        c=STORE.get(d['case_id'])
        if c.version!=d['version']:raise ValueError('STALE_VERSION')
        found=False
        for a in c.artifacts:
            if a.artifact_id==d['artifact_id']:
                found=True;a.corrections.append({'before_hash':a.sha256,'operator':d['operator'],'text':d['text']});a.spans=[Span(method='human_correction',text=d['text'],start=0,end=len(d['text']))]
        if not found:raise ValueError('ARTIFACT_NOT_FOUND')
        return STORE.update(c.case_id,c.version,{'artifacts':[a.model_dump() for a in c.artifacts]}).model_dump()
    if path=='/api/case/run':
        with LOCK:
            if any(a.data['status']=='running' for a in RUNS.values()):raise ValueError('RUN_IN_PROGRESS')
            a=Agent(STORE,d['case_id'],d['version'],retriever=d.get('retriever','auto'));RUNS[a.id]=a
        threading.Thread(target=a.run,daemon=True).start();return {'run_id':a.id}
    if path=='/api/review':return STORE.review(d)
    if path=='/api/training/start':return training.start(STORE,d['scenario_id'])
    if path=='/api/training/turn':return training.turn(STORE,d['session_id'],d['text'])
    if path=='/api/training/debrief':
        result=training.debrief(STORE,d['session_id'],d.get('revision'))
        result['semantic_review']=training.semantic_debrief(STORE,d['session_id'])
        return result
    if path=='/api/training/assist':
        from pipeline import RagRun
        context=training.learner_context(STORE,d['session_id'])
        # No scenario library/latent truth passed; this object sees only visible transcript.
        class Caller:
            model=RagRun.model
            def log(self,*a,**kw):pass
        return Caller().model([{'role':'system','content':'仅依据可见培训对话建议下一条核实追问，不猜隐藏事实。返回JSON {"question":str}。'},{'role':'user','content':json.dumps(context,ensure_ascii=False)}],'training_assistant')
    if path=='/api/graph/sample':
        from .graph_lab import generate
        from .contracts import ToolCall
        from .tools import invoke
        graph,_=generate('dev',seed=55,groups=6)
        case=STORE.create(CaseRecord(query='合成交易结构与排序实验',mode='graph_lab',requester_role='实验研究者',as_of=graph['as_of'],fields={'synthetic_graph':graph}))
        results=[]
        for name in ('graph','score'):
            tool,evidence=invoke(case,ToolCall(tool_name=name));case.evidence.extend(evidence);results.append(tool.model_dump())
        rid=uid();case.status='pending_review'
        STORE.finish(case,{'run_id':rid,'case_id':case.case_id,'case_version':case.version,'status':'pending_review','recommendations':[],'evidence':[e.model_dump() for e in case.evidence],'tool_results':results,'execution':'live_synthetic'})
        observations={e.origin_id:json.loads(e.statement) for e in case.evidence}
        return {'case_id':case.case_id,'case_version':case.version,'run_id':rid,'graph':graph,'analysis':observations.get(results[0]['call_id'],{'notice':'图工具失败'}),'score':observations.get(results[1]['call_id'],{'status':results[1]['status']}),'evidence':[e.model_dump() for e in case.evidence],'tool_results':results}
    raise ValueError('NOT_FOUND')
