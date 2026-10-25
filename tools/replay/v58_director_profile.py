"""Extract measured planner fuel from A2_MICLOG diagnostic benches (not strength evidence).

Usage: python tools/replay/v58_director_profile.py <bench prefix> <report.json>
"""
from pathlib import Path
import glob
import json
import re
import statistics as st
import sys
import zipfile

rows = []
for summary in glob.glob(sys.argv[1] + '-seed*-s*/summary.json'):
    for game in json.loads(Path(summary).read_text(encoding='utf8'))['per_game']:
        replays = list(Path(game['folder']).glob('*.repl26a'))
        assert len(replays) == 1
        with zipfile.ZipFile(replays[0]) as z:
            name = 'team-a.stdout' if game['side'] == 'A' else 'team-b.stdout'
            data = z.read(name)
        for match in re.finditer(rb'DIRECTOR R(\d+) S(\d+) G(-?\d+) fuel(\d+)', data):
            r, slot, group, fuel = map(int, match.groups())
            rows.append(dict(map=game['map'], side=game['side'], round=r, slot=slot, group=group, fuel=fuel))
values = [r['fuel'] for r in rows]
assert values, 'no DIRECTOR diagnostic lines'
report = dict(samples=len(values), mean=st.mean(values), maximum=max(values), over15000=sum(v > 15000 for v in values),
              note='Diagnostic MICLOG changes overall trajectories; sampled local planner fuel is not a normal-build performance result.', samples_detail=rows)
Path(sys.argv[2]).write_text(json.dumps(report, indent=1) + '\n', encoding='utf8')
print({k: v for k, v in report.items() if k != 'samples_detail'})
