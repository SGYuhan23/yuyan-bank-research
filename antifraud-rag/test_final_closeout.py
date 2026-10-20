import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from upgrade import training
from upgrade.store import Store
from upgrade.contracts import CaseRecord,digest,Recommendation,Evidence

class FinalCloseoutTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store=Store(Path(self.tmp.name)/'db')
 def tearDown(self):self.tmp.cleanup()
 def test_all_18_current_variant_facts_and_initial_information(self):
  ss=training.scenarios();self.assertEqual(len(ss),18)
  for s in ss.values():
   with self.subTest(sid=s.scenario_id):
    self.assertEqual(s.rubric,{k:'询问并核对：'+v for k,v in s.allowed_responses.items()})
    session=training.start(self.store,s.scenario_id);d=training.debrief(self.store,session['session_id'])
    for row in d['criteria']:
     known=row['criterion'] in s.initial_information or s.allowed_responses[row['criterion']] in s.visible_facts
     self.assertEqual(row['initially_known'],known)
     self.assertEqual(row['known_fact'],s.initial_information.get(row['criterion'],s.allowed_responses[row['criterion']]) if known else None)
     if known:self.assertIsNone(row['omission'])
     self.assertEqual(row['semantic_status'],'pending_review')
    if s.legitimate and s.family_id=='unreceived_payment':
     self.assertIn('已完成',s.allowed_responses['repeat']);self.assertIn('随后',s.allowed_responses['prior'])
 def test_topic_negation_is_not_correctness(self):
  s=next(s for s in training.scenarios().values() if s.family_id=='account_change' and not s.legitimate and s.clue_level==0)
  sid=training.start(self.store,s.scenario_id)['session_id']
  training.turn(self.store,sid,'不用电话，不必核对账户，本次直接付款')
  d=training.debrief(self.store,sid)
  self.assertEqual(d['matched'],3);self.assertTrue(d['scope_flags']);self.assertEqual(d['review_status'],'pending_human_review')
  self.assertTrue(all(c['semantic_status']=='pending_review' for c in d['criteria']))
 def test_semantic_reviewer_gets_visible_initial_not_unreleased_truth(self):
  s=next(s for s in training.scenarios().values() if s.family_id=='account_change' and s.legitimate and s.clue_level==1)
  sid=training.start(self.store,s.scenario_id)['session_id'];captured=[]
  def model(_self,messages,phase):
   captured.append(json.loads(messages[1]['content']));return {'checks':[],'limitations':['mock contract input test only']}
  with patch('pipeline.RagRun.model',model):training.semantic_debrief(self.store,sid)
  payload=captured[0];self.assertEqual(payload['visible_initial_facts'],s.visible_facts)
  self.assertNotIn('review_only_rubric',payload)
  row=next(r for r in payload['criterion_information'] if r['criterion']=='independent')
  self.assertTrue(row['initially_known']);self.assertIn('已用',row['known_fact'])
  self.assertNotIn('latent_truth',json.dumps(training.learner_context(self.store,sid)))
  self.assertNotIn(s.allowed_responses['change'],json.dumps(payload,ensure_ascii=False))
 def test_session_snapshot_does_not_leak_or_change_after_library_change(self):
  s=next(iter(training.scenarios().values()));sid=training.start(self.store,s.scenario_id)['session_id']
  with patch('upgrade.training.scenarios',return_value={}):
   self.assertEqual(training.learner_context(self.store,sid)['scenario']['visible_facts'],s.visible_facts)
   training.debrief(self.store,sid)
 def test_review_covers_original_risks_and_revision_is_separate(self):
  c=self.store.create(CaseRecord(query='审核'));result={'run_id':'original','case_version':1,'status':'pending_review','recommendations':[],'answer':{'risks':[{'text':'待复核的风险'}]}}
  c.evidence.append(Evidence(case_id=c.case_id,case_version=1,kind='reported_claim',origin_id='test',span={},source_hash='fixture',jurisdiction='Australia',statement='测试事实',limitations=[]));self.store.finish(c,result)
  base=dict(case_id=c.case_id,case_version=1,result_id='original',operator='local',note='检查全部内容')
  accepted=self.store.review(dict(**base,request_id='a',decision='accept',revisions=[]))
  self.assertEqual(accepted['result_hash'],digest(result));self.assertIn('risks',accepted['review_scope'])
  revision=Recommendation(scene='other',target='本次演练',trigger='人工复核',action='人工改写',supporting_evidence_ids=[c.evidence[0].evidence_id],counter_evidence_ids=[],unmet_conditions=[])
  saved=self.store.review(dict(**base,request_id='b',decision='revise',revisions=[revision.model_dump()]))
  self.assertIn('original_result_unchanged',saved['review_scope']);self.assertEqual(self.store.result('original'),result)
  self.store.update(c.case_id,1,{'query':'新材料'})
  with self.assertRaisesRegex(ValueError,'STALE'):self.store.review(dict(**base,request_id='c',decision='accept',revisions=[]))
if __name__=='__main__':unittest.main()
