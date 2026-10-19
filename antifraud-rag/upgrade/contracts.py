"""Strict local contracts. No model controls evidence provenance or review state."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
import datetime, hashlib, json, uuid

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def uid(): return uuid.uuid4().hex
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',validate_assignment=True)
class Span(Strict):
    method:str
    page:int|None=None
    start:int|None=None
    end:int|None=None
    region:list[int]|None=None
    text:str
class Artifact(Strict):
    artifact_id:str=Field(default_factory=uid)
    case_id:str
    sha256:str
    mime:str
    origin:Literal['user_supplied','project_synthetic']
    received_at:str=Field(default_factory=now)
    spans:list[Span]=Field(default_factory=list)
    corrections:list[dict]=Field(default_factory=list)
    content:str='' # text or base64 image; local only, not committed
class Evidence(Strict):
    evidence_id:str=Field(default_factory=uid)
    case_id:str
    case_version:int
    kind:Literal['public_guidance','reported_claim','tool_observation','synthetic_observation','model_inference']
    origin_id:str
    span:dict
    source_hash:str
    observed_at:str=Field(default_factory=now)
    jurisdiction:str
    statement:str
    limitations:list[str]
class Recommendation(Strict):
    scene:str
    target:str=Field(min_length=1)
    trigger:str=Field(min_length=1)
    action:str=Field(min_length=1)
    supporting_evidence_ids:list[str]=Field(min_length=1)
    unmet_conditions:list[str]
    counter_evidence_ids:list[str]
    review_status:Literal['pending']='pending'
class CaseRecord(Strict):
    case_id:str=Field(default_factory=uid)
    version:int=1
    mode:Literal['case','graph_lab','training']='case'
    jurisdiction:str='Australia'
    as_of:str=Field(default_factory=now)
    task_scene:list[str]=Field(default_factory=list)
    requester_role:str='unknown'
    subject_role:str='unknown'
    query:str=Field(min_length=1,max_length=12000)
    artifacts:list[Artifact]=Field(default_factory=list)
    evidence:list[Evidence]=Field(default_factory=list)
    unresolved_questions:list[str]=Field(default_factory=list)
    status:Literal['open','running','needs_input','pending_review','failed','stopped']='open'
    fields:dict=Field(default_factory=dict)
class ToolCall(Strict):
    tool_name:Literal['extract','guidance','links','compare','timeline','graph','score']
    args:dict=Field(default_factory=dict)
class NextAction(Strict):
    action:Literal['call_tools','ask_user','draft','stop']
    calls:list[ToolCall]=Field(default_factory=list,max_length=7)
    questions:list[str]=Field(default_factory=list)
    summary:str
class ToolResult(Strict):
    call_id:str=Field(default_factory=uid)
    case_id:str
    case_version:int
    tool_name:str
    tool_version:str='1'
    validated_args:dict
    args_hash:str
    input_evidence:list[dict]
    status:Literal['ok','partial','unavailable','failed']
    observations:list[dict]
    limitations:list[str]
    latency_seconds:float
    usage:dict|None=None
    data_origin:str
class Review(Strict):
    request_id:str=Field(min_length=1,max_length=100)
    case_id:str
    case_version:int
    result_id:str
    operator:str=Field(min_length=1,max_length=100)
    decision:Literal['accept','reject','revise','export']
    note:str
    revisions:list[Recommendation]=Field(default_factory=list)
