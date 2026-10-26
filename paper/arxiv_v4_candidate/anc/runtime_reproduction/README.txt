Query-layout CPU contract and archived source excerpts
=====================================================

Run from the paper source root:
  python3 -B -m unittest discover -s anc/runtime_reproduction -p 'test_contract.py' -v
  python3 -B anc/runtime_reproduction/contract.py
  python3 -B anc/runtime_reproduction/verify_sources.py

The first command runs 12 CPU tests for query/mask addresses, backing bounds,
phase selection, and layout/state-recipe cache identity. The example compares
24 query addresses. The source verifier checks the eight copied files against
their original Git blob IDs. These commands call no GPU and perform no model
inference or numerical attention replay.

The eight original files were copied byte-for-byte from src/query_layout at
HeteroSpec commit 805864b1e370c4d17defa58bed4fac43c1cfb75e. PROVENANCE.json records
their individual Git blob IDs. SOURCE_INDEX.json also identifies the earlier
campaign commit for each archived header/patch. README.upstream.txt preserves
the original repository instructions; its paths refer to the repository layout.

Packaged native material consists of two real archival patches and an RTX
phase-scope header, plus the method conditions. They are source excerpts, not
a complete build or runnable runtime. Do not apply them to arbitrary upstream
llama.cpp. The Vulkan bridge depends on query_head.h and preceding PR131
admission/source changes. Its supported descriptors are d128/Hq32/Hkv8,
key extent 256 or 512, and q2 or q4. The RTX header belongs to the later
fresh-context service implementation and uses a process-wide layout setter;
it is not the immutable environment selector used by the E2 resident servers.

For E2, the pinned runtime adapter at f997262d6b0accb126a1217c9356745cc8bbf708
routes all Qwen arms and all R/QB arms to the original executable. Only the
SmolLM2/Llama M_PQ and C_PQ arms use the metadata4 executable. Reproduction
must preserve this routing and the unchanged numerical DLLs.

The following dependencies are external to this small CPU subdirectory:
1. The exact source capsule and metadata4 correction, native build recipe,
   toolchain identifiers, and pinned backend libraries listed in PROVENANCE.json.
2. One admitted native capture with original Q/K/V/mask spans and strides,
   reference QK/softmax/AV outputs, the replay executable source, and an equality
   check; no synthetic replacement for these native operands.
3. One complete request fixture with model identities, native input IDs,
   reference output IDs/stop state, phase/layout configuration, and a driver.
4. A clean-machine build and the two native smoke tests on the admitted hardware.

These dependencies have now been assembled and validated on the source hosts:
- RTX: commit3429e2c49626c30e4a406a517a3e8a030aea9c7f,
  scripts/native_reproduction/rtx_bridge/README.md and
  benchmarks/rtx_native_bridge_20261026/RESULT.md.
- B570: commit41cb7504ece1f78109fde6895b10ffc56dff8ef1,
  benchmarks/b570_native_reproduction_v1/README.md and RESULT.md.

Both campaigns include real native stage/request replay and same-host fresh-
directory execution. RTX numerical DLLs remain pinned external dependencies;
B570 numerical libraries are rebuilt from source. The complete bulk archives
remain separately held. See ../followup_20261026/ for compact evidence and
source pins. The tests in this CPU subdirectory still launch no GPU execution.
