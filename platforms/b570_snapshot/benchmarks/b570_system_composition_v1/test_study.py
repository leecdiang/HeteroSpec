"""Synthetic CPU tests, not Windows/Vulkan qualification or collected evidence."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
import study as s


def task(name, domain, n, token):
    ids = [token]*n
    return {'id': name, 'domain': domain, 'prompt_ids': ids,
            'prompt_sha256': s.digest(ids), 'source': 'SYNTHETIC_TEST_ONLY'}


def inputs():
    cal = [task(name, 'GSM8K', n, i+100) for i, (name, n) in enumerate(
        zip(sorted(s.CALIBRATION_IDS), (190, 161, 163, 133)))]
    pool = [task(f'{domain}/new-{group}-{i}', domain, n, 200+di*100+group*10+i)
            for di, domain in enumerate(('MBPP', 'GSM8K'))
            for group, n in enumerate((80, 192, 384)) for i in range(5)]
    history = {'task_ids': [], 'prompt_hashes': [], 'scope': 'synthetic only',
               'exposure_manifest_sha256': 'e'*64}
    return cal, pool, history


def output(first=42):
    ids = [first, 128009]
    return {'ids': ids, 'eog': [False, True], 'cap': 128, 'length': 2,
            'terminal_id': 128009, 'stop_reason': 'EOG'}


def records(plan):
    rows = []
    plan_hash = s.digest(plan)
    for slot in plan['requests']:
        if slot['stage'] != 'validation':
            continue
        rows.append({'slot': slot['id'], 'status': 'COMPLETED', 'pid': 1, 'worker_id': slot['worker_id'],
          'request_sha256': s.digest(s.native_request(slot, 'f'*64, plan_hash)),
          'output': output(), 'runtime_verified': True, 'observation_mode': 'counts',
          'added_sync': False, 'heavy_capture': False, 'natural_prefill': True,
          'restore_used': False, 'request_ms': 100. if slot['arm'] == 'R' else 80.,
          'actual_prefill_schedule': slot['prefill_schedule'],
          'counts': {'target_continuation_width_hist': {'1': 1},
                     'target_continuation_micrographs': 1, 'target_continuation_rows': 1}})
    return rows


class StudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cal, cls.pool, cls.history = inputs()
        cls.plan = s.plan_study(cls.cal, cls.pool, cls.history)
        cls.records = records(cls.plan)
    def analyze(self, rows):
        return s.analyze_validation(self.plan, rows, Path('.'), 'f'*64, verify_files=False)
    def test_total_budget(self):
        self.assertEqual(len(self.plan['requests']), 1576)
        self.assertEqual(len(self.plan['operators']), 48)
        self.assertEqual(len({x['worker_id'] for x in self.plan['requests']})+48, 904)
    def test_warmups_explicit(self):
        self.assertEqual(sum(x['role'] == 'warmup' for x in self.plan['requests']), 720)
    def test_domain_length_coverage(self):
        for domain in ('MBPP','GSM8K'):
            for stratum in ('SHORT','MEDIUM','LONG'):
                self.assertEqual(sum(t['domain']==domain and t['length_stratum']==stratum for t in self.plan['holdout']),4)
    def test_pool_order_invariance(self):
        self.assertEqual(s.select_holdout(self.pool, self.history, self.cal),
                         s.select_holdout(self.pool[::-1], self.history, self.cal))
    def test_history_exclusion_by_id(self):
        h = copy.deepcopy(self.history); h['task_ids'] = [self.plan['holdout'][0]['id']]
        held = s.select_holdout(self.pool, h, self.cal)
        self.assertNotIn(h['task_ids'][0], [t['id'] for t in held])
    def test_history_exclusion_by_prompt(self):
        h = copy.deepcopy(self.history); h['prompt_hashes'] = [self.plan['holdout'][0]['prompt_sha256']]
        held = s.select_holdout(self.pool, h, self.cal)
        self.assertNotIn(h['prompt_hashes'][0], [t['prompt_sha256'] for t in held])
    def test_insufficient_bin_blocks(self):
        with self.assertRaises(ValueError):
            s.select_holdout(self.pool[:3], self.history, self.cal)
    def test_duplicate_pool_rejected(self):
        with self.assertRaises(ValueError):
            s.select_holdout(self.pool+[self.pool[0]], self.history, self.cal)
    def test_prompt_tamper(self):
        x = copy.deepcopy(self.pool[0]); x['prompt_ids'][0] += 1
        with self.assertRaises(ValueError): s.check_task(x)
    def test_no_output_leak(self):
        x = copy.deepcopy(self.pool[0]); x['reference_output'] = [42]
        with self.assertRaises(ValueError): s.check_task(x)
    def test_exact_chunks(self):
        self.assertEqual(s.chunks(133, 128), [128, 5])
        self.assertEqual(s.chunks(384, 128), [128, 128, 128])
        self.assertEqual(s.chunks(384, 512), [384])
    def test_invalid_q_domain(self):
        with self.assertRaises(ValueError): s.chunks(513, 128)
    def test_all_producers_layout_off(self):
        for arm in s.ARMS[1:]: self.assertEqual(s.recipe(arm)['prefill_layout'], 'MQ')
    def test_q1_controls_not_claimed_qb(self):
        self.assertFalse(s.recipe('M128')['draft_enabled'])
        self.assertEqual(s.recipe('M128')['consumer'], 'MQ')
    def test_matrix_immutable(self):
        p = copy.deepcopy(self.plan); p['requests'][0]['recipe']['restore'] = True
        with self.assertRaises(ValueError): s.validate_plan(p)
    def test_wrong_cell_request_rejected(self):
        slot = next(x for x in self.plan['requests'] if x['arm'] == 'C128_QB')
        req = s.native_request(slot, 'f'*64, 'a'*64); req['recipe'] = s.recipe('C512_QB')
        with self.assertRaises(ValueError): s.admit_request(req, slot, 'f'*64, 'a'*64)
    def test_roundtrip_admission(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'r.json'; slot = self.plan['requests'][0]
            req = s.native_request(slot, 'f'*64, 'a'*64); s.write_new(p, req)
            self.assertEqual(s.admit_request(s.load(p), slot, 'f'*64, 'a'*64), s.digest(req))
    def test_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'r.json'; p.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError): s.load(p)
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'r.json'; s.write_new(p, {})
            with self.assertRaises(FileExistsError): s.write_new(p, {})
    def test_scientific_mismatch_is_not_execution_error(self):
        self.assertEqual(s.classify({'status': 'COMPLETED', 'output': output(43)}, {'output': output()}), 'SCIENTIFIC_NONQUALIFIED')
    def test_malformed_eog_rejected(self):
        x = output(); x['eog'] = [True, True]
        with self.assertRaises(ValueError): s.endpoint(x)
    def test_measured_width_not_configured_ub(self):
        r = copy.deepcopy(self.records[0]); self.assertFalse(s.workload(r)['physical_multiquery_observed'])
        r['counts'] = {'target_continuation_width_hist': {'4': 2}, 'target_continuation_micrographs': 2, 'target_continuation_rows': 8}
        self.assertEqual(s.workload(r)['physical_rows_per_micrograph'], 4)
    def test_bad_physical_accounting(self):
        r = copy.deepcopy(self.records[0]); r['counts']['target_continuation_rows'] = 4
        with self.assertRaises(ValueError): s.workload(r)
    def test_complete_synthetic_estimate(self):
        out = self.analyze(self.records)
        self.assertEqual(out['status'], 'COMPLETE_FINITE_PANEL')
        self.assertTrue(all(x['qualified'] and abs(x['speed_ratio']-1.25)<1e-12 for x in out['comparisons']))
    def test_missing_withholds_all_aggregate(self):
        out = self.analyze(self.records[:-1])
        self.assertTrue(all(x['speed_ratio'] is None for x in out['comparisons']))
    def test_mismatch_withholds_not_fast_subset(self):
        rr = copy.deepcopy(self.records)
        slot = next(x for x in self.plan['requests'] if x['stage'] == 'validation' and x['role'] == 'measure' and x['arm'] == 'C128_QB')
        next(x for x in rr if x['slot'] == slot['id'])['output'] = output(43)
        arm = next(x for x in self.analyze(rr)['comparisons'] if x['arm'] == 'C128_QB')
        self.assertFalse(arm['qualified']); self.assertIsNone(arm['speed_ratio'])
    def test_reference_instability_withholds(self):
        rr = copy.deepcopy(self.records)
        slot = next(x for x in self.plan['requests'] if x['stage'] == 'validation' and x['role'] == 'measure' and x['arm'] == 'R')
        next(x for x in rr if x['slot'] == slot['id'])['output'] = output(43)
        self.assertFalse(self.analyze(rr)['reference_stable'])
    def test_warmups_not_time(self):
        rr = copy.deepcopy(self.records); warm = {x['id'] for x in self.plan['requests'] if x['role'] == 'warmup'}
        for r in rr:
            if r['slot'] in warm: r['request_ms'] = 1e9
        self.assertAlmostEqual(self.analyze(rr)['comparisons'][0]['speed_ratio'], 1.25)
    def test_duplicate_records_blocked(self):
        with self.assertRaises(ValueError): self.analyze(self.records+[self.records[0]])
    def test_latency_nan_rejected(self):
        rr = copy.deepcopy(self.records); rr[0]['request_ms'] = float('nan')
        with self.assertRaises(ValueError): self.analyze(rr)
    def test_raw_file_pin_and_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); p = root/'raw'; p.write_bytes(b'raw')
            pin = {'path': 'raw', 'bytes': 3, 'sha256': hashlib.sha256(b'raw').hexdigest()}
            s.verify_pins(root, [pin]); p.write_bytes(b'bad')
            with self.assertRaises(ValueError): s.verify_pins(root, [pin])
            pin['path'] = '../escape'
            with self.assertRaises(ValueError): s.verify_pins(root, [pin])
    def test_serial_is_not_PQ(self):
        self.assertEqual(s.recipe('C128_SERIAL')['continuation_ub'], 1)
        self.assertEqual(s.recipe('C128_PQ')['continuation_ub'], 4)
    def test_nonhex_fingerprint_rejected(self):
        with self.assertRaises(ValueError): s.native_request(self.plan['requests'][0], 'z'*64, 'a'*64)
    def test_direct_comparisons(self):
        out = self.analyze(self.records)
        self.assertEqual(len(out['direct_comparisons']), 8)
        self.assertTrue(all(abs(x['speed_ratio']-1)<1e-12 for x in out['direct_comparisons']))
    def test_changed_output_cap_rejected(self):
        p = copy.deepcopy(self.plan); p['requests'][0]['cap'] = 64
        with self.assertRaises(ValueError): s.validate_plan(p)
    def test_linked_raw_files_and_forged_export(self):
        slot = next(x for x in self.plan['requests'] if x['stage'] == 'validation')
        rec = copy.deepcopy(next(x for x in self.records if x['slot'] == slot['id']))
        req = s.native_request(slot, 'f'*64, s.digest(self.plan))
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            bodies = {'request.json': req, 'result.json': rec,
                      'timer.json': {'slot':rec['slot'],'pid':rec['pid'],'start_ns':1,
                        'end_ns':int(rec['request_ms']*1e6)+1,
                        'scope':'INCLUSIVE_NATURAL_REQUEST_WITH_SELECTION_AND_STATE_TRANSITION'},
                      'identity.json': {'slot':rec['slot'],'pid':rec['pid'],
                        'runtime_fingerprint':'f'*64,'status':'PASS','load_forward_calls':0,'pre_request_reset_passed':True,
                        'added_sync':False,'heavy_capture':False}}
            for name,body in bodies.items(): s.write_new(root/name,body)
            rec.update(raw_request_path='request.json',raw_result_path='result.json',
                       raw_timer_path='timer.json',raw_identity_path='identity.json',raw_pins=[])
            for name in bodies:
                data=(root/name).read_bytes()
                rec['raw_pins'].append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            s.verify_record_evidence(root,rec,req)
            rec['output']=output(43)
            with self.assertRaises(ValueError): s.verify_record_evidence(root,rec,req)
    def test_no_hidden_native_executor(self):
        self.assertFalse(self.plan['native_execution_started_here'])
        self.assertIn('HOST_NATIVE_PORT', self.plan['runtime_status'])



class ArchitectureTests(unittest.TestCase):
    def event(self):
        return {'slot':'test','event_id':0,'source_kind':'SYNTHETIC_TEST','role':'TARGET',
                'phase':'VERIFY','occupied_rows':4,'attention_query_columns':1,
                'attention_query_batches':4,'layout':'QB','key_extent':128,'kv_heads':8,
                'query_heads':32,'key_dim':128,'value_dim':128,'kv_dtype':'F16','q_dtype':'F32'}
    def test_QB_single_column_is_not_global_serialization(self):
        from architecture import summarize
        x=summarize([self.event()]);self.assertEqual(x['groups'][0]['rows_per_event'],4)
    def test_no_invented_memory_or_occupancy(self):
        from architecture import summarize
        x=summarize([self.event()])['events'][0]
        self.assertEqual(x['logical_KV_value_bytes'],524288)
        self.assertIsNone(x['actual_DRAM_bytes']);self.assertIsNone(x['actual_XMX_occupancy'])
    def test_wrong_axis_rejected(self):
        from architecture import summarize
        x=self.event();x['attention_query_batches']=1
        with self.assertRaises(ValueError): summarize([x])
    def test_duplicate_event_rejected(self):
        from architecture import summarize
        with self.assertRaises(ValueError): summarize([self.event(),self.event()])

if __name__ == '__main__':
    unittest.main(verbosity=2)
