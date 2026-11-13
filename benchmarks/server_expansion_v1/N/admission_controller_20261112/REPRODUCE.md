# CPU reproduction and static native build

Use the exact successor plus its pinned PR228/226 ancestors. Python3.10, a Linux
C++17 compiler, readelf and Node for the independent differential are sufficient
for CPU tests. None of the recipes needs a model, tokenizer invocation, CUDA
initialization or a native worker execution.

From this directory, use a fresh short absolute output directory for each test:

    python3 -B test_controller.py --out /tmp/hs-controller-your-unique-id
    python3 -B -O test_controller.py --out /tmp/hs-controller-opt-your-unique-id
    python3 -B test_resources.py --out /tmp/hs-resource-your-unique-id
    python3 -B -O test_resources.py --out /tmp/hs-resource-opt-your-unique-id
    python3 -B -m unittest -v test_stage_verify.py
    python3 -B generate_manifest.py --out /absolute/fresh-plan.json
    python3 -B run_client_tests.py --out /tmp/hs-client-unique-id
    python3 -B run_launcher_tests.py --out /tmp/hs-launch-unique-id

The final staged consumer suite takes several CPU minutes. It generates
artificial source-labeled zero tensors and reads every required raw scalar;
its incremental role prefixes cover27+81+72+81 different provided-file checks.
It creates no runtime/model context. Small unit temporary inputs are generated
from source; final logs, source epochs and retained differential fixtures are
indexed in CPU_EVIDENCE/ and audit/.

run_client_tests.py and run_launcher_tests.py expose their exact compiler/test
options in their argparse help and saved receipts. They compile only the
standard-library/POSIX mock sources and inspect every mock's NEEDED list before
execution. Real-linked R/loop4 artifacts and the closed launcher artifact are
never used as selftests. Their compilation/source identities and flags are
recorded under CPU_EVIDENCE/native_wiring_01/.

test_interop.py requires the exact separately compiled standard-only client_probe
and its SHA. It checks that digest, size and standard-library-only dependencies
before execution. A stdin barrier lets the Python controller bind the actual
owned child PID/start/boot and lease. Its8 request/row events are synthetic
accounting; it never compares a real model state or completes an R stage.

make_worker_descendant.py derives the new worker from the full frozen PR228
worker with exact identity/count-checked substitutions. build_descendant.py
requires the original full Linux sources, numerical archives and pinned
parser-only objects audited on the actual A5000 host. It compiles/links and
uses nm/readelf only. Those large backend/model/system dependencies are not
substituted by the public CPU packet. Never execute the resulting native ELF,
including help, denial, ABI or a model/vocabulary selftest.

The public packet's strict restore checks every path, UTF8 payload length and
SHA before writing. Such readback proves public file bytes only. It does not
repeat native execution, validate loaded libraries, activate resource limits,
grant allocation or turn261 NOT_RUN statuses into native PASS.
