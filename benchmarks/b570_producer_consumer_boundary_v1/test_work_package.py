"""Synthetic CPU contract tests. No model outputs or native results are created."""
import copy
import importlib.util
import pathlib
import json
import datetime
import struct
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("work_package", HERE / "work_package.py")
wp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wp)

def synthetic_bound_plan():
    # Deliberately synthetic unit data. Never written as a scientific plan/result.
    panel = {"status": "FROZEN_BEFORE_FORWARD", "new_model_outputs_used_for_selection": False,
             "candidate_inventory_sha256": "1" * 64, "exposure_audit_sha256": "2" * 64,
             "selection_rule": "SYNTHETIC_UNIT_TEST_ONLY", "inputs": []}
    for i in range(8):
        panel["inputs"].append({"id": "SYNTHETIC_CPU_TEST/" + str(i),
            "prompt_ids": [100 + i] * (100 + i if i < 4 else 260 + i), "cap": 128,
            "stratum": "short" if i < 4 else "long", "domain": "SYNTHETIC",
            "source": {"revision": "SYNTHETIC", "task_id": str(i)},
            "template_sha256": "3" * 64, "selection_hash": "4" * 64,
            "exposure_status": "UNSEEN_FOR_CURRENT_IMPLEMENTATION"})
    runtime = wp.read(HERE / "RUNTIME_TEMPLATE.json")
    runtime.update(status="BUILT_NOT_YET_B0_QUALIFIED", native_extension_implemented=True,
                   executable_sha256="5" * 64, source_manifest_sha256="6" * 64,
                   numeric_modules_manifest_sha256="7" * 64, vocabulary_size=151936, eog_ids=[151645])
    return wp.build_plan(panel, runtime)

def synthetic_b0_records(plan, root):
    """Synthetic isolated gate fixture; never a PR148/native execution record."""
    data = bytearray(4 * plan["runtime"]["vocabulary_size"])
    struct.pack_into("<f", data, 151645 * 4, 1.0)
    (root / "kv.bin").write_bytes(b"SYNTHETIC_BOUNDARY_NOT_NATIVE_STATE")
    (root / "initial.f32").write_bytes(data)
    def meta(path):
        return {"path": path, "bytes": (root / path).stat().st_size, "sha256": wp.sha_file(root / path)}
    start = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    rows = []
    for i, slot in enumerate(s for s in plan["slots"] if s["stage"] == "B0"):
        row = {"slot_id": slot["slot_id"], "status": "COMPLETE_QUALIFIED", "native_started": True,
            "pid": 1, "started_utc": (start + datetime.timedelta(seconds=2*i)).isoformat(),
            "finished_utc": (start + datetime.timedelta(seconds=2*i+1)).isoformat(),
            "runtime_sha256": wp.digest(plan["runtime"]), "prompt_ids_sha256": slot["prompt_ids_sha256"],
            "endpoint": {"ids": [151645], "eog": [True], "length": 1, "terminal_id": 151645, "stop_reason": "EOG"},
            "cycles": [], "vectors": {"target_initial": meta("initial.f32")} if slot["observer"] == "heavy" else {},
            "performance_eligible": False, "checks": {"module_identity": True, "device_placement": True,
                "actual_geometry": True, "restore_roundtrip": True}, "extra_forward_calls_on_restore": 0}
        if slot["observer"] == "heavy" and slot["route"] in {"natural", "natural_spec"}:
            row["boundary"] = {"kv": meta("kv.bin"), "initial_logits": meta("initial.f32"),
                               "kv_min": 0, "kv_max": slot["prompt_tokens"] - 1, "sequence_id": 0}
        if slot["route"] == "resumed":
            donor = next(r for r in rows if r["slot_id"] == slot["donor_slot_id"])
            row["imported_boundary_sha256"] = wp.digest(wp.boundary_signature(donor))
            directory = root / ("restored-" + str(i)); directory.mkdir()
            (directory / "kv.bin").write_bytes((root / "kv.bin").read_bytes())
            (directory / "initial.f32").write_bytes(data)
            row["restored_boundary"] = {"kv": meta(directory.name + "/kv.bin"),
                "initial_logits": meta(directory.name + "/initial.f32"),
                "kv_min": 0, "kv_max": slot["prompt_tokens"] - 1, "sequence_id": 0}
        rows.append(row)
    # Structural audit receipt isolates the restore gate; not claimed PR148 evidence.
    audit = {"plan_sha256": wp.digest(plan), "payloads_rehashed": True, "checks": [
        {"slot_id": slot["slot_id"], "passed": True} for slot in plan["slots"] if slot["historical_reference"]]}
    return rows, audit

