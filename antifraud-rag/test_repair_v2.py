import json,unittest
from pathlib import Path
from pipeline import scope_review_passes
from upgrade.grounding import Audit,validate_audit
class RepairTests(unittest.TestCase):
 def test_optional_other_scene_is_not_false_rejection(self):
  a={'steps':[],'risks':[],'boundaries':[],'questions':[],'scenario':None}
  v={'pass':True,'step_checks':[],'other_checks':[],'scene_checks':[{'scene':'other','essential_checks_present':True}]}
  self.assertTrue(scope_review_passes(v,0,a,['other']))
  v['scene_checks'][0]['essential_checks_present']=False;self.assertFalse(scope_review_passes(v,0,a,['other']))
 def test_extra_unrequested_scene_still_fails(self):
  self.assertFalse(scope_review_passes({'pass':True,'step_checks':[],'scene_checks':[{'scene':'other','essential_checks_present':True}]},0,required_scenes=['seller_receipt']))
 def test_unbacked_question_cannot_pass_on_generic_boolean(self):
  a={'questions':['必须盖章吗？']}
  v=Audit(checks=[dict(field='questions',index=0,supported=True,applicable=True,already_answered=False,unit_id=None,source_quote='',reason='听起来合理')],coverage_ok=True,missing_essential=[])
  with self.assertRaisesRegex(ValueError,'SOURCE_REQUIRED'):validate_audit(v,a,{})
 def test_quote_must_exist_in_scoped_source(self):
  a={'questions':['是否有密语？']};v=Audit(checks=[dict(field='questions',index=0,supported=True,applicable=True,already_answered=False,unit_id='x',source_quote='use password',reason='')],coverage_ok=True,missing_essential=[])
  with self.assertRaisesRegex(ValueError,'QUOTE_INVALID'):validate_audit(v,a,{'x':{'text':'verbally verify request'}})
 def test_answered_question_is_rejected_even_with_source(self):
  v=Audit(checks=[dict(field='questions',index=0,supported=True,applicable=True,already_answered=True,unit_id='x',source_quote='verbally verify',reason='用户已说通过电话核实')],coverage_ok=True,missing_essential=[])
  issues=validate_audit(v,{'questions':['是否已口头核实？']},{'x':{'text':'verbally verify'}});self.assertEqual(len(issues),1)
 def test_cannot_omit_a_question_from_audit(self):
  with self.assertRaises(ValueError):validate_audit(Audit(checks=[],coverage_ok=True,missing_essential=[]),{'questions':['x']},{})

class SpanBindingTests(unittest.TestCase):
 def test_program_binds_source_text_not_generated_quote(self):
  from upgrade.grounding import source_spans,resolve_spans
  units={'u':{'text':'Verify this request. Never rely on screenshots.'}}
  spans=source_spans(units)
  a=Audit(checks=[dict(field='steps',index=0,supported=True,applicable=True,already_answered=False,unit_id='u',source_quote='',source_span_id='u:1',reason='')],coverage_ok=True,missing_essential=[])
  resolve_spans(a,spans);self.assertEqual(a.checks[0].source_quote,'Never rely on screenshots.')
  self.assertEqual(validate_audit(a,{'steps':[{'text':'核实到账'}]},units),[])
 def test_cross_source_span_rejected(self):
  from upgrade.grounding import resolve_spans
  a=Audit(checks=[dict(field='steps',index=0,supported=True,applicable=True,already_answered=False,unit_id='v',source_span_id='u:0',reason='')],coverage_ok=True,missing_essential=[])
  with self.assertRaisesRegex(ValueError,'SPAN_INVALID'):resolve_spans(a,{'u:0':{'unit_id':'u','text':'Verify'}})

class CoverageFallbackTests(unittest.TestCase):
 def test_partial_lexical_hits_trigger_real_adapter_only_in_auto(self):
  import tempfile
  from types import SimpleNamespace
  from unittest.mock import patch
  from upgrade.agent import Agent
  from upgrade.store import Store
  from upgrade.contracts import CaseRecord,Evidence
  from pipeline import Assessment
  assessment=Assessment(sufficient=False,task_scenes=[{'scene':'seller_receipt','question_basis':'交货'}],relevant_ids=[],missing=['未取得到账指引'],conflicts=[])
  def assess(legacy,state):legacy.assessment=assessment
  for mode in ('auto','bm25'):
   with tempfile.TemporaryDirectory() as d:
    store=Store(Path(d)/'db');c=store.create(CaseRecord(query='交货前怎么查？',requester_role='卖方收款'))
    agent=Agent(store,c.case_id,1,retriever=mode)
    agent.case.evidence=[Evidence(case_id=c.case_id,case_version=1,kind='public_guidance',origin_id='bec-guidance',span={'unit_id':'bec-guidance'},source_hash='test',jurisdiction='Australia',statement='变更核实',limitations=[])]
    agent.units={'bec-guidance':{'unit_id':'bec-guidance','text':'verify account change'}}
    failed=SimpleNamespace(status='unavailable',observations=[],model_dump=lambda:{'status':'unavailable','tool_name':'guidance'})
    with patch('upgrade.agent.RagRun.assess',assess),patch('upgrade.agent.RagRun.calculate'),patch('upgrade.agent.invoke',return_value=(failed,[])) as invoke:
     agent.draft({})
    self.assertEqual(invoke.call_count,int(mode=='auto'))
    if mode=='auto':
     self.assertEqual(invoke.call_args.args[1].args,{'mode':'semantic'})
     self.assertIn('语义补检失败',agent.data['summary'])
     self.assertTrue(any(r['kind']=='coverage_retrieval_needed' for r in agent.data['records']))

class EmptyReviewTests(unittest.TestCase):
 def test_empty_question_positive_audit_is_harmless_but_negative_is_not(self):
  a={'steps':[],'risks':[],'boundaries':[],'questions':[],'scenario':None}
  v={'pass':True,'step_checks':[],'other_checks':[{'field':'questions','index':0,'scope_supported':True}],'scene_checks':[]}
  self.assertTrue(scope_review_passes(v,0,a,[]))
  v['other_checks'][0]['scope_supported']=False;self.assertFalse(scope_review_passes(v,0,a,[]))

if __name__=='__main__':unittest.main()
