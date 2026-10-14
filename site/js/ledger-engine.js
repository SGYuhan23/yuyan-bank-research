import{copy,day,derive}from'./contract-engine.js';import{evaluate}from'./supplier-engine.js';
export function prepareReconcile(c){const n=copy(c),e=n.events.find(e=>e.event_id==='O1-materials');if(e.status!=='PROJECTED')return n;e.status='CONFIRMED';e.confirmed_date='2027-01-01';e.evidence='合成付款凭证，仅用于演示';n.version++;n.history.push({version:n.version,operation:'confirm',event_id:e.event_id,reason:'演示开始前确认待付款安排'});return n;}
export function reconcile(c,{observed_balance_fen,base_version,event_id='O1-materials',posted_date='2027-01-08',as_of='2027-01-09',idempotency_key},receipts={}){
 const signature=JSON.stringify({observed_balance_fen,base_version,event_id,posted_date,as_of});
 if(idempotency_key&&receipts[idempotency_key]){if(receipts[idempotency_key].signature!==signature)throw Error('同一提交标识对应了不同参数');return{case:copy(c),receipts,replayed:true};}
 if(base_version!==c.version)throw Error('账本已变化，请重新核对');if(!Number.isSafeInteger(observed_balance_fen))throw Error('余额须精确到分');
 const next=copy(c),e=next.events.find(e=>e.event_id===event_id);if(!e||e.status!=='CONFIRMED')throw Error('只能完整录入已确认且未入账的付款');
 if(day(as_of)<day(c.as_of)||day(posted_date)<day(c.opening_date)||day(posted_date)>=day(as_of)||day(posted_date)<day(e.confirmed_date))throw Error('付款日期或核对边界无效');
 e.status='POSTED';e.posted_date=posted_date;e.evidence='合成付款凭证，仅用于演示';next.as_of=as_of;derive(next);const computed=evaluate(next).actual_balance_fen;
 if(computed!==observed_balance_fen){const err=Error('余额不一致，本次操作没有保存');err.difference_fen=observed_balance_fen-computed;throw err;}
 next.version++;next.history.push({version:next.version,operation:'record_actuals_and_reconcile',event_id,amount_fen:e.amount_fen,observed_balance_fen:computed,as_of});
 return{case:next,receipts:{...receipts,...(idempotency_key?{[idempotency_key]:{signature}}:{})},replayed:false};
}