class ContractTests(unittest.TestCase):
    def test_exact_152_and_ordered_dependencies(self):
        plan = wp.build_plan()
        slots = wp.validate_plan(plan)
        self.assertEqual(len(slots), 152)
        self.assertEqual(sum(s["stage"] == "B0" for s in slots), 32)
        seen = set()
        for s in slots:
            self.assertTrue(set(s["depends_on"]) <= seen)
            self.assertIsNone(s["result"])
            seen.add(s["slot_id"])
        self.assertFalse(plan["execution_authorized"])

    def test_historical_controls_keep_cap64(self):
        controls = wp.read(HERE / "CONTROL_INPUTS.json")["inputs"]
        self.assertEqual([(i["id"], len(i["prompt_ids"]), i["cap"]) for i in controls],
                         [("HumanEval/38", 181, 64), ("HumanEval/115", 349, 64)])

    def test_tail3_is_explicit_2_plus_1(self):
        self.assertEqual(wp.p4_schedule(7), [4, 2, 1])
        self.assertEqual(wp.p4_schedule(8), [4, 4])
        self.assertEqual(wp.p4_schedule(9), [4, 4, 1])

    def test_deleted_slot_and_changed_donor_rejected(self):
        plan = wp.build_plan()
        bad = copy.deepcopy(plan)
        bad["slots"].pop()
        with self.assertRaises(wp.ContractError):
            wp.validate_plan(bad)
        bad = copy.deepcopy(plan)
        bad["slots"][3]["donor_slot_id"] = None
        with self.assertRaises(wp.ContractError):
            wp.validate_plan(bad)

    def test_empty_records_remain_missing_not_pass(self):
        report = wp.audit_records(wp.build_plan(), [])
        self.assertEqual(report["status"], "PENDING")
        self.assertEqual(len(report["missing_slots"]), 152)
        self.assertFalse(report["b0_qualified"])
        self.assertEqual(report["recorded_slots"], 0)

    def test_unbound_plan_cannot_accept_native_pass(self):
        plan = wp.build_plan()
        row = {"slot_id": plan["slots"][0]["slot_id"], "status": "COMPLETE_QUALIFIED",
               "native_started": True}
        report = wp.audit_records(plan, [row])
        self.assertEqual(report["status"], "INVALID")
        self.assertTrue(any("unbound" in e["error"] for e in report["errors"]))

    def test_not_run_is_explicit_and_duplicate_rejected(self):
        plan = wp.build_plan()
        row = {"slot_id": plan["slots"][0]["slot_id"], "status": "NOT_RUN_DEPENDENCY",
               "native_started": False, "reason": "Synthetic unit-test disposition"}
        report = wp.audit_records(plan, [row])
        self.assertEqual(len(report["missing_slots"]), 151)
        self.assertEqual(report["counts"]["NOT_RUN_DEPENDENCY"], 1)
        duplicate = wp.audit_records(plan, [row, row])
        self.assertEqual(duplicate["status"], "INVALID")

    def test_same_bytes_different_paths_compare_equal(self):
        a = {"endpoint": {"ids": [1]}, "cycles": [], "vectors": {
            "target_initial": {"sha256": "a" * 64, "bytes": 4, "path": "a/file.f32"}}}
        b = copy.deepcopy(a)
        b["vectors"]["target_initial"]["path"] = "b/file.f32"
        self.assertTrue(all(wp.compare_records(a, b, True).values()))
        b["vectors"]["target_initial"]["sha256"] = "b" * 64
        self.assertFalse(wp.compare_records(a, b, True)["vectors"])

    def test_payload_hash_and_escape_checks(self):
        with tempfile.TemporaryDirectory() as name:
            root = pathlib.Path(name)
            f = root / "real.bin"
            f.write_bytes(b"synthetic unit-test bytes")
            meta = {"path": "real.bin", "bytes": f.stat().st_size, "sha256": wp.sha_file(f)}
            wp.safe_payload(root, meta)
            with self.assertRaises(wp.ContractError):
                wp.safe_payload(root, dict(meta, path="../real.bin"))
            with self.assertRaises(wp.ContractError):
                wp.safe_payload(root, dict(meta, sha256="0" * 64))

    def test_cycle_conservation_rejects_wrong_rollback(self):
        slot = {"k": 1, "prompt_tokens": 20, "cap": 3}
        row = {"endpoint": {"ids": [10, 11, 12], "eog": [False, False, False]}, "cycles": [
            {"cycle": 0, "base": 20, "seed_id": 10, "proposal": 11,
             "decisions": [11, 12], "accepted": 1, "q_caller": 2,
             "keep": 22, "committed_ids": [11, 12], "target_kv_max": 21, "draft_kv_max": 21}]}
        wp.cycles(row, slot)
        row["cycles"][0]["keep"] = 21
        with self.assertRaises(wp.ContractError):
            wp.cycles(row, slot)

    def test_unimplemented_native_runtime_cannot_freeze(self):
        runtime = wp.read(HERE / "RUNTIME_TEMPLATE.json")
        with self.assertRaises(wp.ContractError):
            wp.check_runtime(runtime)

    def test_bound_freeze_requires_real_binding_fields(self):
        plan = synthetic_bound_plan()
        self.assertEqual(len(wp.validate_plan(plan)), 152)
        bad = copy.deepcopy(plan)
        bad["panel"]["inputs"][0]["prompt_ids"] = None
        with self.assertRaises(wp.ContractError):
            wp.validate_plan(bad)

    def test_historical_raw_audit_rejects_mutation(self):
        plan = synthetic_bound_plan()
        slot = next(s for s in plan["slots"] if s["stage"] == "B0" and s["input_index"] == 0
                    and s["producer"] == "P1" and s["consumer"] == "C1"
                    and s["route"] == "natural" and s["observer"] == "heavy")
        endpoint = {"ids": [151645], "eog": [True], "length": 1,
                    "terminal_id": 151645, "stop_reason": "EOG"}
        with tempfile.TemporaryDirectory() as name:
            root = pathlib.Path(name)
            payload = root / "actual"; payload.mkdir()
            legacy = root / "references" / "qual-0"; legacy.mkdir(parents=True)
            old_vectors = legacy / "qual-0" / "target"; old_vectors.mkdir(parents=True)
            data = b"\x00" * (4 * 151936)
            actual_file = payload / "initial.f32"; actual_file.write_bytes(data)
            (old_vectors / "initial.f32").write_bytes(data)
            old = dict(endpoint, input_id="HumanEval/38", arm="R", cycles=[],
                       target_calls=181, draft_calls=0, actual_signatures=[])
            (legacy / "result.json").write_text(json.dumps({"status": "QUALIFICATION_PASS", "requests": [old, {}, {}]}))
            row = {"slot_id": slot["slot_id"], "status": "COMPLETE_QUALIFIED",
                   "endpoint": endpoint, "cycles": [], "target_calls": 181, "draft_calls": 0,
                   "actual_signatures": [], "geometry_files": {}, "vectors": {
                       "target_initial": {"path": "initial.f32", "bytes": len(data), "sha256": wp.sha_file(actual_file)}}}
            report = wp.audit_controls(plan, [row], root / "references", payload)
            result = next(x for x in report["checks"] if x["slot_id"] == slot["slot_id"])
            self.assertTrue(result["passed"])
            self.assertEqual(result["vectors_checked"], 1)
            actual_file.write_bytes(b"\x01" + data[1:])
            bad = wp.audit_controls(plan, [row], root / "references", payload)
            self.assertEqual(bad["status"], "FAIL")
            self.assertTrue(any("hash mismatch" in x.get("error", "") for x in bad["checks"]))

    def test_self_reported_historical_pass_is_not_a_gate(self):
        plan = synthetic_bound_plan()
        slot = plan["slots"][0]
        row = {"slot_id": slot["slot_id"], "status": "COMPLETE_QUALIFIED", "native_started": True,
               "pid": 1, "started_utc": "2026-01-01T00:00:00Z", "finished_utc": "2026-01-01T00:00:01Z",
               "runtime_sha256": wp.digest(plan["runtime"]), "prompt_ids_sha256": slot["prompt_ids_sha256"],
               "endpoint": {"ids": [151645], "eog": [True], "length": 1, "terminal_id": 151645, "stop_reason": "EOG"},
               "cycles": [], "vectors": {}, "performance_eligible": False,
               "checks": {"module_identity": True, "device_placement": True, "actual_geometry": True,
                          "historical_reference": True}}
        report = wp.audit_records(plan, [row])
        self.assertEqual(report["status"], "INVALID")
        self.assertTrue(any("independent historical control audit" in e["error"] for e in report["errors"]))

    def test_restore_gate_requires_actual_readback_and_payload_rehash(self):
        plan = synthetic_bound_plan()
        with tempfile.TemporaryDirectory() as name:
            root = pathlib.Path(name)
            rows, audit = synthetic_b0_records(plan, root)
            valid = wp.audit_records(plan, rows, root, audit)
            self.assertTrue(valid["b0_qualified"], valid["errors"])
            self.assertEqual(len(valid["restored_boundaries_rehashed"]), 16)
            no_readback = copy.deepcopy(rows)
            for row in no_readback:
                row.pop("restored_boundary", None)
            missing = wp.audit_records(plan, no_readback, root, audit)
            self.assertFalse(missing["b0_qualified"])
            self.assertTrue(any("restored_boundary state missing" in e["error"] for e in missing["errors"]))
            metadata_only = wp.audit_records(plan, rows, None, audit)
            self.assertFalse(metadata_only["b0_qualified"])
            self.assertTrue(any("requires actual payload rehash" in e["error"] for e in metadata_only["errors"]))
            for field in ("kv", "initial_logits"):
                with self.subTest(donor_payload_without_path=field):
                    bad_rows = copy.deepcopy(rows)
                    donor = next(r for r in bad_rows if "boundary" in r)
                    donor["boundary"][field].pop("path")
                    bad = wp.audit_records(plan, bad_rows, root, audit)
                    self.assertFalse(bad["b0_qualified"])
                    self.assertTrue(any("payload path escape" in e["error"] for e in bad["errors"]))

    def test_restored_bytes_and_consumed_initial_vector_must_match(self):
        plan = synthetic_bound_plan()
        with tempfile.TemporaryDirectory() as name:
            root = pathlib.Path(name)
            rows, audit = synthetic_b0_records(plan, root)
            changed = copy.deepcopy(rows)
            resumed_off = next(r for r in changed if "/resumed/off" in r["slot_id"])
            meta = resumed_off["restored_boundary"]["kv"]
            path = root / meta["path"]
            old = path.read_bytes()
            path.write_bytes(b"X" + old[1:])
            meta["sha256"] = wp.sha_file(path)
            bad = wp.audit_records(plan, changed, root, audit)
            self.assertFalse(bad["b0_qualified"])
            self.assertTrue(any("actual restored boundary bytes/positions differ" in e["error"] for e in bad["errors"]))
            path.write_bytes(old)
            changed = copy.deepcopy(rows)
            resumed_heavy = next(r for r in changed if "/resumed/heavy" in r["slot_id"])
            other = root / "actually-consumed-different.f32"
            data = bytearray((root / "initial.f32").read_bytes())
            struct.pack_into("<f", data, 0, 0.5)
            other.write_bytes(data)
            resumed_heavy["vectors"]["target_initial"] = {
                "path": other.name, "bytes": len(data), "sha256": wp.sha_file(other)}
            bad = wp.audit_records(plan, changed, root, audit)
            self.assertFalse(bad["b0_qualified"])
            self.assertTrue(any("actually consumed target_initial" in e["error"] for e in bad["errors"]))

    def test_nonterminal_accept_cannot_omit_bonus(self):
        slot = {"k": 1, "prompt_tokens": 20, "cap": 64}
        row = {"endpoint": {"ids": [10] * 64, "eog": [False] * 64}, "cycles": []}
        base = 20
        for i in range(63):
            row["cycles"].append({"cycle": i, "base": base, "seed_id": 10,
                "proposal": 10, "decisions": [10, 11], "accepted": 1, "q_caller": 2,
                "keep": base + 2, "target_kv_max": base + 1, "draft_kv_max": base + 1,
                "committed_ids": [10]})
            base += 2
        with self.assertRaises(wp.ContractError):
            wp.cycles(row, slot)

    def test_terminal_accept_may_legally_omit_bonus(self):
        for cap, flags in ((2, [False, False]), (64, [False, True])):
            with self.subTest(cap=cap):
                slot = {"k": 1, "prompt_tokens": 20, "cap": cap}
                row = {"endpoint": {"ids": [10, 11], "eog": flags}, "cycles": [
                    {"cycle": 0, "base": 20, "seed_id": 10, "proposal": 11,
                     "decisions": [11, 12], "accepted": 1, "q_caller": 2, "keep": 22,
                     "target_kv_max": 21, "draft_kv_max": 21, "committed_ids": [11],
                     "pending_after": None, "done": True}]}
                wp.cycles(row, slot)

    def test_post_trim_state_and_terminal_cycle_guard(self):
        slot = {"k": 1, "prompt_tokens": 20, "cap": 3}
        row = {"endpoint": {"ids": [10, 11, 12], "eog": [False] * 3}, "cycles": [
            {"cycle": 0, "base": 20, "seed_id": 10, "proposal": 11,
             "decisions": [11, 12], "accepted": 1, "q_caller": 2, "keep": 22,
             "target_kv_max": 21, "draft_kv_max": 21, "committed_ids": [11, 12],
             "pending_after": None, "done": True}]}
        wp.cycles(row, slot)
        for field in ("target_kv_max", "draft_kv_max"):
            bad = copy.deepcopy(row); bad["cycles"][0][field] = 20
            with self.assertRaises(wp.ContractError):
                wp.cycles(bad, slot)
        extra = copy.deepcopy(row); extra["cycles"].append(copy.deepcopy(extra["cycles"][0]))
        with self.assertRaises(wp.ContractError):
            wp.cycles(extra, slot)

if __name__ == "__main__":
    unittest.main()

