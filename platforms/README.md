# Reviewed platform snapshots

The author authorized integration of reviewed experiment chains on 2026-11-07.

- RTX scientific tip: `873d16712fbf3bc04f54e9b3753515c5dbebb60f` (PR195), merged into the root layout without altering its original commit.
- B570 scientific tip: `0575a34a88acff8298191e172205bf8726fe4174` (PR194). Its **complete original root tree** is preserved at `platforms/b570_snapshot/`, Git tree `3613fd0ff4f0cbec904d24a586ae6f4e36a231d5`.

This is an intentional namespace conflict resolution. Both hosts used `benchmarks/tpds_phase1_v1/RESULT.md`, `PLATFORM.json`, `SOURCE_AND_BUILD.json` and other same-name files for different executed studies. Choosing one report over the other would destroy the other platform's visible evidence. The root remains RTX-oriented; the B570 snapshot retains its own relative repository layout and every original blob. Git deduplicates identical blob objects. A snapshot is not a new execution, requalification, combined runtime, or paper revision.

For exact historical replay, use separate worktrees rather than mixing the two trees:

```sh
git worktree add --detach ../heterospec-rtx195 873d16712fbf3bc04f54e9b3753515c5dbebb60f
git worktree add --detach ../heterospec-b570194 0575a34a88acff8298191e172205bf8726fe4174
```

Frozen releases, references, ledgers, failed results and manuscript releases remain unchanged. Reproduction scripts can contain original-host paths; follow their own documented binding steps. The upcoming Linux experiment is a new isolated deployment, not permission to execute old Windows programs unchanged.

Unqualified contract/enforcement, masked-MMA and CPU-only prototype branches are not adopted as production numerical implementations. Historical design notes remain historical; status labels are not upgraded by this integration.
