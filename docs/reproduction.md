# Reproduction

1. Clone the repository and create an isolated Python 3.11 environment.
2. Install the applicable file under `requirements/`.
3. Obtain model weights and upstream benchmark data independently and set the `HETEROSPEC_*` environment variables.
4. Run device gates before experiments. Do not silently fall back between devices.
5. Generate processed CSVs and figures with the tracked analysis scripts.

Raw model and telemetry assets are intentionally not included.

