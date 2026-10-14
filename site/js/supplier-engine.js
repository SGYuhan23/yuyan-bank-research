import{copy,day,addDays}from'./contract-engine.js';
const CASH=new Set(['materials','production','shipment','receivable','prepayment','fee','quality_deduction']);
export function evaluate(c,horizon=60){
 if(!Number.isSafeInteger(c.opening_fen)||!c.necessary_expenses_complete)throw Error('需要期初余额和完整支出');
 if(!Number.isInteger(horizon)||horizon<1||horizon>365)throw Error('测算窗口为1至365天');
 const start=day(c.opening_date),boundary=day(c.as_of);if(start>boundary)throw Error('核对日期早于期初');
 const ids=new Set();let actual=c.opening_fen;const future=[],overdue=[],excluded=[],disputed=[];
 for(const e of c.events){if(ids.has(e.event_id)||!Number.isSafeInteger(e.amount_fen)||Math.abs(e.amount_fen)>1e12)throw Error('重复事件或无效金额');ids.add(e.event_id);day(e.planned_date);
  if(e.status==='DISPUTED'||e.prediction_confidence==='BLOCKED_BY_DISPUTE')disputed.push(e.event_id);
  if(e.status==='POSTED'){const d=day(e.posted_date);if(d<start)excluded.push(e.event_id);else if(d>=boundary)throw Error('实际收付超出核对日期');else actual+=e.amount_fen;}
  else if(['PROJECTED','CONFIRMED'].includes(e.status)&&CASH.has(e.event_type)&&e.prediction_confidence!=='BLOCKED_BY_DISPUTE'){if(day(e.planned_date)<boundary)overdue.push(e.event_id);else future.push(e);}
 }
 const end=Math.max(boundary+horizon-1,...future.map(e=>day(e.planned_date)));if(end-boundary>=365)throw Error('超出365天测算范围');
 let balance=actual,minimum=actual,lowest=c.as_of,negative=0,drivers=[];const series=[];
 for(let d=boundary;d<=end;d++){const date=addDays(c.as_of,d-boundary),changes=future.filter(e=>e.planned_date===date);balance+=changes.reduce((s,e)=>s+e.amount_fen,0);if(balance<minimum){minimum=balance;lowest=date;drivers=changes.map(e=>e.event_id);}if(balance<0)negative++;series.push({date,balance_fen:balance,events:changes.map(({event_id,amount_fen,status})=>({event_id,amount_fen,status}))});}
 return{actual_balance_fen:actual,peak_gap_fen:Math.max(0,-minimum),minimum_date:lowest,minimum_drivers:drivers,negative_days:negative,closing_fen:balance,series,overdue_unresolved:overdue,opening_included_events:excluded,disputed_events:disputed,complete:!overdue.length&&!disputed.length};
}
function roundRate(amount,rate){const s=String(rate);if(!/^(0(?:\.\d{1,8})?|1)$/.test(s))throw Error('折扣格式无效');const parts=s.split('.'),den=10n**BigInt((parts[1]||'').length),num=BigInt(parts.join(''));return Number((BigInt(amount)*num*2n+den)/(2n*den));}
export function simulate(c,p){const{customer_id='C1',delay_days=0,discount='0',fee_fen=0,advance_fen=0}=p;
 if(!Number.isInteger(delay_days)||delay_days<0||delay_days>90||![fee_fen,advance_fen].every(v=>Number.isSafeInteger(v)&&v>=0&&v<=10000000)||!Number.isFinite(Number(discount))||Number(discount)<0||Number(discount)>.1)throw Error('延期为0至90天，费用和每单预付为0至10万元，折扣为0至10%');
 if(customer_id!=='ALL'&&!c.orders.some(o=>o.customer_id===customer_id))throw Error('请选择案例中的客户');
 const next=copy(c),oids=new Set(c.orders.filter(o=>customer_id==='ALL'||o.customer_id===customer_id).map(o=>o.order_id));let cost=0;const changed=[];
 for(const e of [...next.events])if(oids.has(e.order_id)&&e.event_type==='receivable'&&['PROJECTED','CONFIRMED'].includes(e.status)){
  const extra=Math.min(advance_fen,e.amount_fen);e.amount_fen-=extra;if(extra)next.events.push({...e,event_id:'SCENARIO-ADVANCE-'+e.event_id,event_type:'prepayment',amount_fen:extra,planned_date:c.as_of,status:'PROJECTED',confirmed_date:null});
  const deduction=roundRate(e.amount_fen,discount);cost+=deduction;e.amount_fen-=deduction;e.planned_date=addDays(e.planned_date,delay_days);e.status='PROJECTED';e.confirmed_date=null;e.evidence='';changed.push(e.event_id);
 }
 if(fee_fen)next.events.push({event_id:'SCENARIO-FEE',order_id:[...oids].sort()[0],event_type:'fee',amount_fen:-fee_fen,planned_date:c.as_of,status:'PROJECTED'});
 return{...evaluate(next),discount_cost_fen:cost,fee_fen,changed_event_ids:changed,base_version:c.version,saved_as_baseline:false};
}
