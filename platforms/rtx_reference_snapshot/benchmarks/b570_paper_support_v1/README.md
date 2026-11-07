# B570 paper-support experiment v1

Status: DESIGN_AND_CPU_TOOLKIT_ONLY. No new native build, GPU/model execution or positive scientific result is supplied by this PR.

Purpose: test whether the existing phase-scoped independent-query repair can preserve the existing B570 reference through a supported QH_C lowering, and whether it costs less than strong PQ. QH_C is a different physical representation, not proof that the original fourth-axis QB port works unchanged. Keep the current paper's method/state/backend storyline; no new architecture, model family, KV-subset search or AV-only method.

Start with [PROTOCOL.md](PROTOCOL.md), [HOST_PROMPT_ZH.md](HOST_PROMPT_ZH.md), and [NATIVE_HANDOFF.md](NATIVE_HANDOFF.md). [SUPERVISION.md](SUPERVISION.md) specifies the prerequisite engineering repair. [ANALYSIS.md](ANALYSIS.md) defines all three scientific outcomes, including no gain and failed transfer. [BUDGET.json](BUDGET.json) and [SOURCE_LOCK.json](SOURCE_LOCK.json) are machine-readable design inputs.

The owner sends HOST_PROMPT_ZH.md to the B570 host to authorize the bounded staged program. Creating this design PR does not run it. Once instructed, the host should implement, independently review, prospectively freeze and authenticate each stage, then advance automatically when its gates pass. Do not require a new human hash message at every stage. Unresolved identity/semantics, out-of-scope changes or exhausted budgets stop the program; they are not authority to weaken a gate. Old PR112 runs remain terminal.

## Proposed maximum scientific work

| Stage | Model requests (including warmups/diagnostics) | Model processes | Operator/census processes | Graph computes |
|---|---:|---:|---:|---:|
| S0 engineering | 0 | 0 | 0 | 0 GPU |
| S1 native operands | 12 | 4 | 97 | 96 |
| S2 natural pilot | 56 | 56 | 0 | counted in models |
| S3 confirmation | 648 | 72 | 0 | counted in models |
| Total | 716 | 132 | 97 | 96 standalone |

There are at most 229 native host attempts. Each attempt/load and each request is charged even when it fails; unstarted work stays unstarted. Model-internal forwards and kernels are separate counters, not these graph/process counts. Controls, preparation, waiting, storage and optional metadata-only readiness queries have separate explicit ceilings in BUDGET.json.

## Local tools

`python3 study.py plan --output PLAN.json` writes a new deterministic abstract slot plan (exclusive-create). `python3 -m unittest -v` checks plan accounting and adversarial analyzer/selector cases. `study.py select` requires a host-prepared tokenized candidate inventory and audited exposure hashes; it does not tokenize or retrieve datasets. `study.py analyze` accepts source-linked normalized S3 rows plus the frozen panel. It does not authenticate native raw records, inspect backend placement, validate monitoring, or authorize execution. The host must implement those independent checks before using its summaries as evidence.

The abstract S1 plan cannot contain future native tensor hashes. The prospective capture rule is frozen first; the derived actual operand manifest must be sealed before census/replay. S3 actual text/token bytes, every request order, executable/runtime identities and native serializer belong in host F0. Design metadata is not an executable F0.

Deliver complete raw records, missingness, independent reconstruction and a paper claim/evidence table on this PR. Keep Draft. Do not edit the manuscript, merge, publish or alter other experiments.
