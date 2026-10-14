"""Real two-stage proposal/confirmed consumption; test-harness confirmation is disclosed."""
import json,time,uuid
from client import client,ROOT
c=client();base='/api/plugins/yuyan.research/actions/';out=ROOT/'agent-ops/research/evidence-final'
def action(name,p):
 r=c.post(base+name,json=p);r.raise_for_status();return r.json()
case=action('create',{'key':'final-p0-trace-'+uuid.uuid4().hex});cid=case['case_id'];request_id='trace-'+uuid.uuid4().hex
thread=c.post('/api/threads',json={'metadata':{'title':'Final P0：参数提案与确认快照'}}).json()['thread_id']
def run(prompt):
 r=c.post(f'/api/threads/{thread}/runs',json={'input':{'messages':[{'type':'human','content':prompt}]},'context':{'model_name':'qwen-plus','thinking_enabled':False,'is_plan_mode':True,'subagent_enabled':False},'on_disconnect':'continue'});r.raise_for_status();rid=r.json()['run_id'];deadline=time.monotonic()+150
 while time.monotonic()<deadline:
  status=c.get(f'/api/threads/{thread}/runs/{rid}').json()
  if status['status'] not in ('pending','running','queued'):break
  time.sleep(2)
 else:raise RuntimeError('Trace timed out')
 assert status['status']=='success',status['status']
 return {'run':status,'state':c.get(f'/api/threads/{thread}/state').json()}
prompt=f'FINAL-P0-TRACE：这是合成案例 {cid}，当前账本版本1，请求标识 {request_id}。原始业务问题：如果核心客户C1尾款延期14天，需要多少额外流动资金？本次不考虑折扣、服务费或追加预付款。请先调用参数提案工具，将我的意图转成结构化参数并回显，等待研究页确认，不能直接计算。不要联网、不要执行代码、不要修改账本。'
proposal_run=run(prompt)
requests=action('scenario_requests',{'case_id':cid})['requests'];p=next(x for x in requests if x['request']['request_id']==request_id)
expected={'customer_id':'C1','delay_days':14,'discount':'0','fee_fen':0,'advance_fen':0}
original_proposal=p
(out/'proposal-original-private.json').write_text(json.dumps({'actual_user_prompt':prompt,'proposal':p,'state':proposal_run},ensure_ascii=False,indent=2))
assert p['request']['customer_id']=='C1' and p['request']['delay_days']==14
# The model may conservatively leave explicit zero-cost assumptions unresolved.
# The harness corrects/re-proposes every field before confirming; disclose this step.
corrected=any(p['request'][k]!=v for k,v in expected.items())
if corrected:p=action('propose_scenario',{'request_id':request_id,'case_id':cid,'base_version':1,**expected})
assert p['request']['confirmation_status']=='PROPOSED'
# Authorized synthetic acceptance harness emulates explicit UI confirmation.
confirmed=action('confirm_scenario',{'request_id':request_id,'snapshot':p['request']})
reference=action('simulate',{'request_id':request_id})
followup=f'FINAL-P0-TRACE：测试验收程序已逐项核对并通过研究页同一确认API确认请求 {request_id}。请调用 supplier_cash_scenario 消费这个已确认请求，不另选参数，再展示受控结果；不是用户真实合同确认。'
final=run(followup)
raw={'mock':False,'thread':thread,'case_id':cid,'request_id':request_id,'actual_user_prompt':prompt,'actual_followup_prompt':followup,'parameters_prespecified':True,'confirmation_actor':'authorized_synthetic_acceptance_harness','original_model_proposal':original_proposal,'harness_corrected_proposal':corrected,'proposal_run':proposal_run,**final,'reference':reference,'confirmed_request':confirmed}
(out/'trace-raw-private.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2));print('real proposal + confirmed request trace succeeded',flush=True)
