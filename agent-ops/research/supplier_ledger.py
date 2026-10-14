"""Order cash event domain. Integer fen; immutable POSTED facts; explicit synthetic clock.
State transitions are commands; simulations deep-copy and never commit.
"""
from copy import deepcopy
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal,ROUND_HALF_UP
import hashlib,json

STATUSES={'PROJECTED','CONFIRMED','POSTED','CANCELLED','DISPUTED'}
TYPES={'purchase_order','materials','production','shipment','acceptance','invoice','receivable','prepayment','fee','quality_deduction'}
CASH={'materials','production','shipment','receivable','prepayment','fee','quality_deduction'}

def now():return datetime.now(timezone.utc).isoformat()
def rounding(v):return int(Decimal(v).quantize(Decimal(1),rounding=ROUND_HALF_UP))
def day(v):
 if not isinstance(v,str):raise ValueError('日期必须为ISO日期')
 return date.fromisoformat(v)
def validate_event(e):
 if e['status'] not in STATUSES or e['event_type'] not in TYPES:raise ValueError('非法状态或事件类型')
 if type(e['amount_fen']) is not int or abs(e['amount_fen'])>10**12:raise ValueError('金额必须为有界整数分')
 day(e['planned_date'])
 if e['event_type'] in {'receivable','prepayment'} and e['amount_fen']<0:raise ValueError('收入不能为负')
 if e['event_type'] in {'materials','production','shipment','fee','quality_deduction'} and e['amount_fen']>0:raise ValueError('支出或扣款不能为正')
 if e['event_type'] not in CASH and e['amount_fen']!=0:raise ValueError('流程节点不重复计现金')
 if e['status'] in {'CONFIRMED','POSTED'} and not e['evidence'].strip():raise ValueError('确认/入账需要证据说明')
 if e['status']=='POSTED':
  if e['event_type'] not in CASH or not e['posted_date']:raise ValueError('只有现金事件可入账')
  day(e['posted_date'])
 if e['status']=='CONFIRMED' and not e['confirmed_date']:raise ValueError('确认时间缺失')

class ReconciliationMismatch(ValueError):
 def __init__(self, computed, observed):
  self.difference_fen=observed-computed
  super().__init__(f'余额不一致，全部回滚：观察余额−计算余额={self.difference_fen}分；计算余额={computed}分')

def derive_payment_conditions(case, stamp=None):
 """Only PROJECTED dates derive; confirmed/postings are never silently rescheduled."""
 events={e['event_id']:e for e in case['events']}
 for order in case['orders']:
  terms=order.get('payment_terms',{'type':'FIXED_DATE'})
  if terms['type']=='FIXED_DATE':continue
  if terms['type']!='AFTER_INVOICE':raise ValueError('未知合同支付条件')
  for key in ('invoice_after_acceptance_days','payment_after_invoice_days'):
   if type(terms.get(key)) is not int or not 0<=terms[key]<=180:raise ValueError('合同天数必须为0..180')
  chain=[events.get(terms.get(k)) for k in ('acceptance_event_id','invoice_event_id','receivable_event_id')]
  if any(e is None or e['order_id']!=order['order_id'] for e in chain):raise ValueError('合同依赖节点缺失/跨订单')
  acceptance,invoice,receivable=chain
  originals={e['event_id']:deepcopy(e) for e in (invoice,receivable)}
  if [e['event_type'] for e in chain]!=['acceptance','invoice','receivable']:raise ValueError('合同依赖节点类型错误')
  blocked=any(e['status'] in {'DISPUTED','CANCELLED'} for e in chain[:2])
  if invoice['status']=='PROJECTED':
   invoice['planned_date']=str(day(acceptance['planned_date'])+timedelta(days=terms['invoice_after_acceptance_days']))
  if receivable['status']=='PROJECTED':
   receivable['planned_date']=str(day(invoice['planned_date'])+timedelta(days=terms['payment_after_invoice_days']))
  for e in (invoice,receivable):
   if e['status']!='POSTED':
    e['prediction_confidence']='BLOCKED_BY_DISPUTE' if blocked else 'CONDITIONAL_UNVERIFIED' if any(x['status']=='PROJECTED' for x in chain[:2]) else 'CONDITIONS_DOCUMENTED'
    if stamp and originals[e['event_id']]!=e:e['last_updated_at']=stamp

