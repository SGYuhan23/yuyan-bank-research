import{el,details,money}from'./chat-ui.js';import{simulate}from'./supplier-engine.js';
export function replay(parent,trace,originalCase){
 parent.append(el('p','notice','调用回放：以下来自已保存的真实 Qwen 记录，不是刚刚调用模型。用户原先已指定客户、天数及不考虑成本；验收程序完成了缺失参数修正与确认。'));
 const req=trace.original_model_proposal.request,confirmed=trace.confirmed_request.request;
 const steps=[['1 · 用户问题','原问题中的业务部分：核心客户 C1 尾款延期 14 天，需要多少额外流动资金？完整原始提示保留在下方技术详情中。'],['2 · 模型理解',`客户 ${req.customer_id}；延期 ${req.delay_days} 天。模型留空：折扣、费用和追加预付。`],['3 · 参数检查',trace.correction_summary],['4 · 确认参数','验收程序依据原问题将三项成本参数补为 0，再通过确认接口明确确认。这里不是合同确认，也不是当前访客的确认。'],['5 · 调用业务工具',`已记录工具：${trace.tool}。工具仅消费已确认的请求标识。`],['6 · 工具返回',`已记录：峰值资金缺口 ${money(trace.result.scenario.peak_gap_fen)} 元，负余额 ${trace.result.scenario.negative_days} 天。`],['7 · 最终回答','已记录的受控解释：峰值缺口没有增加，但负余额持续时间增加，企业需要承受更久的资金压力。']];
 for(const[title,text]of steps){const step=el('div','trace-step');step.append(el('h3','',title),el('p','',text));parent.append(step);}
 const live=simulate(originalCase,{customer_id:confirmed.customer_id,delay_days:confirmed.delay_days,discount:confirmed.discount,fee_fen:confirmed.fee_fen,advance_fen:confirmed.advance_fen});
 parent.append(el('p','success',`本浏览器用原始合成案例与这组已记录参数重新计算：${money(live.peak_gap_fen)} 元 / ${live.negative_days} 天。${live.peak_gap_fen===trace.result.scenario.peak_gap_fen&&live.negative_days===trace.result.scenario.negative_days?'与已记录工具结果一致。':'与已记录结果不一致，请核查。'}`));
 details(parent,'展开完整原始用户提示与参数（脱敏记录）',trace);parent.append(el('p','muted','其他输入由浏览器规则识别，不会套用这条 C1 / 14 天记录冒充新的模型理解。'));
}
