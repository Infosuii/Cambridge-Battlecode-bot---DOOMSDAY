"""Freeze the initial ten-loss/two-control reproduction cases before live-source runs."""
import json
from deep_preflight import ROOT


def main():
    study = ROOT / 'research/deep-2026-10-28'
    sample = json.loads((study / 'MOMENT_SAMPLE.json').read_text(encoding='utf-8'))
    catalog = {r['match_id']: r for r in json.loads((ROOT / 'artifacts/local-only/deep-2026-10-28/restored-catalog.json').read_text(encoding='utf-8')) if r['partition'] == 'examined'}
    rows = []
    for cid in ['C004', 'C034', 'C070', 'C082', 'C018', 'C030', 'C048', 'C060', 'C011', 'C026', 'C099']:
        card = next(c for c in sample['rows'] if c['card_id'] == cid)
        meta = catalog[card['match_id']]
        rows.append({k: meta[k] for k in ('match_id', 'map', 'cohort', 'opponent', 'result', 'side')} | {'card_id': cid, 'window': [card['start'], card['end']]})
    mid = '1d769695-04a8-402a-86d7-b3e4ccf9e270'
    meta = catalog[mid]
    rows.append({k: meta[k] for k in ('match_id', 'map', 'cohort', 'opponent', 'result', 'side')} | {'card_id': 'matched-C034-control', 'window': [150, 160]})
    assert len({r['match_id'] for r in rows}) == 12
    assert sum(r['result'] == 'loss' for r in rows) == 10
    result = {'status': 'frozen before source-vs-puppet runs', 'cases': 12, 'losses': 10, 'control_wins': 2,
              'hands_off_used': 0, 'source': 'byte-exact local copy of bots/live-69/src; server Wasm hash unavailable',
              'sequence': ['validate raw accepted-input parser against five excluded calibration games by API reapplication/replay bytes and every-round state hashes',
                           'check compiled puppets against original states', 'run frozen source against enemy puppet on exact map/side',
                           'record first differing round, including draft; trace conclusions stop at first divergence',
                           'only then trace effective knobs and candidate takeovers'],
              'state_hash': 'banked, physical champion IDs/types/teams/position/alive/health/max health/gold/gems/kills/items/consumables/channel/timers; camps and capture-group state',
              'rows': rows}
    target = study / 'REPRO_PLAN.json'
    raw = (json.dumps(result, indent=2) + '\n').encode()
    if target.exists():
        assert target.read_bytes() == raw
    target.write_bytes(raw)
    print(json.dumps({'cases': 12, 'losses': 10, 'controls': 2}))


if __name__ == '__main__':
    main()
