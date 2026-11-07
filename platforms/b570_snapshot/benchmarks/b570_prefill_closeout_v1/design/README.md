# B570 final paper closeout

**Design and CPU tools only. No model/GPU process has been launched.**

Read [PROTOCOL.md](PROTOCOL.md), then give [HOST_PROMPT.md](HOST_PROMPT.md) to the platform agent. Fill `REGISTRATION_TEMPLATE.json` with exact host identities, input/order manifests, reservations and author authorization before any native start. The template intentionally fails validation; merging this PR does not supply missing execution authority.

CPU commands:

```sh
python -B -m unittest test_toolkit -v
python -B toolkit.py B570
```

`toolkit.py` generates symbolic timing slots and checks normalized primary panels. It never loads a backend or launches a child process. The 16 tests cover both configurations, counts, order, paired warmups, missing/duplicate/bad results, nonfinite data, A/A imbalance and session reversals. They are not a production native runner, raw-data auditor or GPU qualification. The host must bind actual records and independently verify raw-to-normalized values before using the estimator.

There is no calendar deadline and no success-dependent extension. The allowed scientific matrix has a finite request/process ceiling; final safety timeouts and storage/memory/time budgets must be declared from the actual machine before execution. A counterexample, qualified negative, unresolved small effect or engineering block is an acceptable closeout. The result belongs in a separate result PR, with all failed/unstarted slots retained.
