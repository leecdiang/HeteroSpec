# Complete author-source synchronization for Draft PR #220

The manuscript author's fixed ZIP `HeteroSpec_Final_20261111_Author.zip` (SHA256 `e56013eace463b0615cf69dd130155b90bd2a26385286029891904689084f78b`) contains **130 files**. All 130 are now committed to this versioned subtree under the same source paths, with top-level metadata in `author_archive_root/`.

The final GitHub tree was independently enumerated: **130/130** entries matched the exact local Git blob SHA-1 in the authenticated author ZIP. This includes LaTeX, IEEE class/bibliography, numerical data, scripts, generated and editable figures, PDFs, validation logs and visual review assets. There were no path or hash mismatches.

## Rebuild

```bash
cd papers/reference_compatible/20261111_final/paper
bash build.sh
```

An independent clean-directory extraction of the exact ZIP completed the data tests, figure generation, pdfLaTeX/BibTeX passes and produced **byte-identical** `main.pdf` and `journal.pdf`:

- `main.pdf`: SHA256 `81376232b6765983bc91b8765fa2ed06e57a09edfe88c68db476f61210a6fd61`.
- `journal.pdf`: SHA256 `8d8abaa4fe47eed08a67cdce7828bc319a2f473aba64da20ee4781025d7af2ca`.

The independent build was run from the ZIP, whose files match the repository by Git blob identity. It did not execute a new GPU experiment, recover private native KV captures, or constitute independent on-GPU reproduction.

This PR remains **Draft**; no experiment was merged, and neither arXiv nor TPDS was submitted. The author still decides the publication and access policy for raw native evidence, author metadata and disclosures.
