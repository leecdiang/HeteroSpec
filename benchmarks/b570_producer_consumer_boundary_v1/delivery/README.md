# Evidence delivery

The private repository's [B570 boundary evidence release](https://github.com/leecdiang/HeteroSpec/releases/tag/b570-producer-consumer-boundary-v1-20261029)
holds six ZIP archives (`01`, `02A`–`02D`, `03`), `MANIFEST.json`, and `PACKAGE_RECEIPT.json`.
Repository access is required. `ACCESS.json` pins the release asset IDs, sizes,
SHA256 hashes and authenticated API addresses. Models and numerical DLLs are
excluded; the original PR148/150 dependencies remain separately pinned.

Download all six ZIPs and check their SHA256 hashes against `ACCESS.json`.
Extract them into the same new directory; their duplicate `MANIFEST.json`
entries must agree. Verify every manifest member's size and SHA256. There are
6,826 unique members. Preserve the complete ledger and all payloads, including
the numerical counterexamples.

To rebuild the results without any model execution, run from the extracted root:

```powershell
python source-freeze/benchmarks/b570_producer_consumer_boundary_v1/analyze.py --plan freeze/FROZEN_PLAN.json --records run-primary/REQUESTS.jsonl --payload-root run-primary/raw --reference-root $referenceRoot --out fresh-cpu-audit
python analysis-tools/run_summary.py --plan freeze/FROZEN_PLAN.json --records run-primary/REQUESTS.jsonl --payload-root run-primary/raw --analysis fresh-cpu-audit --out fresh-state-summary
```

`$referenceRoot` is the original PR148/150 reference payload directory; its
release pins are in `delivery-notes/REFERENCE_ACCESS.json` inside the package.
The frozen source tree retains its historical pre-execution documentation;
`review/RESULT.md` contains the completed scientific report. Later delivery-only
wording in the repository does not alter the frozen native experiment.

`ROUNDTRIP.json` records authenticated download and every-member byte checks.
`CPU_READBACK.json` records exact reproduction of all eight analysis/result
files from that downloaded copy. This is a same-account, same-machine remote
delivery and CPU audit, not a second-machine native qualification.

Transport recovery is recorded separately in `TRANSPORT_RECOVERY.json`.
Transport retries do not add model requests or change the primary ledger;
the native experiment remains exactly 152 requests with zero model-request retries.
