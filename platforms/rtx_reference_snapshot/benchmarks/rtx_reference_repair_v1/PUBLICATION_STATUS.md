# Repository publication

This repair branch is now being published through the connected GitHub write tools,
not through the offline `publish_pr.py` helper.

- Repository: `leecdiang/HeteroSpec`
- Base branch: `codex/pr155-qwen14b` (PR156)
- Exact base commit: `47c93985010d0f3c0c55f975f4cd7761e64bcae2`
- New branch: `experiment/reference-repair-20261101`
- Intended pull-request state: Draft, unmerged

The pull-request record is authoritative for the actual PR number, head commit and
current state. Source/code, test fixtures and scientific protocol are unchanged
from the delivered repair ZIP. Only publication and handoff notes are synchronized
for repository use. The original CPU validation receipt describes the earlier
offline-delivery checkpoint, not the current remote state. The 90-test suite was
rerun successfully before publication.

Do not rerun the offline publisher on this branch. Fetch the existing repair branch
and follow HOST_PROMPT.md. No native model/GPU request, Windows worker build, old-PR
merge, reference mutation, or paper submission is performed by repository publication.
