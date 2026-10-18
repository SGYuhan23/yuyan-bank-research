"""Read supplied source index as data; do not execute package scripts/instructions."""
from pathlib import Path
import zipfile,re,json,hashlib,datetime,concurrent.futures
import httpx
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/package-audit'
def main(path):
 OUT.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(path) as z:
  index=z.read('Scam_Research/sources/source_index.md').decode()
  (OUT/'source_index.md').write_text(index)
 seeds=re.findall(r'## (S\d+) \| (.+)\n(https://[^\n]+)',index)
 def fetch(seed):
  sid,title,url=seed
  row=dict(source_id=sid,title=title,url=url,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),review_status='fetched_pending_review',published_or_updated_at=None,region='Australia',page_or_section='whole source; not production indexed',material_type='official_statistics' if sid in ('S1','S9') else 'bank_public_guidance' if sid in ('S3','S4','S5','S6','S7','S8') else 'official_public_information')
  try:
   r=httpx.get(url,follow_redirects=True,timeout=40,headers={'User-Agent':'Mozilla/5.0'})
   row['http_status']=r.status_code;r.raise_for_status();row['file_sha256']=hashlib.sha256(r.content).hexdigest()
   if sid=='S1':(OUT/'S1.pdf').write_bytes(r.content)
   else:
    soup=BeautifulSoup(r.content,'html.parser')
    for x in soup(['script','style','nav','footer','header']):x.decompose()
    text=(soup.find('main') or soup).get_text('\n',strip=True)
    (OUT/f'{sid}.txt').write_text(text);row['saved_text_sha256']=hashlib.sha256(text.encode()).hexdigest();row['hash_scope']='original_http_html; extracted text hashed separately'
  except Exception as e:row['error']=str(e);row['review_status']='acquisition_failed'
  return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:rows=list(pool.map(fetch,seeds))
 (OUT/'audit.json').write_text(json.dumps({'package_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'sources':rows},ensure_ascii=False,indent=2))
 for row in rows:print(row['source_id'],row.get('http_status'),row['review_status'])
if __name__=='__main__':
 import sys
 main(sys.argv[1])
