# Observed cause of attempt1 admission failure

Attempt2 qualification for HumanEval/38 records both:

- `Qcur-0`: shape [128,16,1,1], query axis2 =1.
- `Qcur-0 (view) (permuted)`: shape [128,1,16,1], query axis1 =1 and head axis2 =16.

Attempt1 matched all names starting `Qcur-` and took the maximum of axis2. It therefore combined incompatible layouts and counted the permuted head dimension as query count. It failed closed before the request record was returned. The retained97 raw vectors matched the reference in a postfailure diagnostic, but this does not promote that failed attempt.

Attempt2 observes only `kq-` MUL_MAT outputs, where query is axis1, and persists the Qcur/kq metadata before admission. The first input observed5068 such nodes =181 prompt tokens ×28 draft layers, all q=1. This change repairs instrumentation; numerical submission code and runtime DLLs remain unchanged. All original inputs must pass anew before cost measurement.
