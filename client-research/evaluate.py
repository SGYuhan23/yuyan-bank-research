"""Paired small development evaluation; no claim of superiority or customer benefit."""

import json, argparse, concurrent.futures
from pathlib import Path
from dotenv import load_dotenv
from engine import ResearchRun, SOURCES, COMPANIES, ROOT, atomic
from models import Dossier

CASES = [
    {
        "id": "rifa",
        "company": "rifa",
        "sources": ["rifa-accepted", "rifa-proposed", "rifa-approved"],
        "task": "研究日发布料贴合扩建项目的阶段变化与主体，复算环保投资占计划总投资比例；提出访前服务假设及反证，明确不能推断开工或资金缺口。",
    },
    {
        "id": "qinan",
        "company": "qinan",
        "sources": ["qinan-2025", "qinan-2026h1"],
        "task": "研究秦安股份2025年与2026年半年经营变化，各自比较同比，审查收入下降能否推出资金短缺，不能混同子公司单体财务。",
    },
    {
        "id": "loncin",
        "company": "loncin",
        "sources": ["loncin-2025", "loncin-reprint"],
        "task": "研究隆鑫通用2025年度经营和访前服务方向；识别报告转载，核查“有出口所以尚无汇率管理”判断是否成立。",
    },
    {
        "id": "qinan-cast",
        "company": "qinan-cast",
        "sources": ["qinan-2025", "smart-factory"],
        "task": "研究重庆秦安铸造有限公司，核实与上市公司关系及智能工厂名单中的两个事项；证据不足时停止，不得把集团收入当成该企业单体收入。",
    },
    {
        "id": "zishuo",
        "company": "zishuo",
        "sources": ["rifa-accepted", "rifa-proposed", "rifa-approved"],
        "task": "研究重庆紫硕汽车零部件有限公司一期项目，不要混同日发项目；现有公开信息是否足够判断金融需求？",
    },
]


def one(case, arm):
    out = ROOT / "runs" / ("eval-" + case["id"] + "-" + arm)
    if (out / "run.json").exists():
        return "exists " + out.name
    run = ResearchRun(
        case["task"], case["company"], case["sources"], "snapshot", run_dir=out
    )
    try:
        if arm == "agent":
            run.run()
        else:
            material = [s for s in SOURCES if s["source_id"] in case["sources"]]
            prompt = {
                "task": case["task"],
                "company_id": case["company"],
                "companies": COMPANIES,
                "materials": material,
                "schema": Dossier.model_json_schema(),
            }
            system = "你是一名银行对公访前研究助手。仅基于给定公开原文，一次完成JSON档案。区分事实、计算、服务假设、待核实问题，保留反证与不足。不得编造数据。按给定schema输出；摘录连续原文，来源标识使用source_id。未调用计算工具，calculation_ids留空，可在说明中列算式。不要输出内部思维链。"
            d = run.model(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                ],
                "single-turn-baseline",
            )
            run.result = {
                "dossier": d,
                "evidence_version": None,
                "parent_run_id": None,
                "delta": {},
                "validation": "unfiltered_baseline_output",
            }
            run.read = {s["source_id"]: s for s in material}
            run.log("completed", note="单轮全部相同资料，无工具及修复轮次")
        return out.name + " completed"
    except Exception as e:
        run.log("run_failed", error=str(e)[:1200])
        payload = json.loads((out / "run.json").read_text())
        payload["status"] = "failed"
        atomic(out / "run.json", payload)
        return out.name + " failed"


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--env", required=True)
    p.add_argument("--arm", choices=["agent", "baseline", "both"], default="both")
    p.add_argument("--cases", nargs="*")
    a = p.parse_args()
    load_dotenv(a.env)
    atomic(ROOT / "data/eval-cases.json", CASES)
    jobs = [
        (c, arm)
        for c in CASES
        if not a.cases or c["id"] in a.cases
        for arm in (["agent", "baseline"] if a.arm == "both" else [a.arm])
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(one, c, arm) for c, arm in jobs]
        for f in concurrent.futures.as_completed(futures):
            print(f.result(), flush=True)
