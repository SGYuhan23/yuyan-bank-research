from runtime import configure
configure()
import faulthandler
faulthandler.dump_traceback_later(40)
from deerflow.config.app_config import reload_app_config
import os
config = reload_app_config(os.environ['DEER_FLOW_CONFIG_PATH'])
print('config valid', flush=True)
from deerflow.models import create_chat_model
from langchain_core.messages import HumanMessage
model = create_chat_model('qwen-plus', thinking_enabled=False)
reply = model.bind_tools([{'type':'function','function':{'name':'add','description':'Add two integers','parameters':{'type':'object','properties':{'a':{'type':'integer'},'b':{'type':'integer'}},'required':['a','b']}}}]).invoke([HumanMessage(content='Use the add tool to add 17 and 25.')])
print({'model': os.environ['QWEN_MODEL'], 'region': os.environ['QWEN_REGION'], 'tools': reply.tool_calls, 'usage':reply.usage_metadata}, flush=True)
faulthandler.cancel_dump_traceback_later()
