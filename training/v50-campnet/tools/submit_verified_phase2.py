"""Submit the checked second-phase source once, retaining a deployment receipt."""
import datetime as dt
import json
import re
import subprocess
import zipfile
from pathlib import Path
import train

ROOT = train.ROOT / 'phase2-two-hours'

def main():
    receipt_path = ROOT / 'deployment.json'
    if receipt_path.exists():
        prior = json.loads(receipt_path.read_text())
        if prior.get('submission_version'):
            print('Already uploaded version', prior['submission_version'], '; do not duplicate.')
            return
    report = json.loads((ROOT / 'report.json').read_text())
    verification = json.loads((ROOT / 'verification.json').read_text())
    if report['status'] != 'complete': raise ValueError('Final tests are not complete')
    for score in [report['final_holdout'], *report['additional_comparisons'].values()]:
        if score['faults']: raise ValueError('Candidate bot fault in final checks')
    if not verification['rebuild_executable_sections_equal'] or not verification['training_trace_disabled']:
        raise ValueError('Source verification failed')
    source = ROOT / 'release/bot_neural.zip'
    wasm = ROOT / 'release/bot_neural.wasm'
    if train.sha(source) != verification['source_sha256'] or train.sha(wasm) != verification['wasm_sha256']:
        raise ValueError('Release differs from verified artifact')
    # Check the CLI's exact packaging contains the verified source bytes.
    bundle = ROOT / 'release/platform-upload.zip'
    bot = ROOT / 'release/bot_neural'
    train.command([train.CLI, 'bundle', bot, '--output', bundle])
    with zipfile.ZipFile(source) as expected, zipfile.ZipFile(bundle) as actual:
        a = {p:expected.read(p) for p in expected.namelist() if not p.endswith('/')}
        b = {p:actual.read(p) for p in actual.namelist() if not p.endswith('/')}
        if a != b: raise ValueError('CLI source package differs from verified source')
    note = 'Neural gameplay: 3h total training; selected phase2 checkpoint ' + str(report['selected_iteration'])
    result = subprocess.run([str(train.CLI), 'submit', str(bot), '--note', note],
                            capture_output=True, text=True, encoding='utf-8',errors='replace',timeout=180)
    output = result.stdout + result.stderr
    (ROOT / 'submission.log').write_text(output,encoding='utf-8')
    match = re.search(r'Submitted bot version\s+(\d+)', output)
    receipt = dict(authorization='User: after checks push the new bot and make it live',
        source_sha256=train.sha(source), wasm_sha256=train.sha(wasm),
        upload_package_sha256=train.sha(bundle), upload_contains_exact_verified_source=True,
        submitted_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        submission_version=int(match[1]) if match else None, upload_exit_code=result.returncode,
        status='uploaded_activation_unverified' if match else 'upload_failed',
        live_verified=False, submissions_url='https://2026a.battlecode.co.uk/game/submissions',
        activation_access='CLI has no activation command; authenticated submission-list API returned HTTP 401.',
        note=note)
    train.write(receipt_path, receipt)
    print(output)
    print(json.dumps(receipt,indent=2))
    if result.returncode: raise SystemExit(result.returncode)

if __name__ == '__main__': main()
