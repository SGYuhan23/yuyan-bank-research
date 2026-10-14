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
