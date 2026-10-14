"""Reproducible synthetic branch experiment. No bank internal data; units CNY 10,000.
Run: python agent-ops/examples/fuling.py
Model uses annual average balances, simple FTP, EL proxy and explicit RM capacity.
"""

import csv
import json
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent / "fuling-results"
if (Path.cwd() / "agent-platform/frontend/public").is_dir():
    OUT = Path.cwd() / "agent-platform/frontend/public/examples/fuling"
STRATEGIES = [
    ("维持组合", 1, 1, 0, 1, 1),
    ("规模增长", 1.20, 1.03, 0, 1, 1.25),
    ("低成本负债", 1.03, 1.15, -0.002, 1.06, 1.15),
    ("综合经营", 1.08, 1.10, -0.001, 1.25, 1.3),
    ("均衡配置", 1.07, 1.08, -0.0007, 1.15, 1.15),
]
STRESSES = [
    ("正常环境", 0, 0, 1, None),
    ("贷款降息", -0.005, 0, 1, None),
    ("存款竞争", 0, 0.003, 1, None),
    ("制造业承压", 0, 0, 2, "制造业"),
    ("小微回款压力", 0, 0, 1.7, "商贸服务"),
    ("农业冲击", 0, 0, 2, "农业食品"),
    ("组合压力", -0.005, 0.003, 1.8, None),
]


def customers(seed=2027):
    r = random.Random(seed)
    out = []
    sectors = ["制造业", "农业食品", "商贸服务", "居民经营"]
    for i in range(120):
        sector = sectors[i % 4]
        scale = r.lognormvariate(4.3, 0.7)
        depth = r.uniform(0.2, 0.85)
        out.append(
            dict(
                id=f"SYN-{i + 1:03}",
                sector=sector,
                loan=round(scale * r.uniform(0.4, 0.8), 2),
                deposit=round(scale * depth * r.uniform(0.3, 0.8), 2),
                loan_rate=round(r.uniform(0.034, 0.052), 4),
                deposit_rate=round(0.019 - depth * 0.012, 4),
                pd=round(r.uniform(0.008, 0.035), 4),
                lgd=0.45,
                fee=round(scale * depth * 0.003, 2),
                hours=round(12 + scale * 0.07, 2),
            )
        )
    return out


