import copy
import hashlib
import importlib.util
from pathlib import Path
import struct
import unittest

SPEC = importlib.util.spec_from_file_location("request_oracle", Path(__file__).parents[1] / "request/state_machine.py")
oracle = importlib.util.module_from_spec(SPEC)
import sys
sys.modules[SPEC.name] = oracle
SPEC.loader.exec_module(oracle)


class RequestStateTests(unittest.TestCase):
    def test_bonus_actual_seed_fifth_rejection_actual_correction_continues(self):
        r = oracle.main_fixture()
        a, b, c = r["cycles"]
        self.assertEqual((a["k"], a["accepted"], a["commit_kind"]), (3, 3, "bonus"))
        self.assertEqual(a["pending_after"], b["seed"])
        self.assertEqual((b["accepted"], b["rejected"], b["decision_consumer"]["row"]), (4, True, 4))
        self.assertNotEqual(b["proposals"][4], b["decisions"][4])
        self.assertEqual(b["pending_after"], c["seed"])
        self.assertEqual(c["base"], b["keep"])
        self.assertEqual(r["stop_reason"], "CAP")
        self.assertFalse(r["terminal_emitted_materialized"])

    def test_complete_fixture_compare(self):
        r = oracle.main_fixture()
        check = oracle.compare_requests(r, copy.deepcopy(r))
        self.assertEqual(check["full_vector_pairs"], 17)
        self.assertFalse(check["native_KV_or_geometry_qualified"])

    def test_same_argmax_and_KV_do_not_replace_fifth_vector(self):
        r, candidate = oracle.main_fixture(), oracle.main_fixture()
        v = candidate["cycles"][1]["vectors"][4]
        raw = bytearray.fromhex(v["bytes_hex"])
        raw[:4] = struct.pack("<f", 0.03125)
        v["bytes_hex"], v["sha256"] = raw.hex(), hashlib.sha256(raw).hexdigest()
        self.assertEqual(oracle.read_vector(v, 16)[1], 11)
        with self.assertRaisesRegex(oracle.ContractError, "full requested vector mismatch"):
            oracle.compare_requests(r, candidate)

    def test_missing_untrimmed_state_rejected(self):
        r, c = oracle.main_fixture(), oracle.main_fixture()
        del c["cycles"][1]["state_untrimmed"]
        with self.assertRaisesRegex(oracle.ContractError, "fields missing"):
            oracle.compare_requests(r, c)

    def test_missing_requested_tail_rejected(self):
        r, c = oracle.main_fixture(), oracle.main_fixture()
        c["cycles"][1]["vectors"].pop()
        with self.assertRaisesRegex(oracle.ContractError, "missing full requested"):
            oracle.compare_requests(r, c)

    def test_owner_generation_rejects_stale_read(self):
        owner = oracle.Owner("fixture", 16)
        owner.install([oracle.vector(1)], 1)
        owner.install([oracle.vector(2)], 1)
        with self.assertRaisesRegex(oracle.ContractError, "stale output owner"):
            owner.consume(0, 1)

    def test_failed_install_poisons_owner(self):
        owner = oracle.Owner("fixture", 16)
        bad = oracle.vector(1)
        bad["sha256"] = "0" * 64
        with self.assertRaisesRegex(oracle.ContractError, "SHA256"):
            owner.install([bad], 1)
        with self.assertRaisesRegex(oracle.ContractError, "invalid owner reuse"):
            owner.install([oracle.vector(1)], 1)

    def test_eog_bonus_not_materialized(self):
        p = {"k": 3, "proposals": [1, 2, 3], "vectors": [oracle.vector(x) for x in [1, 2, 3, 15]]}
        r = oracle.constructed_request([2], oracle.vector(4), [p], cap=20, eog_ids=(15,))
        self.assertEqual(r["stop_reason"], "EOG")
        self.assertEqual(r["cycles"][0]["commit_kind"], "bonus")
        self.assertFalse(r["terminal_emitted_materialized"])

    def test_eog_accepted_token_materialized_without_extra_decode(self):
        p = {"k": 3, "proposals": [1, 15, 3], "vectors": [oracle.vector(x) for x in [1, 15, 3, 2]]}
        r = oracle.constructed_request([2], oracle.vector(4), [p], cap=20, eog_ids=(15,))
        self.assertEqual(r["cycles"][0]["accepted"], 2)
        self.assertTrue(r["terminal_emitted_materialized"])
        self.assertEqual(r["final_target"], [2, 4, 1, 15])

    def test_eog_correction_not_materialized(self):
        p = {"k": 3, "proposals": [1, 2, 3], "vectors": [oracle.vector(x) for x in [15, 2, 3, 4]]}
        r = oracle.constructed_request([2], oracle.vector(4), [p], cap=20, eog_ids=(15,))
        self.assertEqual(r["cycles"][0]["accepted"], 0)
        self.assertEqual(r["stop_reason"], "EOG")
        self.assertFalse(r["terminal_emitted_materialized"])


if __name__ == "__main__":
    unittest.main()
