"""Meaningful integrity/charging/leakage tests, not inference tests."""
import unittest
from copy import deepcopy
from audit import DOC,load,index,normalize,action_metrics,save
from replay import QueryAPI,initial,proxy_screen,run

class Risks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ctx=load(DOC/'inputs/OUTCOMES.json')[0];cls.actions=load(DOC/'ACTION_CATALOG.json')[0]['actions']
    def test_duplicate_keys(self):
        with self.assertRaises(ValueError):index(self.ctx['records']+[self.ctx['records'][0]],self.ctx['tasks'],self.ctx['known_conditions'])
    def test_missing_repetition(self):
        with self.assertRaises(ValueError):index(self.ctx['records'][1:],self.ctx['tasks'],self.ctx['known_conditions'])
    def test_endpoint_and_truncation(self):
        with self.assertRaises(AssertionError):normalize({'task':'x','condition':'x','rep':1,'ids':[1,2],'endpoint':'limit'})
        with self.assertRaises(AssertionError):normalize({'task':'x','condition':'x','rep':1,'ids':[151645,2],'endpoint':'EOS'})
    def test_unknown_denominator(self):
        c=load(DOC/'inputs/OUTCOMES.json')[1];r=action_metrics(c,'U2');self.assertEqual(r['status'],'UNKNOWN');self.assertEqual(r['missing_observations'],72);self.assertIsNone(r['reference_matches'])
    def test_unpaid_input_rejected(self):
        a=QueryAPI(self.ctx)
        with self.assertRaises(ValueError):a.request('N1','probe')
        self.assertTrue(a.ledger[0]['charge_before_reveal'])
    def test_reference_acquisition_hides_baseline_labels(self):
        a=QueryAPI(self.ctx);r=a.request('R','reference')
        self.assertNotIn('repairs',r);self.assertNotIn('regressions',r)
        self.assertFalse(a.baseline_acquired)
    def test_every_probe_charged(self):
        r=run(self.ctx,self.actions,'P2');self.assertEqual(r['additional_requested_records'],114)
        self.assertEqual([x['handle'] for x in r['ledger']],['R','N0','H1','U2'])
        self.assertTrue(all(x['charge_before_reveal'] for x in r['ledger']))
    def test_identifiers_do_not_select_remedy(self):
        original=run(self.ctx,self.actions,'P2');c=deepcopy(self.ctx);mapping={t:'anonymous-'+str(i) for i,t in enumerate(c['tasks'])}
        c['name']='other-platform';c['tasks']=[mapping[t] for t in c['tasks']]
        for x in c['records']:x['task']=mapping[x['task']]
        changed=run(c,self.actions,'P2');self.assertEqual(original,changed)
    def test_unqueried_native_label_hidden(self):
        original=run(self.ctx,self.actions,'P2');c=deepcopy(self.ctx)
        refs={(x['task'],x['rep']):x for x in c['records'] if x['condition']=='R'}
        for x in c['records']:
            if x['condition']=='N1':x['ids']=refs[x['task'],x['rep']]['ids'][:];x['endpoint']=refs[x['task'],x['rep']]['endpoint']
        changed=run(c,self.actions,'P2');self.assertEqual(original,changed)
        self.assertNotIn('N1',[x['handle'] for x in original['ledger']])
    def test_unknown_not_selected(self):
        c=load(DOC/'inputs/OUTCOMES.json')[2];a=load(DOC/'ACTION_CATALOG.json')[2]['actions'];r=run(c,a,'P2')
        self.assertEqual(r['decision'],'ABSTAIN_UNKNOWN');self.assertEqual(r['unknown_requested_records'],72)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Risks)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    save(DOC/'TEST_RESULTS.json',{'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'status':'PASS' if result.wasSuccessful() else 'FAIL','policy_tested':'P2 only; P1 not implemented','new_inference_runs':0})
    raise SystemExit(0 if result.wasSuccessful() else 1)
