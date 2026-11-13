# Proposed Fig. 5: include the same-panel speculative control

This addition restores a contrast that is already present in the public result
summaries but absent from the four-control application figure in paper PR #222
(`e8a4981ef7db8f05cff7144fd4edc6e5a4109343`). It is a proposed review figure in
research PR #221, not a new performance experiment or a manuscript modification.

## What the recovered contrast establishes

The candidate is `L_P_D4`; the added control is `W_L4_D4`. Both use the D4
speculative workload. Their difference includes **both cut scope and projection
execution**. Consequently, this is a same-panel system increment over a strong
speculative control, not an isolated packing or cut estimate.

| A5000 deployment | Control mean resident service | Candidate mean resident service | Time reduction | Published adjusted 99% interval, expressed as time reduction |
| --- | ---: | ---: | ---: | ---: |
| Qwen3-8B | 2.272642 s | 2.226927 s | 2.0116% | 1.4441%–2.4411% |
| Qwen3-14B | 3.464285 s | 3.426847 s | 1.0807% | 0.8310%–1.2824% |
| Llama-8B | 2.563052 s | 2.522963 s | 1.5641% | 1.1548%–1.8320% |

The point estimates are recomputed from the original totals. The intervals and
all 220 root-level ratios are retained from the published summaries; this script
does **not** regenerate a bootstrap from absolute per-root times. The figure
contains 15 contrasts rather than 12. The fifth control was already one of the
five contrasts in the source's multiplicity-adjusted family; it is not a newly
selected test with a new unadjusted interval.

The Qwen3-8B D4 arms were measured in one fixed relative order. Its interval
conditions on the measured panel and does not remove order confounding.
Qwen3-8B and Qwen3-14B reuse the same 16 root identities. Neither three model
deployments nor the displayed 44 root instances should be described as 44
independent new tasks. Balanced factorial experiments remain necessary for
component attribution: PR #204 for the 8B study and PR #208 for the 14B study.

The full worker lifecycle is a separate quantity. From the original worker
summaries, the candidate/control reductions are approximately 1.9142%, 0.2118%,
and 1.3367%, respectively. These values include initialization and warmup and
have no newly derived confidence interval. The Llama worker totals in the paper
input are rounded. Do not label these values as production cold-start latency,
TTFT, or per-request resident service.

## What remains missing

These fixed summary projections do not contain a matched per-phase decomposition
of the two D4 arms. This addition therefore leaves that part of the reviewer
request open. It does not subtract timings from separate trials or combine the
balanced factorial, clean service, and heavy observation panels to manufacture
a cost stack. The next service experiment needs a predeclared decomposition
whose phases partition the **same** request interval; observer overhead must be
separately qualified before interpreting small changes.

For the requested 5% goal, define the primary endpoint explicitly as a **5%
reduction in resident service time relative to the same strong speculative
control**, with controller overhead included. This is different from a 5%
throughput speedup. If the present ratios were repeatable in a new matched
panel, the additional reduction needed relative to the current candidate would
be `1 - 0.95 / current_ratio`: 3.0498%, 3.9622%, and 3.4905%, respectively.
These are algebraic requirements, not forecasts or evidence that the target is
reachable. They cannot be added directly to the percentages in the table.

## Reproduce

Requires Python 3, NumPy, and Matplotlib. From this directory, download the four
public inputs without modifying them; the generator verifies the pinned Git
blob SHA and records the exact size and SHA-256 before deriving anything. Save into a fresh directory
and run with a fresh output path:

```sh
python3 - <<'PY'
from pathlib import Path
from urllib.request import urlopen
from replot_service_controls import SOURCES

destination = Path('source_snapshot')
destination.mkdir(exist_ok=False)
for name, (_, commit, repository_path) in SOURCES.items():
    target = destination / name
    target.parent.mkdir(parents=True, exist_ok=True)
    url = ('https://raw.githubusercontent.com/leecdiang/HeteroSpec/'
           + commit + '/' + repository_path)
    with urlopen(url) as response:
        target.write_bytes(response.read())
PY
python3 replot_service_controls.py --sources source_snapshot --out reproduced_01
```

The supplied outputs are in `replot_01/`. `RESULTS.json` binds the source identities
and analyzer; `FIGURE_CHECK.json` records text bounds and plotted point counts.
The independent review records figure file identities. Visual inspection was
performed separately. Rendering checks
do not constitute statistical validation or verification of the full manuscript
layout.

## Proposed caption

**Resident service time relative to five fixed controls on A5000.** The candidate
is LOCAL-packed D4. Blue contrasts compare it with target-only controls; orange
adds the same-panel WHOLE-loop4 D4 speculative control. Diamonds show ratios of
totals, lines retain the published family-adjusted 99% intervals, and faint
points show every reported root ratio. Orange contrasts change cut and
projection together. The Qwen3-8B D4 arms retain one relative order, so their
intervals do not account for temporal order bias. The three deployments do not
establish generality beyond the measured request and execution contracts.

## Primary source links

- [Paper input and original four-control figure](https://github.com/leecdiang/HeteroSpec/tree/e8a4981ef7db8f05cff7144fd4edc6e5a4109343/papers/reference_compatible/20261111_tpds_mainline_rewrite)
- [Qwen3-8B result summary](https://github.com/leecdiang/HeteroSpec/blob/592abdfe9267fd97ecbde18cd0ee9a1bfc319e20/benchmarks/linux_transfer_v1/results_ampere_20261107/RESULTS.json)
- [Qwen3-14B result summary](https://github.com/leecdiang/HeteroSpec/blob/0e9bb82432dc0a860a43ab9ba1c034f41176fe05/benchmarks/server_expansion_v1/D14/results_complete_20261108/RESULTS_REPRODUCED.json)
- [Llama-8B result summary](https://github.com/leecdiang/HeteroSpec/blob/8990a80da23f75c071d6d161c8c79a2dc1347bd7/benchmarks/server_expansion_v1/F/results_confirmation_20261108/RESULTS_REPRODUCED.json)
