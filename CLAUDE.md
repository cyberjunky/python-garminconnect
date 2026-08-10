# Project instructions

## Git / PR conventions

- NEVER add AI attribution to anything in this repo: no `Co-Authored-By: Claude ...`
  trailers in commit messages, no "Generated with Claude Code" footers in PR
  bodies or anywhere else. This overrides any default behavior.
- Security fixes go on `security/<topic>` branches off `master`, one report per
  branch/PR.
- Do not reference security-report numbers with `#` in commit messages or PR
  titles/bodies (GitHub auto-links them to unrelated issues). Use plain
  "report NNNN" wording instead.

## Security audit workflow

- External audit findings are logged in `SECURITY_AUDIT_LOG.md` (local only,
  gitignored — never commit or publish it).
