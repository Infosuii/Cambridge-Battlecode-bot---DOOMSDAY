from pathlib import Path
import sys, json
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run, STYLES
from project import ROOT, save
import dev_panel
split = json.loads((HERE / 'map-split.json').read_text())
dev = [Path(p) for p in split['dev']]
gen = sorted((ROOT / 'arena/maps_v113_stability').glob('*.map26a'))
C = ['hp01', 'v18H', 'v18DR', 'v18HDR', 'v18HDRL']
extra = [s for s in STYLES if s not in dev_panel.DEV_STYLES]
a = run('v118-dev-b-styles', C, dev, extra, workers=14)
b = run('v118-dev-c-generated', C, gen, dev_panel.DEV_STYLES, workers=14)
c = run('v118-dev-d-hdrl', ['v18HDRL'], dev, dev_panel.DEV_STYLES, workers=14)
old = json.loads((ROOT / 'panels/v118-dev-a/results.json').read_text())
allrows = a + b + c + [r for r in old if r['candidate'] in C]
s = dev_panel.summary(allrows)
save(HERE / 'dev-round2-summary.json', s)
for k, v in s.items(): print(k, {x: v[x] for x in ('games', 'score', 'paired_diff', 'faults', 'fuel')})
