"""Project-authored internal analyst exercise; no real banking data or access."""
import json,math
from .contracts import CaseRecord,Recommendation
from .graph_lab import generate

def create(store,model='tabular'):
    if model not in ('tabular','graphsage'):raise ValueError('INVALID_GRAPH_MODEL')
    graph,_=generate('dev',seed=155,groups=6)
    return store.create(CaseRecord(query='内部分析演练：仅有10%的账户核查名额，请按合成交易线索排列待核查账户，并保留正常业务可能性。',mode='graph_lab',requester_role='内部分析演练员（模拟角色）',as_of=graph['as_of'],fields={'synthetic_graph':graph,'graph_model':model,'review_fraction':.1,'purpose':'project_authored_internal_analyst_exercise'}))

def draft(case,tool_results):
    observations={}
    for e in case.evidence:
        if e.kind=='synthetic_observation':
            try:observations[e.origin_id]=(e,json.loads(e.statement))
            except (ValueError,TypeError):continue
    rows={t['tool_name']:observations.get(t['call_id']) for t in tool_results}
    analysis=rows.get('graph');scoring=rows.get('score')
    failed=any(t['status']!='ok' for t in tool_results)
    if failed or not analysis or not scoring or scoring[1].get('status')!='ok':
        return {'status':'needs_input','summary':'合成演练工具未全部完成，未生成核查名单。请检查模型文件或工具错误。','recommendations':[],'unresolved_questions':['模型或交易图不可用；不能把失败解释为没有异常。'],'limitations':['仅项目编写的内部分析演练，不接入真实银行交易。']}
    ev,a=analysis;sev,s=scoring;graph=case.fields['synthetic_graph'];edges=[e for e in graph['edges'] if e['at']<=case.as_of[:10]]
    nodes={e[k] for e in edges for k in ('from','to')};k=max(1,math.ceil(len(nodes)*.1));rankings=s['rankings'][:k]
    if len(rankings)!=min(k,len(nodes)) or any(r['account'] not in nodes for r in rankings):raise ValueError('INVALID_RANKING_COVERAGE')
    candidates=[];recs=[]
    for rank,row in enumerate(rankings,1):
        n=row['account'];incident=[e for e in edges if n in (e['from'],e['to'])]
        incoming=[e for e in incident if e['to']==n];outgoing=[e for e in incident if e['from']==n]
        questions=['本项目演练问题：这些交易对应哪些合同、发票或资金用途说明？当前材料未提供。','本项目演练问题：收付对手是否具有正常结算、归集或分拨关系？不能仅凭结构排除这些解释。']
        cyclic=any(n in c for c in a['cyclic_components'])
        if cyclic:questions.append('本项目演练问题：环路是否有正常资金归集或结算依据？形成环路本身不证明诈骗。')
        candidates.append({'rank':rank,**row,'incident_edge_ids':[e['id'] for e in incident],'incoming_count':len(incoming),'outgoing_count':len(outgoing),'in_cycle':cyclic,'questions':questions,'question_origin':'project_authored_training','missing_business_context':True})
        recs.append(Recommendation(scene='synthetic_internal_analyst',target='本次合成演练账户 '+n,trigger='仅本次10%人工核查名额；排序不证明诈骗，待核实业务用途',action=f'将合成账户 {n} 列为第{rank}个待核查对象，核对所关联交易的业务用途与正常结算解释。',supporting_evidence_ids=[ev.evidence_id,sev.evidence_id],unmet_conditions=questions,counter_evidence_ids=[]).model_dump())
    return {'status':'pending_review','summary':f'合成内部分析演练：{len(nodes)}个账户，按10%名额选取{k}个待核查账户；等待人工判断。','recommendations':recs,'unresolved_questions':['材料没有真实合同、客户身份或交易目的；名单仅用于演练。'],'limitations':['问题由本项目编写，非银行内部操作规程。','排序分数未校准，不是诈骗概率；不能据此冻结、拦截或定罪。','模拟分析角色不构成企业身份认证或全行数据权限。'],'graph_exercise':{'synthetic':True,'authored':True,'budget_fraction':.1,'budget_k':k,'accounts':len(nodes),'model':case.fields.get('graph_model','tabular'),'model_version':s['model_version'],'candidates':candidates,'transactions':edges,'analysis':a,'score':s}}
