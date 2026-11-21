# CLAUDE.md

The shared deploy for YAC's Apps Script projects: one reusable GitHub
workflow (`.github/workflows/deploy.yml`) that each Apps Script repo calls.
Plain code, no model calls or agent logic (those live in `ncssm-yac/yakkety`).

- **It holds no secret.** `CLASPRC_JSON` (the yakkety account's clasp
  sign-in) is a repository secret in each caller (organization secrets
  don't reach private repos on the org's free plan), and each caller passes
  it in. Never add it to this repo, to
  `yakkety`, or to any repo whose workflows run Claude.
- **Callers' code goes live on merge.** A change here changes how every
  script deploys, so keep it small, and say in the PR which callers it
  affects.
- **Never create a project unless the caller asks** (`create_if_missing`).
  A live project holds Script Properties (tokens); a stray copy is wrong.
- Workflow inputs reach scripts only as environment variables, never as
  `${{ }}` inside `run:` (the test checks this).
- `python3 test/check.py` before every push.
