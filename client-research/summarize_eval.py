"""Mechanical measures, plus explicitly non-blind author adjudication. No human-time proxy."""

import json, re
from pathlib import Path
from engine import ROOT, norm

notes = {
    "rifa": {
        "agent": [
            "未交付：反复将fact_id放入source_id字段，最终耗尽12轮；失败草稿含“尚未开工、无缺口”的不当判断。"
        ],
        "baseline": [
            "自行生成项目编号rifa-expansion，不能当官方项目代码。",
            "把未取得关联资料写成未涉及关联方。",
            "没有投资构成明细却称全部是设备与环保投入、资本开支可控。",
            "无来源引入制造业环保投资均值1–3%，并拿道路工程作比较。",
        ],
    },
    "qinan": {
        "agent": [
            "未交付：上年同期表头校验误拒、fact_id/source_id错配，最终耗尽12轮。"
        ],
        "baseline": [
            "引入无来源的现金比率安全阈值和行业资产负债率均值50%–60%。",
            "将所选节录未包含的信息泛化为整个年报未披露，年报220页实有并购付款信息。",
            "对子公司关系摘录使用省略号而非连续原文，另有摘录顺序改写。",
        ],
    },
    "loncin": {
        "agent": ["未交付：假设引用fact_id无法通过旧校验，耗尽12轮。"],
        "baseline": [
            "把年报转载列作独立事件，并将source_id写入事件supersedes。",
            "将转载选取段落未包含结算描述泛化为转载源缺失；已下载转载全文实际包含外汇结算段。",
            "在未核实现有工具及银行覆盖时，称当前信息足以做衍生品补位设计。",
        ],
    },
    "qinan-cast": {
        "agent": [
            "智能工厂名单列名标为approved，容易误读为工程审批；应为disclosed。",
            "未读取完整附注却称单体财务未披露；应限于所读资料未核实。",
        ],
        "baseline": [
            "把2025年末股权关系披露写成2025-12-31子公司成立事件。",
            "两个工厂编号自拟且stage为accepted，均不是环评受理。",
            "称209和222编号连续，并凭条目断言设备体系完全不兼容，无来源。",
            "从截取页推定全文未拆分单体收入，证据范围不足。",
        ],
    },
    "zishuo": {
        "agent": [
            "把环评批准解读为建设启动在即，并提出存在固定资产融资需求；资料不足，需撤回。",
            "事件未表达阶段替代关系，事实正文只提名称，遗漏审批时间等关键变化。",
        ],
        "baseline": [
            "无来源提出12–24个月融资期限与设备集中付款安排。",
            "编入设备供应商品牌以及30%/60%/10%付款结构，原文没有供应商或合同。",
            "未读取政策与项目资质便声称符合绿色/碳减排支持目录。",
        ],
    },
}
rows = []
for cid, arms in notes.items():
    for arm, issues in arms.items():
        d = json.loads((ROOT / f"runs/eval-{cid}-{arm}/run.json").read_text())
        result = d.get("result")
        facts = result["dossier"].get("facts", []) if result else []
        sources = {s["source_id"]: s for s in d["evidence"]}
        matched = 0
        for f in facts:
            s = sources.get(f["source_id"], {})
            if any(
                x["page_or_section"] == f["page_or_section"]
                and norm(f["excerpt"]) in norm(x["text"])
                for x in s.get("sections", [])
            ):
                matched += 1
        calls = [r for r in d["records"] if r["kind"] == "model_call"]
        rows.append(
            {
                "case": cid,
                "arm": arm,
                "status": d["status"],
                "returned_model": sorted({r["model_returned"] for r in calls}),
                "model_calls": len(calls),
                "usage_total_tokens": sum(
                    (r.get("usage") or {}).get("total_tokens", 0) for r in calls
                ),
                "fact_count": len(facts),
                "exact_quote_matches": matched,
                "validation_rejections": sum(
                    r["kind"] == "validation_failed" for r in d["records"]
                ),
                "author_revision_items": issues,
                "author_revision_item_count": len(issues),
                "human_review_seconds": None,
                "blind_human_major_error_score": None,
            }
        )
(ROOT / "docs/eval-results.json").write_text(
    json.dumps(
        {
            "method": "5 paired development cases; same selected source sections and task; temperature 0; same configured model; unfiltered single-turn baseline vs bounded tool loop. Quote match is not semantic correctness. Author annotations are AI-assisted, non-blind, not an independent human trial.",
            "cases": rows,
        },
        ensure_ascii=False,
        indent=2,
    )
)
lines = [
    "# 实际评测结果与失败样本",
    "",
    "运行日期：2026-10-18（北京时间）。5个样本×2种方法，共10个实际模型任务。样本是开发集，非盲测、非真实客户试点。",
    "",
    "同一企业的任务、所选原文段落与模型保持一致，temperature=0。基线一次获得全部相同资料，单轮输出不经修复；Agent自行检索/读取这些资料并调用计算工具，最多12轮。Agent并非获得更多来源，但调用预算更大，不能解读为等成本实验。作者事实表不传给任何一方。",
    "",
    "本轮是修复前的开发版本，结果原样保留；后续修复与更新运行另列，未混入本对照成绩。模型真实返回名与token见eval-results.json及逐运行trace。",
    "",
    "|样本|方法|完成|模型调用|原文连续摘录匹配/事实数|校验拒绝次数|作者列出的修订项|",
    "|---|---|---|---:|---:|---:|---:|",
]
for r in rows:
    lines.append(
        f"|{r['case']}|{r['arm']}|{r['status']}|{r['model_calls']}|{r['exact_quote_matches']}/{r['fact_count']}|{r['validation_rejections']}|{r['author_revision_item_count']}|"
    )
lines += [
    "",
    "## 如何解释",
    "",
    "**早期Agent完成2/5；单轮基线返回5/5。不能宣称Agent更优。** 引用校验可以阻止部分无出处输出，也会误拒和降低完成率。完成不是业务正确：紫硕完成档案仍把审批推成融资需求。",
    "",
    "摘录匹配仅做去空白后的连续原文检查，不证明摘录支持结论、主体匹配或单位正确。失败任务的0/0不算零错误或100%正确。不同输出事实数不同，不直接比较百分比代表综合质量。",
    "",
    "以下问题由本轮Codex对照原文逐项检查、人工可复核，**不是独立人类评审**。没有计时的人类修订实验，因此human_review_seconds及盲评重大错误分数为null，不伪造人工工时。列出已发现的重大事实/推断问题与遗漏，不声称穷尽全部错误。",
]
for cid, arms in notes.items():
    lines += ["", f"## {cid}"]
    for arm, items in arms.items():
        lines += ["", f"**{arm}**"] + ["- " + x for x in items]
lines += [
    "",
    "## 后续修复与保留限制",
    "",
    "- 显式解析当前档案fact_id到已有source_id，避免把引用格式错误当成无证据；不凭空生成引用。",
    "- 允许由“上年同期”表头和报告期间确定比较年份；未消除全部主体/期间语义风险。",
    "- 官方项目代码必须在已读取原文出现；未知填null。",
    "- 单模型增加一次证据复核，修改无来源推断；该复核不是独立评估，不计入以上对照。",
    "- 更新改为按用户所选新资料读取、复核旧假设，仍需使用者人工签核。",
    "- 未做全新留出集；没有稳定完成率结论，没有获客率、转化率或经营收益提升数据。",
]
(ROOT / "docs/EVALUATION.md").write_text("\n".join(lines) + "\n")
print(json.dumps(rows, ensure_ascii=False)[:300])
if __name__ == "__main__":
    pass
