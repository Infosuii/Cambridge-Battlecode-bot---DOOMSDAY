"""Gameplay-bug and behaviour audit of decoded ladder matches (ladder_decode.py dumps): per game and team, standing
still (and why), blocked-movement streaks, deaths (bag lost, outnumbered), banking, unspent gold, items, wards and our
fuel-outs; us against the opponent, split by result, plus the worst individual episodes.
usage: python -I tools/rl_env_1104/ladder_bugs.py --cache artifacts/tmp/ladder_1110 --versions v130 v134 v135 [--json out.json]
"""
import argparse, collections, json, os, statistics as st, struct, sys, zipfile

cheb = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def fuel_outs(zpath, side):
    try:
        with zipfile.ZipFile(zpath) as z:
            name = next((n for n in z.namelist() if n.endswith(f"team-{side}.fuel")), None)
            if not name:
                return None
            b = z.read(name)
        k = (len(b) - 13) // 8
        v = struct.unpack("<%dQ" % k, b[13:13 + 8 * k])[8:]
        return sum(1 for x in v[11:] if x >= 100000)
    except Exception:
        return None


def team_metrics(d, team):
    fr, steps = d["frames"], d["steps"]
    ids = {c[0] for _, cs in fr[:3] for c in cs if c[1] == team}
    by_actor_round = collections.defaultdict(lambda: collections.Counter())
    for s in steps:
        if s[2] in ids:
            by_actor_round[(s[2], s[0])][s[1]] += 1
    m = collections.Counter()
    episodes = []
    hist = collections.defaultdict(list)
    for r, cs in fr:
        for c in cs:
            if c[0] in ids:
                hist[c[0]].append((r, c))
    for cid, h in hist.items():
        run_start = None
        blocked_run = 0
        for i in range(1, len(h)):
            (r0, a), (r1, b) = h[i - 1], h[i]
            if not b[6]:
                continue
            m["alive"] += 1
            m["gold_sum"] += b[8]
            acts = by_actor_round.get((cid, r1), {})
            if acts.get("Movement blocked"):
                blocked_run += 1
            else:
                if blocked_run >= 10:
                    m["blocked_streaks"] += 1
                    m["blocked_streak_rounds"] += blocked_run
                    episodes.append(("blocked", blocked_run, cid, r1 - blocked_run, (b[3], b[4]), b[7]))
                blocked_run = 0
            same = a[6] and (a[3], a[4]) == (b[3], b[4]) and a[3] is not None
            if same:
                m["still"] += 1
                if run_start is None:
                    run_start = i - 1
            if (not same or i == len(h) - 1) and run_start is not None:
                L = (i if same else i - 1) - run_start
                if L >= 20:
                    kinds = collections.Counter()
                    for j in range(run_start, run_start + L + 1):
                        kinds.update(by_actor_round.get((cid, h[j][0]), {}))
                    cause = ("blocked" if kinds.get("Movement blocked", 0) >= L // 2 else
                             "recall-loop" if kinds.get("Recall", 0) >= L // 2 else
                             "fighting" if kinds.get("Attack", 0) + kinds.get("Cast ability", 0) >= L // 3 else "idle")
                    m["long_still_" + cause] += L
                    p = h[run_start][1]
                    episodes.append(("still-" + cause, L, cid, h[run_start][0], (p[3], p[4]), p[7]))
                run_start = None
            # deaths
            if a[6] and not b[6]:
                pass
        # deaths: alive -> dead transitions
        for i in range(1, len(h)):
            (r0, a), (r1, b) = h[i - 1], h[i]
            if a[6] and not b[6]:
                m["deaths"] += 1
                m["gems_lost"] += a[7]
                me = (a[3], a[4])
                frame = next(cs for r, cs in fr if r == r0)
                foes = sum(1 for c in frame if c[1] != team and c[6] and c[3] is not None and cheb((c[3], c[4]), me) <= 4)
                allies = sum(1 for c in frame if c[1] == team and c[0] != cid and c[6] and c[3] is not None and cheb((c[3], c[4]), me) <= 4)
                m["deaths_outnumbered"] += foes > allies + 1
                if a[7] >= 40:
                    episodes.append(("death-bag", a[7], cid, r0, me, a[7]))
    for s in steps:
        if s[2] in ids:
            if s[1] == "Gems submitted":
                m["banks"] += 1
            elif s[1] == "Place ward":
                m["wards"] += 1
            elif s[1] == "Shop":
                m["shops"] += 1
    last = fr[-1][1]
    m["unbanked_end"] = sum(c[7] for c in last if c[1] == team and c[6])
    m["gold_end"] = sum(c[8] for c in last if c[1] == team)
    m["items_end"] = sum(sum(it) for cid, tm, ty, it in d["items"] if tm == team)
    return m, episodes


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--versions", nargs="+", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    matches = json.load(open(os.path.join(a.cache, "matches.json"), encoding="utf-8"))
    rows, all_eps = [], []
    for mt in matches:
        if mt.get("version") not in a.versions:
            continue
        p = os.path.join(a.cache, "dumps", mt["matchId"] + ".json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        side = mt["us"].get("side", "a")
        us_t = 0 if side == "a" else 1
        mu, eu = team_metrics(d, us_t)
        mo, _ = team_metrics(d, 1 - us_t)
        fo = fuel_outs(os.path.join(a.cache, "zips", mt["matchId"] + ".zip"), side)
        rows.append(dict(id=mt["matchId"], map=mt.get("map"), opp=mt["opp"].get("name"), result=mt["us"].get("result"),
                         version=mt["version"], rounds=d["frames"][-1][0], us=dict(mu), them=dict(mo), fuel_outs=fo))
        for e in eu:
            all_eps.append((e, mt.get("map"), mt["opp"].get("name"), mt["us"].get("result"), mt["matchId"]))
    print(f"{len(rows)} decoded games ({collections.Counter(r['result'] for r in rows)})")
    keys = ["still", "long_still_idle", "long_still_blocked", "long_still_recall-loop", "long_still_fighting",
            "blocked_streak_rounds", "deaths", "deaths_outnumbered", "gems_lost", "banks", "unbanked_end",
            "gold_end", "items_end", "wards", "shops"]
    for res in ("win", "loss"):
        rs = [r for r in rows if r["result"] == res]
        if not rs:
            continue
        print(f"\n== {res}s ({len(rs)} games): per game, us | them  (still = % of alive champion-rounds)")
        for k in keys:
            if k == "still":
                u = st.mean(100 * r["us"].get("still", 0) / max(1, r["us"].get("alive", 1)) for r in rs)
                t = st.mean(100 * r["them"].get("still", 0) / max(1, r["them"].get("alive", 1)) for r in rs)
                print(f"  {'still %':26s} {u:8.1f} | {t:8.1f}")
            else:
                u = st.mean(r["us"].get(k, 0) for r in rs)
                t = st.mean(r["them"].get(k, 0) for r in rs)
                print(f"  {k:26s} {u:8.1f} | {t:8.1f}")
        fo = [r["fuel_outs"] for r in rs if r["fuel_outs"] is not None]
        if fo:
            print(f"  {'our fuel-outs':26s} {st.mean(fo):8.1f}")
    print("\n== worst episodes (ours)")
    for kind in ("blocked", "still-blocked", "still-idle", "still-recall-loop", "death-bag"):
        eps = sorted((x for x in all_eps if x[0][0] == kind), key=lambda x: -x[0][1])[:8]
        if eps:
            print(f"  -- {kind}: {sum(1 for x in all_eps if x[0][0] == kind)} episodes")
            for (k, L, cid, r, pos, bag), mp, opp, res, mid in eps:
                print(f"     {L:4d} | champ {cid} round {r:4d} at {pos} bag {bag:3d} | {mp} vs {opp} ({res}) {mid[-12:]}")
    if a.json:
        json.dump(dict(rows=rows, episodes=all_eps), open(a.json, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()
