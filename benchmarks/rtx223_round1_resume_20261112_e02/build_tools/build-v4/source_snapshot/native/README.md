# Narrow Q8_0/F32 paired-group prototype

This is an isolated operator prototype. It is not installed into an existing
runtime or model executor. A and B instantiate the unchanged original
`mul_mat_vec_q<GGML_TYPE_Q8_0,4,false>` function from the bound source prefix:
A launches it twice with four columns each; B launches once with two channel
blocks. C keeps four warps, two output rows, four arithmetic columns, the same
thread-to-K assignment, the same dot helper, per-output K accumulation, ordered
inter-warp adds and XOR warp reduction. C loads one weight fragment per row
and K iteration before updating its two independent four-column groups.

Only Q8_0/F32, q=8, g=2, no IDs, no fusion, contiguous inputs/outputs, K divisible
by 512, no K padding and even M are admitted by the executable. Graphs are
disabled. Changing native width to eight is not used. Any bitwise difference
against independently produced backend-loop4 output stops before timing.

The probe writes both complete quantized activation bytes and all output bytes
for two repetitions of each arm. It then uses three warmups per arm and six
balanced three-arm timing blocks for kernel-only and full-operator measurements.
The full operator includes the common quantizer and event synchronization;
kernel-only excludes the common quantizer after synchronizing it. Host complete
time is recorded separately from CUDA event time. No stage sums are substituted
for complete-request service cost.

Compilation uses the original source kit as a read-only dependency. Rebuild:

```powershell
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' build_tools/build_operator.py --out build_tools/build-v1
```

The build script never executes the resulting probe. Native execution requires
a separately admitted job with the actual device UUID. A host receipt or a
derived real-input fixture does not admit GPU execution or establish a current
q8 model descriptor. No native or performance qualification is claimed here.

The unchanged kernel is extracted rather than linking the whole backend; an
original backend output is a mandatory replay oracle. This verifies only the
frozen operand after execution, not generic dispatcher equivalence. A runtime
integration and complete-request qualification remain separate obligations.

Resources available after execution are compiled registers, static shared
memory, local memory and occupancy-limit API values. Achieved occupancy, DRAM
and L2 counters remain `unknown` without profiler counters. Compiler spill
load/store reports are retained verbatim in the build log. Static source loads
are not measured memory traffic.
