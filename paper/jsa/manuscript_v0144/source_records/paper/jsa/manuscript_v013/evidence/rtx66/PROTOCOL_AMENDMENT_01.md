# Identity-stage clarification, before new cost comparisons

Read-only inspection of the frozen analyze_bcd.py confirms the historical bootstrap seed is **20261005**, not the tentative 5070 named conditionally in PROTOCOL.json. Historical replication will use random.Random(20261005), random.choices, 4000 draws, sorted indices 99 and 3899. The new seed20261008/10000/linear-quantile protocol is unchanged. No comparison, task or timer has changed and no new scalar-reference cost result has been read.

The first schema-inspection command successfully authenticated 384 records and then found that the system Python lacks NumPy. Use the bundled workspace analysis runtime; this is an infrastructure lookup, not an experiment attempt or scientific retry.
