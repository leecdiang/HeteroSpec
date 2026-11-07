# RTX operator frontier

This directory contains the result stacked on the PR170 plan. It uses the archived PR168 Windows RTX worker, compiler commands and numerical backend modules. The experiment has its own executables, contexts and output root. See RESULTS.md for the measured operator frontier and separate natural and append costs.

## Native replication

The host fixture is Qwen3 Q8 on the original RTX 5070 Ti Laptop GPU. Use the PR168 pinned archives and original Qwen8B/0.6B GGUFs. In host.py, FROZEN is the PR168 build at E:/tpds167/build01, ORIG is the PR166 scalar core used by the C1536 oracle, and ROOT is the new evidence directory. Select a fresh root for replication. Existing attempt directories and receipts are exclusive. Immutable PR168 source and statistics stay in place.

The driver includes the frozen probe for its original physical WB slicing and decode. Native binaries link the existing immutable CUDA/CPU backend DLL cohort. Oracle prefix generation and qualification link the original scalar core. Candidate service links the exact PR168 service object, preserving the k3 acceptance/rollback loop. A new source build uses candidate.py. The packed operator patch for review is packed.patch.

For the CUPTI diagnostic build, extract the Windows wheels nvidia-cuda-cupti-cu12 12.9.79, nvidia-cuda-runtime-cu12 12.9.79 and the include directory of nvidia-cuda-nvcc-cu12 12.9.86 into E:/rtx170/profiler/sdk. Their hashes are in the bindings. Use the native driver outside the profiled build for all primary costs. The evidence includes kernel names, grids, thread blocks and GPU timestamps. CUDA activity timestamps, CPU graph definition, host submit and synchronization intervals use separate clocks and scopes.

Run from this directory with the original Python 3.11 environment. Keep native processes serial and use the shared GPU lock.

```powershell
$py = 'D:/HeteroSpec-PC/python311/python.exe'
& $py -B host.py
& $py -B -c "from host import *; build('witness02'); build('replay01')"
& $py -B -c "from host import *; [launch('replay-'+m,'replay01',dict(replay=str(ROOT/('witness-'+m)/'native')),m) for m in ('0.6B','8B')]"
& $py -B witness.py
& $py -B candidate.py
& $py -B matrix.py create prefixes qualify
& $py -B natural.py link_service freeze select
& $py -B -c "from host import *; build('prof03',profiling=True); build('newprof03',core=ROOT/'candidate01',profiling=True)"
& $py -B -c "from matrix import *; launch('profile-replay01','prof03',dict(replay=str(ROOT/'witness-8B/native'))); [launch('profile-'+str(i),exe,dict(units=[unit(f'c{j}-{arm}','profile',family(arm),h,q) for j,(_,q,h,_) in enumerate(CELLS) for arm in arms])) for i,(exe,arms) in enumerate([('prof03',ARMS[:3]),('newprof03',ARMS[3:])])]"
& $py -B matrix.py cost
& $py -B natural.py qualify cost
& $py -B collect.py ops matrix_qual sources costs natural_results
& $py -B results.py
```

A fresh freeze selects a new hash-ranked input panel. To reproduce the delivered inputs exactly, use evidence/natural-inputs.json with the published order, frozen binaries and model bindings. Never run selection in response to timing signs.

## Offline evidence

Run `python results.py` using only the standard library. It checks full-vector and operand hashes, all registered append and natural blocks, branch/transaction correspondence, and recomputes the report. The evidence includes the sampled real Q and FFN activation/output bytes, operator descriptors and weight hashes, all same-operand routes and CUPTI kernel activities. Weights come from the pinned GGUF; the full owned capture, failures and execution logs remain under E:/rtx170. Diagnostic kernel sums are activity durations, not clean end-to-end speedups.

