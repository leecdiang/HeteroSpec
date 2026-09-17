# Core Ultra X7 358H Phase-0 Environment Qualification

Status: **AC REQUALIFICATION MOSTLY COMPLETE / FINAL TELEMETRY-OVERHEAD GATE PENDING**

Frozen: 2026-09-16 CST. This record contains qualification-only compilation and bounded functional smoke tests. No formal latency, throughput, or energy measurement was collected.

## 2026-09-18 AC replacement status

The earlier machine-side qualification remains invalid because the host power condition was not positively frozen. A replacement evidence set was created under `runs/358h/qualification_ac_20260918/` with `PowerOnline=true`, `Discharging=false`, the Windows Balanced scheme, and no formal performance run.

Completed replacement gates:

- CPU lower-level compile reports `EXECUTION_DEVICES=CPU`; bounded generation passes.
- A new NPU 8192-token profile/cache was built under AC power; bounded generation passes.
- Direct import of the new cache reports `EXECUTION_DEVICES=NPU`; bounded single-step inference passes.
- Intel Unified Telemetry 0.2.0-beta1.1 was frozen by distribution and executable SHA256 and successfully collected Package and NPU power domains.
- A frozen 100 ms official-format power configuration passed idle-load-idle, unit/scale, sampling-gap, and nonzero-NPU-activity sanity checks.
- QPC-to-Unified-Telemetry clock calibration spread is 1.907 ms, below the frozen 5 ms limit.
- The Qwen3-8B target artifact is downloaded and verified at exactly 8,709,518,112 bytes and SHA256 `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`.

Remaining gate:

- Repeat the randomized 10-OFF/10-ON observer-overhead qualification for CPU and NPU using the final no-ITT 100 ms collection configuration. The administrator launch was cancelled at the Windows UAC prompt, so this gate has not run. The 1% threshold remains unchanged.

Two earlier telemetry configurations are preserved as engineering failures: stock 1 ms power collection caused 51.2649% CPU observer overhead; the 100 ms trace with dense OpenVINO ITT collection was stopped after confirming ITT remained a material observer. Neither is formal data. The final configuration disables ITT during workload collection and uses adjacent calibration traces solely to map exact QPC boundaries into the Unified Telemetry clock.

## Scientific provenance

- The historically authoritative draft is `Qwen/Qwen3-0.6B-GGUF` revision `23749fefcc72300e3a2ad315e1317431b06b590a`, file `Qwen3-0.6B-Q8_0.gguf`, SHA256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
- The exact upstream Transformers commit used by the historical GGUF publisher was not recorded and could not be recovered. This pre-existing limitation and the recovery search are frozen in `reports/358h/358H_PROVENANCE_AMENDMENT.md`.
- The strongest immutable reconstruction is `Qwen/Qwen3-0.6B` commit `6130ef31402718485ca4d80a6234f70d9a4cf362`, the latest upstream commit preceding the official GGUF upload. It was not selected from a floating branch.
- Source equivalence is classified **STRONGLY_SUPPORTED**, not proven: architecture/config fields match; all 310 mappable tensor shapes match; tokenizer token IDs and all 151,387 merges match; six frozen tokenizer probes match; and deterministic eight-token generation matches completely for five of six prompts and at the first token for six of six. Q8_0 and INT4 numerical identity is neither expected nor claimed.
- The upstream chat template differed from the canonical GGUF template. The OpenVINO representation therefore carries the canonical GGUF template byte-for-byte (SHA256 `57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361`).

Evidence: `runs/358h/qualification/reconstructed_source_equivalence.json`, `runs/358h/qualification/source_gguf_functional_equivalence.json`, and `runs/358h/qualification/canonical_chat_template_overlay.json`.

## Host and runtime

| Field | Frozen value |
|---|---|
| Host | Xiaomi Book Pro 14 |
| CPU | Intel Core Ultra X7 358H |
| GPU | Intel Arc B390 iGPU; driver `32.0.101.8991` dated 2026-08-24 |
| NPU | Intel AI Boost; driver `1005540`; compiler `524290` |
| OS | Windows 11 Home China, build 26200 |
| BIOS | `XMAPT4B0P0A0A`, 2026-06-17 |
| OpenVINO | `2026.3.1-22476-759c5a6ab8c-releases/2026/3` |
| OpenVINO GenAI | `2026.3.1.0` |
| OpenVINO Tokenizers | `2026.3.1.0` |
| Transformers | `5.0.0` |
| Optimum Intel | `1.27.0.dev0` from official release pin `a8c4734741e766ef95d7f1a7d1e29a1d4ba2ab8f` |

