# Core Ultra X7 358H Threshold-Validation Runbook

Status: **PLANNED / NO RESULT CLAIMED**

This is the onboarding and execution guide for the 358H platform. Read it after the repository root `README.md`, then read `paper/notes/VERIFICATION_AMORTIZATION_FRAMEWORK.md` before formal measurements.

## Purpose

The completed M4, RTX 5070 Ti, and Arc B570 studies show that speculative decoding is profitable only when draft cost, correctness-admissible target verification cost, and runtime/orchestration overhead all fit below the useful work committed by each speculative round.

The 358H study tests a new axis: **draft-device capability**. It asks whether the same small draft model can run cheaply enough on a newer consumer AI-PC CPU, Xe3-class iGPU, or ~50-TOPS NPU to approach or cross the existing break-even boundary.

This is a predictive threshold-validation study, not a search for a positive result.

Primary question:

> On Core Ultra X7 358H, how fast can the frozen draft model run on CPU, iGPU, and NPU, and do any measured draft costs make heterogeneous speculative decoding plausibly profitable under the existing cost model?

Secondary question:

> For any path that is predicted to be plausible, does a frozen end-to-end `k=2` speculative run preserve token-exact correctness and improve latency or energy relative to target-only decoding?

## Minimal knowledge checklist

Before formal work, the experimenter should be able to explain:

- [ ] autoregressive decoding: the target normally advances one accepted token at a time;
- [ ] draft vs target model roles;
- [ ] proposal width `k` and why this study starts from `k=2`;
- [ ] acceptance and accepted draft tokens/round;
- [ ] block verification: the target can evaluate multiple candidate positions in one causal forward pass when the draft supplies future inputs;
- [ ] token-exact correctness: generated token IDs must match the paired greedy baseline exactly;
- [ ] `V_k = T_target_verify(k) / T_target_decode(1)` and why values near 1 are strongly amortized while values near `k` are effectively serialized;
- [ ] why high acceptance alone does not guarantee speedup;
- [ ] latency vs throughput for batch-1 local inference;
- [ ] J/output-token and why lower watts do not necessarily mean lower energy;
- [ ] explicit device placement: OpenVINO `AUTO` and `MULTI` are forbidden for single-device CPU/iGPU/NPU claims.

## Scientific rules

Before formal data begin, complete and commit `benchmarks/358h_threshold_validation/preregistration_v1.json`.

The following are scientific variables and must not be silently changed after formal measurement starts:

- model identities, conversions, hashes, and precision;
- runtime/build and driver versions;
- explicit draft device;
- target runtime/device if Phase 3 is reached;
- prompt selection and order;
- greedy settings, seed, `k`, output-token cap;
- context points and repetitions;
- correctness contract;
- telemetry sampling and energy boundary;
- GO / NO-GO rule.

Engineering fixes such as paths, quoting, log parsing, equivalent command syntax, and process launch may be repaired without redefining the science. Preserve failed attempts and document deviations.

## Phase 0 — Platform qualification

Goal: prove that measurements really run on the requested device and that the machine is stable enough for formal work.

- [ ] Record Windows build, BIOS, Intel graphics/NPU driver, OpenVINO/runtime, Python, and repository commit.
- [ ] Record CPU, iGPU, NPU, RAM, AC/battery state, power mode, display/remote-session state.
- [ ] Verify CPU, GPU, and NPU are individually visible.
- [ ] Verify explicit single-device execution; no `AUTO` / `MULTI`.
- [ ] Verify model/conversion SHA256.
- [ ] Verify there is no silent CPU fallback for an iGPU/NPU claim.
- [ ] Measure warm-up behavior and document the steady-state timing protocol before formal timing.
- [ ] Record available telemetry domains. If NPU/iGPU energy cannot be isolated, state that limitation instead of inventing a boundary.

Required output: `reports/358h/358H_ENVIRONMENT_QUALIFICATION.md`.

## Phase 1 — Draft-device latency characterization

Goal: measure the **same frozen draft model** on CPU, iGPU, and NPU before running large speculative workloads.

For each device, collect at minimum:

- steady-state draft latency and tok/s;
- preregistered context sensitivity;
- initialization/warm-up behavior;
- dispatch / host-device handoff overhead when measurable;
- RAM and device-memory use;
- available component power/energy with an explicitly named sensor boundary;
- exact runtime command and evidence that the requested device performed the work.

Use the same model semantics, prompt/input construction, output limit, repetition structure, and thermal/power policy across devices. If the NPU requires a converted representation, freeze the conversion recipe and hash before formal comparison and document that it is a runtime-format difference rather than a model-choice change.

