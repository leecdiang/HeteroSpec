# Publication scope and later source availability

Publication base: PR #183, commit `b07a532ec78eb2ae48bc884d9332b21232e8c68d`, after the native bridge publisher released its single-writer window. This change adds only `experiments/draft_ubatch_probe/rtx_gpu_protocol/`. It does not modify the worker, native bridge, existing evidence, old experiment or reference definition. The PR remains a draft; no merge or deployment is requested.

**NOT_READY_FOR_GPU is unchanged.** Publication is not execution authorization. No GPU task, user-device access, new native/model inference or performance trial was performed for this protocol design/publication. The only new execution here is an arithmetic-only Python check, repeated normally and with `-O`, and integrity/readback checks.

## Original review snapshot remains intact

PROTOCOL.md, SHORT_PROMPT_CN.md, BENCHMARK_PLAN.json and SOURCE_SCOPE.json are preserved byte-for-byte from the final independent design review. `independent_review/reviewed-files.json` pins all four. Historical prose saying that the bridge was still being prepared or that no PR had yet been written describes the review-time snapshot. The publication wrapper does not silently rewrite that history or widen the reviewed numerical scope.

The short pilot explicitly cannot change old R's output reserve1, cap128 admission or resident/reset history to fit a cheaper experiment. A separately bound short-prefix adapter must first bridge the old reference, with actual cap128 work budgeted where needed. Fresh-context R is a distinct family, never an automatic fallback when the old-R gate fails. Old endpoint-only evidence cannot be upgraded to full-vector/active-KV qualification.

## Accessible fixed-head sources

The native bridge is now published at [its fixed-head directory](https://github.com/leecdiang/HeteroSpec/tree/b07a532ec78eb2ae48bc884d9332b21232e8c68d/experiments/draft_ubatch_probe/native_replay_bridge). Its [README](https://github.com/leecdiang/HeteroSpec/blob/b07a532ec78eb2ae48bc884d9332b21232e8c68d/experiments/draft_ubatch_probe/native_replay_bridge/README.md), [source](https://github.com/leecdiang/HeteroSpec/blob/b07a532ec78eb2ae48bc884d9332b21232e8c68d/experiments/draft_ubatch_probe/native_replay_bridge/src/bridge.cpp), [controller](https://github.com/leecdiang/HeteroSpec/blob/b07a532ec78eb2ae48bc884d9332b21232e8c68d/experiments/draft_ubatch_probe/native_replay_bridge/run_bridge.py), [state parser](https://github.com/leecdiang/HeteroSpec/blob/b07a532ec78eb2ae48bc884d9332b21232e8c68d/experiments/draft_ubatch_probe/native_replay_bridge/parse_state.py) and [summary](https://github.com/leecdiang/HeteroSpec/blob/b07a532ec78eb2ae48bc884d9332b21232e8c68d/experiments/draft_ubatch_probe/native_replay_bridge/evidence/SUMMARY.json) were retrieved at this fixed head. Source/controller/parser and summary SHA256 values match the reviewed local versions; the bridge README changed only as part of its publication packaging and is separately pinned in ARTIFACT_LINKS.json.

PROTOCOL.md's former native bridge workspace path is a historical producer location, not a portable download link or GPU output directory. Use the fixed-head links above to inspect published source/summary. Its scratch deliverable directory is likewise historical; this repository directory is the portable copy. Every relative link in this publication is checked against the actual file set, and the seven existing fixed-head source links in PROTOCOL.md were retrieved again before publication.

The native bridge's [LOCAL_ARCHIVE_MANIFEST.json](https://github.com/leecdiang/HeteroSpec/blob/b07a532ec78eb2ae48bc884d9332b21232e8c68d/experiments/draft_ubatch_probe/native_replay_bridge/LOCAL_ARCHIVE_MANIFEST.json) explicitly marks the 1,362,674-byte generated synthetic capture archive LOCAL_ONLY_NOT_UPLOADED. This protocol does not attach it, expose a private download URL, or claim its raw captures are independently readable from the PR. The bridge README documents regeneration; a new run changes process-specific metadata and therefore the archive hash. The compiled local executable is also not a portable artifact offered here. These access limits do not disappear because source and summary hashes match.

Actual GPU model/executable/module paths and the new absolute run_root remain intentionally unbound, not missing promised attachments. The future executor must resolve real authorized paths, report the actual run_root and pass all gates before any device execution. Placeholder paths are not commands to launch a study.

## Evidence and privacy boundary

This directory contains design text, code for arithmetic only, setup/cost-model JSON and review/hash metadata. It contains no user prompt/token contents, private third-party data, or content hashes derived from such inputs. Model architecture sizes and cited source identity hashes are not new measured GPU results. The native CPU summary concerns existing artificial fixtures, not user data or Qwen/Smol GPU execution.

Complete target-byte/state equality is required on the finite observed qualification scope; draft-byte equality is not required. Costs remain models until measured. Every future result must distinguish heavy numerical qualification, the observer bridge, provisional light timing and any unobserved light KV state. None of these promises becomes true just by publishing this plan.
