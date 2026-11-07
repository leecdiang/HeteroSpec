# Offline evidence verification

Each arm has its own content-addressed `.tar.gz` under its new artifact directory. Check the archive SHA-256 against the neighboring `archive_manifest.json`, then extract it into an empty directory. Python 3.11+ and the standard library suffice for offline verification; no models, CUDA hardware or network are needed.

Run from the extracted archive root with bytecode-cache writes disabled (`-B`), so verification does not add files to the strictly checked inventory:

```text
python -B verify_prediction.py .
python -B verify_provenance.py . --arm prediction
```

For the B archive instead:

```text
python -B verify_latency.py .
python -B verify_provenance.py . --arm latency
```

The primary verifiers were frozen before scientific execution. They check the complete archive inventory and every listed file digest, the frozen source byte manifest, raw committed-ID events, commands, prompts, devices, coverage, schedules and scientific gates. B additionally recomputes all native timing intervals, prompt medians, geometric mean and 10,000-sample prompt bootstrap. A verifies the 90-reference engineering qualification, complete exposed discovery and lawful zero-reserved stop.

The supplementary provenance verifier was added after execution; it does not alter inference or the scientific estimators. It checks every retained run's source head against the remotely acknowledged joint execution commit, interval chronology/nonoverlap, R0 coverage, driver observation consistency and the complete A exposure-inventory digest. Its source and role are retained in both evidence packages.

On the original Windows host, adding `--asset-root D:/HeteroSpec-PC` enables byte rehashing of the recorded external model/dataset/runtime paths, and the supplementary verifier also rehashes the recorded driver modules. This flag enables checks against recorded absolute paths; it does not remap those paths. External weights and binaries are deliberately omitted from the archives.

Reports and native runtime records retain UTC timestamps. The final repository `chronology/closeout_checkpoints.json` records report/verification and archive commit receipts after those commits exist. Its archive-contained snapshot predates the packaging commit, avoiding a self-referential archive digest. The draft PR identifies the final closeout commit. Old scientific evidence and manuscript files remain unchanged.
