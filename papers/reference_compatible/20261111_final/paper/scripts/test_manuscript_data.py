"""Independent consistency checks of the supplied numerical evidence projections.
No GPU or network access. A pass is not native numerical qualification.
"""
from pathlib import Path
import csv, hashlib, json, math, unittest
from collections import Counter, defaultdict
import numpy as np
P=Path(__file__).resolve().parents[1]
def get(n): return json.loads((P/'data'/n).read_text())
class EvidenceChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=json.loads((P/'generated/analysis.json').read_text())
        with (P/'data/q32_measurements.csv').open() as stream: cls.rows=list(csv.DictReader(stream))
    def test_all_input_hashes(self):
        m=json.loads((P/'SOURCE_MANIFEST.json').read_text())
        for name,x in m['data'].items():
            self.assertEqual(hashlib.sha256((P/'data'/name).read_bytes()).hexdigest(),x['sha256'],name)
    def test_q32_complete_design(self):
        cells={(r['root'],r['arm'],int(r['round'])) for r in self.rows}
        self.assertEqual(len(cells),96);self.assertEqual(len(self.rows),96)
        self.assertEqual(len({r['root'] for r in self.rows}),4)
        self.assertEqual(set(Counter(r['arm'] for r in self.rows).values()),{16})
    def test_q32_original_six_controls(self):
        self.assertEqual(set(self.a['q32']['totals']),{'W_REF1L_M','W_REF1G_M','L_REF1L_M','L_REF1G_M','W_REF1L_D4','L_REF1G_D4'})
    def test_q32_positive_finite_times(self):
        self.assertTrue(all(float(r['service_s'])>0 and math.isfinite(float(r['service_s'])) for r in self.rows))
    def test_q32_totals(self):
        sums=defaultdict(float)
        for r in self.rows:sums[r['arm']]+=float(r['service_s'])
        for k,v in sums.items():self.assertAlmostEqual(v,self.a['q32']['totals'][k],places=9)
    def test_q32_group_baseline(self):
        q=self.a['q32'];self.assertAlmostEqual(1-q['whole_group_over_loop'],.0561642906,places=8)
        self.assertAlmostEqual(q['draft_over_best_M'],1.1400004759787872,places=12)
    def test_application_all_fixed_controls(self):
        self.assertEqual(len(self.a['applications']),3)
        for a in self.a['applications']:
            self.assertEqual(len(a['totals']),6);self.assertEqual(len(a['reported_ratios']),5)
            self.assertEqual(len(a['reported_intervals']),5)
    def test_application_ratios(self):
        arms=['W_L4_M','W_P_M','L_L4_M','L_P_M','W_L4_D4']
        for a in self.a['applications']:
            for k,r in zip(arms,a['reported_ratios']):self.assertAlmostEqual(a['totals']['L_P_D4']/a['totals'][k],r,places=12)
    def test_application_root_units(self):
        self.assertEqual([x['roots'] for x in self.a['applications']],[16,16,12])
        self.assertEqual([x['formal_per_arm'] for x in self.a['applications']],[64,64,48])
    def test_q8_complete_root_array(self):
        q=get('q8_root_sums.json');self.assertEqual(np.asarray(q['sums']).shape,(8,16));self.assertEqual(len(set(q['roots'])),16)
    def test_q8_all_eight_estimands(self):self.assertEqual(len(self.a['q8']['contrasts']),8)
    def test_q8_all_interval_endpoints(self):
        q=get('q8_root_sums.json');x=np.asarray(q['sums']);idx=np.random.Generator(np.random.PCG64(20261109)).integers(0,16,(10000,16));b=x[:,idx].sum(axis=2)
        for c in self.a['q8']['contrasts']:
            i=q['arms'].index(c['numerator']);j=q['arms'].index(c['denominator'])
            np.testing.assert_allclose(np.quantile(b[i]/b[j],[.00625,.99375]),c['adjusted_interval'],rtol=0,atol=2e-12)
    def test_q8_equal_work_all_cells(self):
        self.assertEqual(len(self.a['equal_work']),4)
        for c in self.a['equal_work']:
            self.assertEqual(len(c['root_ratios']),4)
            self.assertAlmostEqual(c['ratio'],sum(c['q8'])/sum(c['q4pair']),places=12)
    def test_balanced_factor_ratios(self):
        for f in self.a['factors'].values():
            self.assertEqual(len(f['all_fixed_controls']),4)
            for c in f['all_fixed_controls']:
                self.assertEqual(len(c['root_ratios']),16)
                self.assertAlmostEqual(c['total_ratio'],f['totals'][c['numerator']]/f['totals'][c['denominator']],places=12)
    def test_vulkan_complete_108_timings(self):
        cells=get('b570_inputs.json')['cells'];self.assertEqual(len(cells),12)
        self.assertEqual(sum(np.asarray(x).size for x in cells.values()),108)
        for x in cells.values():self.assertTrue(np.isfinite(x).all());self.assertTrue((np.asarray(x)>0).all())
    def test_vulkan_inside_and_crossing_retained(self):
        rows=self.a['vulkan_geometry'];self.assertEqual(len(rows),12)
        self.assertTrue(any(x['ratio']>1 for x in rows));self.assertTrue(any(x['ratio']<1 for x in rows))
    def test_q32_descriptive_no_fabricated_CI(self):self.assertNotIn('confidence_interval',self.a['q32'])
    def test_plans_explicitly_excluded(self):
        m=json.loads((P/'SOURCE_MANIFEST.json').read_text())
        self.assertTrue(any('PR217' in x for x in m['explicit_exclusions']))
        self.assertTrue(any('A4000' in x for x in m['explicit_exclusions']))
if __name__=='__main__':unittest.main()