Full package freezes are `runs/358h/qualification/pip-freeze.txt` and `runs/358h/qualification/conversion-pip-freeze.txt`; machine inventory is `runs/358h/qualification/windows-inventory.json`.

## Frozen OpenVINO representation

One common IR is used for CPU, GPU, and NPU. It was exported from the immutable reconstructed source with `text-generation-with-past`, data-free symmetric INT4, group size 128, ratio 1.0. The exact command and versions are in `runs/358h/qualification/openvino_export_attempt.json`.

| Artifact | SHA256 |
|---|---|
| `openvino_model.xml` | `fc8ad94dbecfc0c45cf3db4f0624344d2bea2cdd6997e0b45ca52d4f7baa1103` |
| `openvino_model.bin` | `2e129cffb1a7239007a3df27e0f3f7bb12f65a40e5c9b1e24a250d952da47837` |
| NPU phase-0 cache (128 ceiling) | `7e979a72bc0601681a36f23bd127a176b3c38a997df957dab40410506f7e1747` |
| NPU phase-0 cache (8192 ceiling) | `5f83743e77a8054cf4b2d7dc2d18401b71716bb7bcb6e4d08f2151ae0a3a2a65` |

All source, tokenizer, IR, and cache file hashes are enumerated in `runs/358h/qualification/phase0_frozen_manifest.json`.

## NPU shape failure and neutral fix

The direct-GGUF NPU path failed at Broadcast shape inference (`expected 1 or 1024; got 0`). Compiling the exported dynamic raw IR directly on NPU also failed at `to_shape` on a dynamic dimension. Both failures are preserved in `canonical_gguf_smoke_npu.json` and `environment_with_openvino_ir.json`.

The fix is the documented OpenVINO GenAI NPU path: the same symmetric INT4 IR is transformed/compiled with explicit NPU static/dynamic shape preparation. The bounded smoke used `MAX_PROMPT_LEN=128`, `MIN_RESPONSE_LEN=4`, `PREFILL_HINT=STATIC`; a separate no-timing ceiling test used `MAX_PROMPT_LEN=8192`, `PREFILL_HINT=DYNAMIC`. No model, tokenizer, or weights were changed for NPU.

## Strict device binding and functional smoke

`AUTO`, `MULTI`, and `HETERO` were not used.

| Requested | Actual `EXECUTION_DEVICES` | Bounded smoke | Notes |
|---|---|---|---|
| `CPU` | `CPU` | PASS | Explicit low-level compile and GenAI generation |
| `GPU` | `GPU.0` | PASS | Explicit low-level compile and GenAI generation |
| `NPU` | `NPU` | PASS | Imported compiled NPU payload reports NPU; bounded low-level infer and GenAI generation pass |
| `NPU`, 8192-token ceiling | `NPU` | PASS | Same IR; dynamic prefill preparation; four output tokens |

The CPU and NPU four-token output IDs match. The GPU differs after the first token; this is retained as a hardware/precision numerical observation and is not hidden or used as performance evidence. All outputs are structurally valid. Evidence is in `openvino_ir_smoke_*.json` and `npu_cache_binding*.json`.

## Recomputed gate

All 14 checks in `runs/358h/qualification/phase0_frozen_manifest.json` are true:

- immutable canonical artifact and transparent provenance amendment;
- immutable, hashed reconstructed source with STRONGLY_SUPPORTED equivalence;
- reproducible, version-frozen OpenVINO conversion;
- hashed IR and compiled NPU caches;
- explicit CPU/GPU/NPU execution-device evidence;
- successful NPU functional smoke through the 8192-token planned ceiling;
- no formal performance data collected.

The machine-side PASS below was superseded by `reports/358h/358H_POWER_STATE_DEVIATION.md` after the operator confirmed that the host was not connected to external power. It is retained only as a description of the completed engineering checks and is not an active qualification.

**358H PHASE-0 QUALIFICATION: INVALID 鈥?AC REQUALIFICATION REQUIRED**

Formal Phase 1 remains prohibited until the completed preregistration is committed.

