"""CPU-only adversarial checks. No model, CUDA API, or legacy source imported."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from admission import (AdmissionError, NativeStateSpec, Owner, admit_descriptor, compare_operator_pair, digest,
                       qualified_fallback, read_artifact, read_native_state, validate_bundle,
                       validate_clean_binding, validate_full_vector, validate_geometry,
                       validate_graph_reuse, validate_identity)


def identity():
    return {"model_sha256": "1" * 64, "vocab_sha256": "2" * 64, "core_sha256": "3" * 64,
            "frontend_sha256": "4" * 64, "exe_sha256": "5" * 64,
            "compiler": {"version": "fixture", "flags": ["-O3"]},
            "loaded_modules": {"ggml-cuda.dll": "6" * 64}, "producer": {"kind": "fixture"},
            "kv": {"K": "F16", "V": "F16", "layout": "dense"},
            "graph_policy": {"layout": "whole", "prefix": "active"},
            "device_uuid": "GPU-FIXTURE", "compute_capability": "12.0", "clean_guard_sha256": "7" * 64}


def tensor(dtype, shape):
    unit, block = (34, 32) if dtype == "Q8_0" else (4, 1)
    row = shape[0] // block * unit
    strides = [unit, row, row * shape[1], row * shape[1] * shape[2]]
    return {"dtype": dtype, "ne": shape, "nb": strides, "contiguous": True,
            "buffer_backend": "CUDA", "buffer_device": "GPU-FIXTURE", "buffer_usage": "COMPUTE",
            "view": False, "padding_clear_conflict": False, "allocation_bytes": strides[3] * shape[3], "data_offset": 0}


def descriptor(arm="B", q=8):
    if arm == "A" or (arm == "B" and q < 8):
        dispatch = [{"route": "MMVQ_Q8_0", "ncols": min(4, q-start), "channels": 1,
                     "samples": 1, "logical_start": start} for start in range(0, q, 4)]
    else:
        dispatch = [{"route": "MMVQ_Q8_0_PAIR4" if arm == "C" else "MMVQ_Q8_0", "ncols": 4,
                     "channels": q // 4, "samples": 1, "logical_start": 0}]
        if q % 4:
            dispatch.append({"route": "MMVQ_Q8_0", "ncols": q % 4, "channels": 1,
                             "samples": 1, "logical_start": q // 4 * 4})
    return {"q": q, "g": q // 4, "device_uuid": "GPU-FIXTURE", "backend": "CUDA", "warp_size": 32,
            "compute_capability": "12.0", "weight": tensor("Q8_0", [32, 16, 1, 1]),
            "activation": tensor("F32", [32, q, 1, 1]), "output": tensor("F32", [16, q, 1, 1]),
            "op": "MUL_MAT", "precision": "DEFAULT", "ids": False, "fusion": False,
            "output_mask": [True] * q, "reserve": q, "dispatch": dispatch,
            "quantizer": {"type": "Q8_1", "wide_once": True, "arithmetic_columns": 4}}


def geometry():
    return {"capacity": 256, "physical_head": 2, "physical_used": 2, "active_positions": 2,
            "padding": 256, "prefix_vector": [256, 256], "layout_policy": "whole", "sequence_ids": [0]}


def state(transposed=False):
    raw = bytearray(struct.pack("<IiII", 0xAF143CD8, 0, 1, 2))
    for pos in range(2):
        raw += struct.pack("<iIi", pos, 1, 0)
    raw += struct.pack("<II", int(transposed), 1)
    raw += struct.pack("<iQ4H", 1, 4, 1, 2, 3, 4)
    if transposed:
        raw += struct.pack("<iII4H", 1, 2, 2, 5, 7, 6, 8)
    else:
        raw += struct.pack("<iQ4H", 1, 4, 5, 6, 7, 8)
    return bytes(raw)


class TestAdmission(unittest.TestCase):
    def rejected(self, code, function, *args):
        with self.assertRaises(AdmissionError) as error:
            function(*args)
        self.assertEqual(error.exception.code, code)

    def test_complete_vector_and_tie_order(self):
        result = validate_full_vector(struct.pack("<4f", 1, 3, 3, -2), 4)
        self.assertEqual(result["greedy"], 1)
        self.rejected("FULL_VECTOR", validate_full_vector, struct.pack("<3f", 1, 2, 3), 4)
        self.rejected("FULL_VECTOR", validate_full_vector, struct.pack("<5f", 1, 2, 3, 4, 5), 4)
        self.rejected("NONFINITE", validate_full_vector, struct.pack("<4f", 1, float("nan"), 3, 4), 4)

    def test_operator_pair_compares_quantized_padding_and_every_output(self):
        quantized = bytes(range(36))
        output = struct.pack("<8f", *range(8))
        self.assertEqual(compare_operator_pair(quantized, quantized, output, output, 36, 8)["relation"], "BITWISE_EQUAL")
        # An unchanged argmax cannot excuse a changed nonmaximal output.
        changed = struct.pack("<8f", -1, *range(1, 8))
        self.rejected("OUTPUT_MISMATCH", compare_operator_pair, quantized, quantized, output, changed, 36, 8)
        self.rejected("ACTIVATION_MISMATCH", compare_operator_pair, quantized, quantized[:-1] + b"\0", output, output, 36, 8)
        self.rejected("ACTIVATION_SIZE", compare_operator_pair, quantized, quantized[:-1], output, output, 36, 8)
        self.rejected("FULL_VECTOR", compare_operator_pair, quantized, quantized, output, output[:-4], 36, 8)

    def test_artifact_hash_length_missing_and_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data").write_bytes(b"data")
            record = {"path": "data", "bytes": 4, "sha256": digest(b"data")}
            self.assertEqual(read_artifact(root, record), b"data")
            self.rejected("HASH", read_artifact, root, dict(record, sha256="0" * 64))
            self.rejected("TRUNCATED_OR_EXTENDED", read_artifact, root, dict(record, bytes=5))
            self.rejected("MISSING_FIELD", read_artifact, root, {"path": "data", "bytes": 4})
            self.rejected("PATH", read_artifact, root, dict(record, path="../data"))

    def test_complete_native_state_and_orientation(self):
        spec = NativeStateSpec(1, 2, 2, 256)
        a = read_native_state(state(), 2, spec)
        b = read_native_state(state(True), 2, spec)
        self.assertEqual(a["active_sha256"], b["active_sha256"])
        self.assertNotEqual(a["raw_sha256"], b["raw_sha256"])
        self.rejected("UNTRIMMED_STATE", read_native_state, state(), 1, spec)
        self.rejected("TRUNCATED_STATE", read_native_state, state()[:-1], 2, spec)
        self.rejected("TRAILING_STATE", read_native_state, state() + b"\0", 2, spec)
        invalid = bytearray(state()); struct.pack_into("<i", invalid, 16, 3)
        self.rejected("STATE_MAPPING", read_native_state, bytes(invalid), 2, spec)

    def test_model_and_loaded_dll_identity_are_separate(self):
        frozen = identity()
        validate_identity(copy.deepcopy(frozen), frozen)
        bad = copy.deepcopy(frozen); bad["loaded_modules"]["ggml-cuda.dll"] = "a" * 64
        self.rejected("IDENTITY_MISMATCH", validate_identity, bad, frozen)
        bad = copy.deepcopy(frozen); del bad["vocab_sha256"]
        self.rejected("MISSING_FIELD", validate_identity, bad, frozen)

    def test_geometry_required_and_exact(self):
        validate_geometry(geometry(), geometry())
        bad = geometry(); bad["prefix_vector"] = [256]
        self.rejected("GEOMETRY_MISMATCH", validate_geometry, bad, geometry())
        bad = geometry(); del bad["physical_head"]
        self.rejected("MISSING_FIELD", validate_geometry, bad, geometry())

    def test_graph_semantic_key_change_rebuilds(self):
        previous = {"prefix_vector": [256] * 8, "active_policy": "active", "layout_policy": "whole",
                    "head_placement_key": ["F32", "GPU"], "n_outputs": 8,
                    "ubatch_topology": [8, 1], "recipe_identity": "fixture"}
        self.assertEqual(validate_graph_reuse(previous, copy.deepcopy(previous), True), "REUSED")
        for field, value in (("prefix_vector", [512] * 8), ("active_policy", "other"),
                             ("layout_policy", "local"), ("head_placement_key", ["F16", "CPU"]),
                             ("n_outputs", 1), ("ubatch_topology", [4, 2]), ("recipe_identity", "other")):
            current = dict(previous, **{field: value})
            self.rejected("GRAPH_REUSE", validate_graph_reuse, previous, current, True)
            self.assertEqual(validate_graph_reuse(previous, current, False), "REBUILT")

    def test_arm_specific_dispatch_and_supported_widths(self):
        for arm in ("A", "B"):
            for q in (4, 5, 7, 8, 9, 11, 12, 31, 32):
                self.assertFalse(admit_descriptor(arm, descriptor(arm, q), "GPU-FIXTURE")["native_qualified"])
        self.assertEqual(admit_descriptor("C", descriptor("C"), "GPU-FIXTURE")["q"], 8)
        self.rejected("C_DOMAIN", admit_descriptor, "C", descriptor("C", 12), "GPU-FIXTURE")
        self.rejected("DISPATCH", admit_descriptor, "A", descriptor("B"), "GPU-FIXTURE")
        self.rejected("DISPATCH", admit_descriptor, "C", descriptor("B"), "GPU-FIXTURE")
        self.rejected("PLACEMENT", admit_descriptor, "B", descriptor("B"), "GPU-OTHER")

    def test_negative_metadata_cases(self):
        cases = [("INTEGER", lambda d: d.update(q=0)),
                 ("INTEGER", lambda d: d.update(q=33)),
                 ("STRIDE", lambda d: d["activation"].update(contiguous=False)),
                 ("STRIDE", lambda d: d["weight"].update(nb=[34, 35, 560, 560])),
                 ("PADDING", lambda d: d["weight"].update(view=True, padding_clear_conflict=True)),
                 ("PLACEMENT", lambda d: d["output"].update(buffer_device="GPU-OTHER")),
                 ("PLACEMENT", lambda d: d["activation"].update(buffer_backend="CPU")),
                 ("BACKEND", lambda d: d.update(warp_size=64)),
                 ("ARITHMETIC_RECIPE", lambda d: d.update(precision="F32")),
                 ("ARITHMETIC_RECIPE", lambda d: d.update(ids=True)),
                 ("ARITHMETIC_RECIPE", lambda d: d.update(fusion=True)),
                 ("DTYPE", lambda d: d["activation"].update(dtype="F16")),
                 ("INTEGER_SPAN", lambda d: d["weight"].update(data_offset=2**31-100, allocation_bytes=2**32)),
                 ("BUFFER_SPAN", lambda d: d["weight"].update(allocation_bytes=1)),
                 ("OUTPUT_MASK", lambda d: d.update(output_mask=[True, False] * 4)),
                 ("OUTPUT_RESERVE", lambda d: d.update(reserve=4))]
        for code, mutate in cases:
            with self.subTest(code=code):
                d = descriptor(); mutate(d)
                self.rejected(code, admit_descriptor, "B", d, "GPU-FIXTURE")

    def test_no_implicit_fallback(self):
        error = AdmissionError("STRIDE", "fixture")
        receipt = {"id": "loop4-fixture", "status": "NOT_RUN", "identity": identity(),
                   "descriptor": descriptor("A"), "evidence_sha256": "8" * 64}
        self.rejected("FALLBACK_UNQUALIFIED", qualified_fallback, error, "loop4-fixture", receipt,
                      identity(), descriptor("A"), {})
        receipt["status"] = "NATIVE_QUALIFIED"
        self.rejected("FALLBACK_UNQUALIFIED", qualified_fallback, error, "loop4-fixture", receipt,
                      identity(), descriptor("A"), {})
        allowlist = {receipt["id"]: digest(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode())}
        self.assertEqual(qualified_fallback(error, "loop4-fixture", receipt, identity(), descriptor("A"), allowlist)["decision"],
                         "QUALIFIED_FALLBACK")

    def test_failure_invalidates_persistent_owner(self):
        def fail():
            raise RuntimeError("injected failure")
        before = Owner("preflight")
        with self.assertRaises(RuntimeError): before.call(fail, native_work=False)
        self.assertTrue(before.valid)
        for failure_stage in ("target", "trim", "draft", "sampling", "reset-postcheck"):
            owner = Owner(failure_stage)
            owner.call(lambda: None, native_work=True)
            with self.assertRaises(RuntimeError): owner.call(fail, native_work=False)
            self.assertFalse(owner.valid)
            self.rejected("OWNER_INVALID", owner.call, lambda: None)

    def test_clean_guard_cannot_be_capture_observer_default(self):
        frozen = identity()
        receipt = {"mode": "clean", "identity": frozen, "descriptor": descriptor(),
                   "always_on_guard": {"executed": True, "predicate_sha256": "7" * 64, "verdict": "PASS"},
                   "capture_observation": False}
        validate_clean_binding(receipt, frozen, descriptor())
        for update in ({"executed": False}, {"predicate_sha256": "a" * 64}):
            bad = copy.deepcopy(receipt); bad["always_on_guard"].update(update)
            self.rejected("CLEAN_GUARD", validate_clean_binding, bad, frozen, descriptor())

    def test_bundle_refuses_missing_vectors_owner_or_state(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def artifact(name, raw):
                (root / name).write_bytes(raw)
                return {"path": name, "bytes": len(raw), "sha256": digest(raw)}
            vector = artifact("logits.f32", struct.pack("<4f", 1, 2, 3, 4))
            native = artifact("sequence.bin", state())
            receipt = {"schema": "heterospec.rtx-round1.evidence.v1", "identity": identity(), "vocab_size": 4,
                       "requested_rows": [0], "vectors": [{"row": 0, "owner": "OWNED_COPY", "artifact": vector}],
                       "states": {owner: {"expected_positions": 2, "artifact": native, "geometry_stage": "commit",
                                          "complete_native_sequence": True,
                                          "capture_point": {"target_untrimmed": "POST_VERIFY_PRE_TRIM",
                                                            "draft_untrimmed": "POST_DRAFT_PRE_TRIM",
                                                            "target": "POST_COMMIT_POST_TRIM",
                                                            "draft": "POST_COMMIT_POST_TRIM"}[owner]}
                                  for owner in ("target_untrimmed", "draft_untrimmed", "target", "draft")},
                       "geometries": {"commit": geometry()}}
            args = (identity(), NativeStateSpec(1, 2, 2, 256), {"commit": geometry()}, [0], 4)
            self.assertEqual(validate_bundle(root, receipt, *args)["status"], "OFFLINE_EVIDENCE_VALID")
            bad = copy.deepcopy(receipt); bad["vectors"] = []
            self.rejected("FULL_VECTOR", validate_bundle, root, bad, *args)
            bad = copy.deepcopy(receipt); bad["vectors"][0]["owner"] = "BORROWED_POINTER"
            self.rejected("OUTPUT_OWNER", validate_bundle, root, bad, *args)
            bad = copy.deepcopy(receipt); del bad["states"]["draft"]
            self.rejected("MISSING_FIELD", validate_bundle, root, bad, *args)
            bad = copy.deepcopy(receipt); del bad["states"]["target_untrimmed"]
            self.rejected("MISSING_FIELD", validate_bundle, root, bad, *args)
            bad = copy.deepcopy(receipt); bad["states"]["target_untrimmed"]["complete_native_sequence"] = False
            self.rejected("INCOMPLETE_STATE", validate_bundle, root, bad, *args)
            bad = copy.deepcopy(receipt); bad["requested_rows"] = [0, 1]
            self.rejected("FULL_VECTOR", validate_bundle, root, bad, *args)
            bad = copy.deepcopy(receipt); bad["vocab_size"] = 1
            bad["vectors"][0]["artifact"] = artifact("one.f32", struct.pack("<f", 3.0))
            self.rejected("FULL_VECTOR", validate_bundle, root, bad, *args)

    def test_self_reported_output_subset_cannot_relax_frozen_request(self):
        with tempfile.TemporaryDirectory() as folder:
            # The request independently requires rows 0..7 and a full vocab.
            # The record lies consistently about having requested only row 0.
            receipt = {"schema": "heterospec.rtx-round1.evidence.v1", "identity": identity(), "vocab_size": 151936,
                       "requested_rows": [0], "vectors": [], "states": {}, "geometries": {}}
            self.rejected("FULL_VECTOR", validate_bundle, Path(folder), receipt, identity(),
                          NativeStateSpec(1, 2, 2, 256), {}, list(range(8)), 151936)

    def test_frozen_22_case_matrix_has_no_native_pass(self):
        path = Path(__file__).resolve().parents[1] / "qualification" / "CASES.json"
        if not path.exists():
            self.skipTest("matrix generated separately before freeze")
        matrix = json.loads(path.read_bytes())
        self.assertEqual(len(matrix["cases"]), 22)
        self.assertEqual({x["id"] for x in matrix["cases"]},
                         {f"P{i:02}" for i in range(1, 12)} | {f"N{i:02}" for i in range(1, 12)})
        for case in matrix["cases"]:
            self.assertEqual(set(case["arms"]), {"A", "B", "C"})
            for arm in case["arms"].values():
                self.assertEqual(arm["native_result"], "NOT_RUN")
                self.assertTrue(arm["expected_decision"])


if __name__ == "__main__":
    unittest.main()
