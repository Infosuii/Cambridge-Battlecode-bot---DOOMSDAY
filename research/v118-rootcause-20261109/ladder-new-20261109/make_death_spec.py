import json, gzip, sys, zipfile, os
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import ladder_loss_analysis as L
ms = json.load(open(HERE / 'matches.json')); specs = []
tmp = HERE / 'replays'; tmp.mkdir(exist_ok=True)
for m in ms:
    o = L.own(m)
    if o['result'] != 'loss': continue
    z = HERE / 'matches' / m['matchId'] / 'replay.zip'
    if not z.exists(): continue
    rp = tmp / (m['matchId'] + '.repl26a')
    if not rp.exists():
        with zipfile.ZipFile(z) as f: rp.write_bytes(f.read('replay.repl26a'))
    n = json.load(gzip.open(HERE / 'matches' / m['matchId'] / 'native.json.gz', 'rt', encoding='utf-8'))
    us = 'team' + o['side'].upper(); deaths = []
    for e in n['events']:
        if e['kind'] == 'death' and e['owner'].get('team') == us and e['owner'].get('kind') == 'champion':
            for v in e['entries']:
                t = v.get('target') or {}
                deaths.append({'id': e['owner']['id'], 'name': e['owner']['name'], 'round': v['timestamp']['round'],
                               'killer': t.get('id') if t.get('kind') == 'champion' else -1, 'killerName': t.get('name') or v.get('context')})
    specs.append({'match': m['matchId'], 'map': m['map'], 'replay': str(rp), 'side': 0 if o['side'] == 'a' else 1, 'deaths': deaths})
json.dump(specs, open(HERE / 'death-spec.json', 'w'))
print(len(specs), sum(len(s['deaths']) for s in specs))
