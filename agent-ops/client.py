"""Authenticated local verification client; never exports session credentials."""
import json
from pathlib import Path
import httpx
ROOT = Path(__file__).resolve().parents[1]
def client():
    account=json.loads((ROOT/'agent-platform/.deer-flow/acceptance/account.json').read_text())
    c=httpx.Client(base_url='http://127.0.0.1:8001',timeout=60,headers={'Origin':'http://127.0.0.1:8001'})
    c.post('/api/v1/auth/login/local',data={'username':account['email'],'password':account['password']}).raise_for_status()
    c.get('/api/v1/auth/me').raise_for_status()
    c.headers['X-CSRF-Token']=c.cookies.get('csrf_token')
    return c
