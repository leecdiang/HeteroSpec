# Packaging-only correction

The first A archive's extracted-copy check failed because importing `verify_common` created `__pycache__` files inside the extracted tree. These generated files were absent from the strict archive inventory. This exposed a verifier invocation requirement, not a scientific record discrepancy.

The first package, archive and failed extraction are retained locally in `work/prediction-packaging-attempt1/`. Final packaging runs the unchanged frozen archive builder and scientific verifiers with `PYTHONDONTWRITEBYTECODE=1`; offline reproduction uses `python -B`. No runner, timer, hypothesis, estimator, raw inference or scientific denominator changed, and no scientific run was repeated. The final two archives independently pass complete inventory, file digest and scientific verification on clean extracted copies.
