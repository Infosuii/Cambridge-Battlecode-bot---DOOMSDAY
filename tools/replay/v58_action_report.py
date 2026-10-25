"""Whole-life action density and survival counters for a completed v58 bench. Offline only.

Usage: python tools/replay/v58_action_report.py <bench prefix> <report.json>
Raw replays/intermediates remain under artifacts/local-only/v58. Uses the audited sanity_audit.mjs counters.
"""
from pathlib import Path
from collections import defaultdict
import glob
import json
import sys
import zipfile
from ledger_bench import run_batches

ROOT = Path(__file__).resolve().parents[2]


def main():
    prefix, output = sys.argv[1:3]
    work = ROOT / 'artifacts/local-only/v58' / Path(prefix).name
    work.mkdir(parents=True, exist_ok=True)
    files, sides = [], {}
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
            files.append(str(p)); sides[name] = 0 if g['side'] == 'A' else 1
    assert files
    cache = work / 'sanity.json'
    if not cache.exists():
        run_batches('sanity_audit.mjs', [], files, cache)
    games = json.loads(cache.read_text(encoding='utf8'))
    assert len(games) == len(files)
    fields = ('alive', 'attacks', 'casts', 'moves', 'idle', 'deaths', 'big_bag_deaths', 'gems_lost', 'wards', 'fuel_out')
    all_stats = {s: defaultdict(float) for s in ('candidate', 'opponent')}
    by_type = {s: defaultdict(lambda: defaultdict(float)) for s in all_stats}
    for game in games:
        for actor in game['actors']:
            side = 'candidate' if actor['team'] == sides[game['id']] else 'opponent'
            for key in fields:
                value = actor.get(key, 0)
                all_stats[side][key] += value
                by_type[side][actor['type']][key] += value
            by_type[side][actor['type']]['actor_games'] += 1
    def rates(data):
        out = dict(data)
        for key in ('attacks', 'casts', 'idle'):
            out[key + '_per100alive'] = 100 * data[key] / max(1, data['alive'])
        out['deaths_per_game'] = data['deaths'] / len(games)
        out['big_bag_deaths_per_game'] = data['big_bag_deaths'] / len(games)
        out['wards_per_game'] = data['wards'] / len(games)
        out['fuel_per_game'] = data['fuel_out'] / len(games)
        return out
    report = {'prefix': prefix, 'games': len(games), 'all': {s: rates(v) for s, v in all_stats.items()},
              'by_type': {s: {str(t): rates(v) for t, v in data.items()} for s, data in by_type.items()}}
    Path(output).write_text(json.dumps(report, indent=1) + '\n', encoding='utf8')
    print('games', len(games))
    for side, data in report['all'].items():
        print(side, {k: v for k, v in data.items() if 'per' in k})
    for t in ('0', '1', '7', '11'):
        print('type', t, {s: report['by_type'][s].get(t, {}).get('casts_per100alive') for s in all_stats})


if __name__ == '__main__':
    main()
