# Completed-experiment integration audit — 2026-11-11

## Preservation contract

Baseline main: `cfc9edf4582bb3c02885c9171a2ab2635bf19588`.
Recovery branch: `audit/pre-experiment-merges-20261111-cfc9edf4`.

The author requested review and integration of completed experiments that remained Open. Integration preserves original scientific commits and uses ordinary merge commits. Completed negative and engineering-blocked results remain evidence; integration does not upgrade their scientific conclusions. Running experiments, unfinished candidates and manuscript PR220 remain separate.

Existing main files are retained while reviewed experiment directories are added. The historical RTX JSA closeout additionally requires additive .gitattributes rules. Original numerical references, private/raw access limits, unsuccessful runs and complete costs are retained. No new GPU experiment is performed by this integration.

## Shared analyzer conflict

PR204 adds optional worker-order validation to `benchmarks/server_expansion_v1/shared/experiment.py`; its Git blob is `b934ad3a1ec545a343b11c117a51dc20286c295b`. The common main helper retains this reviewed version.

PR205, PR206 and PR208 bind the older analyzer. Its exact original bytes are preserved at `legacy_shared/experiment.py` in this directory:

- Git blob: `84b83ff6c743ab2169e22187d03697cbfeb5a897`
- SHA256: `8b1d0f7b794132bf5a33208d5c85124246bd112685f8bf33283156b70d7b0887`

The original replay scripts intentionally check that complete file hash. Their guards are unchanged. To reproduce a historical experiment, use a clean detached checkout/worktree at the original scientific head and follow that snapshot's replay README; do not run the old replay against a substituted current helper.

| Result | Original reviewed scientific head |
|---|---|
| PR203 Linux Ampere | `592abdfe9267fd97ecbde18cd0ee9a1bfc319e20` |
| PR204 M1 attribution | `55f501e9a93013a4b4d82cc4967e82b8d9054a81` |
| PR205 Llama | `8990a80da23f75c071d6d161c8c79a2dc1347bd7` |
| PR206 14B six-arm | `0e9bb82432dc0a860a43ab9ba1c034f41176fe05` |
| PR208 14B factorial | `44ef9b6654cfe3a800059d7311f8ecf73ffd8983` |

For example, `git worktree add --detach /tmp/heterospec-pr205-replay 8990a80da23f75c071d6d161c8c79a2dc1347bd7` restores the exact source snapshot, including its original shared analyzer. The archived analyzer also permits direct byte/hash comparison without changing any historical source file.

## Verification scope

The review checked complete PR path/blob inventories, fixed runtime source identities, available public numerical summaries and request tables, and relevant existing CPU tests. GitHub check/status absence is not a CI pass. Private complete GPU captures were not independently downloaded or regenerated. Scientific qualification remains tied to each original deployment and commit.

## Completed integration result

See [RESULT.md](RESULT.md) for the completed merge list, retained PRs and preservation evidence, and [RESULT.json](RESULT.json) for all 71 original/current heads and machine-readable dispositions.
