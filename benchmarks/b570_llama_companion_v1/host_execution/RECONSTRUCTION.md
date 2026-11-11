# Reconstructing the B570 evidence

The result release is a content-addressed archive. `MEMBERS.json` preserves each included logical path, byte count and SHA256; `INDEX.json` maps each unique object to a ZIP part. Identical bytes are stored once, without discarding their original paths. Obtain every asset listed by `DELIVERY_ASSETS.json` through authorized repository access. Model weights are separate inputs with exact SHA256 identities in the evidence; they are not distributed in the archive.

The Python helpers require only the standard library. Verification and reconstruction execute no model forwards and require no GPU.

```powershell
python -B object_archive.py verify --root <downloaded-assets>
python -B object_archive.py restore --root <downloaded-assets> --out <new-restored-root>
```

The restore destination must not exist. Verification checks every ZIP part, every decompressed unique object and the complete logical mapping. Restoration writes the exact archived bytes. `MEMBERS.json` also records explicit exclusions: separately published historical transport, reproducible build intermediates and preparation dependencies. Source, native runtime binaries, build logs, failures, raw numerical records and the inference ledger are retained.

For a smaller reconstruction containing the final qualification/cost evidence and all native ledger receipts, use:

```powershell
python -B object_archive.py restore --root <downloaded-assets> --out <new-restored-root> --prefix combined-epoch-03 --prefix UNSEEN_PANEL-00.json --prefix research --prefix freeze-code-00 --tail /RECEIPT.json --tail /SUPERVISOR.json --tail /native/result.json
python -B independent_qualification.py --epoch <new-restored-root>/combined-epoch-03 --panel <new-restored-root>/UNSEEN_PANEL-00.json --out <new-output>/QUALIFICATION.json
python -B independent_cost.py --epoch <new-restored-root>/combined-epoch-03 --panel <new-restored-root>/UNSEEN_PANEL-00.json --out <new-output>/COST.json
python -B independent_ledger.py --root <new-restored-root>/research --original-root I:/HeteroSpec/b570-llama-20261102 --relocated-root <new-restored-root> --out <new-output>/LEDGER.json
```

Selection affects restored paths only: every archive object is still verified. The qualification auditor independently reconstructs endpoints, transactions, observer controls, the complete rectangular matrix, every committed scalar-reference vector and full PQ/QB correspondence including rejected rows. The cost auditor independently reconstructs all six Williams periods, every warmup and measurement, reference endpoints, complete process accounting and the predeclared layout screen. The ledger auditor verifies its hash chain and reconciles every native completion, failure, reserved slot and process-cleanup receipt.

Use fresh output paths; these tools do not overwrite previous results. Compare reconstructed reports byte-for-byte with the corresponding published local reports. The remote delivery receipts state the exact scope of the performed readback. Authenticated fresh downloading and reconstruction on the B570 host is not independent third-party replication or anonymous-access verification.