def record_actuals_and_reconcile(case, command):
 required={'operation','event_id','reason','postings','as_of','observed_balance_fen'}
 if set(command)!=required or not isinstance(command['reason'],str) or not command['reason'].strip():raise ValueError('核对命令字段不完整')
 postings=command['postings'];boundary=day(command['as_of'])
 if not isinstance(postings,list) or not 1<=len(postings)<=100:raise ValueError('需要1..100笔完整实际收付，不支持部分核销')
 if boundary<day(case['as_of']):raise ValueError('核对边界不可倒退')
 if type(command['observed_balance_fen']) is not int:raise ValueError('观察余额须为整数分')
 result=deepcopy(case);before=deepcopy(case);seen=set()
 for posting in postings:
  if not isinstance(posting,dict) or set(posting) not in ({'event_id','posted_date','evidence'}, {'event_id','posted_date','evidence','new_event'}):raise ValueError('实际收付字段错误')
  eid=posting['event_id']
  if not isinstance(eid,str) or not eid.strip() or eid in seen:raise ValueError('重复/无效收付事件')
  seen.add(eid)
  matches=[e for e in result['events'] if e['event_id']==eid]
  if 'new_event' in posting:
   if matches:raise ValueError('新增收付事件已存在')
   n=posting['new_event']
   if not isinstance(n,dict) or set(n)!={'order_id','event_type','amount_fen','source'}:raise ValueError('新增收付字段错误')
   if n['order_id'] not in {o['order_id'] for o in case['orders']} or n['event_type'] not in CASH:raise ValueError('实际现金事件订单/类型无效')
   if not isinstance(n['source'],str) or not n['source'].strip():raise ValueError('实际收付需来源')
   e={**n,'event_id':eid,'planned_date':posting['posted_date'],'confirmed_date':posting['posted_date'],'status':'CONFIRMED'}
   result['events'].append(e)
  else:
   if len(matches)!=1 or matches[0]['status']!='CONFIRMED':raise ValueError('只能将已确认未入账事件完整入账；POSTED不可覆盖')
   e=matches[0]
  pd=day(posting['posted_date'])
  if not day(case['opening_date'])<=pd<boundary or pd<day(e['confirmed_date']):raise ValueError('实际日期须在期初与新核对边界之间且不早于确认日期')
  if not isinstance(posting['evidence'],str) or not 1<=len(posting['evidence'].strip())<=2000:raise ValueError('实际收付须有凭据')
  e.update(status='POSTED',posted_date=str(pd),evidence=posting['evidence'],last_updated_at=now());validate_event(e)
 if len(result['events'])>500:raise ValueError('事件上限500')
 result['as_of']=str(boundary);derive_payment_conditions(result,now())
 computed=evaluate(result)['actual_balance_fen']
 if computed!=command['observed_balance_fen']:raise ReconciliationMismatch(computed,command['observed_balance_fen'])
 result['version']+=1
 result['history'].append({'version':result['version'],'operation':'record_actuals_and_reconcile','reason':command['reason'],'at':now(),
   'before':{'as_of':before['as_of'],'events':[e for e in before['events'] if e['event_id'] in seen]},
   'after':{'as_of':result['as_of'],'events':[deepcopy(e) for e in result['events'] if e['event_id'] in seen],'observed_balance_fen':computed}})
 return result

def fixture():
 stamp='2026-10-13T00:00:00+00:00';start=date(2027,1,1)
 orders=[{'order_id':'O1','customer_id':'C1','name':'合成核心客户A','order_amount_fen':60000000}]+[{'order_id':f'O{i}','customer_id':f'C{i}','name':f'合成客户{i}','order_amount_fen':12000000} for i in range(2,5)]
 for o in orders:o['payment_terms']={'type':'FIXED_DATE'}
 orders[0]['payment_terms']={'type':'AFTER_INVOICE','acceptance_event_id':'O1-acceptance','invoice_event_id':'O1-invoice','receivable_event_id':'O1-receivable','invoice_after_acceptance_days':2,'payment_after_invoice_days':7}
 events=[]
 def add(oid,kind,d,amount,status='PROJECTED'):
  eid=f'{oid}-{kind}';planned=str(start+timedelta(days=d))
  events.append(dict(event_id=eid,order_id=oid,event_type=kind,planned_date=planned,confirmed_date='2027-01-01' if status in {'CONFIRMED','POSTED'} else None,posted_date=planned if status=='POSTED' else None,amount_fen=amount,status=status,source='SYNTHETIC / 合成合同情景',evidence='合成验收凭证，仅用于演示' if status in {'CONFIRMED','POSTED'} else '',last_updated_at=stamp))
 add('O1','purchase_order',0,0,'CONFIRMED');add('O1','prepayment',0,12000000,'POSTED')
 for kind,d,a in [('materials',7,-30000000),('production',20,-12000000),('shipment',35,-4000000),('acceptance',36,0),('invoice',38,0),('receivable',45,48000000)]:add('O1',kind,d,a)
 for i in range(2,5):
  add(f'O{i}','purchase_order',0,0,'CONFIRMED');add(f'O{i}','materials',10+i*3,-9000000);add(f'O{i}','receivable',25+i*4,12000000)
 case={'version':1,'evidence_type':'SYNTHETIC','opening_fen':8000000,'opening_date':'2027-01-01','as_of':'2027-01-02','necessary_expenses_complete':True,'orders':orders,'events':events,'history':[],'assumptions':['仅支持录入的合同情景，不代表汽摩行业普遍账期。','期初余额为2027-01-01 00:00；核对边界2027-01-02 00:00，边界不含。','合成凭证不是真实客户证据；事实余额是本实验的POSTED账本口径。']}
 derive_payment_conditions(case)
 return case

