"""Bank research product extension. Model receives read-only deterministic tool only."""
import asyncio,os,sys
from pathlib import Path
from deerflow_extension_api import extension
from deerflow_extension_api.plugins import BackendAction,ModelTool,PluginContribution
sys.path.insert(0,str(Path(__file__).parent/'research'))
from ledger_store import LedgerStore
from supplier_ledger import ReconciliationMismatch

@extension(api='0.2.3',name='yuyan-research')
def install(registry,config):
 store=LedgerStore(os.environ['AGENT_DATABASE_URL']);store.migrate()
 def handler(action):
  async def run(payload,context):
   try:
    return await asyncio.to_thread(store.apply,action,payload,context.principal.user_id)
   except ReconciliationMismatch as exc:
    # Host intentionally sanitizes exception details. Return a typed domain failure
    # after the store transaction has rolled back, never an apparent saved case.
    return {'error':{'code':'BALANCE_MISMATCH','difference_fen':exc.difference_fen,'message':str(exc)},'committed':False}
  return run
 async def model_simulation(payload,context):
  result=await asyncio.to_thread(store.apply,'simulate',payload,context.principal.user_id)
  # Keep authoritative scalar results inline; a long daily series can be externalized
  # by the host tool-output budget and would hide the guard's source from model calls.
  return {**result,'baseline':{k:v for k,v in result['baseline'].items() if k!='series'},'scenario':{k:v for k,v in result['scenario'].items() if k!='series'}}
 async def model_proposal(payload,context):
  return await asyncio.to_thread(store.apply,'propose_scenario',payload,context.principal.user_id)
 proposal_schema={'type':'object','properties':{'request_id':{'type':'string'},'case_id':{'type':'string'},'base_version':{'type':'integer'},'customer_id':{'type':['string','null']},'delay_days':{'type':['integer','null']},'discount':{'type':['string','null']},'fee_fen':{'type':['integer','null']},'advance_fen':{'type':['integer','null']}},'required':['request_id','case_id','base_version','customer_id','delay_days','discount','fee_fen','advance_fen'],'additionalProperties':False}
 simulation_schema={'type':'object','properties':{'request_id':{'type':'string'}},'required':['request_id'],'additionalProperties':False}
 registry.plugin(PluginContribution(namespace='yuyan.research',title='银行经营与资金研究',description='公开事实、合成情景、确定性结果；非授信系统',enabled=True,backend=tuple(BackendAction(a,handler(a)) for a in ('create','list','get','change','propose_scenario','confirm_scenario','scenario_requests','invalidate_scenario','simulate')),tools=(
 ModelTool('supplier_scenario_proposal','只提出情景参数，不确认或计算。字段缺失/歧义填null并请用户在研究页确认；case_id和base_version须来自用户或已授权上下文，不得猜测。request_id用本次唯一标识。折扣为0..0.1字符串，费用和预付是整数分。',proposal_schema,model_proposal),
 ModelTool('supplier_cash_scenario','只消费用户已在研究页确认的request_id；不得另传客户或延期。请求快照/账本版本不匹配即拒绝。金额由确定性工具返回，资金缺口不是授信额度。',simulation_schema,model_simulation))))
