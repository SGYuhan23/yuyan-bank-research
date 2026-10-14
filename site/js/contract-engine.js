export const copy=x=>structuredClone(x);
export function day(s){if(!/^\d{4}-\d{2}-\d{2}$/.test(s)||new Date(s+'T00:00:00Z').toISOString().slice(0,10)!==s)throw Error('请填写有效日期');return Date.parse(s+'T00:00:00Z')/86400000;}
export const addDays=(s,n)=>new Date((day(s)+n)*86400000).toISOString().slice(0,10);
export function derive(caseData){
 const events=new Map(caseData.events.map(e=>[e.event_id,e]));
 for(const o of caseData.orders){const t=o.payment_terms||{type:'FIXED_DATE'};if(t.type==='FIXED_DATE')continue;if(t.type!=='AFTER_INVOICE')throw Error('不支持的合同条件');
  for(const k of ['invoice_after_acceptance_days','payment_after_invoice_days'])if(!Number.isInteger(t[k])||t[k]<0||t[k]>180)throw Error('合同天数须为0至180');
  const chain=['acceptance_event_id','invoice_event_id','receivable_event_id'].map(k=>events.get(t[k]));if(chain.some(e=>!e||e.order_id!==o.order_id))throw Error('合同节点不完整');
  const [a,i,r]=chain;if(i.status==='PROJECTED')i.planned_date=addDays(a.planned_date,t.invoice_after_acceptance_days);if(r.status==='PROJECTED')r.planned_date=addDays(i.planned_date,t.payment_after_invoice_days);
  const blocked=chain.slice(0,2).some(e=>['DISPUTED','CANCELLED'].includes(e.status));
  for(const e of [i,r])if(e.status!=='POSTED')e.prediction_confidence=blocked?'BLOCKED_BY_DISPUTE':chain.slice(0,2).some(e=>e.status==='PROJECTED')?'CONDITIONAL_UNVERIFIED':'CONDITIONS_DOCUMENTED';
 }return caseData;
}
export function changeAcceptance(c,date){day(date);const next=copy(c),e=next.events.find(e=>e.event_id==='O1-acceptance');if(e.status==='POSTED'||e.status==='CANCELLED')throw Error('已入账或已取消记录不能修改');e.planned_date=date;e.status='PROJECTED';e.confirmed_date=null;e.evidence='';derive(next);next.version++;next.history.push({version:next.version,operation:'reschedule',event_id:e.event_id,before:c.events.find(x=>x.event_id===e.event_id)?.planned_date,after:date});return next;}
