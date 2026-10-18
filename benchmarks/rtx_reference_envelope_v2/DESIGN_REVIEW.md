# Design review and delivery validation

Date: 2026-10-18. Status: **design self-review completed; implementation untested**.
This is not an independent review, CUDA qualification, or scientific result.

## Evidence checked

- Re-fetched main/PR118 metadata and recent PRs. Parent remains
  `8a4cbb4246323a3f159f94cae8c92544d5a215dc`; the new work is stacked on PR118.
- Read CONTRIBUTING.md, the original S1B protocol, actual PR118 r2 result,
  PR104 final result, PR111 final result, and PR116 actual numerical-delivery result.
  Used the previously inspected PR110 model and PR118 native/graph source findings.
- Distinguished PR116's old preparation RESULT.md from its later numerical result,
  and PR118's stale opening description from the terminal r2 evidence.
- Related-work entries summarize primary sources reviewed in the accompanying
  research audit; they are not fresh comparative performance experiments.

## Local mechanical checks

A CPU-only Python check parsed both JSON files; checked UTF-8/LF and trailing
newlines, local Markdown links, 40-character source commits and URL/path consistency;
recomputed the core and optional call counts; and checked all six layout orders.
It also verified that the run template retains null runtime/freeze identities and
an empty resolved matrix. The check passed. No native host, model, CUDA or profiler
was executed, and no implementation tests are claimed.

Core N1: 24 × 3 × 3 = 216 hosts; 216 × (2 + 32) = 7344 calls.
Core T1: 24 × 3 × 6 = 432 hosts; 432 × (8 + 30) = 16416 calls.
Optional N1 diagnostics: at most 72 additional one-call hosts.
Optional T1 profiling: at most 36 hosts / 1368 calls, inside the stage/global wall
budget. Raw counts and diagnostic/performance counts must remain separate.

## Consistency changes made during review

1. Added explicit diagnostic/profiler allowances so secondary evidence does not
   require hidden unbudgeted evaluations.
2. Specified first input-inclusive cost as one first-call phase sum per resident
   host, not 30 fictitious input-inclusive samples. Repeated uploads/reallocation
   required by a workaround are charged on every affected call.
3. Distinguished the empirical oracle envelope from a deployable frozen selector,
   and used compulsory traffic rather than arbitrary actual traffic in a bound.
4. Added a conditional mature external attention comparator, with explicit byte-
   reference admission and adapter costs; determinism is not assumed compatibility.
5. Separated unavailable profiler, local-only raw retention, and optional model
   failures from core numerical/timing qualification. Kept actual correctness,
   placement and safe task cleanup as non-negotiable conditions.

## Remaining work for RTX

Resolve actual CAS data/tool interfaces; implement the new runner and analysis;
diagnose the lifecycle issue; freeze actual source/runtime/input identities; execute
eligible experiments; regenerate results and review their scope. Eight-hour first-
dispatch completion is a budget, not a feasibility guarantee. Full R1/M1/W1 coverage
can require later bounded dispatches. No hardware benefit is assumed.
