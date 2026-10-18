import unittest,json,hashlib
from pipeline import ROOT,RagRun,Claim,Answer,Assessment
from retrieval import bm25
class Integrity(unittest.TestCase):
 def test_metadata_and_units(self):
  units=json.loads((ROOT/'data/units.json').read_text())
  for u in units:
   for k in ['source_id','title','url','published_or_updated_at','retrieved_at','region','material_type','page_or_section','file_sha256','review_status']:self.assertIn(k,u)
   self.assertEqual(u['unit_sha256'],hashlib.sha256(u['text'].encode()).hexdigest())
   self.assertNotIn(u['material_type'],['project_authored_training','eval_fixture_not_official'])
 def test_case_privacy_and_conditions_together(self):
  u=next(u for u in json.loads((ROOT/'data/units.json').read_text()) if u['unit_id']=='bec-case')
  self.assertIn('one or more real scam reports',u['text']);self.assertIn('contact your bank',u['text']);self.assertIn('$17,000',u['text'])
 def test_production_does_not_read_eval(self):
  for name in ['pipeline.py','retrieval.py']:
   text=(ROOT/name).read_text();self.assertNotIn('cases.json',text);self.assertNotIn('must_check',text)
 def test_exact_citation_guard(self):
  run=object.__new__(RagRun);run.units={'a':{'text':'Original statement with a limitation.'}}
  with self.assertRaises(ValueError):run.check_citations([Claim(text='unsupported',citations=[{'unit_id':'a','quote':'Invented original sentence'}])])
 def test_unknown_reference_guard(self):
  run=object.__new__(RagRun);run.units={}
  with self.assertRaises(ValueError):run.check_citations([Claim(text='bad',citations=[{'unit_id':'unknown','quote':'Some invented original'}])])
 def test_full_section_citation_materialized(self):
  run=object.__new__(RagRun);run.units={'a':{'text':'Original complete section.'}};events=[];run.log=lambda kind,**data:events.append(kind)
  claim=Claim(text='test',citations=[{'unit_id':'a'}]);run.check_citations([claim]);self.assertEqual(claim.citations[0].quote,'Original complete section.');self.assertIn('citation_materialized',events)
 def test_conditional_scope_restored(self):
  run=object.__new__(RagRun);text='A supplier or employee claim they haven’t received payment. Investigate the payment history.'
  run.units={'bec-guidance':{'text':text}};run.data={'task':'knowledge','query':'供应商账户变更'};run.calculations=[];events=[]
  run.log=lambda kind,**data:events.append(kind);run.call=lambda *args,**kwargs:{'pass':True,'issues':[]}
  run.assessment=Assessment(sufficient=True,relevant_ids=['bec-guidance'],missing=[],conflicts=[])
  run.answer=Answer(steps=[Claim(text='核查付款历史',citations=[{'unit_id':'bec-guidance','quote':text}])],risks=[],boundaries=[],questions=[],scenario=None,scenario_label='not_applicable',review_status='pending_human_review')
  run.validate({});self.assertTrue(run.data['result']['answer']['steps'][0]['text'].startswith('如果供应商或员工称未收到付款'));self.assertIn('condition_scope_applied',events)
 def test_baseline_empty_query(self):self.assertEqual(bm25('xyz',[{'search_labels':'供应商','text':'supplier','unit_id':'x'}])[0][1],0)
if __name__=='__main__':unittest.main()
