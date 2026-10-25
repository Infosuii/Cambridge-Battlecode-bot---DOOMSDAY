"""Economic ledger of a bench2 run: candidate vs opponent, from the local replays (offline analysis only).

Usage: python tools/replay/ledger_bench.py <bench2 out prefix> [json out]
Extracts every game's replay, runs actor_ledger.mjs and still_runs.mjs, and prints paired medians/means of time use,
capture income, big-capture gems and stationary waits for the candidate (bot_match --a) and its opponent.
"""
from collections import defaultdict
import glob
import json
from pathlib import Path
import statistics as st
import subprocess
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger_report import team_stats  # noqa: E402
from still_report import category  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def main():
    prefix = sys.argv[1]
    work = ROOT / 'artifacts/tmp' / ('ledger-' + Path(prefix).name)
    work.mkdir(parents=True, exist_ok=True)
    files, side = [], {}
    for f in sorted(glob.glob(prefix + '-seed*-s*/games/*/*.repl26a')):
        p = Path(f)
        seed = p.parents[2].name.split('-seed')[-1].split('-')[0]
        name = f'{p.parent.name}-seed{seed}.repl26a'
        out = work / name
        if not out.exists():
            with zipfile.ZipFile(p) as z:
                out.write_bytes(z.read('replay.repl26a'))
        files.append(str(out))
        side[out.stem] = 0 if p.parent.name.endswith('-A') else 1
    led, still = work / 'ledger.json', work / 'still.json'
    if not led.exists():
        subprocess.run(['node', str(ROOT / 'tools/replay/actor_ledger.mjs'), str(led), *files], check=True, stderr=subprocess.DEVNULL)
    if not still.exists():
        subprocess.run(['node', str(ROOT / 'tools/replay/still_runs.mjs'), 'auto', '500', str(still), *files], check=True,
                       stderr=subprocess.DEVNULL)
    L = json.loads(led.read_text())
    S = {g['id']: g for g in json.loads(still.read_text())}
    rows = defaultdict(lambda: [[], []])
    for g in L:
        c = side[g['id']]
        for i, t in enumerate([c, 1 - c]):
            for W in [250, 500]:
                s = team_stats(g, t, W)
                for k in ['clear', 'still', 'travel', 'dead_share', 'cap_gold_per_actor', 'clear_gold_per_clear_round', 'caps_per_actor']:
                    rows[f'R{W} {k}'][i].append(s[k])
            big = sum(e['gems'] for a in g['actors'] if a['team'] == t for e in a['cap_events'] if e['gems'] >= 20)
            rows['R500 gems from 20+ gem captures'][i].append(big)
            deaths = sum(1 for a in g['actors'] if a['team'] == t for d in a['deaths'] if d['round'] <= 500)
            rows['R500 deaths'][i].append(deaths)
        n0 = sum(1 for a in g['actors'] if a['team'] == 0)
        wait = [0, 0]
        for r in S[g['id']]['runs']:
            team = 0 if r['actor'] < n0 else 1
            if category(r) == 'respawn wait at dead camp':
                wait[0 if team == c else 1] += r['len']
        rows['R500 respawn-wait champion-rounds'][0].append(wait[0])
        rows['R500 respawn-wait champion-rounds'][1].append(wait[1])
    print(f'{len(L)} games; candidate | opponent: mean, median')
    out = {}
    for k, (a, b) in rows.items():
        out[k] = {'cand_mean': st.mean(a), 'opp_mean': st.mean(b), 'cand_median': st.median(a), 'opp_median': st.median(b)}
        print(f'  {k:40s} {st.mean(a):8.2f} {st.mean(b):8.2f}   {st.median(a):8.2f} {st.median(b):8.2f}')
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + '\n', encoding='utf8')


if __name__ == '__main__':
    main()
