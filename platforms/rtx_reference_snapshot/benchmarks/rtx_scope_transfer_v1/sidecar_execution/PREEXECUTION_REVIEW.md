# Separate registered diagnostic and incremental archive admission

This sidecar implements the existing PR151 A0/A1/A2 plan. It adds no request,
input, repair, replay, checkpoint import or retry. The main factorial source
directory, execution identity, source binding, executable/core/DLLs, models,
references, date schedule, thresholds and retained streams are unchanged.

The author authorized this work in the current chat and requested the latest
[handoff](https://github.com/leecdiang/HeteroSpec/pull/151#issuecomment-6514022858).
Day0 and all 196 qualification requests are preserved and never rerun.

## Native compatibility and isolated binding

The unchanged metadata4 executable already accepts family Llama, requires fresh
contexts for it, supports NATIVE/P1/P4_NATIVE, verifies actual executable/model
and numerical-module hashes, validates all supplied slots before model loading,
and releases every request's contexts. The sidecar supplies only the registered
18 A1 slots and 36 A2 slots. The sparse panel retains original source indices
8/6/3; unselected indices are null and cannot be referenced by the frozen slots.

The diagnostic PLAN copy accurately labels its fresh lifecycle and makes all
timings ineligible for performance. Its independent identity uses the existing
metadata4 build hashes and the registered Llama model/tokenizer pins. Runtime
and host source maps are committed before the first RUN handshake. There is
no rebuild and no edit to the main FREEZE_COMMIT or CURRENT_SOURCE_BINDING.

A1 and A2 have separate clean processes, with both model weights resident per
unit and fresh target/draft contexts per request. Model-load free memory must
be at least 512 MiB before RUN. This is a model-load admission, not a claim that
the frozen executable can pre-provision Llama fresh contexts: allocation errors
are retained as failures and do not permit a retry. Limits are A1 2700 seconds,
A2 3600 seconds, total 6300 seconds, 24 GiB diagnostic payload and 20 GiB disk
headroom. These are sidecar limits and do not change the main caps or reserve.

## Checks and outcome handling

Five CPU tests cover all 54 unique registered slots, fresh lifecycles, the
complete unexamined decision-vector inventory, strict observed metadata4 alias
matching, formal-date priority and the pre-formal deadline. Preparation hashes
both model files, the existing EXE and 21 DLLs. Historical R/PQ/QB records,
observer streams, masks and full logits for the three fixed inputs are copied
with the PR144 raw-manifest hashes verified. A0 reproduces the known endpoint
divergence at index81 (16 versus15), and retains both passing controls. Whole
PQ/QB logit-file equality is checked separately from endpoint equality. No
operator localization is inferred from that equality.

Every new heavy request must retain all target/draft decision vectors including
unexamined rows; the sidecar checks finite float32 vectors, their greedy argmax,
exact transaction reconstruction, 32-layer Llama geometry, actual producer call
counts, scope and teardown. New R/reference or consumer/R mismatches are retained
diagnostic outcomes. Observer off/heavy, PQ/QB vectors and canonical-state
comparisons are reported independently. A disappeared known failure is runtime
dependence, never a repair claim. A2 supports only bundled recipe interpretation.

The initial CPU preparation attempt used a positional assertion against a sparse
panel and stopped without launching a worker. Its directory is retained. The
assertion now locates the known-failure source index explicitly; a negative
metadata test also led to a missing-name-safe operand lookup. Both are pre-run
sidecar changes; GPU requests at this review are zero. This is a host-side code
and CPU review, not an independent reviewer or another-host replication.

## Formal priority and archives

Sidecar work first validates the main freeze and completed attempts. It refuses
an incomplete formal date that is already eligible, and requires its bounded
work window plus 1800 seconds before the next formal date. It atomically acquires
the existing HOST.lock protocol with a distinct owner and removes only its own
lock. All diagnostic, CPU audit, compression, upload and readback work is serial
with formal workers; no sealed main stream is modified by this lock handshake.

Archives contain immutable copies of completed bundles, with a member manifest,
bounded ZIP parts, asset hashes, fresh remote downloads and verification of every
downloaded member. Existing manifests and parts are never overwritten. The
archive includes no external model weights or numerical DLLs. Upload/readback
receipts must distinguish local packing from verified remote delivery. Old
qualification/day0 indices remain historical snapshots.

The existing frozen study.py audit/analyze interface remains the final three-date
analysis gate; no first-day performance estimates guide later work. Date1 is
October31 and date2 November1, with all original first-session gaps and order.
