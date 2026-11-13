# M study and completed Linux M1 result

The [A5000/Linux M1 result](results_ampere_m1_20261107/README.md) contains the
completed balanced four-arm D4 panel, native qualification, actual projection
witnesses, full costs, retained failure and reconstruction material. M2 was not run.

Read PLAN.md and HOST_PROMPT.md, then ../shared/COORDINATION.md and ADAPTER.md for
the authoring protocol. `study.json` retains its prospective authoring status;
actual execution status is in the independent result directory. The runtime and
unchanged independent R bind qualified PR203, not design-only PR196. See
[M1_REBUILD.md](M1_REBUILD.md).

```sh
python3 -m unittest discover -s benchmarks/server_expansion_v1/shared/tests -v
```

Shared helper tests are distinct from the actual native proofs and measurements.
