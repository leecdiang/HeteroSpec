# B570 Ledger Anonymity Audit — v0.8.3

| Field | Rating | Reason |
|---|---|---|
| Prediction-file content SHA-256 | SAFE | Identifies bytes without directly identifying an author; check publication links before release. |
| Reserved task IDs | SAFE | Benchmark identifiers, with no personal identity. |
| Sequence lengths | SAFE | Result metadata. |
| Truncated per-sequence digests | SAFE | Inspectable fingerprint; full digests stay in the artifact ledger. |
| Event ordering | SAFE | Relative sequence of recorded events. |
| Exact UTC timestamps | REVIEW | May link an anonymous submission to public commits or posts. |
| Git commit SHA | DO NOT EXPOSE | Searchable public commit may reveal author identity. |
| Repository URL | DO NOT EXPOSE | Direct author identity link. |
| Username | DO NOT EXPOSE | Direct identifier. |
| Local path | DO NOT EXPOSE | May contain a username or organization. |
| Machine hostname | DO NOT EXPOSE | May identify a person or institution. |
| Public artifact URL | DO NOT EXPOSE | May reveal repository ownership or author. |
| Identifying branch name | DO NOT EXPOSE | Searchable repository linkage. |

This is a field-risk audit, not a final PDF selection. A file digest proves content identity, a Git marker binds bytes to repository history, and recorded times support ordering. None alone cryptographically proves when the material became public.
