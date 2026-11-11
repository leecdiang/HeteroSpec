# 358H Canonical Draft Model Resolution

Status: **CANONICAL GGUF RESOLVED / RECONSTRUCTED SOURCE QUALIFIED**

Scope: Phase 0 only. No formal benchmark, latency, throughput, or energy measurement was performed.

Repository examined: `leecdiang/HeteroSpec` `main` at `330530e98e189ff91a8bb944b6d31f77ff746974` (2,196-file recursive tree, not truncated).

## Resolution

The completed M4/Metal, Windows/CUDA, and Arc B570/Vulkan cross-platform experiments used one byte-identical draft artifact:

| Field | Canonical value |
|---|---|
| Hugging Face repository | `Qwen/Qwen3-0.6B-GGUF` |
| Repository revision | `23749fefcc72300e3a2ad315e1317431b06b590a` |
| Filename | `Qwen3-0.6B-Q8_0.gguf` |
| Size | 639,446,688 bytes |
| SHA256 | `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031` |
| Runtime format / precision | GGUF / Q8_0 |
| Declared upstream base model | `Qwen/Qwen3-0.6B` |

This is not a conclusion based on the 358H example path. It is supported by the following repository evidence:

- `reports/b570/B570_ENVIRONMENT_QUALIFICATION.md:153-158` records the exact draft filename, byte size, SHA256, official Qwen GGUF source, and revision.
- `artifacts/m4_humaneval_code_conditioned/manifest.json:39-41` records the same filename, byte size, and SHA256 for M4.
- `artifacts/windows_humaneval_replication/windows-humaneval-replication-30q.json:11` records the same draft SHA256 for CUDA.
- `benchmarks/b570_backend_control/preregistration_v2.json:46-48` freezes the same draft SHA256 for Vulkan.
- `reports/m4/M4_CONFIRMATORY_VALIDATION.md:9-11`, `reports/m4/M4_HUMANEVAL_CODE_CONDITIONED.md:10-12`, and `reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.md:7` identify the Qwen3-0.6B Q8_0 draft used by the completed studies.

The canonical file was downloaded at the exact revision and independently re-hashed on the 358H machine. The result matches the historical SHA256. Its local manifest is `runs/358h/qualification/canonical_draft_manifest.json`.

## Answers to the resolution questions

### 1. Exact draft model ID

For the completed cross-platform study, the exact consumed artifact is `Qwen/Qwen3-0.6B-GGUF`, file `Qwen3-0.6B-Q8_0.gguf`. The GGUF declares its base model as `Qwen/Qwen3-0.6B`.

The repository also contains an earlier OpenVINO-only draft characterization using `OpenVINO/Qwen3-0.6B-int4-ov` (`scripts/download_qwen_draft.py:9-12`). That asymmetric INT4 representation is not the byte-identical Q8_0 artifact used by the completed M4/CUDA/Vulkan comparison.

### 2. Exact revision / commit

- Canonical GGUF repository revision: `23749fefcc72300e3a2ad315e1317431b06b590a`.
- Exact upstream `Qwen/Qwen3-0.6B` Transformers revision used to create that GGUF: **not recorded** in HeteroSpec, the GGUF metadata, or the pinned GGUF model card.

The latter is a material conversion-provenance gap. A present-day or time-inferred base-model commit must not be substituted silently.

### 3. Tokenizer revision

The historical runtime tokenizer is embedded in the pinned GGUF, so its tokenizer semantics are frozen with the artifact revision and hash. It contains 151,936 tokens and 151,387 merges; the canonical JSON fingerprint of all embedded tokenizer fields is:

`59afe9d266b6304529b469e538d5dc65f4bdf152ef392f76a87168d2420c73e7`

The embedded chat-template SHA256 is:

`57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361`

An independent upstream tokenizer commit is **not recorded**, so it cannot be asserted to equal the current `Qwen/Qwen3-0.6B` tokenizer revision. B570 explicitly used the frozen GGUF tokenizer through `llama-tokenize` (`benchmarks/b570_backend_control/preregistration_v2.json:23`).

### 4. Original weight format

The exact historical artifact consumed by M4/CUDA/Vulkan is GGUF Q8_0. Its declared upstream base is a Transformers Qwen3 model, but the exact source snapshot and per-file hashes of the pre-GGUF weights were not committed. Therefore the raw source snapshot cannot presently be reconstructed from HeteroSpec alone.

### 5. Precision

