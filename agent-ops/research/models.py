"""Deterministic research models; amounts in integer fen and Decimal rates.
No bank production data, no model calls, no approval or payment decisions.
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date,timedelta
D=Decimal

def cents(value):return int((D(str(value))*100).quantize(D('1'),rounding=ROUND_HALF_UP))
def rounded(value):return int(D(value).quantize(D('1'),rounding=ROUND_HALF_UP))

def supplier_case(prepayment='0.20',delay_days=0,discount='0',fee_yuan='0'):
    pre,disc=D(prepayment),D(discount)
    if not D(0)<=pre<=1 or not D(0)<=disc<=D('.1') or not 0<=delay_days<=90 or D(fee_yuan)<0:
        raise ValueError('Invalid scenario parameters')
    start=date(2027,1,1);opening=cents(80000);order=cents(600000)
    upfront=rounded(D(order)*pre);final=rounded(D(order-upfront)*(1-disc))
    events=[(0,'预付款',upfront),(7,'材料采购',-cents(300000)),(20,'工资与制造支出',-cents(120000)),(35,'物流及必要支出',-cents(40000)),(45+delay_days,'尾款',final)]
    if D(fee_yuan)>0:events.append((7,'分期/服务费用',-cents(fee_yuan)))
    horizon=max(60,45+delay_days);balance=opening;series=[];minimum=opening;negative=0
    for day in range(horizon+1):
        changes=[{'label':label,'amount_fen':amount} for d,label,amount in events if d==day]
        balance+=sum(e['amount_fen'] for e in changes)
        minimum=min(minimum,balance);negative+=balance<0
        series.append({'date':str(start+timedelta(days=day)),'day':day,'balance_fen':balance,'events':changes})
    return {'opening_fen':opening,'prepayment':str(pre),'delay_days':delay_days,'discount':str(disc),'fee_fen':cents(fee_yuan),'discount_cost_fen':order-upfront-final,'peak_gap_fen':max(0,-minimum),'negative_days':negative,'closing_fen':balance,'series':series}

def deposit_case(balance_yuan='10000000',rate='.015',effective_funding_factor='.8',ftp='.02',replacement='0',service_yuan='20000'):
    b=cents(balance_yuan);r,s,f,k=map(D,(rate,effective_funding_factor,ftp,replacement));cost=cents(service_yuan)
    if b<=0 or not 0<=s<=1 or any(v<0 for v in (r,f,k)) or cost<0:raise ValueError('Invalid deposit parameters')
    # effective_funding_factor is a scenario haircut on useful funding, not a predicted probability.
    if k != 0:raise ValueError('V2不计替代资金成本：未建资产承诺与资金缺口，避免重复扣减。')
    gross=D(b)*(s*f-r)
    contribution=rounded(gross)-cost
    ceiling=s*f-D(cost)/D(b)
    needed=(r+D(cost)/D(b))/f if f else None
    return {'balance_fen':b,'rate':str(r),'effective_funding_factor':str(s),'ftp':str(f),'replacement':str(k),'service_fen':cost,'contribution_fen':contribution,'break_even_rate':str(ceiling),'break_even_effective_funding_factor':str(needed) if needed is not None else None}

def deposit_grid():
    return [deposit_case(rate=str(D(bp)/10000),effective_funding_factor=str(D(p)/100)) for bp in range(50,251,25) for p in range(50,101,5)]

if __name__=='__main__':
    import json
    print(json.dumps({'supplier':supplier_case(),'deposit':deposit_case()},ensure_ascii=False,indent=2))


def allocate_actions(actions, capacity_hours):
    """Exact 0/1 knapsack over integer hours. One candidate action per customer."""
    if capacity_hours < 0:raise ValueError('Negative capacity')
    dp=[(0,()) for _ in range(capacity_hours+1)]
    for i,a in enumerate(actions):
        h=a['hours'];value=a['benefit_fen']
        if h<1 or not isinstance(h,int):raise ValueError('Hours must be positive integers')
        for budget in range(capacity_hours,h-1,-1):
            prev=dp[budget-h]
            candidate=(prev[0]+value,prev[1]+(i,))
            if candidate[0]>dp[budget][0]:dp[budget]=candidate
    value,ids=dp[-1]
    return {'benefit_fen':value,'hours':sum(actions[i]['hours'] for i in ids),'selected':[actions[i]['id'] for i in ids]}
