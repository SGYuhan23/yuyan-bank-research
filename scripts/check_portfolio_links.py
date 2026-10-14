"""Check local file links in the portfolio reading path (not upstream website routes)."""
from pathlib import Path
import re,json
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1]
paths=[*ROOT.glob('*.md'),* (ROOT/'docs').rglob('*.md'),*(ROOT/'third_party').glob('*.md'),ROOT/'agent-ops/README.md',ROOT/'agent-ops/research/README.md']
issues=[];checked=0
for p in paths:
 text=re.sub(r'```.*?```','',p.read_text(),flags=re.S)
 for value in re.findall(r'\]\(([^\n)]+)\)',text):
  value=value.split(' "')[0].strip('<>')
  if re.match(r'^[a-zA-Z][\w+.-]*:',value) or value.startswith('#'):continue
  value=unquote(value.split('#')[0])
  if not value:continue
  checked+=1
  if not (p.parent/value).exists():issues.append({'document':str(p.relative_to(ROOT)),'target':value})
print(json.dumps({'scope':'Portfolio root/docs/attribution and current agent-ops README files; upstream docs/site routes excluded','checked_local_file_links':checked,'broken':issues},ensure_ascii=False,indent=2))
raise SystemExit(bool(issues))
