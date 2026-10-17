"""Explicit bounded update workflow: selected new sources -> model re-check -> version diff.
This is not a simulated historical replay and does not run a second agent.
"""

import argparse, json
from pathlib import Path
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from engine import ResearchRun, atomic


def update(parent_path, source_ids, output, mode="snapshot"):
    parent = json.loads(Path(parent_path).read_text())
    run = ResearchRun(
        "加入所选公开资料重新审查旧档案；撤回无证据的服务假设，保留历史事实。",
        parent["company_id"],
        source_ids,
        mode,
        parent,
        output,
    )
    run.run_update()
    return run


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--env")
    p.add_argument("--parent", required=True)
    p.add_argument("--sources", nargs="+", required=True)
    p.add_argument("--output")
    p.add_argument("--mode", choices=["snapshot", "live"], default="snapshot")
    a = p.parse_args()
    if a.env:
        load_dotenv(a.env)
    run = update(a.parent, a.sources, a.output, a.mode)
    print(run.dir)
