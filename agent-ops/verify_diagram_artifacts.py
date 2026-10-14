"""Read both persisted artifacts via authenticated API and validate their structures."""
from client import client,ROOT
import json
from xml.etree import ElementTree as ET
p=ROOT/'agent-ops/evidence/diagram-ef2f17bf-fcff-4ebe-9784-86466a1a8ce9.json'
x=json.loads(p.read_text());c=client();checks={}
for path in x['state']['values']['artifacts']:
 response=c.get(f"/api/threads/{x['thread']}/artifacts/{path.lstrip('/')}");response.raise_for_status()
 root=ET.fromstring(response.content)
 if path.endswith('.svg'):checks['svg_nodes']=len(root.findall('{http://www.w3.org/2000/svg}rect'))==5
 if path.endswith('.drawio'):
  checks['editable_nodes']=len(root.findall('.//mxCell[@vertex="1"]'))==4
  checks['editable_edges']=len(root.findall('.//mxCell[@edge="1"]'))==3
(ROOT/'agent-ops/evidence/diagram-download.json').write_text(json.dumps(checks,indent=2));print(checks);assert all(checks.values())
