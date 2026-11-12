"""Loss study: one row per recent loss to a strong team (tools/ladder/losses_recent.py), with what both teams did.

  python tools/ladder/loss_study.py [--data data/ladder/losses48] [--replays artifacts/local-only/losses48] [--jobs 4]
Steps: extract replay.repl26a from each match bundle; run tools/replay/winner_profile.mjs over them in parallel
chunks (cached in <replays>/profiles/); read each summary for items, emblems, consumables, wards, deposits, kills
and gem losses; write research/x3/losses48/rows.json (row: match, map, our side, opponent, rating, both drafts,
and per team "us" / "them": profile + summary stats).
"""
import argparse, json, os, subprocess, sys, zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
CHAR = json.loads((ROOT / 'data/ladder/char_ids.json').read_text())  # platform character id -> name


def summary_stats(s, team):
    ev = [(e['kind'], x) for e in s['events'] if e['owner'].get('team') == team for x in e['entries']]
    rnd = lambda x: x['timestamp']['round']
    buys = sorted([(rnd(x), x['target']['name'], int(x['value'])) for k, x in ev if k == 'buyItem'])
    fam = lambda n: n.split(' ')[0]
    by300 = {}
    for r, n, q in buys:
        if r < 300: by300[fam(n)] = by300.get(fam(n), 0) + q
    tot = {}
    for r, n, q in buys: tot[fam(n)] = tot.get(fam(n), 0) + q
    emb = sorted([(rnd(x), x['target']['name']) for k, x in ev if k == 'itemCombination'])
    cons = {}
    for k, x in ev:
        if k == 'buyConsumable': cons[x['target']['name']] = cons.get(x['target']['name'], 0) + int(x['value'])
    wards = sorted(rnd(x) for k, x in ev if k == 'wardPlacement')
    deps = sorted((rnd(x), int(x['value'])) for k, x in ev if k == 'gemSubmission')
    kills = sorted(rnd(x) for k, x in ev if k == 'kill')
    deaths = sorted(rnd(x) for k, x in ev if k == 'death')
    lost = sum(int(x['value']) for k, x in ev if k == 'gemLoss')
    clears = sorted(rnd(x) for k, x in ev if k == 'campClear')
    order, seen = [], set()
    for r, n, q in buys:
        f = fam(n) + (' ' + n.split(' of ')[-1] if ' of ' in n else '')
        if f not in seen: seen.add(f); order.append((r, f))
    return dict(
        first_buys=order[:6], first_emblem=emb[0] if emb else None, emblems_by_300=sum(1 for r, _ in emb if r < 300), emblems=len(emb),
        shards_by300=by300, shards_total=tot, consumables=cons, wards=len(wards), first_ward=wards[0] if wards else None,
        deposits=len(deps), deposit_mean=round(sum(v for _, v in deps) / len(deps), 1) if deps else 0, first_deposit=deps[0][0] if deps else None,
        banked_by=[sum(v for r, v in deps if r < R) for R in (150, 300, 600, 1000)], kills_by=[sum(1 for r in kills if r < R) for R in (150, 300, 600)],
        deaths_by=[sum(1 for r in deaths if r < R) for R in (150, 300, 600)], gems_lost=lost, clears_by=[sum(1 for r in clears if r < R) for R in (150, 300, 600)])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--data', default='data/ladder/losses48'); ap.add_argument('--replays', default='artifacts/local-only/losses48')
    ap.add_argument('--jobs', type=int, default=4); ap.add_argument('--out', default='research/x3/losses48')
    a = ap.parse_args()
    data, rep, out = ROOT / a.data, ROOT / a.replays, ROOT / a.out
    (rep / 'rep').mkdir(parents=True, exist_ok=True); (rep / 'profiles').mkdir(exist_ok=True); out.mkdir(parents=True, exist_ok=True)
    matches = json.loads((data / 'matches.json').read_text(encoding='utf-8'))
    have = []
    for m in matches:
        z, r = rep / f"{m['matchId']}.zip", rep / 'rep' / f"{m['matchId']}.repl26a"
        if not r.exists() and z.exists():
            try:
                with zipfile.ZipFile(z) as zz: r.write_bytes(zz.read('replay.repl26a'))
            except Exception as e: print('bad bundle', m['matchId'], e); continue
        if r.exists(): have.append(m)
    todo = [m for m in have if not (rep / 'profiles' / f"{m['matchId']}.json").exists()]
    print(len(matches), 'losses;', len(have), 'replays;', len(todo), 'to profile', flush=True)
    env = dict(os.environ, NFS_REPLAY_ENGINE='2.0.0')
    chunks = [todo[i::a.jobs * 6] for i in range(a.jobs * 6)]
    def run(chunk):
        if not chunk: return
        tmp = rep / 'profiles' / f"_chunk_{chunk[0]['matchId']}.json"
        subprocess.run(['node', str(ROOT / 'tools/replay/winner_profile.mjs'), str(tmp)] + [str(rep / 'rep' / f"{m['matchId']}.repl26a") for m in chunk],
                       env=env, capture_output=True)
        if tmp.exists():
            for m, p in zip(chunk, json.loads(tmp.read_text())):
                (rep / 'profiles' / f"{m['matchId']}.json").write_text(json.dumps(p))
            tmp.unlink()
    with ThreadPoolExecutor(a.jobs) as ex: list(ex.map(run, chunks))
    rows = []
    for m in have:
        pf, sf = rep / 'profiles' / f"{m['matchId']}.json", data / 'summaries' / f"{m['matchId']}.json"
        if not pf.exists() or not sf.exists(): continue
        p = json.loads(pf.read_text()); s = json.loads(sf.read_text(encoding='utf-8'))
        if 'teams' not in p: continue
        ui = 0 if m['side'] == 'a' else 1; us, them = ('teamA', 'teamB') if ui == 0 else ('teamB', 'teamA')
        names = lambda d: [CHAR.get(str(c), str(c)) for c in (d or [])]
        rows.append(dict(m, our_names=names(m['our_draft']), their_names=names(m['their_draft']), rounds=p.get('rounds'),
                         first_blood_by=None if not p.get('first_blood') else ('us' if p['first_blood']['by'] == ui else 'them'),
                         first_blood_round=(p.get('first_blood') or {}).get('round'),
                         us=dict(profile=p['teams'][ui], **summary_stats(s, us)), them=dict(profile=p['teams'][1 - ui], **summary_stats(s, them))))
    (out / 'rows.json').write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
    print(len(rows), 'rows ->', out / 'rows.json')


if __name__ == '__main__':
    main()
