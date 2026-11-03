# RTX reference-preserving parallel execution

This directory contains the independent successor to the PR166 Qwen runtime. The executed numerical backend is the sealed RTX cohort from commit `abd36bea639bf814159ad68ab015bc983c5338b1`. Use the adjacent protocol for the predeclared comparison. The results report distinguishes scalar-reference compatibility, scheduled operator geometry and measured service costs.

## Reproduction on the original RTX host

Use the PR166 Qwen source, CMake command manifest, dynamic CUDA and CPU backends, old original Qwen8 worker and model files on the paths in the scripts. Restore the retained PR166 assets first. The candidate writes to a new study root. Existing attempt directories identify previous executions and must be preserved. Choose an empty output root for a new replication and retain its new freeze and input identities separately. The historical build bindings and command replay belong to the Windows host. Python 3.11 is used for the study drivers.

From the independent worktree run these commands under PowerShell.

```powershell
cd benchmarks/tpds_parallel
$py = 'D:/HeteroSpec-PC/python311/python.exe'
& $py -B build.py prepare configure core worker link
& $py -B oracle_build.py
& $py -B service_build.py
& $py -B mechanism.py origin --widths 2,4,8,16,32
& $py -B mechanism.py boundary256 --bases 253 --widths 8,32
& $py -B mechanism.py boundary512 --ctx 1536 --bases 510 --widths 16
& $py -B mechanism.py eight --model 8B --bases 253 --widths 32
& $py -B mechanism.py fourteen --model 14B --widths 8
& $py -B panel.py
& $py -B study.py freeze
& $py -B study.py run
```

`lowering.patch` shows the actual native delta against the sealed PR166 llama source, including real tensor views, matmuls, KV extent handling, graph storage and head placement. To inspect application against the original mixed-line-ending source use `git apply --ignore-space-change --check`. The build script constructs the same source from that cohort. `service_build.py` retains the PR166 k3 acceptance and rollback loop and adds the physical call boundaries. The probe records raw full-vocabulary binary32 outputs, layer-zero graph scheduler observations and actual physical batch counts.

## Offline reproduction

Run `python reproduce.py` from this directory with the accompanying evidence folder. This uses the Python standard library and needs no GPU. It checks the numerical digests and observed attention group widths, reconstructs the committed reference checks and recomputes all eight paired service ratios from the delivered warmup and measured receipts. Native files and failed attempts are retained under `E:/tpds167`. The compressed JSON evidence contains hashes of the vocabulary buffers and the native measurements. The full model files and vocabulary buffers are not embedded in Git.

