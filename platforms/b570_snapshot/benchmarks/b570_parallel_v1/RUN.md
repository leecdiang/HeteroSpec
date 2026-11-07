# Original B570 execution

Restore the PR165 evidence and its PR152/PR163 dependencies at the locations declared in `paths.py`. The original numerics, model SHA-256 values and contexts are separate inputs. Set `ROOT` to a fresh directory on a drive with capacity for all saved states and raw vectors. Run the following commands from this directory with the recorded Python 3.12 interpreter, MSVC 2022 and Vulkan SDK 1.4.357.0. Run GPU commands serially.

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python stage.py
python host.py reference
python host.py reference-O
python host.py reference-D
python host.py candidate-D
python host.py reference-reuse
python host.py candidate-reuse
python register.py
python deployments.py
python natural.py pool
python natural.py supplement
python short_pool.py
python poll.py build
python profile_build.py
python campaign.py control
python tiny_probe.py
python campaign.py mechanism
python campaign.py regress
python campaign.py poll
python campaign.py freeze
python campaign.py blind
python campaign.py paired
python campaign.py fixed
python recompute.py I:/HeteroSpec/b570-parallel-20261103 --verify-objects
```

The raw release preserves each native executable, its loaded library hashes, exact job, command, process cleanup, stdout, stderr and request records. The measured D worker source is retained beside its binary manifest. The later diagnostic worker additionally supports several queries in a single restored context to test graph reuse. For an exact D driver rebuild, pass the archived D `worker.cpp` as the `worker` argument to `host.driver`. An ordinary deployment with only the target resident has its own zero-forward gate, reference manifest and checkpoint namespace. Its result keys use `qwen_target`. Retain failed gates at their original paths.

The primary Qwen natural panel uses all-GPU resident target and draft weights at C1024. A request opens only the target context. In the separate k1 regression the draft context must pass admission too. `poll.py` compares polling modes with the same per-role executable and retains a missing cell when its workload cannot be admitted.

The four-arm Williams panel has 288 measured slots. Twelve native-fast reference measurements each share one input/session block, six immediately before the four arms and six immediately after them. Report them with their own numerical flags and matched block times. The serial arm uses an actual UB1 context in cost measurements. `SCALAR-*.json` independently qualifies this configuration before implementation freeze.

For timestamp attribution, a separate library adds tensor names to the Vulkan timestamp reports for CONT and CONCAT. It is used only for mechanism traces. The original formal library bytes are restored and the trace vectors are checked against the corresponding formal role.

The scripts retain units that completed or failed. Use a fresh output root for an independent reproduction. An existing result directory is an evidence record, and is also usable for CPU-only recomputation.

## CPU-only verification of the evidence release

Use a GitHub account with repository access and fresh output directories. The release includes the object archive utility, recomputation program and their standalone dependencies.

```powershell
gh release download b570-reference-parallel-v1-evidence-20261103 --repo leecdiang/HeteroSpec --dir archive
python archive/object_archive.py verify --root archive
python archive/object_archive.py restore --root archive --out restored --prefix units --prefix vectors --prefix repro --tail .json
python archive/recompute.py restored --verify-objects
```

The archive verifies all stored objects before selective restoration. The final command checks full-vector hashes, raw native comparison records, paired timing records and serialized checkpoint bytes.
