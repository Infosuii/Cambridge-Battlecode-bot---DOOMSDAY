"""Team strength ratings from decoded platform replays (decode_archive.py output), with the A/B order verified.

    python tools/replay/team_ratings.py --decoded artifacts/local-only/replays-<date> [--out <json>]

Member names list two team ids whose A/B order is not documented. Held-out prediction cannot decide it (the wrong order
is an exact mirror: swapped winners and inverted ratings predict equally well), so the order is chosen by draft
consistency: bots field similar champions every game, so the correct order gives each frequent team a lower-entropy
champion-type distribution. Bradley-Terry ratings (minorise-maximise, weak prior of one win and one loss against an
average team) are then fitted on all matches. Output: per-team rating (log-strength), games and
wins, and per-replay team ids for team A and B.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def load(decoded):
    rows = []
    for part in sorted(Path(decoded).glob('part*')):
        index = json.loads((part / 'index.json').read_text(encoding='utf-8'))['replays']
        manifest = json.loads((part / 'manifest.json').read_text(encoding='utf-8'))
        for shard in manifest['shards']:
            side = json.loads((part / shard['json']).read_text(encoding='utf-8'))
            with np.load(part / shard['npz'], allow_pickle=False) as z:
                meta, champs, offsets = z['meta'], z['final_champions'], z['champion_offsets']
            cols = side['meta_columns']
            for entry in side['replays']:
                m = dict(zip(cols, meta[entry['row']].tolist()))
                info = index[entry['replay']]
                c = champs[offsets[entry['row']]:offsets[entry['row'] + 1]]
                rows.append(dict(types=[c[c[:, 1] == t][:, 2].tolist() for t in (0, 1)],
                                 replay=entry['replay'], part=part.name, kind=info['kind'], t1=info['team_ids'][0], t2=info['team_ids'][1],
                                 outcome=m['outcome'], rounds=m['rounds'], gems_a=m['submitted_gems_a'], gems_b=m['submitted_gems_b']))
    return rows


def fit(a, b, a_wins, n_teams, iterations=200):
    """Bradley-Terry by MM: p_i <- W_i / sum_j n_ij / (p_i + p_j), with one virtual win and loss vs an average team."""
    p = np.ones(n_teams)
    wins = np.bincount(np.where(a_wins, a, b), minlength=n_teams) + 1.0
    for _ in range(iterations):
        inv = 1.0 / (p[a] + p[b])
        denom = np.bincount(a, inv, n_teams) + np.bincount(b, inv, n_teams) + 2.0 / (p + 1.0)
        p = wins / denom
        p /= np.exp(np.mean(np.log(p)))
    return np.log(p)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--decoded', type=Path, required=True)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    rows = [r for r in load(args.decoded) if r['outcome'] in (1, 2) and r['rounds'] >= 50]
    teams = sorted({r['t1'] for r in rows} | {r['t2'] for r in rows})
    tid = {t: i for i, t in enumerate(teams)}
    t1 = np.array([tid[r['t1']] for r in rows]); t2 = np.array([tid[r['t2']] for r in rows])
    a_won = np.array([r['outcome'] == 1 for r in rows])
    test = np.array([int(hashlib.sha256(r['replay'].encode()).hexdigest()[:8], 16) % 10 == 0 for r in rows])
    verdict = {}
    for name, (a, b) in {'first_is_A': (t1, t2), 'first_is_B': (t2, t1)}.items():
        s = fit(a[~test], b[~test], a_won[~test], len(teams))
        prob = 1 / (1 + np.exp(-(s[a[test]] - s[b[test]])))
        verdict[name] = dict(heldout_accuracy=float(((prob > .5) == a_won[test]).mean()),
                             heldout_logloss=float(-np.mean(np.where(a_won[test], np.log(prob), np.log(1 - prob)))))
    from collections import Counter
    busiest = [t for t, _ in Counter([r['t1'] for r in rows] + [r['t2'] for r in rows]).most_common(60)]
    for name, first_side in (('first_is_A', 0), ('first_is_B', 1)):
        entropies = []
        for team in busiest:
            c = Counter()
            for r in rows:
                if team in (r['t1'], r['t2']):
                    c.update(r['types'][first_side if r['t1'] == team else 1 - first_side])
            q = np.array(list(c.values()), float); q /= q.sum(); entropies.append(float(-(q * np.log(q)).sum()))
        verdict[name]['draft_entropy_top60'] = float(np.mean(entropies))
    order = min(verdict, key=lambda k: verdict[k]['draft_entropy_top60'])
    a, b = (t1, t2) if order == 'first_is_A' else (t2, t1)
    strength = fit(a, b, a_won, len(teams))
    games = np.bincount(a, minlength=len(teams)) + np.bincount(b, minlength=len(teams))
    wins = np.bincount(np.where(a_won, a, b), minlength=len(teams))
    out = dict(order=order, verdict=verdict, matches=len(rows), teams=len(teams),
               ratings={teams[i]: dict(rating=float(strength[i]), games=int(games[i]), wins=int(wins[i])) for i in range(len(teams))},
               replays={r['replay']: dict(team_a=teams[a[i]], team_b=teams[b[i]], outcome=r['outcome'], part=r['part'], kind=r['kind'])
                        for i, r in enumerate(rows)})
    path = args.out or args.decoded / 'team_ratings.json'
    path.write_text(json.dumps(out) + '\n', encoding='utf-8')
    top = sorted(out['ratings'].items(), key=lambda kv: -kv[1]['rating'])
    print(json.dumps(dict(order=order, verdict=verdict, matches=len(rows), teams=len(teams), out=str(path),
                          top10=[(t[:8], round(v['rating'], 2), v['games'], v['wins']) for t, v in top[:10]],
                          rated_20plus=sum(1 for _, v in top if v['games'] >= 20)), indent=1))


if __name__ == '__main__':
    main()
