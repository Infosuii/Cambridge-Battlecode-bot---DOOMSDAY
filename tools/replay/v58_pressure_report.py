"""Audit completion/abandonment of cleared gold-bearing camps under nearby enemy pressure (offline only).

Usage: python tools/replay/v58_pressure_report.py <bench prefix> <report.json>
Or: python tools/replay/v58_pressure_report.py --ladder <raw replay directory> <report.json>
Uses snapshots through R500. Raw replays and caches remain local-only. Capture/interruptions are observed inferences,
not engine progress counters; simultaneous kills or purchases can obscure capture recognition. Gold-free groups are excluded.
"""
import glob
import json
import os
from pathlib import Path
import statistics as st
import sys
import zipfile
from ledger_bench import run_batches

ROOT = Path(__file__).resolve().parents[2]


def main():
    files, sides = [], {}
    ladder = sys.argv[1] == '--ladder'
    if ladder:
        raw_dir, output = Path(sys.argv[2]), sys.argv[3]
        work = ROOT / 'artifacts/local-only/v58/r2-ladder-pressure'
        work.mkdir(parents=True, exist_ok=True)
        parts = json.loads((ROOT / 'evaluation/schedules/map_partitions.json').read_text())['partitions']
        normal = lambda name: name.replace('_', '').replace('-', '')
        dev = {normal(m) for m in parts['training'] + parts['selection']}
        meta = json.loads((ROOT / 'research/v55/V55_LIFE_DATA.json').read_text(encoding='utf8'))
        for g in meta:
            if g['opp'] == 'Claudus Maximus' and normal(g['map']) in dev:
                p = raw_dir / (g['id'] + '.repl26a')
                assert p.is_file()
                files.append(str(p))
                sides[g['id']] = 0 if g['side'] == 'a' else 1
    else:
        prefix, output = sys.argv[1:3]
        work = ROOT / 'artifacts/local-only/v58' / Path(prefix).name
        work.mkdir(parents=True, exist_ok=True)
        for summary in sorted(glob.glob(prefix + '-seed*-s*/summary.json')):
            seed = Path(summary).parent.name.split('-seed')[-1].split('-')[0]
            for g in json.loads(Path(summary).read_text(encoding='utf8'))['per_game']:
                name = f"{g['map']}-{g['side']}-seed{seed}"
                p = work / (name + '.repl26a')
                if not p.exists():
                    matches = list(Path(g['folder']).glob('*.repl26a'))
                    assert len(matches) == 1
                    with zipfile.ZipFile(matches[0]) as z:
                        p.write_bytes(z.read('replay.repl26a'))
                files.append(str(p))
                sides[name] = 0 if g['side'] == 'A' else 1
    assert files, 'no completed games'
    cache = work / 'capture-pressure-r500.json'
    if not cache.exists():
        os.environ['NFS_FUNNEL_UNTIL'] = '500'
        run_batches('capture_pressure.mjs', [], files, cache)
    games = json.loads(cache.read_text(encoding='utf8'))
    assert len(games) == len(files)
    rows = []
    for game in games:
        row = {'game': game['id']}
        for label, team in [('candidate', sides[game['id']]), ('opponent', 1 - sides[game['id']])]:
            metrics = {}
            for window in (250, 500):
                caps = [c for c in game['captures'] if c['team'] == team and c['round'] <= window and c['gold'] > 0]
                interruptions = [c for c in game['interruptions'] if c['team'] == team and c['round'] <= window and c['gold'] > 0]
                metrics[f'captures_R{window}'] = len(caps)
                metrics[f'base_capture_gold_R{window}'] = sum(c['gold'] for c in caps)
                metrics[f'capture_delay_R{window}'] = st.mean(c['round'] - c['clear_end'] for c in caps) if caps else None
                metrics[f'interruptions_R{window}'] = len(interruptions)
                metrics[f'interruptions_near_enemy_R{window}'] = sum(c['near_enemy'] for c in interruptions)
                enemy_clears = [c for c in caps if any(h['team'] != team for h in c['hitters']) and
                                not any(h['team'] == team for h in c['hitters'])]
                metrics[f'enemy_only_basic_clear_captures_R{window}'] = len(enemy_clears)
                metrics[f'enemy_only_basic_clear_gold_R{window}'] = sum(c['gold'] for c in enemy_clears)
            row[label] = metrics
        rows.append(row)
    aggregate = {}
    for key in rows[0]['candidate']:
        aggregate[key] = {}
        for label in ('candidate', 'opponent'):
            values = [r[label][key] for r in rows if r[label][key] is not None]
            aggregate[key][label] = dict(n=len(values), mean=st.mean(values) if values else None)
    report = dict(games=len(games), note=__doc__.splitlines()[-1], metrics=aggregate, per_game=rows,
                  labels={'candidate': 'historical DOOMSDAY v55', 'opponent': 'Claudus Maximus'} if ladder else
                  {'candidate': 'bench candidate', 'opponent': 'bench opponent'})
    Path(output).write_text(json.dumps(report, indent=1) + '\n', encoding='utf8')
    print('games', len(games))
    for key, value in aggregate.items():
        print(key, value['candidate']['mean'], value['opponent']['mean'])


if __name__ == '__main__':
    main()
