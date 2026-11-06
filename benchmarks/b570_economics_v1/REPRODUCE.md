# Reproduce the B570 PR189 native economics result

The new experiment is separate from PR187. Its raw archive does not duplicate
the already published PR187 archive. Both are explicit inputs to read-only
reconstruction; model weights are not needed for that reconstruction.

## Evidence and immutable dependency

- New evidence: [b570-economics-v1-evidence-20261106](https://github.com/leecdiang/HeteroSpec/releases/tag/b570-economics-v1-evidence-20261106).
- Original R, forced-prefix bank and old results: [PR187 recovery v2](https://github.com/leecdiang/HeteroSpec/releases/tag/b570-decisive-recovery-v2-evidence-20261105).
- PR187 INDEX SHA256: `9366216e4f92c08c14837ef48dbe9f9da3affd353e9e7887e13b88ebc697d3c4`.
- PR187 FREEZE SHA256: `5b4b0445c45b0ac1a7ee4aae2c52027149ffcf14f2de93a8229d641fe15fc897`.
- New branch starts at actual PR189 head `03bc44b6f382919e08a8c1aaa198c2dd723b5c8f`.

Download every `raw-objects-*.zip`, `INDEX.json`, `MEMBERS.json`,
`object_archive.py`, `recompute.py` and `README.md` from the new release into
one fresh DOWNLOAD directory. Use GitHub access appropriate to this repository.
The final result PR's `evidence/DELIVERY_READBACK.json` records the new index and
authenticated fresh-download verification. This is same-host verification,
not independent external native replication or an anonymous-access claim.

Restore the PR187 dependency with its own delivered object transport, or use an
already verified complete restoration of that exact release. Choose fresh paths;
the tools refuse to overwrite an existing restoration.

```powershell
python DOWNLOAD/object_archive.py verify --root DOWNLOAD
python DOWNLOAD/object_archive.py restore --root DOWNLOAD --out NEW_RESTORED
python -m pip install -r NEW_RESTORED/repro/repository/benchmarks/b570_decisive_v1/requirements-host.txt
python -B DOWNLOAD/recompute.py NEW_RESTORED PR187_RESTORED | Set-Content -Encoding utf8 checked.json
```

Compare `checked.json` as parsed JSON with `NEW_RESTORED/AUDIT.json`. The reader
rebases only the fixed new-study and original PR187 evidence roots into these
two supplied restorations. It does not read model files, call a native worker,
download a model, substitute R, or fall back to other host experiment directories.
It reconstructs serialized sequence states from authenticated token chunks,
checks complete F32 vectors/active KV/frontier and ending/pending contracts,
verifies runtime manifests against loaded DLL hashes, retains all ledger failures,
and recomputes the clean pilot and all control totals. Reconstructing full states
uses CPU/RAM and can take several minutes. Native execution rejects Python `-O`.

The new package retains raw commands, requests, supervisor receipts, all warmups,
measured outputs, cost sidecars, full vectors and exact reconstructible states.
State chunks already present in the explicit PR187 dependency are read through
once rather than copied again. Regenerable build intermediates, Python bytecode
and model weights are excluded with counts/reasons in MEMBERS; native binaries,
source, import/static libraries, configuration and failed build logs remain.

## Native source and build

The actual used source and runtime are retained at:

| Purpose | Archive path |
|---|---|
| Unchanged arithmetic + timers | `a1-build/{M,H1,C4U4}-mode{0,1,2}` |
| Resident private core | `core01/source`, `core01/OUTPUT_SOURCE.json` |
| Compatible parallel private core | `parallel-core02/source`, `parallel-core02/OUTPUT_SOURCE.json` |
| Clean resident and parallel frontends | `resident04`, `parallel04` |
| Separate observed frontends | `observed02` |
| Used known-token mechanism worker | `known-probe02` |
| Unused metadata-only follow-up build | `known-probe03` |
| Resource-only original-reference observer | `forced-resource02`, `REFERENCE_RESOURCE_BRIDGE.json` |
| Header/library/generated-version dependencies | `repro/native-inputs` |
| Inherited Vulkan backend and all shader source | `repro/native-inputs/pr169-ggml` |
| Native run arguments and environment | `units/*/COMMAND.json`, `runs/*/{REQUESTS.jsonl,ENV.json}` |

The same unchanged original R runtime remains in the PR187 dependency. Numerical
libraries and the actual loaded library identities are pinned per worker. The
PR169 inherited backend is `059163952ce66e26722dde75eb9dba30b4dfba59a428b3d9577b9b0d637c186e`.
F32/p021 mapping is phase/geometry driven and shared by M, SIMPLE and LOCAL.

On Windows x64 with Visual Studio 2022 C++ tools, CMake and the Vulkan SDK:

```powershell
$env:HS_ECON_ROOT = (Resolve-Path NEW_RESTORED).Path
$env:HS_ECON_PR187 = (Resolve-Path PR187_RESTORED).Path
python -B NEW_RESTORED/repro/repository/benchmarks/b570_economics_v1/rebuild_host.py FRESH_BUILD
```

This builds both private cores and resident M / parallel M / parallel D4 from
delivered source and dependencies, without external absolute build paths or model
requests. `--all` builds the resident/parallel four-arm mode0/1 frontends. It reuses
the pinned inherited ggml/common binaries, as the actual experiment did. The full
inherited Vulkan source is retained for inspection/further rebuilds. Recompiled
binaries have their own hashes; a build pass does not inherit R qualification.

The original-host experiment code is in the delivered `repro/repository` tree.
`native_host.py`, `resident_host.py`, `parallel_host.py`, `campaign_host.py`,
`resident_campaign.py`, `probe_host.py` and `development_host.py` implement the
recorded build/qualification/diagnostic/pilot order. Runtime manifests and source
snapshots identify the actual executed epochs; factory defaults can refer to a
later engineering build. In particular the known-probe02 rollback metadata omits
two replay rows in `known_tokens`, but actual `caller_rows` and graph traces include
them; known-probe03 only adds explicit metadata and supplies no replacement timing.

For a new native replication, use fresh output directories and a new ledger,
verify exact model SHA256 and actual device capacity first, then reproduce whole
warm/reset/request units from the supplied commands. Preserve original prompt IDs,
k1, C1024, cap128/native EOG, seed123, greedy sampling, F16 KV and thread10 settings.
Retain the independent original producer before scalar forced continuation. Run
full R qualification on new binaries/trajectories before clean timing; do not
overwrite this closed experiment or treat a replica as another session in it.

Exact model inputs (not included):

| Model | Bytes | SHA256 |
|---|---:|---|
| SmolLM2-1.7B-Instruct-Q8_0 | 1820414944 | `0c6e8955788b1253f418c354a4bdc4cf507b8cfe49c48bb10c7c58ae713cfa2a` |
| SmolLM2-135M-Instruct-Q8_0 | 144811072 | `40f7094960b6ede829145d102ca79451b364b27d9d8694d4406e002024cff357` |

The actual Arc B570 driver is 32.0.101.9150; physical device-local memory is
10,563,354,624 bytes. Resource floors and signed remaining-budget observations,
not calculated model-byte estimates, govern admission. Optional Qwen transfer was
not attempted here; historical capacity failures are not admitted by this kit.

## Interpretation

Read `RESULTS.md` and `AUDIT.json`. Clean service is primary. Instrumented host
envelopes, synchronized diagnostics, heavy state dumps, offline qualification,
provisioning and delivery are retained separately. Missing clocks remain null;
inclusive driver/storage and nested native costs are not added twice. All four
fixed exposed roots and eight parallel controls are kept. No blind natural panel,
performance-based input filtering, extra rescue timing, AUTO fit, RTX/arXiv edit,
merge, model download or rental is part of this result.
