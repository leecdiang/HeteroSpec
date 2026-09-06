# Pre-publication security check

## Checked patterns

- HF token
- GitHub token
- OpenAI key
- Authorization
- Credential assignment
- Email
- Windows username
- Original absolute root
- IPv4

## Findings

- No candidate-file matches.

## Actions

- Large/local asset directories are ignored.
- Secret values are never copied into this report.
- Root PowerShell/CMD wrappers remain local when they contain machine-specific paths.

## Remaining TODO

- Choose a license and finalize author metadata.
- Run a final scan immediately before public release.
