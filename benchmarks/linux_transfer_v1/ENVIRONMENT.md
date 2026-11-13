# Local user-space environment

The read-only inventory and standard-library source/host tools use Python 3.11+
(recommended). Statistical analysis and the full test suite additionally use NumPy;
this authoring validation used NumPy 2.3.5. No Python package is installed by the
native execution runner.

After read-only inventory, use an existing approved environment or create a private
virtual environment rather than changing company system Python:

```sh
python3 -m venv "$HOME/.venvs/heterospec-linux-transfer"
. "$HOME/.venvs/heterospec-linux-transfer/bin/activate"
python -m pip install -r benchmarks/linux_transfer_v1/requirements-analysis.txt
python -m unittest discover -s benchmarks/linux_transfer_v1/tests -v
```

Use the company's approved package mirror or offline wheelhouse where required.
No sudo, global package upgrade or driver installation is authorized. If the
available Python is older, install an approved user-space interpreter or record
a tested compatibility adaptation; don't bypass validation to claim completion.

Native builds require CMake >=3.24, Ninja, a C/C++17 compiler, and an installed
compatible CUDA toolkit with nvcc. A driver reported by nvidia-smi does not prove
that nvcc exists. Exact compiler/toolkit versions are discovered and frozen on the
server. The build uses at most two compile jobs by default, four only within the
allocation. Tool changes after the numerical freeze require a new deployment
version and requalification. Git and an authenticated gh client are needed for
online acquisition; the source tool also accepts preapproved offline inputs.

The initial candidate source archive is about39 MB; the plan does not require the
1.27GB Windows runtime archive or multi-GB historical KV releases. Model weights
are independent, exact-hash inputs, and must not be silently requantized. Keep
corporate authentication, unrelated datasets and internal inventories out of the
published scientific artifact.