def apply_command(case,command):
 if not isinstance(command,dict):raise ValueError('变更必须为对象')
 if command.get('operation')=='record_actuals_and_reconcile':return record_actuals_and_reconcile(case,command)
 fields={'confirm':{'confirmed_date','evidence'},'post':{'posted_date','evidence'},'reschedule':{'planned_date'},'amend':{'amount_fen'},'dispute':{'evidence'},'cancel':set(),'reconcile':{'as_of','observed_balance_fen'},'add':{'order_id','event_type','planned_date','amount_fen','source'}}
 op=command.get('operation')
 if op not in fields or set(command)!=fields[op]|{'operation','event_id','reason'}:raise ValueError('变更字段缺失或包含不支持字段')
 for k in ('reason','event_id'):
  if not isinstance(command[k],str) or not 1<=len(command[k].strip())<=1000:raise ValueError('原因和事件标识必填且须有界')
 if 'evidence' in command and (not isinstance(command['evidence'],str) or not 1<=len(command['evidence'].strip())<=2000):raise ValueError('凭证说明必填且须有界')
 result=deepcopy(case);reason=command['reason'].strip()
 if op=='add':
  if len(case['events'])>=500:raise ValueError('事件数量上限500')
  if command['order_id'] not in {o['order_id'] for o in case['orders']}:raise ValueError('订单不存在')
  if any(e['event_id']==command['event_id'] for e in case['events']):raise ValueError('重复事件ID')
  if not isinstance(command['source'],str) or not 1<=len(command['source'].strip())<=1000:raise ValueError('来源说明必填')
  event={k:command[k] for k in ('event_id','order_id','event_type','planned_date','amount_fen','source')}
  event.update(status='PROJECTED',confirmed_date=None,posted_date=None,evidence='',last_updated_at=now())
  validate_event(event);result['events'].append(event);evaluate(result)
  result['version']+=1;result['history'].append({'version':result['version'],'event_id':event['event_id'],'operation':'add','before':None,'after':deepcopy(event),'reason':reason,'at':now()});return result
 if command.get('operation')=='reconcile':
  boundary=day(command['as_of'])
  if not reason or boundary<day(case['as_of']):raise ValueError('核对日期不可倒退且需说明')
  result['as_of']=str(boundary)
  if type(command.get('observed_balance_fen')) is not int or evaluate(result)['actual_balance_fen']!=command['observed_balance_fen']:raise ValueError('核对余额与已录入事实不一致，请先核实流水；预测不参与核对')
  result['version']+=1;result['history'].append({'version':result['version'],'operation':'reconcile','before':{'as_of':case['as_of']},'after':{'as_of':str(boundary)},'reason':reason,'at':now()});return result
 eid=command['event_id']
 if not reason:raise ValueError('变更原因必填')
 matches=[e for e in result['events'] if e['event_id']==eid]
 if len(matches)!=1:raise ValueError('事件不存在或重复')
 event=matches[0];before=deepcopy(event);op=command['operation'];stamp=now()
 if event['status']=='POSTED':raise ValueError('已入账事实不可修改或重复入账；需要单独核对补偿，禁止覆盖')
 if event['status']=='CANCELLED':raise ValueError('取消事件不能恢复或入账')
 if op=='reschedule':
  if event['status'] not in {'PROJECTED','CONFIRMED','DISPUTED'}:raise ValueError('状态不支持改期')
  day(command['planned_date']);event['planned_date']=command['planned_date']
  for order in result['orders']:
   terms=order.get('payment_terms',{})
   if terms.get('type')=='AFTER_INVOICE':
    if terms.get('receivable_event_id')==eid:raise ValueError('条件回款日期由合同依赖推导；请修改验收/开票日期，延期方案在情景比较中调整')
    if terms.get('invoice_event_id')==eid:
     acceptance=next(e for e in result['events'] if e['event_id']==terms['acceptance_event_id'])
     lag=(day(command['planned_date'])-day(acceptance['planned_date'])).days
     if not 0<=lag<=180:raise ValueError('开票不可早于验收或超过180天')
     terms['invoice_after_acceptance_days']=lag
  # A newly negotiated date loses previous contractual confirmation.
  event.update(status='PROJECTED',confirmed_date=None,evidence='')
 elif op=='amend':
  if type(command.get('amount_fen')) is not int:raise ValueError('金额须为整数分')
  event.update(amount_fen=command['amount_fen'],status='PROJECTED',confirmed_date=None,evidence='')
 elif op=='confirm':
  if event['status']!='PROJECTED':raise ValueError('仅预测安排可以确认')
  event.update(status='CONFIRMED',confirmed_date=command['confirmed_date'],evidence=command.get('evidence',''))
  day(event['confirmed_date'])
 elif op=='post':
  if event['status']!='CONFIRMED':raise ValueError('先核对并确认安排，再录入收付款事实')
  pd=day(command['posted_date'])
  if pd<day(event['confirmed_date']):raise ValueError('入账日期不可早于确认日期')
  if not day(case['opening_date'])<=pd<day(case['as_of']):raise ValueError('入账日期必须在期初与核对边界之间，边界不含；先核对余额和日期')
  event.update(status='POSTED',posted_date=str(pd),evidence=command.get('evidence',''))
 elif op=='dispute':event.update(status='DISPUTED',evidence=command.get('evidence',''))
 elif op=='cancel':
  if event['event_type'] not in CASH:raise ValueError('流程节点不可单独取消：需逐笔核对关联资金安排')
  event.update(status='CANCELLED')
 else:raise ValueError('不支持的操作')
 event['last_updated_at']=stamp;validate_event(event)
 prior={e['event_id']:deepcopy(e) for e in result['events']}
 derive_payment_conditions(result,stamp)
 derived=[{'before':prior[e['event_id']],'after':deepcopy(e)} for e in result['events'] if prior[e['event_id']]!=e]
 result['version']+=1;result['history'].append({'version':result['version'],'event_id':eid,'operation':op,'reason':reason,'before':before,'after':deepcopy(event),'derived_changes':derived,'payment_terms_before':[o.get('payment_terms') for o in case['orders']],'payment_terms_after':[o.get('payment_terms') for o in result['orders']],'at':stamp})
 return result

