# Q4 experiment entry

Read PLAN.md and HOST_PROMPT.md first, then ../shared/COORDINATION.md and ADAPTER.md.
This PR includes the same versioned shared tools as its sibling study PRs. Each
study lives in a separate directory and binds the actual qualified Linux successor;
the running PR196 tree is never changed by this package.

```sh
python3 -m unittest discover -s benchmarks/server_expansion_v1/shared/tests -v
python3 -m unittest discover -s benchmarks/server_expansion_v1/Q4/tests -v
```

The tools do source/data planning, model-header inspection and complete-record
analysis. They are not a compiled CUDA adapter or a successful model experiment.
Use study.json's prospective panel after the relevant native gates; a JSON `k`,
context or type declaration is not evidence the implementation has changed.