def calculate(rows, strategy, stress, rm=8):
    name, lm, dm, dc, fm, hm = strategy
    sn, ld, dd, loss, sector = stress
    loan = deposit = interest = funding = fees = el = hours = 0
    by_sector = {}
    for row in rows:
        l = row["loan"] * lm
        d = row["deposit"] * dm
        loan += l
        deposit += d
        interest += l * (row["loan_rate"] + ld)
        funding += d * max(0, row["deposit_rate"] + dc + dd)
        fees += row["fee"] * fm
        hours += row["hours"] * hm
        el += (
            l
            * row["pd"]
            * row["lgd"]
            * (loss if sector is None or row["sector"] == sector else 1)
        )
        by_sector[row["sector"]] = by_sector.get(row["sector"], 0) + l
    # Symmetric FTP on net funding avoids counting deposit benefit twice.
    ftp = (deposit - loan) * 0.02
    service = rm * 18
    capacity = rm * 1000
    return dict(
        strategy=name,
        stress=sn,
        rm=rm,
        loan=round(loan, 2),
        deposit=round(deposit, 2),
        interest=round(interest, 2),
        funding=round(funding, 2),
        ftp=round(ftp, 2),
        fees=round(fees, 2),
        el=round(el, 2),
        service=service,
        contribution=round(interest - funding + ftp + fees - el - service, 2),
        hours=round(hours, 2),
        capacity=capacity,
        feasible=hours <= capacity,
        concentration=round(max(by_sector.values()) / loan, 4),
    )


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = customers()
    results = [
        calculate(rows, s, t, rm)
        for rm in range(1, 13)
        for s in STRATEGIES
        for t in STRESSES
    ]
    data = dict(
        version="2026-10-13.v1",
        seed=2027,
        unit="万元 / 年",
        disclosure="所有客户、余额、定价、风险和产能均为情景假设；不是重庆农商行内部数据。区域公开数据仅用于研究背景，没有校准客户级分布。",
        strategies=[s[0] for s in STRATEGIES],
        stresses=[s[0] for s in STRESSES],
        results=results,
        assumptions=[
            {
                "parameter": "FTP",
                "value": "2%",
                "type": "情景假设",
                "reason": "净资金缺口统一定价；不是内部FTP",
            },
            {
                "parameter": "LGD",
                "value": "45%",
                "type": "情景假设",
                "reason": "仅为预期损失代理，不是监管或审批参数",
            },
            {
                "parameter": "RM年成本",
                "value": "18万元/人",
                "type": "情景假设",
                "reason": "含简化服务成本，不含全行管理分摊",
            },
            {
                "parameter": "RM产能",
                "value": "1000小时/人年",
                "type": "情景假设",
                "reason": "可投入客户服务的时间",
            },
            {
                "parameter": "基准组合",
                "value": "120户，固定随机种子2027",
                "type": "合成数据",
                "reason": "规模呈对数正态、关系深度影响存款和中收",
            },
        ],
        sources=[
            {
                "title": "2025年各区县GDP增速",
                "url": "https://nyncw.cq.gov.cn/zwxx_161/rdtt/202602/t20260210_15414119_wap.html",
                "published": "2026-02-09（页面标注）",
                "period": "2025",
                "fact": "涪陵GDP增速6.7%；重庆全市5.3%。",
                "type": "政府网站转载统计报道",
                "retrieved": "2026-10-13",
            },
            {
                "title": "重庆农商行投资者关系",
                "url": "https://www.cqrcb.com/cqrcb/investorRelations/index.html",
                "published": "持续更新",
                "period": "2025/2026",
                "fact": "年报与中报官方检索入口；本版未将报表数值用作模型参数。",
                "type": "官方资料入口",
                "retrieved": "2026-10-13",
            },
        ],
    )
    (OUT / "results.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (OUT / "customers.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    with (OUT / "scenarios.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    (OUT / "model.py").write_text(
        Path(__file__).read_text(encoding="utf-8"), encoding="utf-8"
    )
    print(f"{len(rows)} synthetic customers; {len(results)} calculated scenarios")


if __name__ == "__main__":
    build()

# V2: public industry themes inform prototypes, never customer market shares.
SECTORS_V2 = ('先进材料/制造业', '新能源汽车及零部件', '食品农业/榨菜产业链', '商贸物流', '小微/居民经营')
DISCLOSURE_V2 = '客群原型来自公开产业结构，数量与金融参数为合成实验设计，并非重庆农商行或涪陵真实客户分布。scenario_weight ≠ real_market_share。'


def prototypes(seed=2027, weights=(1, 1, 1, 1, 1), count=120):
    """Largest-remainder experimental weighting; deterministic, not calibration."""
    from decimal import Decimal
    if len(weights) != 5 or any(Decimal(str(w)) < 0 for w in weights) or sum(weights) <= 0 or not 1 <= count <= 300:
        raise ValueError('Invalid experimental weights')
    exact = [Decimal(str(w)) * count / sum(map(lambda x: Decimal(str(x)), weights)) for w in weights]
    counts = [int(x) for x in exact]
    for i in sorted(range(5), key=lambda i: (-(exact[i]-counts[i]), i))[:count-sum(counts)]: counts[i] += 1
    rng = random.Random(seed)
    rows = []
    for sector, n in zip(SECTORS_V2, counts):
        for _ in range(n):
            deposit_fen = rng.randrange(20, 151)*100000
            rng.randrange(10, 26)  # Discard legacy unused draw; preserve all business inputs.
            rows.append({'id': f'SYN-V2-{len(rows)+1:03}', 'sector': sector,
                         'deposit_fen': deposit_fen,
                         'annual_transaction_count': rng.randrange(100, 6001),
                         'payroll_employee_count': rng.randrange(0, 201),
                         'eligible_supply_chain_links': rng.randrange(0, 9),
                         'relationship_contribution_fen': rng.randrange(5, 61)*10000,
                         'attrition_scenario': str(rng.choice([0, 10, 25, 40])/100),
                         'source_fact_ids': {'先进材料/制造业':'FL-CLUSTERS', '新能源汽车及零部件':'FL-CLUSTERS', '食品农业/榨菜产业链':'FL-FOOD', '商贸物流':'FL-LOGISTICS', '小微/居民经营':'ASSUMPTION-NO-REGIONAL-SHARE'}[sector],
                         'evidence_type': 'SYNTHETIC', 'scenario_weight': str(weights[SECTORS_V2.index(sector)]),
                         'disclosure': DISCLOSURE_V2})
    return rows


def candidate_actions(rows):
    """Net annual incremental contribution assumptions, mutually exclusive per customer.
    No new credit, no loan-income or credit approval optimization.
    """
    from decimal import Decimal, ROUND_HALF_UP
    # All unit margins, adoption/rescue rates, costs and hours below are ASSUMPTION.
    # Unit margins exclude the one-time implementation cost; one-year horizon.
    specs = [
        ('结算深化', 10, 35000, 'annual_transaction_count', '年交易笔数×每笔净服务边际150分×采用率40%',
         lambda r: Decimal(r['annual_transaction_count'])*150*Decimal('.4'),
         '授权交易流水、可迁移笔数、真实每笔边际及接入报价', '采用率不足覆盖成本或客户拒绝流水授权即停止'),
        ('存款关系深化', 5, 20000, 'deposit_fen', '合成年均余额×可新增有效资金比例20%×假设资金边际1.5%',
         lambda r: Decimal(r['deposit_fen'])*Decimal('.2')*Decimal('.015'),
         '年均余额、有效资金变化、付息与资金边际口径', '新增有效资金不成立或净贡献非正即停止'),
        ('代发/支付场景', 15, 65000, 'payroll_employee_count', '可授权员工数×年人均服务边际2400分×采用率50%',
         lambda r: Decimal(r['payroll_employee_count'])*2400*Decimal('.5'),
         '企业代发意愿、员工授权数量、活跃率及单位服务成本', '无企业/员工授权或活跃人数无法覆盖成本即停止'),
        ('供应链上下游连接', 25, 120000, 'eligible_supply_chain_links', '合格上下游连接数×年单连接服务边际80000分×采用率35%',
         lambda r: Decimal(r['eligible_supply_chain_links'])*80000*Decimal('.35'),
         '上下游双方授权、可核对合同、连接资格与非信贷服务需求', '对手方不配合、连接不合格或净贡献非正即停止'),
        ('客户经营维护', 5, 15000, 'relationship_contribution_fen + attrition_scenario', '既有年关系贡献×情景流失比例×可避免流失比例40%',
         lambda r: Decimal(r['relationship_contribution_fen'])*Decimal(r['attrition_scenario'])*Decimal('.4'),
         '既有关系贡献扣成本口径、流失原因及维护干预可行性', '无可干预原因或保留贡献不覆盖维护成本即停止'),
    ]
    out=[]
    for row in rows:
        for key in ('annual_transaction_count','payroll_employee_count','eligible_supply_chain_links','relationship_contribution_fen','deposit_fen'):
            if type(row.get(key)) is not int or row[key]<0: raise ValueError('Missing/nonnegative business driver: '+key)
        if not Decimal(0)<=Decimal(row['attrition_scenario'])<=1: raise ValueError('Invalid attrition assumption')
        for code,(kind,h,cost,driver,formula,value,evidence,stop) in enumerate(specs):
            gross=int(value(row).quantize(Decimal(1),rounding=ROUND_HALF_UP))
            fields=driver.split(' + ')
            out.append({'id':row['id']+f'-A{code}', 'customer_id':row['id'], 'sector':row['sector'],
                        'action_type':kind, 'service_hours':h,'expected_benefit_fen':gross,
                        'implementation_cost_fen':cost,'benefit_fen':gross-cost,
                        'value_formula':formula, 'business_drivers':'; '.join(k+'='+str(row[k]) for k in fields),
                        'stop_condition':stop, 'source_fact_ids':row.get('source_fact_ids','ASSUMPTION'),
                        'risk_confidence':'未校准：单价、采用率、成本、工时均为研究假设',
                        'evidence_requirement':evidence,'evidence_type':'ASSUMPTION'})
    return out


def optimize_resources(actions, capacity_hours, concentration=None):
    """Exact grouped knapsack, 5-hour units. At most one action/customer.
    concentration caps sector hours / ACTUAL selected hours, not available budget.
    Enumerate total hours, independently solve each sector then convolve sectors.
    """
    from decimal import Decimal
    if type(capacity_hours) is not int or capacity_hours<0 or capacity_hours>1200: raise ValueError('Capacity must be 0..1200 hours')
    ratio=Decimal(str(concentration)) if concentration is not None else Decimal(1)
    if not 0<ratio<=1: raise ValueError('Invalid concentration assumption')
    if len({a['id'] for a in actions})!=len(actions): raise ValueError('Duplicate action')
    sectors=sorted({a['sector'] for a in actions});budget=capacity_hours//5
    curves={}
    for sector in sectors:
        groups={}
        for a in actions:
            if type(a['service_hours']) is not int or a['service_hours']<=0 or a['service_hours']%5: raise ValueError('Use positive 5-hour units')
            if a['sector']==sector:groups.setdefault(a['customer_id'],[]).append(a)
        dp={0:(0,())}
        for group in groups.values():
            nxt=dict(dp)
            for h,(value,ids) in dp.items():
                for a in group:
                    nh=h+a['service_hours']//5;nv=value+a['benefit_fen']
                    if nh<=budget and nv>nxt.get(nh,(-10**30,()))[0]:nxt[nh]=(nv,ids+(a['id'],))
            dp=nxt
        curves[sector]=dp
    best=(0,());used=0
    for total in range(1,budget+1):
        cap=int(Decimal(total)*ratio);dp={0:(0,())}
        for sector in sectors:
            nxt={}
            for h,(v,ids) in dp.items():
                for sh,(sv,sids) in curves[sector].items():
                    nh=h+sh
                    if sh<=cap and nh<=total and v+sv>nxt.get(nh,(-10**30,()))[0]:nxt[nh]=(v+sv,ids+sids)
            dp=nxt
        candidate=dp.get(total,(-10**30,()))
        if candidate[0]>best[0]:best=candidate;used=total*5
    selected=set(best[1]);allocation={s:sum(a['service_hours'] for a in actions if a['id'] in selected and a['sector']==s) for s in sectors}
    chosen_customers={a['customer_id'] for a in actions if a['id'] in selected}
    rejected=[{**a,'reason': '净增量贡献非正' if a['benefit_fen']<=0 else '同客户已选其他动作' if a['customer_id'] in chosen_customers else '未进入当前产能/集中约束下的最优组合；不等于客户不值得服务'} for a in actions if a['id'] not in selected]
    return {'capacity_hours':capacity_hours,'hours':used,'benefit_fen':best[0],'selected':list(best[1]),
            'sector_hours':allocation,'max_sector_share':str(Decimal(max(allocation.values(),default=0))/used) if used else '0',
            'concentration_limit':str(ratio),'rejected':rejected,'evidence_type':'MODEL OUTPUT'}
