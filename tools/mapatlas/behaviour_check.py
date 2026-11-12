"""Did a strategy change the team's behaviour the way it should? Profiles the candidate's own team in local dz games
(tools/replay/winner_profile.mjs on the runs' replays) and compares runs side by side on the replay metrics the loss
study measured on the winners (research/x3/losses48/REPLAY_FINDINGS.md).
  python tools/mapatlas/behaviour_check.py RUN [RUN ...]
"""
import json, os, subprocess, sys, zipfile, statistics as st
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'research/x3/losses48'))
from replay_compare import feats, m  # noqa: E402

KEYS = ['grouped_0-150', 'grouped_150-400', 'spread_0-150', 'workers_together', 'contact_allies', 'contact_hp',
        'own_half_400-800', 'own_half_800+', 'clears_400-800', 'clears_800+', 'recalls_400-800', 'gold_600']


def profile_run(run):
    games = ROOT / 'artifacts/tmp/dz' / run / 'games'
    out = ROOT / 'artifacts/local-only/behaviour' / run; out.mkdir(parents=True, exist_ok=True)
    reps, sides = [], []
    for g in sorted(games.iterdir()):
        b = next(g.glob('*.repl26a'), None)
        if not b: continue
        r = out / f'{g.name}.repl26a'
        if not r.exists():
            with zipfile.ZipFile(b) as z: r.write_bytes(z.read('replay.repl26a'))
        reps.append(r); sides.append(0 if g.name.endswith('-A') else 1)
    res = out / 'profiles.json'
    if not res.exists():
        subprocess.run(['node', str(ROOT / 'tools/replay/winner_profile.mjs'), str(res)] + [str(r) for r in reps],
                       env=dict(os.environ, NFS_REPLAY_ENGINE='2.0.0'), capture_output=True)
    P = json.loads(res.read_text())
    return [feats(p['teams'][s]) for p, s in zip(P, sides) if 'teams' in p]


def main():
    runs = sys.argv[1:]
    data = {r: profile_run(r) for r in runs}
    print(f"{'metric':18s} " + ' '.join(f'{r[:16]:>16s}' for r in runs))
    for k in KEYS:
        print(f'{k:18s} ' + ' '.join(f'{m([x[k] for x in data[r]]):16.2f}' for r in runs))


if __name__ == '__main__':
    main()
