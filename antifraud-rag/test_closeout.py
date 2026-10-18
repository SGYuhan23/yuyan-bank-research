import json,unittest
from unittest.mock import patch
from pipeline import ROOT,RagRun,preserve_case_loss
from retrieval import retrieve
UNITS=json.loads((ROOT/'data/units.json').read_text())
CASE=next(x for x in UNITS if x['unit_id']=='bec-case')['text']
class Closeout(unittest.TestCase):
 def test_auto_fallback_logs(self):
  events=[]
  with patch('retrieval.semantic',return_value=[(UNITS[0],.7)]) as sem:
   result=retrieve('xyznotinknowledge',units=UNITS,log=lambda kind,**d:events.append({'kind':kind,**d}))
  sem.assert_called_once();self.assertEqual(result[0]['unit'],UNITS[0]);self.assertEqual([e['method'] for e in events if e['kind']=='retrieval_started'],['bm25','semantic']);self.assertTrue(any(e.get('reason')=='bm25_no_positive_score' for e in events));self.assertEqual(events[-1]['source_ids'],[UNITS[0]['source_id']])
 def test_explicit_bm25_no_fallback(self):
  with patch('retrieval.semantic') as sem:self.assertEqual(retrieve('xyznotinknowledge','bm25',UNITS),[]);sem.assert_not_called()
 def test_bm25_hit_no_fallback(self):
  with patch('retrieval.semantic') as sem:self.assertTrue(retrieve('供应商账户变更',units=UNITS));sem.assert_not_called()
 def test_explicit_semantic(self):
  with patch('retrieval.semantic',return_value=[(UNITS[0],.7)]) as sem,patch('retrieval.bm25') as lexical:
   retrieve('hello','semantic',UNITS);sem.assert_called_once();lexical.assert_not_called()
 def test_unavailable_is_failure_not_no_evidence(self):
  events=[]
  with patch('retrieval.semantic',side_effect=RuntimeError('credential must not appear')):
   with self.assertRaisesRegex(RuntimeError,'语义检索不可用') as raised:retrieve('xyznotinknowledge',units=UNITS,log=lambda kind,**d:events.append({'kind':kind,**d}))
  self.assertNotIn('credential',str(raised.exception));self.assertEqual(events[-1]['kind'],'retrieval_failed');self.assertFalse(any(e['kind']=='retrieval_attempt_completed' and e['method']=='semantic' for e in events))
 def test_case_amount_reference_not_model_judged(self):
  for bad in ['John案例中伪造邮件导致$17,000损失及后续连锁损失超$30,000。','最初1.7万澳元，另损失3万澳元。']:
   corrected=preserve_case_loss(bad,CASE)
   self.assertIn('估计总损失超过30,000澳元',corrected);self.assertIn('包含最初17,000澳元',corrected);self.assertIn('不能将两笔金额相加',corrected)
  with self.assertRaisesRegex(ValueError,'SOURCE_CHANGED'):preserve_case_loss('$30,000','different source')
 def test_unrelated_amount_not_rewritten(self):self.assertEqual(preserve_case_loss('无金额的核实建议',CASE),'无金额的核实建议')
if __name__=='__main__':unittest.main()