Do not use marketing TOPS as a latency result. A high-TOPS NPU may still lose because of dispatch, unsupported operators, conversion, synchronization, or handoff overhead.

Required output: `reports/358h/358H_DRAFT_DEVICE_CHARACTERIZATION.md` and `analysis/358h_draft_device_summary.csv`.

## Phase 2 — Predictive break-even gate

Before any large end-to-end speculative run, plug measured draft cost into the existing framework:

`T_spec/token = [T_d(k) + T_v(k,e) + T_x(e)] / C`

`speedup = T_b * C / [T_d(k) + V_k(e) * T_b + T_x(e)]`

For each draft device classify the path as:

- **NO-GO** — clearly cannot cross break-even even under favorable accepted-work assumptions;
- **BORDERLINE** — close enough that end-to-end measurement is informative;
- **GO** — predicted to cross the threshold under the frozen assumptions.

Write the assumptions, measured draft costs, reused target/verification evidence, and threshold calculation to `reports/358h/358H_DRAFT_THRESHOLD_ANALYSIS.md` **before Phase 3**.

Advance based on measured latency and the preregistered rule, not TOPS or preference for a positive result.

## Phase 3 — End-to-end validation for plausible paths only

Only BORDERLINE or GO paths may advance.

1. Run a small frozen correctness gate first.
2. If the path satisfies the preregistered correctness rule, run the frozen HumanEval30 IDs already used by the cross-platform study.
3. Use batch-1 greedy decoding, fixed seed, `k=2`, frozen model revisions, explicit device placement, and a paired target-only baseline.
4. Record exactness, timing, acceptance, memory, and any valid energy telemetry.

Primary outputs:

- exact pairs / total pairs;
- exact prompts / total prompts;
- geometric-mean paired speedup and 95% bootstrap CI;
- prompts faster / total prompts;
- acceptance and accepted draft tokens/round when directly available;
- target verification factor where measurable;
- J/output-token only when the sensor boundary is valid and documented.

A correctness-divergent path may be retained as diagnostic evidence, but its timing cannot be presented as a correctness-admissible optimization result.

## Phase 4 — Closeout

Regardless of outcome:

- [ ] do not tune after seeing the result unless a new preregistered follow-up is explicitly created;
- [ ] preserve authoritative raw data;
- [ ] generate processed summaries and reports;
- [ ] create a manifest with SHA256 and exclusions;
- [ ] record deviations and blocked stages;
- [ ] push a dedicated branch and open a PR;
- [ ] mark the platform COMPLETE, NO-GO, or BLOCKED with a reason.

## What not to do

Do not:

- sweep `k`, prompt sets, precisions, drivers, backends, or models to search for a positive result;
- silently move work between CPU, iGPU, and NPU;
- use OpenVINO `AUTO` / `MULTI` for a single-device claim;
- call semantic similarity or code functionality “token exact”;
- mix board, package, component, and wall-energy domains;
- report a fast but correctness-divergent path as an optimization result;
- infer a 358H result from the config file or from vendor TOPS claims.

## Experimenter acceptance checklist

Before collecting formal data, answer these five questions in your own words:

1. Why is 358H testing the **draft-cost threshold** rather than repeating the B570 backend study?
2. What does `V_k` mean, and why is acceptance alone insufficient?
3. Why must CPU/iGPU/NPU execution be explicitly bound?
4. What makes a timing result correctness-admissible?
5. What measured behavior could make a 50-TOPS NPU scientifically uninteresting for this workload?

If any answer is unclear, reread `paper/notes/VERIFICATION_AMORTIZATION_FRAMEWORK.md` and `paper/notes/CROSS_PLATFORM_MECHANISM.md`.

## Expected repository outputs

A completed campaign should add, at minimum:

- `reports/358h/358H_ENVIRONMENT_QUALIFICATION.md`
- `reports/358h/358H_DRAFT_DEVICE_CHARACTERIZATION.md`
- `reports/358h/358H_DRAFT_THRESHOLD_ANALYSIS.md`
- `reports/358h/358H_HUMANEVAL30_VALIDATION.md` if Phase 3 is reached
- `analysis/358h_draft_device_summary.csv`
- `analysis/358h_threshold_summary.json`
- `artifacts/358h_threshold_validation/<run-id>/manifest.json`
- a final 358H platform closeout report

Negative, blocked, or NO-GO outcomes are valid outcomes. Do not optimize the study toward a favorable answer.
