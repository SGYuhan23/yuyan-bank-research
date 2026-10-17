"""Re-evaluate a historical draft with deterministic guards; explicitly not a new LLM run."""

import argparse, json
from pathlib import Path
from engine import ResearchRun

p = argparse.ArgumentParser()
p.add_argument("--parent", required=True)
p.add_argument("--output", required=True)
p.add_argument("--baseline")
a = p.parse_args()
parent = json.loads(Path(a.parent).read_text())
run = ResearchRun(
    "对历史档案执行新增保守断言规则；未调用模型",
    parent["company_id"],
    parent=json.loads(Path(a.baseline).read_text()) if a.baseline else parent,
    run_dir=a.output,
)
run.mode = "deterministic_review_of_real_model_output"
run.read = {s["source_id"]: s for s in parent["evidence"]}
run.calculations = parent.get("calculations", [])
run.log("rule_review_started", parent_run_id=parent["run_id"], model_called=False)
run.finish(parent["result"]["dossier"])
print(run.dir)
