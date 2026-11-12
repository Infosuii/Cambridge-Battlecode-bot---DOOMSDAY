"""Pooled ladder metrics on the same complete local schedules (not changing sets of losses).

Usage: compare_runs.py RUN [RUN ...]. Every run needs local_index.py and timelines.
Early-even uses c_engage's existing fight clustering, equal numbers, HP ratio
0.8..1.25 and first hit before R300. No new games are played.
"""
import contextlib
import io
import json
from pathlib import Path
import runpy
import sys
from collections import Counter

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / 'tools/v67'))
from c_engage import analyse

runs = sys.argv[1:]
for run in runs:
    index = f'research/v75/{run}_index.json'
    summaries = {}
    for script, var in [('split', 'C'), ('micro', 'C'), ('farm_eff', 'S')]:
        sys.argv = [script, index, '.']
        with contextlib.redirect_stdout(io.StringIO()):
            ns = runpy.run_path(str(root / 'research/v75/teamfight_scripts' / f'{script}.py'))
        pooled = Counter()
        for key in ('us-loss', 'us-win'):
            pooled.update(ns[var][key])
        summaries[script] = pooled
    even = Counter()
    for r in json.loads(Path(index).read_text()):
        tl = json.loads((root / r['matchId'] / 'timeline.json').read_text())
        result = analyse(tl, 0 if r['side'] == 'a' else 1)
        for f in result['fights']:
            if f['round'] < 300 and f['local'][0] == f['local'][1] and f['local'][0] > 0 and 0.8 <= f['hp'][0]/max(1, f['hp'][1]) <= 1.25:
                even['n'] += 1
                even['our_deaths'] += f['dead'][0]
                even['their_deaths'] += f['dead'][1]
    summaries['early_even'] = even
    out = root / 'research/v75' / f'{run}_metrics.json'
    out.write_text(json.dumps(summaries, indent=1) + '\n')
    s, m, f = [summaries[k] for k in ('split', 'micro', 'farm_eff')]
    print(f'{run}: grouped={s["rounds"]} split-hit-out={s["split_hit_out"]/s["rounds"]:.1%} '
          f'all-out={s["all_out"]/s["rounds"]:.1%} all-hit={s["all_hit"]/s["rounds"]:.1%}; '
          f'contact={m["n"]} cast={m["cast"]/m["n"]:.1%} move-only={m["move_only"]/m["n"]:.1%}; '
          f'dead-R500={f["dead"]/(f["dead"]+f["alive"]):.1%} farm-gold/camp-hit={f["farm_gold"]/max(1,f["camp"]):.2f}; '
          f'early-even={even["n"]} deaths={even["our_deaths"]/max(1,even["n"]):.2f}/{even["their_deaths"]/max(1,even["n"]):.2f}', flush=True)
