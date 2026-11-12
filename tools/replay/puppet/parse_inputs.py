"""Preserve exact accepted input parameters for selected calibration/examined replays."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deep_preflight import ROOT
from replay_format import parse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--partition', choices=['calibration-excluded', 'examined'], required=True)
    ap.add_argument('--ids', nargs='*')
    a = ap.parse_args()
    local = ROOT / 'artifacts/local-only/deep-2026-10-28'
    catalog = json.loads((local / 'restored-catalog.json').read_text(encoding='utf-8'))
    maps = {p.stem.replace('-', '').replace('_', ''): p for p in (ROOT / 'maps/local-benchmarks').glob('*.map26a')}
    selected = [r for r in catalog if r['partition'] == a.partition and (not a.ids or r['match_id'] in a.ids)]
    assert selected and (a.partition == 'calibration-excluded' or a.ids), 'Select examined IDs explicitly'
    out = local / 'replay-inputs'
    out.mkdir(exist_ok=True)
    for row in selected:
        mid = row['match_id']
        replay = (local / 'replays' / a.partition / (mid + '.repl26a')).read_bytes()
        native = json.loads((local / 'replays' / a.partition / (mid + '.summary.json')).read_text(encoding='utf-8'))
        mp = maps[row['map'].replace('-', '').replace('_', '')]
        map_bytes = mp.read_bytes()
        inputs = parse(replay, map_bytes)
        assert len(inputs) == native['match']['finalInput']
        result = {'match_id': mid, 'partition': a.partition, 'map_file': mp.relative_to(ROOT).as_posix(),
                  'map_sha256': hashlib.sha256(map_bytes).hexdigest(), 'replay_sha256': hashlib.sha256(replay).hexdigest(),
                  'roster': [{'id': c['id'], 'team': 0 if c['team'] == 'teamA' else 1} for c in native['roster']['champions']],
                  'inputs': inputs}
        target = out / (mid + '.json')
        if target.exists():
            old = json.loads(target.read_text(encoding='utf-8'))
            assert old['replay_sha256'] == result['replay_sha256']
            continue
        target.write_bytes((json.dumps(result) + '\n').encode())
        print(str(target.relative_to(ROOT)))


if __name__ == '__main__':
    main()
