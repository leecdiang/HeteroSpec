# Numerical readiness review and prospective choice

Review base: PR114 `449ead854424a1ac88d538332994bcf9f8813e1e`.
The closed run remains `pr113-s1a-bridge-v1`: 240 unstarted native slots,
zero native hosts and graph calls, one readiness/admission failure. The one
query reported utilization32%, exceeding the frozen5% ceiling. Its process
exited successfully; no native execution followed. Memory119/12227MiB,
temperature46C, AC power, driver616.92 and balanced power scheme otherwise
matched. Neither process-level attribution nor a second temporal sample exists.
The source of32% is UNKNOWN. This review does not reclassify the old failure.

NVIDIA defines GPU utilization as the fraction of the preceding sample period
during which at least one kernel executed, with a product-dependent period
between1s and1/6s. It is neither a numerical error probability nor a promise of
future inactivity. [NVIDIA System Management Interface](https://docs.nvidia.com/deploy/nvidia-smi/index.html#utilization).
The archived cuBLAS12.6.1 documentation describes reproducibility conditions
in terms of toolkit/hardware, streams/workspace and atomics; it does not give
a5% admission theorem. Its cuBLAS guarantee cannot certify every custom GGML
CUDA kernel. [cuBLAS12.6.1 reproducibility](https://docs.nvidia.com/cuda/archive/12.6.1/cublas/index.html#results-reproducibility).

## A: retain strict idle, independent execution window — RECOMMENDED AND IMPLEMENTED

Retain the original5%,55C,512MiB free, AC and exact power/device/driver checks
at every census/numerical admission. A new approved attempt needs an externally
arranged quiet window. No polling loop, cooldown, auto-retry or added probe is
registered. A first failed readiness consumes that attempt and terminates the
new run.5% is conservative isolation continuity, not necessary/sufficient proof
of correctness. Risk: desktop activity can again stop the run before any graph;
a low reading also does not prove continuous isolation or identify all workloads.

Numerical qualification still requires actual CUDA bindings and modules, complete
input/output bytes, MQ own-path, historical PQ/QB, all q1 common paths, independent
fresh-process repeats and completion synchronization. Memory/thermal/power and
Windows JobObject limits remain independent safety/admission requirements.
OS executable conflict metadata is checked before admission and each slot; it
does not identify unknown GPU clients or prove globally exclusive GPU use.

## B: numerical-specific tiered readiness — evaluated, NOT REGISTERED

A defensible future B could retain every hard identity/resource/power/conflict
gate, classify utilization above5% as an interference observation and keep all
complete results and repetitions, while reserving strict idle for timing. This
would change the environment population and possibly timeout exposure. Arbitrary
new ceilings such as32%,50% or100% are not derived from these records. Nor do two
matching repetitions prove arbitrary contention cannot affect implementation,
workspace, error behavior or selection. Requiring attributable permitted
background clients would need a separately validated process-observation
contract, particularly with WDDM visibility limits. No such new device evidence
is authorized or available here. Therefore B remains a proposal, not a hidden
fallback; no B option or policy switch exists in the new executor.

## Scope and subsequent evidence

Numerical correctness, safety, interference and clean cost measurement are four
different questions. Even A passing and240 matching results would establish only
this exposed24-context numerical envelope. S1B clean timing retains its own
strict isolation, independent F0/budget/authorization and separate trace hosts;
no numerical wall time is performance evidence. Original PR113474/720 and the
closed zero-start Bridge are separate historical results, never merged withv2.

New host changes only run/stage identity in formal_gate.h; graph/arithmetic,
core initialization, serializers, numerical DLLs and execution environment stay
unchanged. Because the executable hash and admitted wire/F0 change, one new
complete support census is REQUIRED. Old120/120 support is impact-review evidence,
not transferred admission. New census and numerical require separate approvals.
