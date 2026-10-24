"""Lead integration check: build bot/src under several profiles with the official CLI and run short engine smokes.

teacher_exact must stay byte-identical to the original. Other profiles are built in scratch trees
(artifacts/tmp/profiles/<profile>/src) via tools/install_models.py and smoke-run vs the original at default fuel.
This is an untrained-framework plumbing check, NOT evidence of playing strength.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine  # noqa: E402

PY = sys.executable


def build_profile(profile: str) -> Path:
    d = ROOT / 'artifacts/tmp/profiles' / profile
    engine.make_bot_dir(ROOT / 'bot/src', d)
    r = subprocess.run([PY, str(ROOT / 'tools/install_models.py'), '--profile', profile, '--src', str(d / 'src'),
                        '--receipt', str(d / 'receipt.json')], capture_output=True, text=True, cwd=ROOT)
    if r.returncode:
        raise SystemExit(f'install_models failed for {profile}:\n{r.stdout}{r.stderr}')
    return engine.official_build(d, d / f'{profile}.wasm')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--profiles', nargs='+', default=['teacher_exact', 'neutral_credit', 'dev_untrained', 'training'])
    ap.add_argument('--maps', type=int, default=2)
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    orig = ROOT / 'references/builds/original.wasm'
    out = {}
    for p in a.profiles:
        w = build_profile(p)
        row = dict(wasm=str(w), sha256=engine.sha256(w), identical_to_original=engine.sha256(w) == engine.sha256(orig),
                   code_identical=engine.code_section_sha(w) == engine.code_section_sha(orig))
        jobs = []
        for m in engine.maps()[:a.maps]:
            for side in 'AB':
                x, y = (w, orig) if side == 'A' else (orig, w)
                jobs.append(dict(a=x, b=y, map_path=m, candidate_side=side, log_limit=16777216,
                                 folder=ROOT / 'artifacts/tmp/profiles' / p / 'runs' / f'{m.stem}-{side}'))
        res = engine.run_jobs(jobs, a.workers)
        row['smoke'] = [dict(r.row(), stdout_nfs1=engine.team_stdout(r.folder, r.side).count('NFS1 '),
                             stdout_nft1=engine.team_stdout(r.folder, r.side).count('NFT1 '),
                             bot_errors=engine.team_stdout(r.folder, r.side).count('bot error')) for r in res]
        out[p] = row
        print(p, json.dumps({k: v for k, v in row.items() if k != 'smoke'}), flush=True)
        for s in row['smoke']:
            print('   ', s['map'], s['side'], 'win', s['win'], 'gems', s['gems'], s['opponent_gems'], 'faults', s['faults'],
                  'fuelEx', s['fuel_exhausted'], 'NFS1', s['stdout_nfs1'], 'NFT1', s['stdout_nft1'], 'err', s['bot_errors'],
                  flush=True)
    engine.write_json(ROOT / 'evaluation/results/lead_profile_check.json', out)


if __name__ == '__main__':
    main()
