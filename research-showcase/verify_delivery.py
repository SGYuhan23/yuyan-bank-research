"""Validate delivered bytes and the static page/data binding without changing research."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parent
for name,expected in json.loads((ROOT/'evidence/artifact-hashes.json').read_text()).items():
    assert hashlib.sha256((ROOT/'dist'/name).read_bytes()).hexdigest()==expected,name
expected=json.loads((ROOT/'dist/data.json').read_text())
for name in ['dist/index.html','渝研_交互研究页面.html']:
    html=(ROOT/name).read_text()
    embedded=re.search(r'<script id="research-data" type="application/json">(.*?)</script>',html,re.S)
    assert embedded and json.loads(embedded[1])==expected,name
    assert '__RESEARCH_DATA__' not in html and '__REPORT_DOWNLOAD__' not in html
print('Delivered artifact hashes and embedded data: PASS')
