# Prospective RTX adapter notes

New UUID, new entry `runner.py`, same pinned numerical DLLs and exact graph
headers. Inputs are copied byte-for-byte from the sealed PR121 input index;
fresh serial references are captured in this run. Old results are not repetitions.

Initial installed-tool inspection found no admitted tracer. During the bounded
preparation window, official NVIDIA CUPTI12.8.90 Windows wheel(7MB) was unpacked
locally, plus CUDA headers(runtime wheel944KB, NVCC33MB downloaded but ONLY its
headers extracted; no compiler/driver installation). Download URL/hash receipts
are retained. No downloaded cudart is loaded: original frozen runtime wins by
exact path. Collector dynamically loads the exact CUPTI module only in profile
jobs. Callback API records successful capture/instantiate/launch and call indices;
activity API requests kernels/copies/driver/runtime timeline. These capabilities
remain pending actual GPU proof. Keep dual plan, OFF fallback draft and initial
unavailability receipt. No unverified ON result enters clean comparisons.

At most21 qualification hosts are instrumented(18ON distinct signatures with
value0,3OFF QB boundary controls); two of four separately capped value-alternating
capability hosts instrument ON. Total profile cap23, within24. Capability hosts
each2warmups+6calls, all input update/readback bytes retained; no timing inference.
Both value realizations share graph signatures checked on CPU and actual graphs.

H1 checked readback remains per call; output/record buffers preallocated and
files/JSON flushed after replay. Optional P0 is implemented as one actual interval
from complete preexisting permuted Q copy/transpose through upload, computation,
full synchronization and ordinary readback. It is not the PR121 phase sum.
Cold allocation and resident KV/mask setup stay outside P0 and separately charged.

The inherited Windows Job supervisor enforces process count/commit/timeout and
bounded streams. Requested50ms polling is not a certified maximum gap contract;
PR118's old strict1s experiment is not resumed or relabeled. Actual supervisor
and resource receipts are retained. No new supervision framework is introduced.
