import csv, collections, sys
root = sys.argv[1]
winners = {}
for r in csv.DictReader(open(root + '/MATCH_INDEX.csv')):
    a, b = int(r['score_a']), int(r['score_b'])
    winners[r['match_id']] = r['side_a'] if a > b else r['side_b']
seq = collections.defaultdict(list)  # (match, team, actor, champion) -> emblem completions in order
stat = collections.defaultdict(collections.Counter)
for r in csv.DictReader(open(root + '/PURCHASES.csv')):
    key = (r['match_id'], r['team'], r['actor'], r['champion'])
    it = r['item']
    if 'Emblem' in it and r['event'] in ('purchase', 'combine', 'combination'):
        seq[key].append((int(r['round']), it))
    if 'Shard' in it and r['event'] == 'purchase':
        stat[r['champion']][it.split(' of ')[-1]] += int(r['quantity'])
events = collections.Counter(r['event'] for r in csv.DictReader(open(root + '/PURCHASES.csv')))
print('events', dict(events))
order = collections.defaultdict(lambda: collections.Counter())
for key, s in seq.items():
    s.sort(); fams = []
    for _, it in s:
        f = it.split(' Emblem')[0]
        if f not in fams: fams.append(f)
    tag = 'W' if winners.get(key[0]) == key[1] else 'L'
    order[(key[3], tag)][' > '.join(fams[:3])] += 1
for (champ, tag), c in sorted(order.items()):
    print(f'{champ:14s} {tag}', c.most_common(4))
print()
for champ, c in stat.items(): print(f'{champ:14s} shard stats', dict(c))