def evaluate(case, horizon_days=60):
 if type(case.get('opening_fen')) is not int or not case.get('necessary_expenses_complete'):raise ValueError('缺少余额或必要支出完整性，只能核对事件，不能做整体测算')
 start=day(case['opening_date']);boundary=day(case['as_of'])
 if start>boundary:raise ValueError('核对边界早于期初')
 ids=[e['event_id'] for e in case['events']]
 if len(ids)!=len(set(ids)):raise ValueError('重复事件ID')
 actual=case['opening_fen'];future=[];overdue=[];excluded=[];disputed=[]
 for e in case['events']:
  validate_event(e)
  if e['status']=='DISPUTED' or e.get('prediction_confidence')=='BLOCKED_BY_DISPUTE':disputed.append(e['event_id'])
  if e['status']=='POSTED':
   d=day(e['posted_date'])
   if d<start:excluded.append(e['event_id'])
   elif d>=boundary:raise ValueError('POSTED超出核对边界，需核对')
   else:actual+=e['amount_fen']
  elif e['status'] in {'PROJECTED','CONFIRMED'} and e['event_type'] in CASH and e.get('prediction_confidence')!='BLOCKED_BY_DISPUTE':
   if day(e['planned_date'])<boundary:overdue.append(e['event_id'])
   else:future.append(e)
 if not 1<=horizon_days<=365:raise ValueError('支持窗口1..365天')
 end=max([boundary+timedelta(days=horizon_days-1)]+[day(e['planned_date']) for e in future])
 if (end-boundary).days>=365:raise ValueError('超出365天窗口，不截断')
 series=[];balance=actual;minimum=actual;lowest=str(boundary);negative=0;drivers=[]
 for offset in range((end-boundary).days+1):
  d=boundary+timedelta(days=offset);changes=[e for e in future if e['planned_date']==str(d)]
  balance+=sum(e['amount_fen'] for e in changes)
  if balance<minimum:minimum=balance;lowest=str(d);drivers=[e['event_id'] for e in changes]
  negative+=balance<0;series.append({'date':str(d),'balance_fen':balance,'events':[{'event_id':e['event_id'],'amount_fen':e['amount_fen'],'status':e['status']} for e in changes]})
 # Missing milestones remain in the denominator; deleting an unverified node
 # must never improve the completeness ratio. Count order/type, not event rows.
 expected={(o['order_id'],kind) for o in case['orders'] for kind in ('purchase_order','acceptance','invoice','receivable')}
 supported=sum(any(e['order_id']==oid and e['event_type']==kind and e['status'] in {'CONFIRMED','POSTED'} and bool(e['evidence']) for e in case['events']) for oid,kind in expected)
 by_customer={}
 for o in case['orders']:by_customer[o['customer_id']]=by_customer.get(o['customer_id'],0)+o['order_amount_fen']
 total=sum(by_customer.values());shares=sorted(by_customer.values(),reverse=True)
 return {'evidence_type':'MODEL OUTPUT','actual_balance_fen':actual,'peak_gap_fen':max(0,-minimum),'minimum_date':lowest,'minimum_drivers':drivers,'negative_days':negative,'closing_fen':balance,'series':series,'overdue_unresolved':overdue,'opening_included_events':excluded,'disputed_events':disputed,'complete':not overdue and not disputed,'evidence_completeness':{'supported':supported,'required':len(expected),'definition':'关键节点有确认说明的数量；不是信用评分，也不鉴定证据真伪'},'concentration':{'top1':str(Decimal(shares[0])/total) if total else None,'top3':str(Decimal(sum(shares[:3]))/total) if total else None,'basis':'合成订单金额，不是银行授信集中度'},'boundary':'资金缺口≠授信额度；日终余额不能保证日内逐笔支付；未落实安排不是可用现金。'}

