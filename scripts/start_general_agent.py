from pathlib import Path
import os, subprocess, sys
from dotenv import dotenv_values
root = Path(__file__).resolve().parents[1]
for key, value in dotenv_values(root / "agent-ops/.env.local").items():
    if value is not None:
        os.environ.setdefault(key, value)
if not os.environ.get("AGENT_NODE"):
    bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
    if bundled.exists():
        os.environ["AGENT_NODE"] = str(bundled)
raise SystemExit(subprocess.call([sys.executable, str(root / "agent-ops/start.py")], cwd=root))
