# Provenance and validation

Prepared 2026-11-13. Project-authored guide, not an official JPDC document.

## Sources

- JPDC Guide for Authors: https://www.sciencedirect.com/journal/journal-of-parallel-and-distributed-computing/publish/guide-for-authors
- Elsevier LaTeX guidance: https://www.elsevier.com/latex
- Official template URL linked in the supplied guide: https://assets.ctfassets.net/o78em1y1w4i4/5uFmLZJTPDMAUjFnHRpjj8/6f19a979146eb93263763d87a894ab0d/els-cas-templates.zip
- Artwork: https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions
- Submission portal: https://submit.elsevier.com/JPDC

The two user-supplied Markdown excerpts cover writing/formatting and supplementary/data/references/submission rules. Their guide content was read in full. The live journal page returned `Site Unavailable` in this environment; we do not claim independent live verification of those journal-specific rules or completeness of the excerpts. Private reviewer materials were read for scope; they are not redistributed here and are not official journal requirements.

The template was independently fetched from the official CDN above. The uploaded ZIP and live ZIP have different container hashes, but their `els-cas-templates/` payload files match byte-for-byte. The uploaded ZIP additionally contains macOS metadata. This repository includes the unchanged live ZIP, SHA-256:

`36d97da01c6bbd134f315bff6c3de553735e2550444a6ddd4f869ddc67a20757`

## License

Official CAS Bundle version 2.4. Complete archive is retained unchanged, including upstream README, manifest, documentation and copyright headers. Source headers specify LPPL 1.3c or later; the README also contains an older LPPL 1.2-or-later statement. These original notices are preserved rather than rewritten. Official authorship is Elsevier's, not this project; project guidance does not relicense the vendor bundle. LPPL: https://www.latex-project.org/lppl/ .

## Validation

- PASS: ZIP CRC/integrity; required class/style/template/documentation files present.
- PASS: official CDN payload compared with user-supplied template payload; all common official files identical.
- NOT COMPLETED: PDF compilation. `latexmk` and `pdflatex` executables exist, but this environment lacks the `pdflatex.fmt` format and core LaTeX files. Initial attempt could not write its default TeX cache; using a writable temporary cache then confirmed the missing format. No template syntax failure has been established. Use a full TeX Live/MiKTeX installation and the README command before writing/submission.
- No scientific result was regenerated or changed; no GPU/model execution.
