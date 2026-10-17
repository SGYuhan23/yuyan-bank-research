"""Author-reviewed reference table. NEVER imported by the model execution pipeline."""

import json
from pathlib import Path
from decimal import Decimal

R = Path(__file__).parent
S = {s["source_id"]: s for s in json.loads((R / "data/sources.json").read_text())}


def company(cid, name, aliases, region, industry, parent=None, sources=None):
    return dict(
        company_id=cid,
        legal_name=name,
        aliases=aliases,
        parent_relationship=parent,
        region=region,
        industry=industry,
        sources=sources or [],
    )


companies = [
    company(
        "rifa",
        "重庆日发汽车零部件有限公司",
        ["重庆日发"],
        "重庆高新区曾家镇",
        "汽车座椅复合布料",
        sources=["rifa-accepted", "rifa-approved"],
    ),
    company(
        "qinan",
        "重庆秦安机电股份有限公司",
        ["秦安股份"],
        "重庆",
        "汽车零部件／真空镀膜",
        sources=["qinan-2025"],
    ),
    company(
        "qinan-cast",
        "重庆秦安铸造有限公司",
        ["秦安铸造"],
        "重庆江津区",
        "汽车零部件制造",
        {
            "parent_company_id": "qinan",
            "relationship": "直接持股100%",
            "as_of": "2025-12-31",
            "source_id": "qinan-2025",
            "page_or_section": "PDF第227页",
        },
        ["smart-factory", "qinan-2025"],
    ),
    company(
        "loncin",
        "隆鑫通用动力股份有限公司",
        ["隆鑫通用"],
        "重庆",
        "摩托车及通用机械",
        sources=["loncin-2025"],
    ),
    company(
        "zishuo",
        "重庆紫硕汽车零部件有限公司",
        ["重庆紫硕"],
        "重庆高新区含谷镇",
        "汽车座椅",
        sources=["rifa-accepted", "rifa-approved"],
    ),
]
(R / "data/companies.json").write_text(
    json.dumps(companies, ensure_ascii=False, indent=2)
)
facts = []


def fact(
    fid, cid, sid, sec, text, limit, stage=None, date=None, project=None, values=None
):
    s = S[sid]
    loc = s["sections"][sec]
    facts.append(
        dict(
            fact_id=fid,
            company_id=cid,
            statement=text,
            source_id=sid,
            excerpt=loc["text"],
            page_or_section=loc["page_or_section"],
            published_at=s["published_at"],
            period=s["period"],
            event_date=date,
            stage=stage,
            project_id=project,
            limitations=limit,
            values=values,
            review_status="author_source_checked_pending_human_signoff",
        )
    )


