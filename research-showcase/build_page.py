from pathlib import Path
import json,base64,hashlib
R=Path(__file__).parent
template=(R/'page.html').read_text()
data=json.dumps(json.loads((R/'dist/data.json').read_text()),ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
base=template.replace('__RESEARCH_DATA__',data)
(R/'dist/index.html').write_text(base.replace('__REPORT_DOWNLOAD__',''))
pdf=base64.b64encode((R/'dist/渝研_产业经营研究报告.pdf').read_bytes()).decode()
standalone=base.replace('__REPORT_DOWNLOAD__',"document.getElementById('report-download').href='data:application/pdf;base64,"+pdf+"';")
(R/'渝研_交互研究页面.html').write_text(standalone)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'dist').iterdir() if p.is_file()}
(R/'evidence/artifact-hashes.json').write_text(json.dumps(manifest,indent=2))
print('Built deployable dist/ and self-contained HTML with embedded PDF')
