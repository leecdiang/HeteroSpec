# Manuscript asset synchronization status

Draft PR #220; author-owned source SHA256:
`e56013eace463b0615cf69dd130155b90bd2a26385286029891904689084f78b`.

The directly synced LaTeX entrypoints, seven main sections, TikZ diagrams, bibliography and typography files match the 2026-11-11 author ZIP at Git-blob identity. Other assets must still be imported before this branch is independently buildable; **a README is not a substitute for the missing figures and data**.

Run from a clean checkout on `paper/recovery-final-20261111`, with the provided author ZIP saved locally:

```bash
python3 papers/reference_compatible/20261111_final/import_author_assets.py \
    --archive /path/to/HeteroSpec_Final_20261111_Author.zip --mode check
python3 papers/reference_compatible/20261111_final/import_author_assets.py \
    --archive /path/to/HeteroSpec_Final_20261111_Author.zip --mode commit-and-push
```

The importer validates the top-level archive SHA256 and all 129 manifest-listed members, verifies any already-synced files byte-for-byte, writes all 130 entries, compiles main/journal in an isolated temporary copy and pushes a normal fast-forward commit. All assets remain confined to this paper subtree. It never merges or publishes the manuscript.

Once completed, verify the branch includes 130 author entries plus the original PR metadata, and confirm the new head matches the modelled `PACKAGE_MANIFEST.json` before declaring source sync complete.
