"""ScenarioRequest: explicit proposal, human confirmation, immutable computation identity."""
from dataclasses import dataclass,asdict
from decimal import Decimal,InvalidOperation
import hashlib,json
PARAMS=('customer_id','delay_days','discount','fee_fen','advance_fen')
@dataclass(frozen=True)
class ScenarioRequest:
 request_id:str
 case_id:str
 base_version:int
 customer_id:str|None
 delay_days:int|None
 discount:str|None
 fee_fen:int|None
 advance_fen:int|None
 confirmation_status:str='PROPOSED'

 def snapshot(self):return asdict(self)
 def parameter_hash(self):return hashlib.sha256(json.dumps({k:v for k,v in self.snapshot().items() if k!='confirmation_status'},sort_keys=True).encode()).hexdigest()

def proposal(payload,case):
 required={'request_id','case_id','base_version',*PARAMS}
 if set(payload)!=required:raise ValueError('ScenarioRequest字段不完整/未知')
 for k in ('request_id','case_id'):
  if not isinstance(payload[k],str) or not 1<=len(payload[k])<=128:raise ValueError('请求标识无效')
 if type(payload['base_version']) is not int or payload['base_version']!=case['version']:raise ValueError('案例版本已变化，请重新提出参数')
 for key,maximum in [('delay_days',90),('fee_fen',10000000),('advance_fen',10000000)]:
  v=payload[key]
  if v is not None and (type(v) is not int or not 0<=v<=maximum):raise ValueError('非法参数 '+key)
 if payload['customer_id'] is not None and payload['customer_id'] not in {'ALL',*[o['customer_id'] for o in case['orders']]}:raise ValueError('客户不存在')
 if payload['discount'] is not None:
  try:r=Decimal(payload['discount'])
  except (InvalidOperation,TypeError):raise ValueError('折扣须为十进制字符串')
  if not isinstance(payload['discount'],str) or not r.is_finite() or not 0<=r<=Decimal('.1'):raise ValueError('非法折扣')
 return ScenarioRequest(**payload)

def envelope(request):
 d=request.snapshot()
 return {'request':d,'parameter_hash':request.parameter_hash(),'missing_fields':[k for k in PARAMS if d[k] is None],
  'confirmation_required':request.confirmation_status!='CONFIRMED',
  'message':'请在研究页逐项核对客户、延期、折扣、费用、预付及账本版本后明确确认。缺失字段不得猜测；模型无确认权限。'}

def confirm_request(stored,snapshot,case):
 if stored.confirmation_status!='PROPOSED' or stored.snapshot()!=snapshot:raise ValueError('确认快照不一致/已被修改')
 if stored.base_version!=case['version']:raise ValueError('案例版本冲突')
 if any(getattr(stored,k) is None for k in PARAMS):raise ValueError('参数存在歧义或缺失，须补全并重新确认')
 return ScenarioRequest(**{**stored.snapshot(),'confirmation_status':'CONFIRMED'})

def assert_consumable(request,case):
 if request.confirmation_status!='CONFIRMED':raise ValueError('请求尚未人工确认')
 if request.base_version!=case['version']:raise ValueError('账本已变，旧请求和结果失效')
 if any(getattr(request,k) is None for k in PARAMS):raise ValueError('参数不完整')
