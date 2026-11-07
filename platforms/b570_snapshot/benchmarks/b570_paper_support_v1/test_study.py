"""Synthetic negative controls for the CPU toolkit, not native/GPU acceptance."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import study


def digest(x):
    return hashlib.sha256(str(x).encode()).hexdigest()


def fixtures():
    pool = []
    for d, b in study.GROUPS:
        for i in range(5):
            name = f'{d}-{b}-{i}'
            pool.append(dict(id=name, domain=d, token_count=study.BINS[b][0],
                             prompt_sha256=digest(name), token_ids_sha256=digest('tokens-' + name)))
    exp = dict(inventory_audited=True, inventory_sha256=digest('inventory'), coverage='synthetic test only', prompt_sha256=[])
    panel = study.select(pool, exp); bykey = {p['task_key']: p for p in panel}; rows = []
    for p in study.plan()['processes']:
        if p['stage'] != 'S3': continue
        for r in p['requests']:
            t = bykey[r['task_key']]
            rows.append({**r, 'prompt_sha256': t['prompt_sha256'], 'token_ids_sha256': t['token_ids_sha256'],
                         'qualified': True, 'endpoint_sha256': digest('endpoint-' + r['task_key']),
                         'raw_path': 'synthetic/' + r['request_id'], 'raw_sha256': digest(r['request_id']),
                         'duration_ms': 103.0 if r['arm'] == 'C_R_PQ' else 100.0})
    return pool, exp, panel, rows


class StudyTests(unittest.TestCase):
    def setUp(self): self.pool, self.exp, self.panel, self.rows = fixtures()
    def test_plan_budget(self):
        p = study.plan(); self.assertEqual(p['totals']['model_requests'], 716)
        self.assertEqual(p['totals']['native_process_attempts'], 229)
        for stage, requests, processes in [('S1',12,101),('S2',56,56),('S3',648,72)]:
            ps = [x for x in p['processes'] if x['stage'] == stage]
            self.assertEqual(len(ps),processes);self.assertEqual(sum(len(x['requests']) for x in ps),requests)
    def test_each_block_warmup_two_complete_passes(self):
        for p in study.plan()['processes']:
            if p['stage'] == 'S3':
                self.assertEqual(len(p['requests']),9)
                self.assertEqual(p['requests'][0]['role'],'warmup')
                for rep in (0,1):self.assertEqual(len({r['task_key'] for r in p['requests'] if r['repeat']==rep}),4)
    def test_full_gain(self):
        d = study.analyze(self.panel,self.rows);self.assertEqual(d['status'],'MEASURED_FIXED_PANEL_GAIN')
        self.assertAlmostEqual(d['comparisons']['C_R_PQ/C_R_QH']['ratio'],1.03)
        self.assertEqual(len(d['comparisons']['C_R_PQ/C_R_QH']['strata']),6)
    def test_parity_retained(self):
        for r in self.rows:r['duration_ms']=100
        self.assertEqual(study.analyze(self.panel,self.rows)['status'],'QUALIFIED_TRANSFER_NO_PREDECLARED_GAIN')
    def test_slower_candidate_retained(self):
        for r in self.rows:
            if r['arm']=='C_R_QH':r['duration_ms']=110
        d=study.analyze(self.panel,self.rows);self.assertLess(d['comparisons']['C_R_PQ/C_R_QH']['ratio'],1)
        self.assertEqual(len(d['comparisons']['C_R_PQ/C_R_QH']['regressions']),24)
    def test_one_reversed_session_blocks_gain_label(self):
        for r in self.rows:
            if r['arm']=='C_R_PQ':r['duration_ms']=99 if r['session']==0 else 110
        d=study.analyze(self.panel,self.rows);self.assertGreater(d['comparisons']['C_R_PQ/C_R_QH']['ratio'],1.02)
        self.assertEqual(d['status'],'QUALIFIED_TRANSFER_NO_PREDECLARED_GAIN')
    def test_missing_warmup_blocks_cost(self):
        self.rows.pop(0);d=study.analyze(self.panel,self.rows)
        self.assertEqual(len(d['missing']),1);self.assertIsNone(d['comparisons']['C_R_PQ/C_R_QH']['ratio'])
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):study.analyze(self.panel,self.rows+[self.rows[0]])
    def test_unknown_coordinate_rejected(self):
        self.rows[0]['session']=False
        with self.assertRaises(ValueError):study.analyze(self.panel,self.rows)
    def test_reference_instability(self):
        next(r for r in self.rows if r['arm']=='R')['endpoint_sha256']=digest('different')
        d=study.analyze(self.panel,self.rows);self.assertEqual(d['status'],'UNQUALIFIED_OR_INCOMPLETE')
    def test_candidate_divergent_warmup(self):
        next(r for r in self.rows if r['arm']=='C_R_QH' and r['role']=='warmup')['endpoint_sha256']=digest('different')
        self.assertEqual(study.analyze(self.panel,self.rows)['status'],'UNQUALIFIED_OR_INCOMPLETE')
    def test_pq_divergence_not_good_baseline(self):
        next(r for r in self.rows if r['arm']=='C_R_PQ')['endpoint_sha256']=digest('different')
        self.assertIsNone(study.analyze(self.panel,self.rows)['comparisons']['C_R_PQ/C_R_QH']['ratio'])
    def test_invalid_record_preserved(self):
        row=next(r for r in self.rows if r['arm']=='C_R_QH');row.update(qualified=False,reason='native failure',duration_ms=None)
        d=study.analyze(self.panel,self.rows);self.assertIn(row['request_id'],d['failed'])
    def test_nan_bool_time_rejected(self):
        for val in (float('nan'),float('inf'),True,0,-1):
            rows=copy.deepcopy(self.rows);rows[0]['duration_ms']=val
            with self.assertRaises(ValueError):study.analyze(self.panel,rows)
    def test_missing_provenance_rejected(self):
        self.rows[0]['raw_sha256']=None
        with self.assertRaises(ValueError):study.analyze(self.panel,self.rows)
    def test_input_substitution_rejected(self):
        self.rows[0]['prompt_sha256']=digest('other')
        with self.assertRaises(ValueError):study.analyze(self.panel,self.rows)
    def test_selector_order_invariant(self):
        self.assertEqual(self.panel,study.select(list(reversed(self.pool)),self.exp))
    def test_exposure_excluded(self):
        excluded=self.panel[0]['prompt_sha256'];self.exp['prompt_sha256']=[excluded]
        self.assertNotIn(excluded,[r['prompt_sha256'] for r in study.select(self.pool,self.exp)])
    def test_outcome_selection_rejected(self):
        self.pool[0]['latency']=1
        with self.assertRaises(ValueError):study.select(self.pool,self.exp)
    def test_unfilled_stratum_rejected(self):
        with self.assertRaises(ValueError):study.select(self.pool[2:],self.exp)
    def test_duplicate_prompt_alias_rejected(self):
        self.pool[1]['prompt_sha256']=self.pool[0]['prompt_sha256']
        with self.assertRaises(ValueError):study.select(self.pool,self.exp)
    def test_unreviewed_exposure_rejected(self):
        self.exp['inventory_audited']=False
        with self.assertRaises(ValueError):study.select(self.pool,self.exp)
    def test_wrong_panel_stratum_rejected(self):
        self.panel[0]['token_count']=1024
        with self.assertRaises(ValueError):study.analyze(self.panel,self.rows)
    def test_output_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';study.write_new(p,{'a':1})
            with self.assertRaises(FileExistsError):study.write_new(p,{'a':2})
    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';p.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError):study.load(p)


if __name__ == '__main__': unittest.main(verbosity=2)
