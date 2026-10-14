"""Local runtime wiring. Model credentials are loaded without printing or copying them."""
import os
from pathlib import Path
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT / 'agent-platform'
OPS = ROOT / 'agent-ops'


def configure():
    source = Path(os.environ.get('YUQI_MODEL_ENV_FILE', ROOT / 'yuqi-core' / '.env'))
    values = dotenv_values(source) if source.is_file() else {}
    for key in ('QWEN_API_KEY', 'QWEN_MODEL', 'QWEN_ENDPOINT', 'QWEN_REGION', 'QWEN_IMAGE_ENDPOINT', 'QWEN_IMAGE_MODEL', 'QWEN_SEARCH_ENDPOINT'):
        if key not in os.environ and values.get(key):
            os.environ[key] = values[key]
    os.environ.setdefault('QWEN_MODEL', 'qwen-plus')
    os.environ.setdefault('QWEN_ENDPOINT', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    os.environ.setdefault('QWEN_REGION', 'cn-beijing')
    os.environ.setdefault('QWEN_IMAGE_ENDPOINT', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation')
    os.environ.setdefault('QWEN_SEARCH_ENDPOINT', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
    os.environ.setdefault('QWEN_IMAGE_MODEL', 'qwen-image-2.0')
    if not os.environ.get('QWEN_API_KEY'):
        raise RuntimeError('QWEN_API_KEY is missing; configure it in a local ignored environment file.')
    if not os.environ.get('AGENT_DATABASE_URL'):
        raise RuntimeError('AGENT_DATABASE_URL is missing; set it explicitly in the process environment.')
    os.environ['DEER_FLOW_CONFIG_PATH'] = str(OPS / 'config.qwen.yaml')
    os.environ['DEER_FLOW_PROJECT_ROOT'] = str(PLATFORM)
    os.environ['DEER_FLOW_HOME'] = str(PLATFORM / '.deer-flow')
    os.environ['DEER_FLOW_EXTENSIONS_CONFIG_PATH'] = str(OPS / 'extensions.json')
    os.environ['LANGSMITH_TRACING'] = 'false'
    os.environ['DEER_FLOW_DATE_TIMEZONE'] = 'Asia/Shanghai'
    os.chdir(PLATFORM / 'backend')
