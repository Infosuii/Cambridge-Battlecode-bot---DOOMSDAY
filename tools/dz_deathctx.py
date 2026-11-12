import json, glob, os, re, sys, collections
run = sys.argv[1]; maxshow = int(sys.argv[2]) if len(sys.argv) > 2 else 6
kinds = {0: 'Farm', 1: 'Bank', 2: 'Home', 3: 'Retreat', 4: 'Idle', 5: 'Yield'}
pat = re.compile(r'DZ_FIGHT round=(\d+) slot=(\d+) kind=(\d+) hp=(\d+) max=(\d+) enemies=(\d+) nearest=(\d+) allies6=(\d+) pos=(\d+),(\d+)')
summary = collections.Counter(); shown = 0
for g in sorted(glob.glob(f'artifacts/tmp/dz/{run}/games/*')):
    side = os.path.basename(g)[-1]; me = 'team' + side
    d = json.load(open(os.path.join(g, 'summary.json')))
    out = open(os.path.join(g, 'candidate.stdout'), encoding='utf-8', errors='replace').read()
    ids = sorted(c['id'] for c in d['champions'] if c['team'] == me); slot = {i: k for k, i in enumerate(ids)}
    fights = collections.defaultdict(dict)
    for m in pat.finditer(out):
        fights[int(m[2])][int(m[1])] = dict(kind=kinds[int(m[3])], hp=int(m[4]), max=int(m[5]), enemies=int(m[6]),
                                            nearest=int(m[7]), allies=int(m[8]), pos=(int(m[9]), int(m[10])))
    for e in d['events']:
        if e['kind'] != 'death' or e['owner'].get('team') != me: continue
        s = slot[e['owner']['id']]
        for x in e['entries']:
            if x['context'] != 'champion': continue
            r = x['timestamp']['round']
            hist = [(rr, fights[s][rr]) for rr in range(r - 12, r + 1) if rr in fights[s]]
            summary['deaths'] += 1
            if not hist: summary['no_sighting_in_12'] += 1; continue
            f0 = hist[0][1]
            summary['first_' + f0['kind']] += 1
            summary['ever_retreat'] += any(h['kind'] == 'Retreat' for _, h in hist)
            summary['ever_home'] += any(h['kind'] == 'Home' for _, h in hist)
            summary['outnumbered_at_first'] += f0['enemies'] > f0['allies'] + 1
            summary['healthy_at_first(>60%)'] += f0['hp'] > .6 * f0['max']
            summary['first_seen_dist<=3'] += f0['nearest'] <= 3
            summary['turns_seen_before_death'] += len(hist)
            if shown < maxshow:
                shown += 1
                print(os.path.basename(g), 'slot', s, e['owner']['name'], 'killed by', x['target']['name'], 'round', r)
                for rr, h in hist: print('   ', rr, h['kind'], f"hp={h['hp']}/{h['max']} enemies={h['enemies']} nearest={h['nearest']} allies6={h['allies']} pos={h['pos']}")
print(dict(summary))
