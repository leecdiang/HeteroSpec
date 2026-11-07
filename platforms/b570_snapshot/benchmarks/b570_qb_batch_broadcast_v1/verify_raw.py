"""CPU-only verification of already saved raw tensors; never loads a GPU backend."""
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import json, hashlib, pathlib
import numpy as np
root = pathlib.Path(__file__).parent
raw = root / "results"
report = {"status": "STARTED", "gpu_execution": False, "reference": "NumPy FP64 einsum on saved F16 operands; no GGML graph", "coordinates": []}
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def check(actual, expected):
    assert actual.shape == expected.shape
    err = np.abs(actual.astype(np.float64) - expected)
    assert np.isfinite(actual).all() and np.isfinite(expected).all()
    assert (err <= 0.0002 + 0.002 * np.abs(expected)).all()
    return {"max_abs_error": float(err.max()), "elements": int(err.size), "passed": True}
for n in [1023, 1024, 1025]:
    for q in [1, 2, 4]:
        pair = {"key": n, "q": q, "modes": {}}
        for mode in ["QB", "QH_C"]:
            p = raw / f"{n}-q{q}-{mode}"
            Q = np.fromfile(p/"q.f32", dtype="<f4").astype(np.float64).reshape(8,q,128)
            K = np.fromfile(p/"k.f16", dtype="<f2").astype(np.float64).reshape(8,n,128)
            V = np.fromfile(p/"v.f16", dtype="<f2").astype(np.float64).reshape(8,128,n)
            mask = np.fromfile(p/"mask.f32", dtype="<f4").astype(np.float64).reshape(32,n)[:q]
            expected_mask = np.zeros((q,n))
            for j in range(q): expected_mask[j,n-q+j+1:] = -np.inf
            assert np.array_equal(mask, expected_mask)
            scores = np.einsum("hjd,hnd->jhn", Q, K)
            logits = scores * float(np.float32(1.0)/np.sqrt(np.float32(128.0))) + mask[:,None,:]
            probs = np.exp(logits - logits.max(axis=-1,keepdims=True))
            probs /= probs.sum(axis=-1,keepdims=True)
            final = np.einsum("hdn,jhn->jhd", V, probs)
            def stage(name, width):
                x = np.fromfile(p/name, dtype="<f4")
                if mode == "QH_C" and q > 1:
                    return x.reshape(8,q,width).transpose(1,0,2)
                return x.reshape(q,8,width)
            checks = {
                "qk": check(stage("gpu_qk.f32",n), scores),
                "softmax": check(stage("gpu_softmax.f32",n), probs),
                "av": check(stage("gpu_av.f32",128), final),
                "final": check(np.fromfile(p/"gpu_final.f32",dtype="<f4").reshape(q,8,128),final),
                "post_timing_final": check(np.fromfile(p/"gpu_final_after_timing.f32",dtype="<f4").reshape(q,8,128),final),
            }
            for name, original in [("q","q.f32"),("k","k.f16"),("v","v.f16"),("mask","mask.f32")]:
                for when in ["before","after-numerical","after-timing"]:
                    assert digest(p/original) == digest(p/f"{name}.{when}.bin")
            checks["all_input_readbacks_byte_identical"] = True
            pair["modes"][mode] = checks
        assert digest(raw/f"{n}-q{q}-QB"/"gpu_final.f32") == digest(raw/f"{n}-q{q}-QH_C"/"gpu_final.f32")
        pair["pair_final_byte_identical"] = True
        report["coordinates"].append(pair)
report["status"] = "CPU_RAW_RECHECK_ALL_PASS"
(root/"CPU_RAW_RECHECK.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"status": report["status"], "coordinates": len(report["coordinates"]), "mode_slots": 18, "stage_checks": 90, "input_readbacks":216}))
