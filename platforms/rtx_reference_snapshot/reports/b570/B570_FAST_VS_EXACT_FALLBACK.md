# B570 Fast Path versus Exact Fallback

| Path | Correctness | V2(512) | V2(2048) | Speedup GM | Board-energy ratio |
|---|---:|---:|---:|---:|---:|
| Fast path | 45/90 pairs | 1.2426 | 1.6373 | 0.5383 | 0.6961 |
| Serialized fallback | 60/90 pairs | 1.9827 | 1.9917 | 0.3087 | 0.3023 |

Fast-path timing remains diagnostic because its correctness gate failed. Serialized-fallback timing is globally admissible only when all 90 normalized pairs are exact.
