# Source-only numerical reconstruction

The original execution entry is a verified **same-host cache continuation**.
`source_materials.py` additionally captures the complete actual pristine-R and
qualified-candidate numerical source trees, shared S3 frontend, generated header
inputs, original compile/link recipes, compiler identities and installed SDK
dependency hashes. It contains no old numerical object, archive, ELF, model or
oracle as a build input. The model's exact licensed acquisition remains separate.

The source archive is supplementary reconstruction material, not another GPU
qualification or performance run. Review its immutable `RECIPE.json` and archive
index before executing its compiler commands. Do not replace either source tree
with a moving upstream checkout. Uncompiled upstream HTTP/audio examples with
RFC1918-shaped literals are withheld with hashes; none is a compiler input.
Path-templated CMake installation receipts are provenance only, never installed.

After strict archive replay, set `SOURCE` to its restored directory, `NEW_OUT`
to a fresh build directory, and `TOOLS` to a JSON object mapping `${TOOL_n}`
markers to installed executables. Keys and exact executable SHA-256 values are
in `RECIPE.json`; no tool download or version substitution is automatic. System
CUDA12.5, GCC11, NCCL and other SDK files must exist at their recorded paths with
the recorded hashes. This entry does not provision a clean operating system.

```sh
python -B cold_rebuild.py --source "$SOURCE" --out "$NEW_OUT" \
  --tools "$TOOLS" --cpus 34,35
```

The default validates every captured source, tool and external dependency and
expands all 735 compiler/archive/link steps; it runs zero compilers and zero model
requests. It refuses existing output. The two authorized CPU cores are examples
for the original host; select actually authorized cores on another host.

Full source compilation is explicit and bounded to two concurrent translation
units, 30 minutes per command and six hours overall. It stops on failure without
retry. A build on the experiment host must wait for the terminal S3 state and its
controller-close receipt and take the same shared activity lock:

```sh
python -B cold_rebuild.py --source "$SOURCE" --out "$NEW_BUILD" \
  --tools "$TOOLS" --cpus 34,35 --execute \
  --stage-state "$S3_STATE" --activity-lock "$STUDY_ACTIVITY_LOCK"
```

On a separately allocated idle host, use `--isolated-host --execute` instead of
the original host's state/lock. All stdout/stderr, expanded commands, step costs,
failure and output hashes are saved. `CUDA_VISIBLE_DEVICES` is empty; neither
rebuilt executable is run. Successful compilation is explicitly **unqualified**:
fresh independent R, full numerical/state/physical checks, resource/budget gates
and prospective freezes are still required before another GPU experiment.

The original experiment's qualified binary hashes and oracle remain unchanged.
Relocation can change build paths and ELF hashes, so a source reconstruction is
not claimed to reproduce an old ELF byte for byte. Public saved-data replay and
independent statistical recomputation do not constitute independent GPU replay.
