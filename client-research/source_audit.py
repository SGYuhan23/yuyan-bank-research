"""Explicit author source audit of an actual model draft. Not a human sign-off or LLM run.
Raw input remains immutable; every changed field is recorded with before/after values.
"""

import json
from pathlib import Path
from engine import ROOT, ResearchRun, now, digest

parent = json.loads((ROOT / "runs/qinan-guarded-update/run.json").read_text())
run = ResearchRun(
    "作者逐原文校核实际模型档案；不冒称客户经理确认",
    "qinan",
    parent=parent,
    run_dir=ROOT / "runs/qinan-source-audited",
)
run.mode = "author_source_audit_not_human_signoff"
run.read = {s["source_id"]: s for s in parent["evidence"]}
run.calculations = parent["calculations"]
d = json.loads(json.dumps(parent["result"]["dossier"]))


def change(obj, key, value, path):
    before = obj.get(key)
    obj[key] = value
    run.log(
        "source_audit_revision",
        field=path,
        before=before,
        after=value,
        editor="Codex逐原文核校；非人类独立复核",
        evidence_version=parent["result"]["evidence_version"],
    )


change(
    d,
    "why_relevant",
    "2025年全年与2026年上半年收入方向不同，且并购改变合并范围。可了解收入构成、并购后的账户与结算安排；当前资料不能证明资金缺口、未做汇率管理或技改融资需求。",
    "why_relevant",
)
limitations = {
    "f1": "此处为合并全年数据；本次只选取部分页，不对完整报告披露范围作否定判断。",
    "f2": "利润总额不是归母净利润；当前片段不足以解释全部变动原因。",
    "f3": "原文已包含上年同期收入675,374,807.79元；半年同比不能与全年数据直接混算。",
    "f4": "原文已包含上年同期利润总额90,931,487.87元；变化原因仍需继续核实。",
    "f5": "这是公司合并口径披露，现金规模不能直接代表各子公司可用资金，也不能证明没有任何后续资金需求。",
    "f6": "此页记载主要经营地及注册地为重庆，不足以确认具体区县；不得用合并财务替代本法人财务。",
    "f7": "补读原年报第220页，不是新公告；现金净额不能直接代表合同总价或未来付款义务。",
}
for f in d["facts"]:
    if f["fact_id"] in limitations:
        change(
            f, "limitations", limitations[f["fact_id"]], f["fact_id"] + ".limitations"
        )
    if f["fact_id"] == "f6":
        change(
            f,
            "statement",
            "重庆秦安铸造有限公司为秦安股份直接持股100%的子公司；该页主要经营地、注册地均列重庆，业务为汽车零部件制造和销售。",
            "f6.statement",
        )
    if f["fact_id"] == "f7":
        change(
            f,
            "statement",
            "2025年取得子公司支付的现金净额为499,700,885.17元。",
            "f7.statement",
        )
for e in d["events"]:
    if e["event_type"] == "acquisition":
        change(
            e,
            "event_date",
            None,
            e["event_id"] + ".event_date（年内完成不能补造12月31日交割）",
        )
change(
    d,
    "next_questions",
    [
        "2026年上半年收入同比增长中，原有汽车零部件业务和新增并表业务分别贡献多少？",
        "并购后账户、收付款和资金调配如何安排，哪些结算环节仍需改进？",
        "是否存在尚未落实的设备采购或付款安排？如有，请提供合同、时间表及既有资金来源。",
    ],
    "next_questions",
)
change(
    d,
    "missing_information",
    [
        "最新业务分部与并表贡献",
        "单体财务及资金调配权限",
        "当前采购/付款安排及现有银行服务覆盖",
    ],
    "missing_information",
)
change(
    d,
    "stop_reason",
    "已核实所选期间指标、并购及现金附注，4项同比由工具计算。无法仅据这些资料形成具体贷款或汇率产品需求判断，保留中性访前问题。",
    "stop_reason",
)
change(
    d,
    "coverage_limit",
    "只覆盖2025年报第6、30、227、220页及2026年半年报摘要第2页，不宣称已检索完整最新公告。此次为Codex作者源文校核，不是银行人员或使用者签核。",
    "coverage_limit",
)
run.finish(d)
print(run.dir)
