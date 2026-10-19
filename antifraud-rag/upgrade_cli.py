"""Local CLI shares the exact same Agent as the web endpoint."""
import argparse,json
from dotenv import load_dotenv
from upgrade.store import Store
from upgrade.contracts import CaseRecord
from upgrade.agent import Agent
p=argparse.ArgumentParser();p.add_argument('query');p.add_argument('--role',default='unknown');p.add_argument('--jurisdiction',default='Australia');p.add_argument('--retriever',choices=['auto','bm25','semantic','hybrid','all'],default='auto');p.add_argument('--env');p.add_argument('--case-id');p.add_argument('--version',type=int);a=p.parse_args()
if a.env:load_dotenv(a.env)
s=Store();c=s.get(a.case_id) if a.case_id else s.create(CaseRecord(query=a.query,requester_role=a.role,jurisdiction=a.jurisdiction));r=Agent(s,c.case_id,a.version or c.version,retriever=a.retriever).run();print(json.dumps(r,ensure_ascii=False,indent=2))
