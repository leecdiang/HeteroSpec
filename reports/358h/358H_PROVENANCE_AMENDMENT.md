# 358H Provenance Amendment

Status: **HISTORICAL SOURCE REVISION UNRECOVERABLE / RECONSTRUCTION REQUIRED**

Scope: This amendment applies only to the Core Ultra X7 358H Phase-0 qualification. It does not revise or reinterpret the completed M4, CUDA, or Vulkan measurements.

## Authoritative historical artifact

The historically authoritative cross-platform draft artifact is:

- repository: `Qwen/Qwen3-0.6B-GGUF`;
- repository revision: `23749fefcc72300e3a2ad315e1317431b06b590a`;
- file: `Qwen3-0.6B-Q8_0.gguf`;
- bytes: `639446688`;
- SHA256: `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`;
- embedded tokenizer metadata fingerprint: `59afe9d266b6304529b469e538d5dc65f4bdf152ef392f76a87168d2420c73e7`;
- embedded chat-template SHA256: `57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361`.

This artifact was consumed byte-identically by the completed M4/Metal, Windows/CUDA, and Arc B570/Vulkan studies.

## Missing historical link

The original immutable `Qwen/Qwen3-0.6B` Transformers commit used to create the canonical GGUF was not recorded by the historical experiments and cannot now be reconstructed exactly.

The following sources were checked without finding an explicit mapping:

- HeteroSpec `main`, all visible remote branches, commit search, merged pull requests, archived manifests, B570 provenance, M4/CUDA artifacts, and historical OpenVINO reports/scripts;
- the local incomplete Git object database and reflog;
- local Hugging Face and download caches;
- all source-, tokenizer-, and quantization-related GGUF metadata fields;
- the official GGUF repository card and commit history;
- the upstream `Qwen/Qwen3-0.6B` commit history around the GGUF upload.

The official GGUF repository identifies only `base_model: Qwen/Qwen3-0.6B`. Its first model upload was committed on 2025-05-05, but it does not record the upstream source commit or the llama.cpp conversion revision.

This is a pre-existing historical provenance limitation. It was not introduced by the 358H experiment.

## Reconstruction rule

Any Transformers checkpoint used to construct an OpenVINO IR for 358H is a **reconstructed runtime source**, not a recovered historical source.

Before formal data may be admitted, the reconstructed source must:

1. be pinned to an immutable commit;
2. have every consumed config, tokenizer, and weight file hashed;
3. pass architecture, configuration, tokenizer, tensor-shape, and deterministic functional equivalence qualification against the canonical GGUF;
4. receive an equivalence classification of `PROVEN` or `STRONGLY_SUPPORTED`;
5. retain this limitation in every Phase-0/Phase-1 manifest and report.

No floating branch, current `main`, filename inference, or model-family similarity may substitute for this qualification.

## Strongest reconstruction candidate

The strongest candidate available from official immutable history is:

- repository: `Qwen/Qwen3-0.6B`;
- commit: `6130ef31402718485ca4d80a6234f70d9a4cf362`;
- commit date: 2025-04-29T08:56:31Z;
- rationale: it is the latest upstream commit preceding the official GGUF repository's initial model upload on 2025-05-05; that commit changed README content, while the model/config/tokenizer objects were already present.

Contemporaneity is supporting evidence only. It does not prove that this exact commit was the historical conversion input. The candidate must independently pass the content/semantic-equivalence gate before conversion.