def simulate(case,delay_days=0,customer_id='C1',discount='0',fee_fen=0,advance_fen=0):
 if type(delay_days) is not int or not 0<=delay_days<=90 or type(fee_fen) is not int or not 0<=fee_fen<=10000000:raise ValueError('非法情景参数')
 if type(advance_fen) is not int or not 0<=advance_fen<=10000000:raise ValueError('追加预付须为0..10万元整数分')
 rate=Decimal(str(discount))
 if not rate.is_finite() or not 0<=rate<=Decimal('.1'):raise ValueError('折扣范围0..10%')
 if customer_id not in {'ALL',*[o['customer_id'] for o in case['orders']]}:raise ValueError('客户不存在')
 c=deepcopy(case);oids={o['order_id'] for o in c['orders'] if customer_id=='ALL' or o['customer_id']==customer_id};cost=0;changed=[]
 for e in c['events']:
  if e['order_id'] in oids and e['event_type']=='receivable' and e['status'] in {'PROJECTED','CONFIRMED'}:
   extra=min(advance_fen,e['amount_fen']);e['amount_fen']-=extra
   if extra:
    c['events'].append(dict(event_id='SCENARIO-ADVANCE-'+e['event_id'],order_id=e['order_id'],event_type='prepayment',planned_date=case['as_of'],confirmed_date=None,posted_date=None,amount_fen=extra,status='PROJECTED',source='ASSUMPTION / 追加预付，未到账',evidence='',last_updated_at=now()))
   deduction=rounding(Decimal(e['amount_fen'])*rate);cost+=deduction;e['amount_fen']-=deduction;e['planned_date']=str(day(e['planned_date'])+timedelta(days=delay_days));e['status']='PROJECTED';e['confirmed_date']=None;e['evidence']='';changed.append(e['event_id'])
 if fee_fen:
  c['events'].append(dict(event_id='SCENARIO-FEE',order_id=sorted(oids)[0],event_type='fee',planned_date=case['as_of'],confirmed_date=None,posted_date=None,amount_fen=-fee_fen,status='PROJECTED',source='ASSUMPTION',evidence='',last_updated_at=now()))
 result=evaluate(c);result.update(discount_cost_fen=cost,fee_fen=fee_fen,changed_event_ids=changed,base_version=case['version'],saved_as_baseline=False)
 return result