p = "2602-500356-07-01-664445"
fact(
    "R1",
    "rifa",
    "rifa-accepted",
    0,
    "布料贴合扩建项目环评于2026-08-11受理。",
    "不代表批准或开工。",
    "accepted",
    "2026-08-11",
    p,
)
fact(
    "R2",
    "rifa",
    "rifa-proposed",
    0,
    "项目进入拟审批公示；披露总投资约553万元、环保投资30万元、拟年产复合布料200万米。",
    "均为规划口径；不能当成实际支出、实际产量或融资缺口。",
    "proposed",
    "2026-08-18",
    p,
    {"planned_investment_wan": "553", "environment_wan": "30"},
)
fact(
    "R3",
    "rifa",
    "rifa-approved",
    0,
    "环评于2026-08-25批准，公告日期2026-08-26，文号渝（高新）环准〔2026〕34号。",
    "没有取得开工或验收证据；公司财务、采购合同与融资安排未知。",
    "approved",
    "2026-08-25",
    p,
)
fact(
    "Q1",
    "qinan",
    "qinan-2025",
    0,
    "2025年合并营业收入1,352,249,546.74元；2024年1,599,923,214.87元。",
    "合并数据不能代替秦安铸造单体财务。",
    values={
        "revenue_2025": "1352249546.74",
        "revenue_2024": "1599923214.87",
        "unit": "CNY",
    },
)
fact(
    "Q2",
    "qinan",
    "qinan-2025",
    1,
    "公司披露2025年末货币资金及交易性金融资产余额11.34亿元；收购亦高光电99%股权并纳入合并。",
    "余额及管理层评价不能证明各子公司可支配资金；也不能仅凭收入下降推断资金短缺。",
)
fact(
    "Q3",
    "qinan-cast",
    "qinan-2025",
    2,
    "秦安铸造是秦安股份直接持股100%的子公司。",
    "截至2025年末的关系；不得混同法人及财务口径。",
)
fact(
    "Q4",
    "qinan-cast",
    "smart-factory",
    0,
    "秦安铸造汽车缸盖重力铸造项目列入2025年基础级智能工厂名单第209行。",
    "名单不是贷款需求、补贴到账或新建工程证据。",
)
fact(
    "Q5",
    "qinan-cast",
    "smart-factory",
    1,
    "秦安铸造汽车缸体压铸项目列入同名单第222行。",
    "与第209行为同一企业的不同工厂事项，不应去重成一条。",
)
fact(
    "Q6",
    "qinan",
    "qinan-2026h1",
    0,
    "2026年上半年合并营业收入705,550,828.01元；上年同期675,374,807.79元。",
    "半年同比与全年同比不可混算；撤回“收入仍在持续下降”的泛化判断，不删除2025年历史事实。",
    values={
        "revenue_2026h1": "705550828.01",
        "revenue_2025h1": "675374807.79",
        "unit": "CNY",
    },
)
fact(
    "L1",
    "loncin",
    "loncin-2025",
    0,
    "2025年合并营业收入19,135,154,464.95元，2024年16,822,240,957.81元。",
    "不能据增长推出新增融资需求。",
    values={
        "revenue_2025": "19135154464.95",
        "revenue_2024": "16822240957.81",
        "unit": "CNY",
    },
)
fact(
    "L2",
    "loncin",
    "loncin-2025",
    1,
    "披露欧洲市场基本实现人民币结算；其他海外市场仍以美元结算为主，部分人民币计价并随汇率调整价格。",
    "已有汇率管理措施；未核实套保比例及银行合作，不应提出从零启用汇率管理的判断。",
)
fact(
    "L3",
    "loncin",
    "loncin-reprint",
    0,
    "新浪转载同一2025年年报的营业收入数据。",
    "不是新事件或独立印证；采用巨潮原报告作为规范来源。",
)
fact(
    "Q7",
    "qinan",
    "qinan-cash-appendix",
    0,
    "2025年取得子公司支付现金净额499,700,885.17元；期末现金及现金等价物1,026,155,658.34元。",
    "是原年报第220页的补充读取，不是新公告；不能据此证明不存在任何后续付款或资金需求。",
)
if "loncin-reprint-pdf" in S:
    fact(
        "L4",
        "loncin",
        "loncin-reprint-pdf",
        0,
        "雪球转载同一2025年年报，收入数据与巨潮原文一致。",
        "同一事项第二个转载渠道，不计新增经营事件。",
    )
fact(
    "Z1",
    "zishuo",
    "rifa-approved",
    0,
    "紫硕项目环评于2026-08-25获批，文号32号，项目代码2508-500356-07-01-594593。",
    "与同表日发项目不同；财务、开工和资金安排均未知。",
    "approved",
    "2026-08-25",
    "2508-500356-07-01-594593",
)
(R / "data/reference-facts.json").write_text(
    json.dumps(facts, ensure_ascii=False, indent=2)
)
lines = [
    "# 来源事实表（作者逐原文核对，待使用者人工签核）",
    "",
    "核对日期：2026-10-18。非银行客户试点；仅覆盖所列公开资料，不声明穷尽最新披露。模型执行不读取此表。",
    "",
    "|ID|主体|事实|位置及来源|限制|",
    "|---|---|---|---|---|",
]
for f in facts:
    lines.append(
        "|"
        + "|".join(
            [
                f["fact_id"],
                f["company_id"],
                f["statement"],
                f"[{f['page_or_section']}]({S[f['source_id']]['url']})",
                f["limitations"],
            ]
        )
        + "|"
    )
