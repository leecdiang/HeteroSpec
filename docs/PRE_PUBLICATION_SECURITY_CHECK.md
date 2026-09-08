# Pre-publication security check

## Checked patterns

- HF token
- GitHub token
- OpenAI key
- Authorization
- Credential assignment
- Email
- Windows user path
- macOS user path
- Linux user path
- Original absolute root

## Findings

- `artifacts/m4_humaneval_code_conditioned/results.json`: macOS user path

## Actions

- Large/local asset directories are ignored.
- Secret values are never copied into this report.
- Root PowerShell/CMD wrappers remain local when they contain machine-specific paths.
- The M4 authoritative run record retains local model/data paths for provenance; review or redact the username-bearing path before public release.

## Remaining TODO

- Choose a license and finalize author metadata.
- Decide and document the public-release treatment of local provenance paths.
- Run a final scan immediately before public release.