- Completed M4/CUDA/Vulkan cross-platform draft: Q8_0.
- Earlier CPU/iGPU OpenVINO characterization: asymmetric INT4, ratio 0.8, group size 128 (`scripts/phase1_draft_qualification.py:195-200`).
- Earlier bounded NPU qualification: symmetric INT4, group size 128, ratio 1.0, symmetric INT8 backup (`reports/NPU_QWEN_QUALIFICATION.md:17-28`).

The INT4 artifacts are runtime representations with different numerical behavior; they must not be described as the same byte-level model as the canonical Q8_0 file.

### 6. Existing SHA256 / manifest

Yes for the canonical GGUF: the SHA256 above appears in M4, CUDA, and B570 records and was independently reproduced on 358H.

No complete committed manifest was found for either historical OpenVINO IR:

- `analysis/all_models.csv:2` points to `env/model manifest/export metadata`, but the recursive `main` tree contains no corresponding `env` model manifest.
- The NPU report references local export logs and environment files, but those files and the IR XML/BIN hashes are absent from `main`.

### 7. Same model across M4 / CUDA / Vulkan

Yes. All three completed studies used the same filename, size, Q8_0 precision, and SHA256. This is byte identity, not merely a shared model family.

### 8. 358H semantic requirement

Yes. `docs/358H_RUNBOOK.md:75-87` requires the same frozen draft model and the same model semantics across CPU/iGPU/NPU. A different runtime representation is allowed only when its conversion recipe and hashes are frozen and the difference is documented as representation—not model choice.

### 9. Reusable OpenVINO conversion recipe

Only a partial recipe exists:

- the committed downloader fetches a preconverted asymmetric INT4 artifact;
- the NPU report records symmetric INT4, group 128, ratio 1.0, symmetric INT8 backup and `text-generation-with-past`;
- the actual successful export command/log, exact source revision, tokenizer revision, converter package freeze, and output IR hashes are not committed.

This is not sufficient for a provenance-complete reproduction.

### 10. One IR or NPU-specific representation

Repository evidence shows that the asymmetric CPU/iGPU IR is not NPU-legal, while a symmetric INT4 artifact can compile on NPU. The earlier symmetric artifact was also exercised on CPU and GPU, so the preferred design is one frozen symmetric IR used on all three devices if it passes all three compilation and semantic-equality gates.

If the 358H NPU ultimately requires a distinct static-shape IR, it must be generated from the exact same frozen source snapshot and tokenizer with the conversion delta explicitly recorded and hashed. A different model is forbidden. The prior bounded `static max prompt 128` result does not qualify the planned longer contexts.

## 358H bounded smoke observations

The exact canonical GGUF was passed directly to OpenVINO GenAI 2026.3.1 without formal timing:

| Requested device | Bounded generation | Output equality | Independent `EXECUTION_DEVICES` proof |
|---|---|---|---|
| CPU | PASS | CPU/GPU output hashes match | Not exposed by the GGUF `LLMPipeline` Python API |
| GPU | PASS | CPU/GPU output hashes match | Not exposed by the GGUF `LLMPipeline` Python API |
| NPU | FAIL | Not available | NPU shape inference failed at a Broadcast target shape (`expected 1 or 1024; got 0`) |

These are qualification-only observations. No elapsed time was recorded as a result.

The direct-GGUF path does not satisfy the Phase-0 gate because NPU fails and actual compiled `EXECUTION_DEVICES` cannot be independently queried through this API surface.

## Resolution amendment (2026-09-16)

The exhaustive recovery pass did not find the exact historical upstream Transformers revision. The limitation is now explicitly frozen in `reports/358h/358H_PROVENANCE_AMENDMENT.md`; no missing revision was invented.

The immutable contemporaneous upstream candidate `Qwen/Qwen3-0.6B@6130ef31402718485ca4d80a6234f70d9a4cf362` was independently audited against the canonical GGUF. Architecture, every mapped tensor shape, tokenizer IDs and merges, frozen tokenization probes, and a bounded deterministic generation diagnostic support a `STRONGLY_SUPPORTED` classification. The canonical GGUF chat template is overlaid byte-for-byte because the upstream template differs.

A common symmetric-INT4 OpenVINO IR (group 128, ratio 1.0) was exported from that immutable source, fully hashed, and qualified on CPU, GPU, and NPU. NPU uses documented GenAI shape preparation rather than a different model. See `runs/358h/qualification/phase0_frozen_manifest.json` and `reports/358h/358H_ENVIRONMENT_QUALIFICATION.md`.
