"""Build only the frozen Final P0 public data; legacy output is explicitly opt-in."""
import argparse,csv,json
from pathlib import Path
from build_v2 import build_v2
ROOT=Path(__file__).resolve().parents[2]
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--legacy',action='store_true');args=parser.parse_args()
 if args.legacy:
  import build_legacy_data
 else:
  out=ROOT/'agent-platform/frontend/public/research';out.mkdir(parents=True,exist_ok=True)
  data=build_v2(out)
  (out/'sources.json').write_bytes(Path(__file__).with_name('sources.json').read_bytes())
  rows=data['deposit']['grid']
  with (out/'deposit-sensitivity.csv').open('w',encoding='utf-8-sig',newline='') as f:
   writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
  print(json.dumps({'version':data['version'],'customers':len(data['fuling']['customers']),'candidate_actions':len(data['fuling']['actions'])}))
