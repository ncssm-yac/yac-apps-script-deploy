# YAC Apps Script deploy (shared)

One reusable workflow that deploys YAC's Apps Script projects from GitHub,
so nobody pastes code into the Apps Script editor and every change goes
through a reviewed PR. It's the `yac-birthdays` deploy (Nov 2026), made
generic.

For each calling repo:

| Caller's event | What runs |
| --- | --- |
| Pull request | Its tests. The Google sign-in is never touched. |
| Merge to `main` / Run workflow | Tests, `clasp push` to the project, then the drift check. |
| Daily schedule | Drift check only: fails if the live code differs from the repo (someone edited it in the editor) or the clasp sign-in stopped working. |

The project is found by its **title** in `ncssm.yac.yakkety@gmail.com`'s
Apps Script list. A missing project fails the run, unless the caller sets
`create_if_missing` (only for a brand-new script).

## Using it from an Apps Script repo

`.github/workflows/apps-script.yml` in the calling repo:

```yaml
name: Apps Script
on:
  push:
    branches: [main]
    paths: ['src/**', 'test/**', '.github/workflows/apps-script.yml']
  pull_request:
    paths: ['src/**', 'test/**', '.github/workflows/apps-script.yml']
  schedule:
    - cron: '17 15 * * *'   # daily drift check
  workflow_dispatch:
permissions:
  contents: read
jobs:
  deploy:
    uses: ncssm-yac/yac-apps-script-deploy/.github/workflows/deploy.yml@main
    with:
      title: YAC Notes Trigger      # exactly as in the Apps Script list
      src_dir: src                  # .gs files + appsscript.json
      test_command: npm test
    secrets:
      CLASPRC_JSON: ${{ secrets.CLASPRC_JSON }}
```

Callers today: `yac-birthdays` (YAC Birthday Trigger), `yac-notes-trigger`
(YAC Notes Trigger).

## Setup (one time, owner)

1. **Make this repo and every caller public.** Organization secrets reach
   only public repos on the organization's current (free) plan, and a public
   repo's workflow can be called by any repo, with no Access setting. Before
   a repo goes public, check that its code, history and Actions logs hold no
   member data, tokens or webhook URLs (the YAC tool repos keep those in
   Sheets and secrets by rule).
2. **One organization secret, `CLASPRC_JSON`**: `ncssm-yac` Settings →
   Secrets and variables → Actions → New organization secret. Value: the
   contents of `~/.clasprc.json` after `clasp login` as
   `ncssm.yac.yakkety@gmail.com`. Repository access: **selected
   repositories**, only the callers. A new Apps Script repo just gets ticked
   in that list. Never tick a repo whose workflows run Claude (such as
   `yakkety`). A caller must not have its own repository secret with the
   same name: it would override the org one and be missed at renewal.
3. **Apps Script API on** for the yakkety account:
   script.google.com/home/usersettings (done Nov 2026).

## When the sign-in breaks

A password change or Google signing the account out ends the clasp login,
and every caller's daily drift check goes red the same day. On your computer:

```powershell
npx.cmd @google/clasp login
Get-Content $HOME\.clasprc.json -Raw | Set-Clipboard
```

Paste it as the new value of the `CLASPRC_JSON` organization secret, then
clear the clipboard (`Set-Clipboard -Value " "`) and delete
`$HOME\.clasprc.json`.

## Tests

```bash
pip install pyyaml && python3 test/check.py
```

Checks the workflow without running it: the inputs callers rely on, that pull
requests never reach the sign-in, that a scheduled run never pushes, that the
secret reaches only the sign-in step and is always deleted, that inputs reach
scripts only as environment variables, and that every shell step is valid
bash.
