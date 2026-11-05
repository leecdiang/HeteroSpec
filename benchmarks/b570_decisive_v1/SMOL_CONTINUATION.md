# Separate Smol continuation of PR187

The original Qwen capacity stop and v1 release remain unchanged. Five Qwen
zero-forward attempts include the real DXGI reservation experiment: binding the
Vulkan device LUID removed an adapter-name ambiguity, Windows accepted the
reservation, and signed remaining budget after contexts was still negative.
No smaller context, reserve reduction, weight unloading or numerical DLL change
was used to relabel that lane as admitted.

The available, historically referenced SmolLM2-1.7B/135M Q8 pair is a separate
secondary deployment allowed by PR185 `protocols/B570.md`. Its original frontends,
model hashes, original tokenizer/template and numerical DLLs are authenticated.
Its lifecycle is resident/reset. It does not use the PR165 Qwen caller/runtime.
The original target R binary is unchanged; old raw top-two scores are available,
but historical full vectors and KV are not retroactively claimed.

## Development repairs and scope

On exposed HumanEval/42, the old native target producer used prompt-minus-one
followed by one, while R used the whole prompt. The endpoint matched but target
scores differed. Matching R's target caller and its final requested output row
fixed those observed differences. Independent original scalar forced-reference
runs then matched 25 complete conditional vectors and 13 committed active
KV/frontier states. Heavy/off final state also matched. This is one finite
development example, not qualification of the new panel.

The separate campaign preserves natural long inputs. Target prefill uses the
original R outer chunks of at most512. The inherited stronger whole-prompt
draft UB1 baseline is retained as H1 (also outer-chunked at512 for legal long
inputs), alongside M, C1U1, C4U1, C4U2 and C4U4. All candidate draft prompt
calls request only the final prompt output; later sync/propose remains singleton.
Width4 tails of three use2+1. The accepted EOG/cap branch now stops before an
extra output can be emitted, with normal trim still performed.

M uses the original target algorithm with the same draft weights and unused
draft context resident; draft reset/synchronization is included. Native arms
retain original online full-state transfer, restoration and comparison costs.
Their target continuation context is created/destroyed within the service window.
Those costs are not removed if speculation loses to M.

The first new M heavy run hit its180s deadline while using the original
transposed-V serializer's many small GPU reads. All partial files, requests and
cleanup evidence remain. The new offline observer calls the unchanged memory
writer through its pinned ABI and coalesces reads per tensor. It emits only the
writer-requested bytes; the first capture in each process must equal the public
original serializer byte for byte. Numerical DLLs, output flags, sampling and
forward calls are unchanged. The heavy observer is absent from clean timing.
Only active state is qualified; incidental temporary reads of padding confer no
claim about allocator/driver closure.

Closed complete snapshots can now be packed while the diagnostic worker runs.
A Windows sharing check excludes open writer handles; exact format/length and
the existing round-trip SHA check precede removal of a redundant flat copy.
Partial writes remain raw. Every original byte remains reconstructible from
content-addressed F16 token chunks. A real saved-state fixture checks open,
complete and failed partial writes. Four exposed diagnostic requests bridge the
same executable with this storage path:149 conditional vectors,75 committed
states and heavy/off final state match the previously independent qualification.
No extra pilot or confirmation timing slots were introduced. Packing can overlap
native work, and its elapsed time is reported without double-counting it.

## Prospective secondary panel

Before test outputs: four development roots and twelve test roots, natural
original-tokenizer C1024 eligibility, no truncation/padding, fixed hash-root/path
selection. PR175's44 exposed roots and PR177's authenticated additional exposure
are excluded. The initial PR177 path filter missed its actual evidence directory;
the retained supplemental audit finds no intersection with the selected16 roots,
so input identities/order are unchanged. No output/performance filter is used.

Keeping the extra strong H1 control gives six arms and six Williams sessions:
432 measurements and432 immediate same-arm warmups. This is an explicit
prospective amendment of the five-arm600-slot Qwen default, within the unchanged
6144 request /12000000 decoded-row /2048 operator ceilings. No new AUTO is fitted.
Development pilot uses the four fixed development roots and every arm. Numerical
or resource failures remain gates; performance is never a reason to remove a
control or select another input.

Each scheduled arm/root pair has a fresh worker and model load outside service,
then an immediate resident warm request and measured reset request. All loads
are separately retained. Qualification repeats this priming sequence in heavy
and clean workers, checks their final active KV/frontier and autonomous original
R endpoint, and uses independent original-R scalar forced prefixes for all
captured conditional target vectors and committed states. R never receives
candidate values or tapes during autonomous generation. Original unused
intermediate prefill rows retain their output flags but are not part of the
full-vector observation claim.

The service field includes reset/sync, prefill, sampling/propose/verify/trim,
required state transfer/checks, continuation context destruction, and response
capture file close. Qualification dumps are outside clean service. Native
workers have900s total and180s request-progress bounds,16GiB Job memory,20GiB
disk reserve,2GiB RAM reserve and128MiB signed device reserve. Failure cleanup
includes actual Job descendants. Every model request, including failed,
teacher-forced and warm requests, is reserved before native creation.

The fixed analyzer reports all15 contrasts, primary total-service ratio,
equal-root log sensitivity, root-cluster family intervals, absolute differences
and complete costs. No additional sessions for a favorable mean. No merge,
paper edit, model download, rental or cross-platform speed ranking.

Actual per-root qualifications, pilot, freeze and confirmation status must be
read from their receipts. Their execution is not implied by this declaration.

The four fixed development roots have now passed all six native arms, including
the147-token2+1 tail and584-token512+72 target prefill. The fixed pilot completed
all24 measurements and24 warmups. Measured service totals across the four roots
were M4.629248s, H145.466576s, C1U145.490480s, C4U145.459491s,
C4U245.838786s and C4U444.603271s. This negative exploratory result does not
remove any control, change the selected test roots or add timing repetitions.
The confirmation still requires the actual published source/data freeze and its
own complete qualification and864-slot panel.

All native attempts, failures and reservations are metered. Early CPU preparation
and some early lossless packing were not separately wall-metered; that limitation
is retained. Later coordinator receipts include child work and storage and are
not added to native wall a second time. Provisioning-to-ready observations include
process/library/backend/model/context setup, with100ms polling resolution; they
are not labeled pure weight-load time. Clean measured service remains its native
response-commit clock. No inference about unobserved hidden allocator state or a
general model/backend domain follows from these finite checks.
