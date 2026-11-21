#!/usr/bin/env python3
"""Checks the shared deploy workflow without running it: YAML parses, the
workflow_call contract is what callers rely on, every shell step is valid
bash, and the safety rules hold. No network, no Google."""
import pathlib, re, subprocess, sys, tempfile
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
wf = yaml.safe_load((ROOT / '.github/workflows/deploy.yml').read_text())
on = wf.get(True) or wf.get('on')  # PyYAML reads the key `on` as True
failed = 0
def check(name, ok):
    global failed
    print(('ok - ' if ok else 'FAIL - ') + name)
    failed += 0 if ok else 1

call = on['workflow_call']
check('inputs callers use', {'title', 'src_dir', 'test_command', 'create_if_missing'} <= set(call['inputs']))
check('title, src_dir and test_command are required', all(call['inputs'][k]['required'] for k in ('title', 'src_dir', 'test_command')))
check('create_if_missing defaults to false', call['inputs']['create_if_missing']['default'] is False)
check('CLASPRC_JSON is the only secret', list(call['secrets']) == ['CLASPRC_JSON'])
check('read-only token', wf['permissions'] == {'contents': 'read'})

jobs = wf['jobs']
check('pull requests never reach the sign-in', jobs['sync']['if'] == "github.event_name != 'pull_request'" and jobs['sync']['needs'] == 'test')
check('the test job never sees the secret', 'secrets.' not in yaml.safe_dump(jobs['test']))
steps = {s.get('name', s.get('uses', s.get('run', ''))): s for s in jobs['sync']['steps']}
check('a scheduled run only checks, never pushes', steps['Deploy']['if'] == "github.event_name != 'schedule'")
check('the sign-in is always deleted', steps['Forget the sign-in']['if'] == 'always()' and 'rm -f "$HOME/.clasprc.json"' in steps['Forget the sign-in']['run'])
check('the secret reaches only the sign-in step', [n for n, s in steps.items() if 'CLASPRC_JSON' in yaml.safe_dump(s)] == ['Sign in as the yakkety account'])
check('inputs reach scripts only as environment variables', all('${{' not in s.get('run', '') for j in jobs.values() for s in j['steps']))
check('a missing project is created only when asked, never on schedule', 'if [ "$CREATE" != true ] || [ "$EVENT" = schedule ]; then' in steps['Find the project']['run'])

for j in jobs.values():
    for s in j['steps']:
        if 'run' not in s: continue
        with tempfile.NamedTemporaryFile('w', suffix='.sh', delete=False) as f:
            f.write(s['run'])
        r = subprocess.run(['bash', '-n', f.name], capture_output=True, text=True)
        check('bash syntax: ' + s.get('name', s['run'][:40]), r.returncode == 0)

print(('%d failed' % failed) if failed else 'all passed')
sys.exit(1 if failed else 0)
