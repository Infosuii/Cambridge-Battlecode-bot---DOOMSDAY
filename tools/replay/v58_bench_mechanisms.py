"""Measure v58 economy targets on completed benches; raw replays and intermediates stay local-only.

Usage: python tools/replay/v58_bench_mechanisms.py <bench prefix> <report.json>
Reports team capture gold, elk-size captures, carry ownership/Treasure, capture delay, deaths and fuel.
"""
from pathlib import Path
import glob
import json
import os
import statistics as st
import sys
import zipfile

from ledger_bench import run_batches

ROOT = Path(__file__).resolve().parents[2]


def mean(values):
    return st.mean(values) if values else None


def main():
    prefix, output = sys.argv[1:3]
    work = ROOT / 'artifacts/local-only/v58' / Path(prefix).name
    work.mkdir(parents=True, exist_ok=True)
    files, games = [], {}
    selected_seeds = set(filter(None, os.environ.get('NFS_ANALYSIS_SEEDS','').split(',')))
    for summary in sorted(glob.glob(prefix + '-seed*-s*/summary.json')):
        seed = Path(summary).parent.name.split('-seed')[-1].split('-')[0]
        if selected_seeds and seed not in selected_seeds: continue
        for g in json.loads(Path(summary).read_text(encoding='utf8'))['per_game']:
            name = f"{g['map']}-{g['side']}-seed{seed}"
            path = work / (name + '.repl26a')
            native = Path(g['folder'])
            if not path.exists():
                replay = list(native.glob('*.repl26a'))
                assert len(replay) == 1
                with zipfile.ZipFile(replay[0]) as z:
                    path.write_bytes(z.read('replay.repl26a'))
            files.append(str(path))
            games[name] = (g, json.loads((native / 'summary.json').read_text(encoding='utf8')))
    assert files, 'no completed games'
    suffix = '-seeds' + '-'.join(sorted(selected_seeds)) if selected_seeds else ''
    ledger_path, funnel_path = work / ('ledger'+suffix+'.json'), work / ('funnel'+suffix+'.json')
    if not ledger_path.exists():
        run_batches('actor_ledger.mjs', [], files, ledger_path, until=500)
    if not funnel_path.exists():
        os.environ['NFS_FUNNEL_UNTIL'] = '250'
        run_batches('capture_funnel.mjs', [], files, funnel_path)
    ledgers = json.loads(ledger_path.read_text(encoding='utf8'))
    funnels = {g['id']: g['captures'] for g in json.loads(funnel_path.read_text(encoding='utf8'))}
    assert len(ledgers) == len(files) == len(funnels)
    rows = []
    for game in ledgers:
        meta, native = games[game['id']]
        us = 0 if meta['side'] == 'A' else 1
        row = {'game': game['id']}
        for label, team in (('candidate', us), ('opponent', 1 - us)):
            actors = sorted((a for a in game['actors'] if a['team'] == team), key=lambda a: a['id'])
            carry = next((a for a in actors if a['type'] == 1), actors[0])
            windows = [a['w'].get('250', {}) for a in actors]
            gold = sum(w.get('cap_gold', 0) for w in windows)
            caps = [c for c in funnels[game['id']] if c['team'] == team and c['round'] <= 250]
            elks = [c for c in caps if c['hp'] >= 2400]
            team_name = 'teamA' if team == 0 else 'teamB'
            cs = [c for c in native['champions'] if c['team'] == team_name]
            treasure = carry['emblems'].get('treasure')
            row[label] = {
                'capture_gold_R250': gold,
                'elk_captures_R250': len(elks),
                'elk_base_gold_R250': sum(c['gold'] for c in elks),
                'elk_hitters_R250': mean([len([h for h in c['hitters'] if h['team'] == team]) for c in elks]),
                'elk_clear_rounds_R250': mean([c['clear_end'] - c['clear_start'] for c in elks]),
                'first_elk_capture_round': min((c['round'] for c in elks), default=None),
                'carry_type': carry['type'], 'vesper_drafted': carry['type'] == 1,
                'carry_capture_share_R250': carry['w'].get('250', {}).get('cap_gold', 0) / gold if gold else 0,
                'carry_treasure_by120': treasure is not None and treasure <= 120,
                'carry_treasure_round_censored500': treasure if treasure is not None and treasure <= 500 else 501,
                'split_capture_share_R250': mean([len(c['capturers']) > 1 for c in caps]),
                'capture_delay_R250': mean([c['round'] - c['clear_end'] for c in caps]),
                'deaths': sum(int(c['metrics']['deaths']) for c in cs),
                'faults': int(native['diagnostics']['botFaults'][team_name]),
                'fuel': sum(len(e['entries']) for e in native['events'] if e['kind'] == 'fuelExhausted' and isinstance(e['owner'], dict) and e['owner'].get('team') == team_name),
            }
        rows.append(row)
    metrics = {}
    for key in rows[0]['candidate']:
        metrics[key] = {}
        for side in ('candidate', 'opponent'):
            xs = [r[side][key] for r in rows if r[side][key] is not None]
            metrics[key][side] = {'n': len(xs), 'mean': mean(xs), 'median': st.median(xs) if xs else None}
    vesper_only = {}
    for side in ('candidate', 'opponent'):
        subset = [r[side] for r in rows if r[side]['vesper_drafted']]
        vesper_only[side] = {}
        for key in ('carry_capture_share_R250', 'carry_treasure_by120', 'carry_treasure_round_censored500'):
            xs = [r[key] for r in subset if r[key] is not None]
            vesper_only[side][key] = {'n': len(xs), 'mean': mean(xs), 'median': st.median(xs) if xs else None}
    report = {'prefix': prefix, 'analysis_seeds': sorted(selected_seeds), 'engine': os.environ.get('NFS_REPLAY_ENGINE','1.0.3'), 'games': len(rows), 'metrics': metrics, 'vesper_only_metrics': vesper_only,
              'carry_definition': 'Vesper if drafted, otherwise lowest actor-id slot; missing Treasure censored at501, not omitted.',
              'funnel_note': 'Observed capture detection, basic-attack hitters, SDK camp base values; spell-only hits may be missed. Same analysis for both teams.',
              'per_game': rows}
    Path(output).write_text(json.dumps(report, indent=1) + '\n', encoding='utf8')
    print('games', len(rows))
    for key, sides in metrics.items():
        print(key, sides['candidate']['mean'], sides['opponent']['mean'])


if __name__ == '__main__':
    main()
