"""Synthetic wire-format tests; these are NOT model/GPU experimental evidence."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock
import experiment as e


def state(n=3, transposed=False, value=1.0):
    b = bytearray(struct.pack('<IiII', 0xaf143cd8, 0, 1, n))
    for i in range(n): b.extend(struct.pack('<iIi', i, 1, 0))
    b.extend(struct.pack('<II', int(transposed), 32))
    for role in ('K', 'V'):
        for layer in range(32):
            b.extend(struct.pack('<i', 1))
            b.extend(struct.pack('<II', 2, 1024) if role == 'V' and transposed else struct.pack('<Q', 2048))
            b.extend(struct.pack('<e', value) * (n * 1024))
    return bytes(b)


class KVTests(unittest.TestCase):
    def test_wire_layouts(self):
        for transpose in (False, True):
            b = state(transposed=transpose)
            d = e.layout(b, 3)
            self.assertEqual(len(d['tensors']), 64)
            self.assertEqual(d['v_transposed'], transpose)
            self.assertTrue(e.finite_kv(b, d))

    def test_every_own_path_is_exact(self):
        for transpose in (False, True):
            b = state(transposed=transpose)
            for name in ('ALL', 'EMPTY', *e.SELECTORS):
                mixed, audit = e.splice(b, b, 3, name)
                self.assertEqual(mixed, b)
                self.assertEqual(audit['changed_bytes'], 0)

    def test_all_cross_is_exact_donor(self):
        for transpose in (False, True):
            a, b = state(transposed=transpose), state(transposed=transpose, value=2.0)
            self.assertEqual(e.splice(a, b, 3, 'ALL')[0], b)
            self.assertEqual(e.splice(a, b, 3, 'EMPTY')[0], a)

    def test_role_and_layer_scope(self):
        a, b = state(), state(value=2.0)
        mixed, audit = e.splice(a, b, 3, 'K_layer0')
        self.assertEqual(audit['selected_bytes'], 3 * 2048)
        for t in e.layout(a, 3)['tensors']:
            lo, hi = t['offset'], t['offset'] + t['bytes']
            self.assertEqual(mixed[lo:hi], b[lo:hi] if t['role'] == 'K' and t['layer'] == 0 else a[lo:hi])

    def test_disjoint_roles_and_layer_groups_cover_all(self):
        d = e.layout(state(), 3)
        for group in (('K_all', 'V_all'), ('KV_early', 'KV_middle', 'KV_late')):
            spans = [set(i for a, b in e.spans(d, name) for i in range(a, b)) for name in group]
            self.assertEqual(sum(map(len, spans)), len(set.union(*spans)))
            self.assertEqual(len(set.union(*spans)), 64 * 3 * 2048)

    def test_transposed_positions_are_not_row_major(self):
        n = 129
        a, b = state(n, True), state(n, True, 2.0)
        mixed, audit = e.splice(a, b, n, 'KV_tail128')
        self.assertEqual(audit['selected_bytes'], 64 * 2048)
        for t in e.layout(a, n)['tensors']:
            for feature in (0, 1, 511, 1023):
                for position in (0, 127, 128):
                    off = t['offset'] + (2 * (feature * n + position) if t['transposed'] else 2048 * position + feature * 2)
                    self.assertEqual(mixed[off:off+2], (b if position == 128 else a)[off:off+2])

    def test_empty_tail_is_structural_null(self):
        a, b = state(), state(value=2.0)
        mixed, audit = e.splice(a, b, 3, 'KV_tail128')
        self.assertEqual(mixed, a)
        self.assertEqual(audit['selected_bytes'], 0)

    def test_reject_crop_extension_and_bad_n(self):
        b = state()
        for bad in (b[:-1], b + b'\0'):
            with self.assertRaises(ValueError): e.layout(bad, 3)
        for n in (0, 2, 4, 769, True):
            with self.assertRaises(ValueError): e.layout(b, n)

    def test_reject_metadata_mutations(self):
        original = state()
        for offset in (0, 4, 8, 12, 16, 20, 24, 52, 56, 60, 64):
            b = bytearray(original); b[offset] ^= 0x02
            with self.assertRaises(ValueError): e.layout(bytes(b), 3)

    def test_reject_different_value_storage(self):
        with self.assertRaises(ValueError): e.splice(state(), state(transposed=True), 3, 'K_all')
        with self.assertRaises(ValueError): e.selection('unknown', 3)

    def test_nonfinite_values(self):
        for bad in (float('inf'), float('nan')):
            b = state(value=bad)
            self.assertFalse(e.finite_kv(b, e.layout(b, 3)))

    def test_position_partitions_cover_all(self):
        for transpose in (False, True):
            d = e.layout(state(129, transpose), 129)
            counts = [sum(b-a for a,b in e.spans(d, s)) for s in ('KV_prefix128', 'KV_tail128')]
            self.assertEqual(sum(counts), 64 * 129 * 2048)

    def test_endpoint_classification_not_success_selection(self):
        a, b, c = {'ids': [1, 2]}, {'ids': [1, 3]}, {'ids': [1, 4]}
        self.assertEqual(e.classify(a,a,b,0), 'STRUCTURAL_NULL')
        self.assertEqual(e.classify(a,a,b,7), 'VALID_ENDPOINT_NULL')
        self.assertEqual(e.classify(b,a,b,7), 'DONOR_ENDPOINT_REPRODUCED')
        self.assertEqual(e.classify(c,a,b,7), 'VALID_ALTERNATIVE_TRAJECTORY')
        self.assertEqual(e.first_difference([1,2], [1,3]), 1)
        self.assertEqual(e.first_difference([1], [1,2]), 1)
        self.assertIsNone(e.first_difference([1], [1]))

    def test_hash_and_path_rejection(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); (root/'x').write_bytes(b'abc')
            row = {'path':'x', 'bytes':3, 'sha256':e.digest(b'abc')}
            self.assertEqual(e.checked_payload(root,row), b'abc')
            for bad in (dict(row, sha256='0'*64), dict(row, bytes=2), dict(row,path='../x')):
                with self.assertRaises(ValueError): e.checked_payload(root,bad)

    def test_immutable_receipt(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)/'receipt.json'; e.write_new(p, {'a':1})
            with self.assertRaises(FileExistsError): e.write_new(p, {'a':2})
            self.assertEqual(e.read(p), {'a':1})

    def test_freeze_rejects_missing_remote_authentication(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t); e.write_new(p/'FREEZE.json', {'runtime':[], 'inputs':[]})
            with mock.patch.object(e.subprocess, 'check_output', side_effect=[(p/'FREEZE.json').read_bytes(), b'wrong']):
                with self.assertRaises(ValueError): e.verify_freeze(p,p,'a'*40,'registered.json')


if __name__ == '__main__': unittest.main(verbosity=2)
