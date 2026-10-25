"""Economic ledger of a bench2 run: candidate vs opponent, from the local replays (offline analysis only).

Usage: python tools/replay/ledger_bench.py <bench2 out prefix> [json out]
Extracts every game's replay, runs actor_ledger.mjs and still_runs.mjs, and prints paired medians/means of time use,
capture income, big-capture gems and stationary waits for the candidate (bot_match --a) and its opponent.
"""
from collections import defaultdict
import glob
import json
import os
from pathlib import Path
import statistics as st
import subprocess
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger_report import team_stats  # noqa: E402
from still_report import category  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def run_batches(script, args, files, output, until=None):
    """Bound child command lines on Windows; combine complete, ordered JSON arrays."""
    rows = []
    for start in range(0, len(files), 32):
        part = output.with_name(output.stem + f'-part{start // 32}.json')
        command = ['node', str(ROOT / 'tools/replay' / script), *args, str(part), *files[start:start + 32]]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, env=None if until is None else dict(os.environ, NFS_LEDGER_UNTIL=str(until)))
        rows.extend(json.loads(part.read_text(encoding='utf-8')))
        print(f'{script}: {min(start + 32, len(files))}/{len(files)}', flush=True)
    output.write_text(json.dumps(rows), encoding='utf-8')


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
        run_batches('actor_ledger.mjs', [], files, led, until=500)
    if not still.exists():
        run_batches('still_runs.mjs', ['auto', '500'], files, still)
    L = json.loads(led.read_text())
    S = {g['id']: g for g in json.loads(still.read_text())}
    rows = defaultdict(lambda: [[], []])
    for g in L:
        c = side[g['id']]
        for i, t in enumerate([c, 1 - c]):
            actors = [ac for ac in g['actors'] if ac['team'] == t]
            for W in [100, 250, 500]:
                if all(str(W) in ac.get('gear', {}) for ac in actors):
                    rows[f'R{W} equipment'][i].append(sum(ac['gear'][str(W)] for ac in actors))
                vesper = [ac for ac in actors if ac['type'] == 1]
                if vesper:
                    team_cap = sum(ac['w'].get(str(W), {}).get('cap_gold', 0) for ac in actors)
                    team_gold = sum(ac['w'].get(str(W), {}).get('gold_income', 0) for ac in actors)
                    if team_cap:
                        rows[f'R{W} Vesper capture-gold share (if drafted)'][i].append(sum(ac['w'].get(str(W), {}).get('cap_gold', 0) for ac in vesper) / team_cap)
                    if team_gold:
                        rows[f'R{W} Vesper inferred gold-income share (if drafted)'][i].append(sum(ac['w'].get(str(W), {}).get('gold_income', 0) for ac in vesper) / team_gold)
                if W == 100:
                    continue
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
        if not a or not b:
            out[k] = {'cand_n': len(a), 'opp_n': len(b), 'cand_mean': st.mean(a) if a else None, 'opp_mean': st.mean(b) if b else None}
            print(f'  {k}: candidate n={len(a)}, opponent n={len(b)} (conditional cohort)')
            continue
        out[k] = {'cand_n': len(a), 'opp_n': len(b), 'cand_mean': st.mean(a), 'opp_mean': st.mean(b), 'cand_median': st.median(a), 'opp_median': st.median(b)}
        print(f'  {k:40s} {st.mean(a):8.2f} {st.mean(b):8.2f}   {st.median(a):8.2f} {st.median(b):8.2f}')
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + '\n', encoding='utf8')


if __name__ == '__main__':
    main()
