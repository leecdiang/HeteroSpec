# CPU reproduction evidence

`reproduction_01/STATE.json` is the terminal PASS from the first execution of `run_cpu_tests.py`. It rebuilt and ran eight standard-only synthetic programs in35.427 seconds using one compiler at a time. Component tests passed52 normal/52 NDEBUG, private IPC17/17, independent budget8, Session12, raw-file helper5 and active-KV host helpers194. All eight ELF dependency whitelists passed before the first test executable ran. Real model/backend/context/placement/forward calls and real native-linked executable invocations were zero.

Every compiled source/header and executable identity, command, result, raw stdout/stderr digest and public path-only redaction is recorded. Empty log files are preserved as zero bytes. `RUNNING.json` is the immutable initial marker; the terminal state is `STATE.json`. Partial synthetic files and the provided large synthetic journal fixtures remain in the original private fresh output directory; they are recreated by the tests and are not native captures.

On Linux with Python3.9+, g++ and readelf, run from this successor directory:

```
python3 run_cpu_tests.py --out /tmp/hs-n227-cpu-repro-your-unique-id
```

The output path must be absolute, fresh and short enough for private UNIX sockets. The runner refuses non-allowlisted source/includes, native/loader API calls, extra dynamic dependencies, missing tools, old output paths or unexpected counts. It runs no native build or model/vocabulary helper. Timeouts stop only its own compiler/mock process group, retain all outputs and never retry. A missing compiler is an explicit precheck failure, not an instruction to install software or fall back to another runtime.

These are CPU implementation checks and provided-byte tests. They do not establish native numerical/state qualification or authorize GPU execution.
