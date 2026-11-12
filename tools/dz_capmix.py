import json, glob, os, sys, collections
def mix(run, upto=500):
    by = collections.Counter(); cnt = collections.Counter(); champs = 0; games = 0
    for f in glob.glob(f'artifacts/tmp/dz/{run}/games/*/summary.json'):
        side = os.path.basename(os.path.dirname(f))[-1]; me = 'team' + side
        d = json.load(open(f)); games += 1
        caps = collections.defaultdict(int)
        for e in d['events']:
            if e['kind'] == 'gemCollection' and e['owner'].get('team') == me:
                for x in e['entries']:
                    if x['context'] == 'campGroup' and x['timestamp']['round'] <= upto:
                        caps[(x['timestamp']['round'], x['target']['id'])] += int(x['value'])
        for v in caps.values():
            b = '0' if v == 0 else '1-9' if v < 10 else '10-19' if v < 20 else '20-39' if v < 40 else '40-99' if v < 100 else '100+'
            by[b] += v; cnt[b] += 1
    order = ['0', '1-9', '10-19', '20-39', '40-99', '100+']
    print(run, 'per game to R%d:' % upto if False else 'per game, up to round', upto)
    print('   gems  ', {b: round(by[b] / games, 1) for b in order})
    print('   counts', {b: round(cnt[b] / games, 1) for b in order})
for r in sys.argv[1:]: mix(r)
