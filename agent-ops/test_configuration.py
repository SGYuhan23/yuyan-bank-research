"""Deployment contract checks; no provider requests."""
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parent

def test_runtime_boundaries():
    cfg=yaml.safe_load((ROOT/'config.qwen.yaml').read_text())
    assert cfg['database']['backend']=='postgres'
    assert cfg['sandbox']['allow_host_bash'] is False
    assert cfg['sandbox']['use'].endswith('AioSandboxProvider')
    assert cfg['models'][0]['api_key']=='$QWEN_API_KEY'
    assert cfg['models'][0]['extra_body']['enable_thinking'] is False
    assert cfg['token_budget']['enabled'] is True
    assert cfg['recursion_limit']<=cfg['max_recursion_limit']
    assert all('sql' not in t['name'] for t in cfg['tools'])

def test_database_not_public():
    cfg=yaml.safe_load((ROOT/'compose.yaml').read_text())
    assert all(p.startswith('127.0.0.1:') for p in cfg['services']['db']['ports'])

def test_retrieval_evidence_survives_framework_budget():
    cfg=yaml.safe_load((ROOT/'config.qwen.yaml').read_text())
    assert cfg['tool_output']['tool_overrides']['web_fetch']>=24000
    assert cfg['tool_output']['fallback_max_chars']>=24000
