"""Fetch allowlisted original sources. Preserve raw bytes and provenance."""
from pathlib import Path
import json,hashlib,datetime
import httpx
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent
SEEDS=[
('westpac-bec','https://www.westpac.com.au/security/types-of-scams/business-email-scams/','bank_public_guidance'),
('scamwatch-bec','https://www.scamwatch.gov.au/types-of-scams/business-email-compromise-scams','official_guidance'),
('scamwatch-case','https://www.scamwatch.gov.au/stop-check-protect/real-life-stories/false-billing-john-updated-supplier-details-and-it-ended-up-costing-thousands','official_public_case'),
('westpac-receipt','https://www.westpac.com.au/security/latest-scams/past-scams-and-alerts/','bank_public_guidance'),
('asic-invest','https://moneysmart.gov.au/check-and-report-scams/check-before-you-invest','official_guidance'),
('scamwatch-stats','https://www.scamwatch.gov.au/research-and-resources/targeting-scams-report','official_statistics')]
def main():
 rows=[]
 for sid,url,kind in SEEDS:
  r=httpx.get(url,timeout=45,follow_redirects=True,headers={'User-Agent':'Mozilla/5.0'})
  if r.status_code!=200:
   with (ROOT/'data/acquisition-failures.jsonl').open('a') as f:f.write(json.dumps({'url':url,'status':r.status_code,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()})+'\n')
   print(sid,'FAILED',r.status_code);continue
  raw=r.content
  (ROOT/'data/raw'/f'{sid}.html').write_bytes(raw)
  soup=BeautifulSoup(raw,'html.parser')
  for x in soup(['script','style','nav','footer','header']):x.decompose()
  main=soup.find('main') or soup.find('article') or soup
  text=main.get_text('\n',strip=True)
  (ROOT/'data/raw'/f'{sid}.txt').write_text(text)
  rows.append(dict(source_id=sid,title=soup.title.get_text(strip=True) if soup.title else sid,url=str(r.url),published_or_updated_at=None,date_status='not_yet_verified',retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),region='Australia',material_type=kind,page_or_section='pending_section_selection',file_sha256=hashlib.sha256(raw).hexdigest(),review_status='fetched_pending_author_check',seed_provenance='independently_discovered_official_source_material_pack_not_found'))
  print(sid,len(text))
 (ROOT/'data/source-index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
