"""Strict public trace projection. Private provider captures are never read here."""
import json
import re
from pathlib import Path

REQUEST = 'request_id case_id base_version customer_id delay_days discount fee_fen advance_fen confirmation_status'.split()
METRICS = 'evidence_type actual_balance_fen peak_gap_fen minimum_date minimum_drivers negative_days closing_fen overdue_unresolved opening_included_events disputed_events complete boundary discount_cost_fen fee_fen changed_event_ids base_version saved_as_baseline'.split()
FORBIDDEN = re.compile(r'system_message|working_directory|skill_system|provider_system|skill instructions|/mnt/|/Users/|/home/|/private/|/tmp/|[A-Za-z]:\\',re.I)

def pick(source, names):
    result = {}
    for key in names:
        if key in source:
            value = source[key]
            if isinstance(value,dict) or (isinstance(value,list) and any(isinstance(v,(dict,list)) for v in value)):
                raise ValueError('Unexpected structured value in public scalar field')
            result[key] = value
    return result

def proposal(value):
    return {**pick(value,['parameter_hash','missing_fields','confirmation_required']), 'request':pick(value['request'],REQUEST)}

def metrics(value):
    return {**pick(value,METRICS),
            'evidence_completeness':pick(value['evidence_completeness'],['supported','required','definition']),
            'concentration':pick(value['concentration'],['top1','top3','basis']),
            **({'series':[{**pick(row,['date','balance_fen']), 'events':[pick(event,['event_id','amount_fen','status']) for event in row['events']]} for row in value['series']]} if 'series' in value else {})}

def export_public(raw):
    from trace_guard import render_result
    messages=raw['state']['values']['messages'];reference=raw['reference']
    assert raw['mock'] is False and raw['run']['status']=='success'
    calls={c['id']:c for m in messages for c in m.get('tool_calls',[])}
    tool=next(m for m in reversed(messages) if m.get('type')=='tool' and m.get('name','').startswith('ext_yuyan_research_supplier_cash_scenario_'))
    result=json.loads(tool['content']);result=result.get('result',result)
    expected={**reference, **{scope:{k:v for k,v in reference[scope].items() if k!='series'} for scope in ('baseline','scenario')}}
    assert result==expected
    final=messages[-1]
    assert final['additional_kwargs']['financial_result_source']=='deterministic_tool' and final['content']==render_result(result)
    assert calls[tool['tool_call_id']]['args']=={'request_id':raw['request_id']}
    data={'mock':False,'status':'verified','model':'qwen-plus','recorded_at':raw['state']['created_at'],
          'question':raw['actual_user_prompt'],'actual_user_prompt':raw['actual_user_prompt'],'actual_followup_prompt':raw['actual_followup_prompt'],
          'system_policy_summary':'模型只提出参数；需明确确认；金额与最终回答由确定性工具及受控模板生成。',
          'parameters_prespecified':True,'confirmation_actor':raw['confirmation_actor'],
          'original_model_proposal':proposal(raw['original_model_proposal']),
          'harness_corrected_proposal':raw['harness_corrected_proposal'],
          'correction_summary':'验收程序依原问题将模型留空的折扣、费用、预付补为零，再显式确认；不是模型自主完成。',
          'confirmed_request':proposal(raw['confirmed_request']),
          'tool':'supplier_cash_scenario','arguments':{'request_id':raw['request_id']},
          'result':{**proposal(result),'base_version':result['base_version'],'baseline':metrics(result['baseline']),'scenario':metrics(result['scenario'])},
          'answer':final['content'],
          'boundary':'真实合成验收，参数预先指定；确认者是验收程序，不是真实客户。原始模型提案并未完整抽取成本。结果绑定确认快照和账本版本；公开记录仅含人工策略摘要，不披露完整内部提示。',
          'redaction_note':'标识一致替换为CASE-A、REQUEST-A、THREAD-A；哈希保留原始快照哈希，不能用脱敏标识重算。用户问题未简化。'}
    assert type(data['harness_corrected_proposal']) is bool
    def redact(value):
        if isinstance(value,str):
            for key,label in [('case_id','CASE-A'),('request_id','REQUEST-A'),('thread','THREAD-A')]:value=value.replace(raw[key],label)
            return value
        if isinstance(value,list):return [redact(v) for v in value]
        if isinstance(value,dict):return {k:redact(v) for k,v in value.items()}
        return value
    data=redact(data)
    if FORBIDDEN.search(json.dumps(data,ensure_ascii=False)):raise ValueError('Internal context detected; public export refused')
    return data

if __name__=='__main__':
    root=Path(__file__).resolve().parents[2]
    raw=json.loads(Path(__file__).with_name('evidence-final').joinpath('trace-raw-private.json').read_text())
    data=export_public(raw)
    (root/'agent-platform/frontend/public/research/trace.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    print('Sanitized public trace exported using strict nested allowlists')
