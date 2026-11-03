"""Economy of a duel arm: our team vs theirs in its won and lost games (gold, camp damage, gems, kills, deaths at
rounds 150 / 300 / 600; Bruiser shards). Summaries cached by ladder_duel.py report --margins.
  python research/x3/duel/arm_econ.py PLAN ARM"""
import json, sys, statistics as st
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/replay')); import ladder_duel as ld
plan = json.load(open(sys.argv[1], encoding='utf-8')); arm = sys.argv[2]; info = plan['arms'][arm]
by = ld.finished_groups({g for g in info['groups'] if g}, info['since'])
def ser(runs):
    o, t = [], 0
    for r in runs: o.append((t, float(r['value']))); t += r['duration']
    return o
def at(s, T):
    v = 0
    for a, x in s:
        if a > T: break
        v = x
    return v
rows = []
for gid, ms in by.items():
    for m in ms:
        f = ROOT / 'artifacts/local-only/duels' / f"{m['matchId']}.json"
        if not f.exists(): continue
        s = json.load(open(f, encoding='utf-8'))
        u = next(t for t in m['teams'] if t['name'] == 'DOOMSDAY')
        us = 'team' + u['side'].upper(); th = 'teamB' if us == 'teamA' else 'teamA'
        r = {'win': u['result'] == 'win', 'map': m['map']}
        for tag, side in (('u', us), ('t', th)):
            for met in ('earnedGold', 'monsterDamageDone', 'collectedGems', 'kills', 'deaths'):
                for T in (150, 300, 600):
                    r[f'{tag}{met}{T}'] = sum(at(ser(x['runs']), T) for x in s['championTimelines'] if x['owner']['team'] == side and x['metric'] == met)
            r[tag + 'bru'] = sum(int(i['quantity']) for c in s['champions'] if c['team'] == side for i in c['itemsBought'] if i['item'].startswith('Bruiser'))
        rows.append(r)
print(len(rows), 'games,', sum(r['win'] for r in rows), 'wins')
for res in (True, False):
    g = [r for r in rows if r['win'] == res]
    if not g: continue
    print('WINS' if res else 'LOSSES', len(g), '(median us / them)')
    for met in ('earnedGold', 'monsterDamageDone', 'collectedGems', 'kills', 'deaths'):
        print(f'  {met:18s}', '  '.join(f"r{T} {st.median(r[f'u{met}{T}'] for r in g):6.0f} / {st.median(r[f't{met}{T}'] for r in g):6.0f}" for T in (150, 300, 600)))
    print(f"  bruiser shards     {st.mean(r['ubru'] for r in g):.0f} / {st.mean(r['tbru'] for r in g):.0f}")
