# B570 PR185 execution: prefill repair and measured capacity stop

The prompt-tail repair, original-interface tests, original-host builds and real
descendant-cleanup checks are complete. The Qwen3-8B/0.6B Q8 C1024 deployment
**fails G0 capacity admission**, including mandatory unchanged C1U1. No numerical
qualification, pilot or confirmation performance result is claimed.

This result branch starts at PR185 actual head
`8befecc2484d749085ed95fca064b6acc42e7b1d`. Prior PR165 references and PR175's
AUTO null result remain intact.

## Repair and tests

The original `NativeContext::prefill` accepts caller widths1,2,4. The proposed
q4 scheduler emitted width3 for lengths congruent to3 modulo4. Both native
`draft_schedule` and Python `caller_chunks` now decompose that tail as2+1.
The inherited prefill method still owns the final-output flag; no extra prompt
logits or token consumption are introduced. Prompt content is unchanged.

`tests/test_original_prefill.cpp` invokes the verbatim historical method with a
recording decode double. It checks8192 length/caller cases, complete token order,
positions, one final output flag and2+1 tails; it also reproduces the original
interface's rejection of width3. The adjacent fixture manifest authenticates the
historical source and method bytes. The previous8199 standalone helper checks
also pass. All76 Python tests pass normally and under `python -O`.

A real Windows failure-path test exposed an open SQLite connection during a
rejected budget change. `Ledger` now closes that connection before raising.
The original failing test log is retained.

## Native execution and resource result

R,C1U1,C4U1,C4U2,C4U4 compiled on the B570 host with Visual Studio2022. Only
driver code changed; each original/candidate numerical DLL is authenticated
against the historical release and the actual loaded-module inventory.

The initial corrected guard rejected legacy `free > physical total`. Inspection
of the pinned Vulkan source shows unsigned `heapBudget - heapUsage`. A fresh
metadata-only epoch queries `VK_EXT_memory_budget` in the same process, computes
signed remaining bytes and clamps negative remaining capacity to zero. It does
not rebuild or modify numerical DLLs. Both failed epochs remain retained.

| Zero-forward attempt | Physical bytes | Budget bytes after contexts | Usage bytes | Signed remaining bytes | Result |
|---|---:|---:|---:|---:|---|
| R initial guard | 10563354624 | not separately recorded | not separately recorded | wrapped legacy value rejected | FAIL |
| R resource epoch01 | 10563354624 | 8881590272 | 8946769920 | -65179648 | FAIL128MiB reserve |
| C1U1 resource epoch01 | 10563354624 | 8881758208 | 8948736000 | -66977792 | FAIL128MiB reserve |

These failures occurred after both target and draft weights and both C1024
contexts were constructed, before any model forward. Logs disclose37/37 target
and29/29 draft layers offloaded to Vulkan, F16 KV144MiB target/112MiB draft,
non-flash attention and unchanged CPU_Mapped framework buffers.

Limits are900s per native worker,180s per request,16GiB Job memory,20GiB disk,
2GiB RAM and128MiB device reserve. The B570 ceiling remains6144 model requests,
12000000 decoded rows and2048 isolated operator replays. Each worker is created
suspended, assigned to a kill-on-close Job and resumed; the default active-process
limit is1. Actual parent-failure and timeout tests with live descendants verify
zero remaining active processes. The initial fixture's assumption of exactly two
Windows Python processes was false (the actual startup chain had three); its
failure and the corrected bounded-count test are both retained.

Three zero-forward attempts cost25.015 owned-process seconds in total. Decoded
model requests, token rows and operator replays are all zero. Build command times,
model-load times and every failure are retained separately; they are not a
performance comparison.

## Protocol disposition

`protocols/B570.md` requires closing the Qwen lane if M/C1U1 cannot run safely.
Mandatory C1U1 fails before numerical qualification, so reference/observer bridge,
trained-model qualification, four-root pilot and the default600-slot confirmation
are `NOT_RUN_GATED`. No held-out cohort or outputs were exposed. No input was
discarded, and C4U1 and the optional wide arms were not removed for speed: all
remain in the declared roster, with unexecuted stages explicitly recorded.
Capacity, KV precision, context length and weight residency were not relaxed.

The already available, previously referenced SmolLM2 pair and original runtime
were authenticated and inspected. Its historical draft caller is a whole-prompt
decode and its lifecycle is resident/reset, different from this PR165 caller
intervention. No secondary Smol campaign was opened; the protocol also permits
stopping. It is not presented as a Qwen success or a tested Smol failure.

## Reproduction and evidence

`evidence/RECONSTRUCTION.json` independently checks signed budgets, failed native
results, process cleanup, unchanged numerical DLLs and the durable zero-work
ledger. `AUTHENTICATION.json`, `CLEANUP_PROOF.json`, `TESTS.json`,
`GATE_DISPOSITION.json` and `SMOL_INSPECTION.json` give compact receipts.

The raw release retains all attempts, original/compiler logs, generated sources,
runtime manifests/binaries, imported libraries, API headers and tests. It contains
no target/draft weights. Supply the exact model hashes in the authentication
receipt and restore historical PR165 sources from their separate pinned release
when using `host.py setup` on a fresh output root. `HS_DECISIVE_ROOT` chooses that
root; existing attempts are never overwritten.

For a standalone driver rebuild from the restored evidence, configure any role's
`kit/b570_producer_consumer_boundary_v1` with Visual Studio2022, an installed Vulkan
SDK for budget01 roles, `LLAMA_SOURCE=portable/api/original` (R) or `candidate`, and
`QUALIFIED_BUILD=portable/libs/original` or `candidate`. Historical numerical DLLs
are under the corresponding role's `build/bin/Release`; stage them next to the
rebuilt executable. Complete executed argv/JOB examples are in `units`.

Run the read-only audit with:

```powershell
python RESTORED/repro/host/closeout.py audit RESTORED
```

Fresh-download restoration verification is recorded separately after publication.
No native external replication, successful model qualification or service gain
follows from packaging checks. No merge, paper edit, model download or rental.
