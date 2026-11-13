# C1 serial-group diagnostic

Frozen e08 C keeps `tmp[2][4][2]`, 16 float accumulators/thread, and
`partial[2][3][4][2][32]`, 6144 bytes/CTA. A/B's case-4 path keeps
8 float accumulators/thread and a 3072-byte shared reduction buffer. C's
unrolled groups also extend weight/activation/pointer temporary live ranges.
The compiler's 63->91 physical-register change cannot be exactly assigned
to the eight extra source accumulators alone; register allocation includes
temporaries, scheduling and liveness. No measured performance cause follows.

C1 uses one non-unrolled outer group loop, eight accumulators/thread and one
3072-byte shared buffer. Every output retains the original lane partition,
K start/step, K traversal, dot primitive, cross-warp add order and warp reduce.
All warps remain alive; an inter-group barrier protects shared-buffer reuse.
It reloads the weight fragment for group1 rather than sharing it across two
simultaneously live groups. It is a resource diagnostic, not proof that the
original C's explicit weight reuse was beneficial or that occupancy caused
its regression. There is only one new candidate and no register cap/tuning sweep.

Before GPU qualification, falsifiable compiler target: <=64 registers,
3072 shared bytes, no spill. First frozen build meets this: C1=64/3072/0,
A/B=63/3072/0. Same frozen nvcc/MSVC, sm_120a and fast-math settings as e08.
Expected theoretical occupancy must be queried separately; achieved occupancy
and DRAM/L2 traffic are NOT_MEASURED. Additional barriers and weight reloads
can lose more time than lower resource pressure saves. GPU data will decide.

Performance hypothesis: for the one frozen genuine q8 fixture, C1 closes the
old C/B gaps (14.77% projection,12.64% complete operator). Twelve alternating
B/C1 pairs per boundary, four repetitions/batch, all raw samples retained.
If C1 remains clearly slower, stop expansion; if near/faster, propose independent
cross-input validation only. No service or population claim from this fixture.
