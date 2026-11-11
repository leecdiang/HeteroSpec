"""Host-only admission and raw-vector guards; no native program or model is invoked."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from protocol import ARMS, BUDGET, calculated_budget, cases, plan
from run import validate_publication
from verify import blob, validate_trim, validate_work, vector


class HostGuards(unittest.TestCase):
    def test_complete_native_work_is_bounded(self):
        self.assertEqual(calculated_budget(), BUDGET)
        self.assertEqual(sum(sum(a['schedule'])+1 for a in ARMS), 56)
        self.assertEqual(sum(len(a['schedule'])+1 for a in ARMS), 17)
        self.assertEqual([len(c['history']) for c in cases()], [248, 252])
        self.assertEqual(plan()['performance_admitted'], False)

    def test_publication_rejects_content_change_and_unverified_commit(self):
        sources = {'example.cpp': {'bytes': 5, 'sha256': 'a'*64}}
        publication = {'commit': 'b'*40, 'remote_source_verified': True, 'sources': sources}
        validate_publication(publication, sources)
        changed = copy.deepcopy(sources);changed['example.cpp']['sha256'] = 'c'*64
        with self.assertRaises(ValueError):
            validate_publication(publication, changed)
        publication['remote_source_verified'] = False
        with self.assertRaises(ValueError):
            validate_publication(publication, sources)
        publication['remote_source_verified'] = True;publication['commit'] = 'main'
        with self.assertRaises(ValueError):
            validate_publication(publication, sources)

    def test_full_vector_guard_rejects_truncation_and_nonfinite(self):
        full = struct.pack('<128f', *[0.25]*128)
        vector(full, 1)
        with self.assertRaises(ValueError):
            vector(full[:-4], 1)
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.assertRaises(ValueError):
                vector(struct.pack('<f', value)+full[4:], 1)

    def test_raw_blob_guard_rejects_tampering_and_path_substitution(self):
        with tempfile.TemporaryDirectory() as directory:
            native = Path(directory);(native/'blobs').mkdir()
            data = b'host-only-test';sha = hashlib.sha256(data).hexdigest()
            path = native/'blobs'/(sha+'.bin');path.write_bytes(data)
            desc = {'sha256': sha, 'bytes': len(data), 'path': 'blobs/'+sha+'.bin'}
            self.assertEqual(blob(native, desc), data)
            bad = dict(desc, path='../outside.bin')
            with self.assertRaises(ValueError):
                blob(native, bad)
            path.write_bytes(data[:-1]+b'X')
            with self.assertRaises(ValueError):
                blob(native, desc)

    def test_missing_stage_and_physical_counter_tampering_are_rejected(self):
        # An explicitly fabricated host-only accounting fixture, never a native receipt.
        case, arm = cases()[0], ARMS[0]
        counts = {};stages = {};prefix = case['name']+'/'+arm['name']+'/'
        for name, calls, rows, histogram in [('prefill', 8, 248, {'32': 7, '24': 1}),
                                             ('operation', 2, 8, {'4': 2}), ('continuation', 1, 1, {'1': 1})]:
            prefill = name == 'prefill'
            counts[name] = {'total_native_calls': calls, 'total_target_rows': rows,
                            'prefill_calls': calls if prefill else 0, 'prefill_rows': rows if prefill else 0,
                            'outer_calls': 0 if prefill else calls, 'target_rows': 0 if prefill else rows,
                            'physical_calls': calls, 'physical_widths': histogram}
            stages[prefix+name] = {'reserved_calls': calls, 'reserved_rows': rows,
                                   'attempted_calls': calls, 'attempted_rows': rows}
        record = {'status': 'REFERENCE_CAPTURED', 'counts': counts}
        work = {'by_stage': stages, 'reserved_native_calls': 11, 'reserved_target_rows': 257,
                'attempted_native_calls': 11, 'attempted_target_rows': 257}
        validate_work([record], [(case, arm)], work)
        missing = copy.deepcopy(work);del missing['by_stage'][prefix+'prefill']
        missing.update(reserved_native_calls=3, attempted_native_calls=3, reserved_target_rows=9, attempted_target_rows=9)
        with self.assertRaises(ValueError):
            validate_work([record], [(case, arm)], missing)
        corrupt = copy.deepcopy(record);corrupt['counts']['operation']['physical_widths'] = {'4': 1}
        with self.assertRaises(ValueError):
            validate_work([corrupt], [(case, arm)], work)

    def test_trim_rejected_before_qualification_or_missing_from_complete_frontier(self):
        wide = ARMS[4]
        record = {'trim_calls': 0, 'checks': {'shared_operation_vectors': False}, 'status': 'FAIL'}
        validate_trim(record, wide)
        with self.assertRaises(ValueError):
            validate_trim(dict(record, trim_calls=1), wide)
        with self.assertRaises(ValueError):
            validate_trim({'trim_calls': 0, 'checks': {'shared_operation_vectors': True}, 'status': 'PASS'}, wide)
        with self.assertRaises(ValueError):
            validate_trim({'trim_calls': 1, 'checks': {'shared_operation_vectors': True}, 'status': 'PASS'}, ARMS[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
