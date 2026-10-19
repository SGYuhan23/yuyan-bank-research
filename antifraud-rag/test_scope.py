import unittest,json
from unittest.mock import Mock
from pipeline import ROOT,Answer,Assessment,Operation,TaskScene,scope_issues,RagRun,scoped_evidence,scope_review_passes
U={u['unit_id']:u for u in json.loads((ROOT/'data/units.json').read_text())}
def assessment(*scenes):return Assessment(sufficient=True,relevant_ids=list(U),missing=[],conflicts=[],task_scenes=[TaskScene(scene=s,question_basis='问题') for s in scenes])
def answer(scene,source,target,trigger,text='对本次请求核实'):
 return Answer(steps=[Operation(scene=scene,target=target,trigger=trigger,text=text,citations=[{'unit_id':source}])],risks=[],boundaries=[],questions=[],scenario=None,scenario_label='not_applicable',review_status='pending_human_review')
class Scope(unittest.TestCase):
 def test_seller_cannot_take_supplier_action_even_if_conditional(self):
  a=answer('unreceived_payment','bec-guidance','此前货款','如果供应商称未收到款')
  self.assertTrue(scope_issues(a,assessment('seller_receipt')))
 def test_account_change_does_not_imply_unreceived(self):
  a=answer('unreceived_payment','bec-guidance','此前货款','供应商称未收到款')
  self.assertTrue(scope_issues(a,assessment('account_change')))
 def test_legitimate_unreceived_condition_and_source_preserved(self):
  a=answer('unreceived_payment','bec-guidance','供应商声称未收到的上周货款及该笔补付','对方明确声称未收到此前付款，调查前')
  self.assertEqual(scope_issues(a,assessment('unreceived_payment')),[])
  self.assertEqual(a.steps[0].target,'供应商声称未收到的上周货款及该笔补付')
 def test_comparison_allows_both_roles(self):
  a=answer('seller_receipt','receipt-guidance','本次销售货款及交货','交货前确认到账')
  a.steps+=answer('account_change','bec-guidance','本次变更账户及其付款','独立核实该请求前').steps
  self.assertEqual(scope_issues(a,assessment('seller_receipt','account_change')),[])
 def test_wrong_source_cannot_support_seller_operation(self):
  a=answer('seller_receipt','bec-guidance','买家本笔货款','发货前')
  self.assertTrue(scope_issues(a,assessment('seller_receipt')))
 def test_scope_fields_not_enough_to_pass_broad_actual_text(self):
  # Mocked reviewer flags the semantic target error, not a banned-word regex.
  r=object.__new__(RagRun);r.units=U;r.assessment=assessment('account_change');r.calculations=[]
  r.data={'query':'本次账户变更','task':'knowledge'};r.log=lambda *a,**k:None
  r.answer=answer('account_change','bec-guidance','本次变更请求','核实本次变更前','暂停后续支付动作：不得执行新付款、补付或重复付款。')
  r.scope_repaired=True
  r.review_scope=Mock(return_value={'pass':False,'issues':['正文没有限定付款对象，字段不能免责'],'step_checks':[{'index':0,'role_matches':True,'target_bounded':False,'condition_preserved':True,'source_supported':False}]})
  with self.assertRaisesRegex(ValueError,'OUTPUT_SCOPE_REVIEW_FAILED'):r.validate({})
  self.assertIn('不得执行新付款',r.answer.steps[0].text)
 def test_missing_per_step_review_cannot_pass(self):
  r=object.__new__(RagRun);r.units=U;r.assessment=assessment('seller_receipt');r.calculations=[];r.data={'query':'到账？','task':'knowledge'};r.log=lambda *a,**k:None
  r.answer=answer('seller_receipt','receipt-guidance','本次销售货款','交货前核实实际到账');r.scope_repaired=True;r.review_scope=Mock(return_value={'pass':True,'issues':[],'step_checks':[]})
  with self.assertRaisesRegex(ValueError,'OUTPUT_SCOPE_REVIEW_FAILED'):r.validate({})
 def test_scope_spans_keep_required_trigger_and_separate_other_scene(self):
  change=scoped_evidence(U,assessment('account_change'))
  guide=next(x for x in change if x['unit_id']=='bec-guidance')
  self.assertIn("verbally verified",guide['text']);self.assertNotIn("haven’t received payment",guide['text'])
  unpaid=next(x for x in scoped_evidence(U,assessment('unreceived_payment')) if x['unit_id']=='bec-guidance')
  self.assertIn('A supplier or employee claim they haven’t received payment.',unpaid['text']);self.assertIn('payment history and emails',unpaid['text'])
  seller=scoped_evidence(U,assessment('seller_receipt'));self.assertNotIn('bec-guidance',[x['unit_id'] for x in seller])
  self.assertIn('Never rely on a receipt',next(x['text'] for x in seller if x['unit_id']=='receipt-guidance'))
 def test_global_approval_cannot_override_failed_step(self):
  v={'pass':True,'step_checks':[{'index':0,'role_matches':True,'target_bounded':False,'condition_preserved':True,'source_supported':True}]}
  self.assertFalse(scope_review_passes(v,1))
 def test_actual_historical_regressions_rejected_by_runtime(self):
  rows=json.loads((ROOT/'eval/scope/historical-audits.json').read_text())['results']
  self.assertEqual(len(rows),3)
  for row in rows:
   old=json.loads((ROOT/'runs'/row['old_run']/'run.json').read_text())
   self.assertFalse(scope_review_passes(row['verdict'],len(old['result']['answer']['steps'])))
 def test_question_cannot_bypass_scope_review(self):
  a={'steps':[],'risks':[],'boundaries':[],'questions':['如未收到款则再查付款历史'],'scenario':None}
  v={'pass':True,'step_checks':[],'other_checks':[{'field':'questions','index':0,'scope_supported':False,'reason':'卖方任务混入付款方核查'}]}
  self.assertFalse(scope_review_passes(v,0,a))
 def test_essential_checks_required_even_when_each_step_supported(self):
  v={'pass':True,'step_checks':[{'index':0,'role_matches':True,'target_bounded':True,'condition_preserved':True,'source_supported':True}], 'scene_checks':[{'scene':'unreceived_payment','essential_checks_present':False,'reason':'只有查付款历史，遗漏邮件与调查前不重复支付同笔款项'}]}
  self.assertFalse(scope_review_passes(v,1,required_scenes=['unreceived_payment']))
 def test_optional_null_scenario_audit_not_a_false_rejection(self):
  a={'steps':[],'risks':[],'boundaries':[],'questions':[],'scenario':None}
  v={'pass':True,'step_checks':[],'other_checks':[{'field':'scenario','index':0,'scope_supported':True}]}
  self.assertTrue(scope_review_passes(v,0,a))
  v['other_checks'][0]['scope_supported']=False
  self.assertFalse(scope_review_passes(v,0,a))
if __name__=='__main__':unittest.main()
