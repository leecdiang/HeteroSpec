# 358H draft-device characterization

Formal Track-L latency is telemetry-OFF. CPU Track-E duration is used only for energy integration.

- CPU ctx 512: host median 1424.260 ms, TTFT 11.315 ms, TPOT 11.127 ms, 89.868 tok/s, energy 0.30487761383696144
- CPU ctx 2048: host median 1972.738 ms, TTFT 14.988 ms, TPOT 15.420 ms, 64.849 tok/s, energy 0.5194851206156428
- CPU ctx 8192: host median 4152.863 ms, TTFT 31.650 ms, TPOT 32.460 ms, 30.807 tok/s, energy 1.1962086489550983
- NPU ctx 512: host median 1615.697 ms, TTFT 220.273 ms, TPOT 10.985 ms, 91.036 tok/s, energy NOT_ADMISSIBLE
- NPU ctx 2048: host median 2154.208 ms, TTFT 456.806 ms, TPOT 13.346 ms, 74.926 tok/s, energy NOT_ADMISSIBLE
- NPU ctx 8192: host median 6384.705 ms, TTFT 3744.492 ms, TPOT 20.797 ms, 48.083 tok/s, energy NOT_ADMISSIBLE

NPU energy: NOT_ADMISSIBLE.