(R / "docs/FACT_TABLE.md").write_text("\n".join(lines))
briefs = {
    "rifa": (
        "环评已从受理推进到批准，实际建设进度未知。",
        "可了解设备采购付款与结算安排；不能先认定融资需求。",
        ["R1", "R2", "R3"],
        [
            "是否开工，能否提供进度与设备采购合同？",
            "计划投资哪些已支付，资金来自哪里？",
            "是否有结算或付款管理方面的困难？",
        ],
    ),
    "qinan": (
        "2025年收入下降，同时完成并购；2026年上半年收入同比转为增长。",
        "了解并购后的账户、结算与资金统筹；撤回持续收入下降或必然资金短缺的判断。",
        ["Q1", "Q2", "Q6", "Q7"],
        [
            "半年增长来自原业务还是并表变化？",
            "资金能否跨主体调配，是否已有结算统筹方案？",
            "当前最需要解决的是结算效率还是现金时点？",
        ],
    ),
    "qinan-cast": (
        "两项基础级智能工厂列名；与上市公司是不同法人。",
        "目前证据不足，不建议据此形成明确金融服务判断。",
        ["Q3", "Q4", "Q5"],
        [
            "工厂目前的改造进度与运营效果如何？",
            "是否存在新的设备采购和付款安排？",
            "能否提供本法人单体财务及现有服务情况？",
        ],
    ),
    "loncin": (
        "2025年收入增长，年报已披露人民币结算及汇率管理措施。",
        "可了解现有跨境结算覆盖与效率，撤回“尚无汇率管理”的假设。",
        ["L1", "L2", "L3", "L4"],
        [
            "当前不同市场结算币种和账期有无变化？",
            "现有汇率管理如何覆盖净敞口？",
            "哪些环节仍需要改进，现有银行是否已提供相关服务？",
        ],
    ),
    "zishuo": (
        "同一公告中的另一独立建设主体；环评批准不等于建成。",
        "仅凭审批资料无法判断资金需求。",
        ["Z1"],
        ["一期工程目前实际进度？", "资金来源及付款安排是否已落实？"],
    ),
}
for cid, (what, why, ids, qs) in briefs.items():
    c = next(c for c in companies if c["company_id"] == cid)
    text = f"# {c['legal_name']}｜访前研究底稿\n\n作者研究，待人工签核；非实时Agent生成。研究日2026-10-18。\n\n## 发生什么\n{what}\n\n## 为什么值得了解（服务假设）\n{why}\n\n## 公开事实与限制\n"
    for fid in ids:
        f = next(f for f in facts if f["fact_id"] == fid)
        text += f"- {f['statement']} [{fid} · {f['page_or_section']}]({S[f['source_id']]['url']})；发布{f['published_at']}，期间{f['period']}。限制：{f['limitations']}\n"
    text += "\n## 程序计算\n"
    if cid == "rifa":
        a, b = Decimal("30"), Decimal("553")
        text += f"环保投资占计划总投资：30万元 ÷ 553万元 × 100 = {(a / b * 100).quantize(Decimal('0.01'))}%。不表示支出完成率。\n"
    elif cid == "qinan":
        text += (
            "2026H1收入同比：(705,550,828.01 − 675,374,807.79) ÷ 675,374,807.79 ×100 = "
            + str(
                (
                    (Decimal("705550828.01") / Decimal("675374807.79") - 1) * 100
                ).quantize(Decimal(".01"))
            )
            + "%。输入均为人民币元、合并半年期间。\n"
        )
    else:
        text += "无必须计算的项目，不补造指标。\n"
    text += (
        "\n## 下一步问什么\n"
        + "\n".join("- " + q for q in qs)
        + "\n\n未核实联系人、合同、现有银行关系及资金缺口，全部留空。\n"
    )
    (R / f"docs/manual-{cid}.md").write_text(text)
print("Reference:", len(facts), "facts;", len(briefs), "briefs")
