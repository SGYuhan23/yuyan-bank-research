import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from upgrade.graph_sage import prepare,predict,score,train,evaluate
from upgrade.graph_lab import ROOT,generate
from upgrade.graph_exercise import create
from upgrade.agent import Agent
from upgrade.store import Store
from upgrade.contracts import CaseRecord,ToolCall
from upgrade.tools import allowed,invoke
ART=ROOT/'eval/graphsage-v1/actual'
class GraphSageTests(unittest.TestCase):
 def test_numpy_checkpoint_permutation_equivariance(self):
  g,_=generate('dev',222,4);nodes,x,_,a=prepare(g);cp=json.loads((ART/'graphsage-11-checkpoint.json').read_text());p=np.random.default_rng(20).permutation(len(x))
  np.testing.assert_allclose(predict(cp,x,a)[p],predict(cp,x[p],a[p][:,p]),atol=1e-6)
 def test_model_uses_neighbors_and_ablation_does_not(self):
  g,_=generate('dev',222,4);_,x,_,a=prepare(g)
  cp=json.loads((ART/'graphsage-11-checkpoint.json').read_text());self.assertGreater(float(np.max(abs(predict(cp,x,a)-predict(cp,x,np.zeros_like(a))))),.001)
  cp=json.loads((ART/'sage_no_messages-11-checkpoint.json').read_text());np.testing.assert_array_equal(predict(cp,x,a),predict(cp,x,np.zeros_like(a)))
 def test_group_disjointness_and_label_separation(self):
  import networkx as nx
  sets=[]
  for split in ('train','dev','test'):
   g=json.loads((ART/f'{split}-observations.json').read_text());self.assertNotIn('labels',g);self.assertNotIn('accounts',g)
   net=nx.Graph();net.add_edges_from((e['from'],e['to']) for e in g['edges']);self.assertEqual(nx.number_connected_components(net),60);sets.append(set(net))
  for a,b in ((0,1),(0,2),(1,2)):self.assertFalse(sets[a]&sets[b])
 def test_no_future_transactions_enter_scoring(self):
  g,_=generate('dev',222,4);original=score(g,g['as_of']);g['edges'].append({'id':'future','from':'future-a','to':'future-b','at':'2099-01-01','amount':1,'currency':'AUD'})
  self.assertEqual(original,score(g,'2025-12-31'))
 def test_checkpoint_tamper_fails_explicitly(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'demo-manifest.json').write_text(json.dumps({'checkpoint':'cp.json','sha256':'wrong'}));(p/'cp.json').write_text('{}')
   self.assertEqual(score({'synthetic':True,'edges':[]},'2026',p)['status'],'unavailable')
 def test_metric_ap_and_budget_are_not_accuracy(self):
  r=evaluate([1,0,1,0],[.9,.8,.7,.1]);self.assertEqual(r['review_budget_k'],1);self.assertEqual(r['recall_at_k'],.5);self.assertNotIn('pr_auc',r);self.assertAlmostEqual(r['average_precision'],5/6)
 @unittest.skipUnless(importlib.util.find_spec('torch'),'Optional torch training dependency absent; inference tests still run')
 def test_actual_training_changes_weights_and_exports_selected_checkpoint(self):
  def data(seed):
   g,t=generate('train',seed,8);n,x,f,a=prepare(g);return n,x,f,a,np.array([t['accounts'][i] for i in n])
  tr,dev=data(42),data(43);cp,h,_=train(tr,dev,11,epochs=8)
  self.assertEqual(len(h),8);self.assertNotEqual(h[0]['train_loss'],h[-1]['train_loss']);self.assertEqual(cp['dev_ap'],max(r['dev_ap'] for r in h));self.assertTrue(np.isfinite(predict(cp,dev[1],dev[3])).all())
class GraphExerciseTests(unittest.TestCase):
 def test_regular_customer_case_cannot_use_graph_tools(self):
  c=CaseRecord(query='客服查到账',fields={'synthetic_graph':{'synthetic':True,'edges':[]}})
  self.assertNotIn('graph',allowed(c))
  with self.assertRaisesRegex(ValueError,'NOT_APPLICABLE'):invoke(c,ToolCall(tool_name='score'))
 def test_same_case_live_tools_review_export_and_invalidation(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(Path(d)/'db');c=create(s,'graphsage')
   def forbidden(*args):raise AssertionError('Fixed graph exercise must not claim LLM execution')
   a=Agent(s,c.case_id,1,model=forbidden);r=a.run();self.assertEqual(r['status'],'pending_review');ex=r['graph_exercise']
   self.assertEqual(ex['budget_k'],int(np.ceil(ex['accounts']*.1)));self.assertEqual(len(ex['candidates']),ex['budget_k'])
   edges={e['id']:e for e in c.fields['synthetic_graph']['edges']}
   for candidate,rec in zip(ex['candidates'],r['recommendations']):
    self.assertTrue(all(candidate['account'] in (edges[i]['from'],edges[i]['to']) for i in candidate['incident_edge_ids']))
    self.assertEqual(len(rec['supporting_evidence_ids']),2);self.assertIn('不证明诈骗',rec['trigger']);self.assertTrue(any('正常' in q for q in rec['unmet_conditions']))
   self.assertEqual({t['tool_name'] for t in r['tool_results']},{'graph','score'});self.assertFalse(any(e['kind']=='public_guidance' for e in r['evidence']))
   review={'request_id':'test','case_id':c.case_id,'case_version':1,'result_id':a.id,'operator':'test','decision':'reject','note':'缺少业务用途说明，不能以排名定罪'};s.review(review);self.assertEqual(len(s.export(c.case_id)['reviews']),1)
   s.update(c.case_id,1,{'query':'修改本次演练任务'});self.assertTrue(s.export(c.case_id)['results'][0]['stale'])
   with self.assertRaisesRegex(ValueError,'STALE'):s.review({**review,'request_id':'stale'})
 def test_unavailable_model_does_not_create_rankings(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(Path(d)/'db');c=create(s,'graphsage')
   with patch('upgrade.graph_sage.score',return_value={'status':'unavailable','reason':'missing'}):r=Agent(s,c.case_id,1).run()
   self.assertEqual(r['status'],'needs_input');self.assertEqual(r['recommendations'],[]);self.assertNotIn('graph_exercise',r)
 def test_real_data_marker_rejected(self):
  with self.assertRaisesRegex(ValueError,'SYNTHETIC_ONLY'):score({'synthetic':False,'edges':[]},'2026')
if __name__=='__main__':unittest.main()
