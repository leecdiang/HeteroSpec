# RTX merge ledger — 2026-10-18

Explicit user request: consolidate PR120–123 evidence and merge RTX PRs.
Merged research evidence into main with merge commits; original scientific heads
remain addressable. No experiment UUID was restarted and no qualification status
was changed by merging. Historical “keep Draft/no merge authorization” statements
remain historical records; the current user instruction authorized these merges.

## Scope and pre-merge checks

All ten open RTX PRs were included: independent PR104/110, then dependency chain
PR113→114→116→118→120→121→122→123. Child PRs were retargeted to main only after
their predecessors merged. B570 PRs and paper PR102 were not included.
All changed-file inventories were enumerated: only added benchmarks/ or relevant
docs/experiments/ files; no production-code modifications/deletions.
Review submissions and inline threads were empty; no check runs/status contexts
were registered for the scientific heads. An empty pending status is not a
successful CI run. main was unprotected; no protection rule was bypassed.
Each merge used the inspected expected head SHA. Research results were reviewed
from committed reports and relevant compact tables; this was not a fresh raw audit.

| PR | Scientific head | Merge commit |
|---|---|---|
| [#104](https://github.com/leecdiang/HeteroSpec/pull/104) | f997262d6b0accb126a1217c9356745cc8bbf708 | 92c764cc5ddffcfee15211f56f02a8960f07233f |
| [#110](https://github.com/leecdiang/HeteroSpec/pull/110) | dae5aea9f9009a686196dd89981c0ae9699ae612 | 4e00c863199a28aba2defbd54e1ee88b2bcfd1bc |
| [#113](https://github.com/leecdiang/HeteroSpec/pull/113) | 64a9feb7b7086ccfde1a98b9514edd812116aa7f | 1d5ccf70a8e27e6daf6b86c8023cf1c617145c27 |
| [#114](https://github.com/leecdiang/HeteroSpec/pull/114) | 449ead854424a1ac88d538332994bcf9f8813e1e | 5d30d2017e604cad399bcccf3b3e946a7f61120c |
| [#116](https://github.com/leecdiang/HeteroSpec/pull/116) | 2b5ed1552263907df3adfdff9b0121d115734a6c | 46fa3524b7dc9dc10c14daef58f0fc603055f4ff |
| [#118](https://github.com/leecdiang/HeteroSpec/pull/118) | 8a4cbb4246323a3f159f94cae8c92544d5a215dc | bbce4ca08f386d2db44a08221ecef3b6269002ac |
| [#120](https://github.com/leecdiang/HeteroSpec/pull/120) | c6eb66368bc876332afe82f9df5ea51fe0b4b5ec | a8a7ad04cdd22d20447ce713a4b8102eb99c24a3 |
| [#121](https://github.com/leecdiang/HeteroSpec/pull/121) | d82ec4097adfa032886040e075e71e41cfeb5855 | 98585471a5d7360057f80ca63107c7cbe34d94c7 |
| [#122](https://github.com/leecdiang/HeteroSpec/pull/122) | a1f15bfc8222054aa7b94b40f41af0dd0492ddab | ecee74b6465fcfb29288efa1c400be28784b56d3 |
| [#123](https://github.com/leecdiang/HeteroSpec/pull/123) | f38ed240d904db09e121bf50158cd207e829a12f | f2e5fdfb814f9acaa22efd9cc6bd416a4edaaf73 |

SOFTWARE_FIRST/HOLD remains. Partial panels, qualification failures, engineering
stops and local-only raw limitations remain unchanged. No new raw data were added
by this synthesis. Pre-existing historical artifacts were preserved without
rewriting their commits. No branches deleted, releases or GPU runs initiated.

Evidence synthesis is delivered separately in this directory; its merge receipt
is available from the synthesis PR itself, avoiding a self-referential commit hash.
