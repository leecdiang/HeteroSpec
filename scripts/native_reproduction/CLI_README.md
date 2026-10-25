# Portable evidence inventory

This standard-library utility checks file integrity. It never launches a model,
calls a GPU or network service, or decides numerical qualification.

Stage the small source/patch, build instructions, native stage/request fixtures
and execution receipts you intend to hand over. Keep model weights, credentials,
machine caches and bulk run directories outside that directory. File selection is
explicit: each `--include` names one file relative to `--root`; nothing else is
scanned. Use forward slashes for portable paths.

```text
python scripts/native_reproduction/bundle_manifest.py create --root STAGED_BUNDLE --platform rtx --output STAGED_BUNDLE/manifest.json --include source.patch --include build.txt --include fixtures/stage.bin --include fixtures/request.json --include receipts/smoke.json --identity-json identity.json
python scripts/native_reproduction/bundle_manifest.py verify --root FRESH_COPY --manifest FRESH_COPY/manifest.json
```

Use `--platform b570` for that host. The filenames above illustrate the command;
select the actual files produced by the platform work. An existing output is never
overwritten; use a new filename or versioned bundle for a new inventory.

`--identity-json` is an optional JSON object. Suggested fields are `source_commit`,
`build_identity`, `model_identity`, and `device_identity`; their values can be
structured objects containing hashes and versions. Missing fields are reported as
`PARTIAL`, so preparation can continue. Supplied identities remain declarations;
the utility does not authenticate the build or infer a successful GPU run.

Verification reports all missing and changed selected files. It does not reject
unlisted files, so do not treat it as a privacy or publication-release checker.
Paths escaping the bundle, including external symlinks, are rejected. Hashes are
computed over exact bytes in 1 MiB chunks. Verification writes nothing.

Exit codes: `0` = inventory created / selected-file integrity passed; `1` = missing
or changed files; `2` = invalid input or I/O error. A failed inventory concerns that
bundle only: preserve its report, repair or complete the affected files, and
continue independent recovery work. It is not a global experiment-stop rule.

Tests:

```text
python -B -m unittest discover -s scripts/native_reproduction -p test_bundle_manifest.py -v
```
