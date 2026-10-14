export function parse(text,context={hours:150,cap:null}){
 const s=text.trim();const no={intent:'unsupported'};
 if(/股票|股市|推荐股|净息差|GDP|好吃|贷款审批|审批.*贷款|授信审批/i.test(s))return no;
 if(/执行过程|调用回放|trace|AI.*(怎么|完成)|模型.*记录/i.test(s))return{intent:'trace_replay'};
 if(/核对|实际.*付|实际支出|余额.*(错|对)|核销/.test(s))return{intent:'supplier_reconcile'};
 if(/验收|开票|合同|固定日期/.test(s))return{intent:'supplier_contract'};
 if(/余额.*(一样|相同)|同余额|交易多|员工多|供应链连接多|关系维护价值/.test(s))return{intent:'fuling_customer_compare'};
 if(/25\s*%|行业.*(限制|约束|分散)|集中.*约束/.test(s))return{intent:'fuling_constraint_explain',available_hours:context.hours??150,industry_limit:/取消|不启用|不限制/.test(s)?null:.25};
 const hours=s.match(/(-?\d+(?:\.\d+)?)\s*(?:小时|h\b)/i);if(hours)return{intent:'fuling_allocate',available_hours:Number(hours[1]),industry_limit:context.cap??null};
 const who=/所有|全部|\bALL\b/i.test(s)?'ALL':s.match(/\bC([1-4])\b/i)?.[0].toUpperCase()||(/核心客户/.test(s)?'C1':null);
 const days=s.match(/(-?\d+(?:\.\d+)?)\s*天/)||s.match(/(?:ALL|C[1-4])\s*[+/／]\s*(-?\d+(?:\.\d+)?)/i);
 if(who&&(days||/延期|晚|回款/.test(s)))return{intent:who==='ALL'?'supplier_all_delay':'supplier_delay',customer_id:who,delay_days:days?Number(days[1]):null,discount:'0',fee_fen:0,advance_fen:0,needs_clarification:/折扣|费用|预付/.test(s)};
 if(/有订单|缺现金|缺钱|流动|资金缺口|风险.*增加|缺口.*(不变|没变)/.test(s))return{intent:'supplier_liquidity_explain'};
 return no;
}
