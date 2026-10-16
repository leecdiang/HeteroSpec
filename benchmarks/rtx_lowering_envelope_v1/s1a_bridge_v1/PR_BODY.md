Depends on Draft #113 at `64a9feb7b7086ccfde1a98b9514edd812116aa7f`.

PR113 numerical v2 stopped at its budget boundary after474 qualified slots; its
controller then lost terminal receipts during final CPU analysis and marked the
previous completed slot when the next start reservation failed. This adds an
independent fixed24-context S1A Bridge and a bounded controller that seals durable
stop/end receipts, clears completed slots, defers full reconstruction to CPU
delivery and replaces hot whole-tree scans with reservations/journal/reconciliation.
Old v2,old720,GPU14,PR104/110,B570,paper,main and automations are unchanged.

Actual shared-core native CPU integration:240 serialized graph wires/3612 nodes,
60 q1 common graphs,full address/serializer tests,15 native admission negatives;
generic analyzer controls,finite-QH-difference acceptance,real Windows deadline,
pipe and commit-limit tests,production-controller CPU fixture flows and lossless
archive recovery negatives. Unexpected CPU engineering/fixture errors are retained.
Native arithmetic source/headers and numerical DLL/model bytes remain unchanged.

Actual CPU S1B clean graph audit covers72 graphs and ordinary dependency identity;
clean timing loop and trace collector remain unadmitted. No installed admitted
Nsight/CUPTI collector. Actor PE/link audit still finds static core archives;
actual header mask3/cache CPU tests pass but actor initialization/KV/rollback and
natural endpoints remain NO-GO.

`AMENDMENT.md` prospectively limits a possible S1B numerical prerequisite to the
original pre-result24 selector; it does not fill or qualify the original72.
Prepared F0 SHA256:
`4dcd6bcdbf4facdd92d4d67329bbca1155ea2499827d5ff468a2d2dd1c79a2f9`.
Proposed new census120 graphs/1806 queries,then separately approved240 numerical
graphs/3612 queries,q1 first. At most966 GPU-stage processes including helpers,
7200 conservative owned seconds plus separately bounded2700 CPU delivery seconds;
conservative all-derived1,486,177,658bytes under4GiB. No old budget or repeats reused.

This PR executed **zero GPU queries,CUDA loads,graph computes,profiling or models**.
No census/numerical approval is supplied. Next step is author review of this exact
F0/amendment for support-only census; its actual authenticated decision must precede
separate numerical authorization. No timing/actor/S2/S3 or hardware claim is unlocked.
