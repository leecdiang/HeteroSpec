# Additive endpoint and packaging clarifications

The frozen implementation stores the existing native `endpoint` field as the
termination reason, EOS or limit. Complete array equality already includes the
committed length and terminal token. To make the separate stop boundary explicit,
BOUNDARY_COMPARISONS.json adds the tuple (length, reason, terminal token ID),
reconstructed by a supplementary CPU parser from all 171 selected raw logs.

U2/N1: reason 57/57, full boundary 57/57, joint array/boundary 57/57.
U2/N0 and N0/N1: reason 57/57, full boundary 54/57, joint 51/57.
The three unequal boundaries are /15's 25-versus-28-ID EOS outputs. /25 differs
in IDs while retaining 75-ID EOS boundaries. No length difference is hidden behind
the reason-only count. These are additive post-matrix definitions/tables, not a
replacement of a frozen outcome rule, execution repair, retry or new protocol run.

The frozen package builder omitted suffixless `.gitignore` from its inventory.
Before any delivered archive was built, an additive delivery builder was introduced
to include every freeze-bound file and the copied JSONL ledger. The original frozen
code is preserved. No numerical code, argv, capture, selected attempt, or denominator
changed. The final archive has 2,276 logical files; later reports, this supplementary
boundary audit, and delivery receipts are separate Git objects. The archive snapshot
contains the earlier explicitly labelled reason-only table; the final Git report
also includes the strict boundary column. Both reconstruct the same primary arrays
and joint counts.
