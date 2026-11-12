#!/usr/bin/env python3
"""Network runtime statistics of jdrun.py runs whose candidate was built with JD_NN_LOG (FEAT-003 NN_BENCH.md).

  py tools/jd_g5070-1104/nn_bench.py <run> [<run> ...]  [--out research/jd-g5070-1104/nn_bench.json]

Per run (candidate games only, our team's stdout in each replay bundle):
  decisions per champion (JDN D lines per game and slot), network fuel per decision p50 / p95 / max (event arm: all
  pipeline steps of one decision; every arm: features + forward on the turn), suspended decision steps (JDN O / the
  every arm's crossed-round flag), fallback rate by reason and applied rate over out-of-contact turns, target switches
  per 100 turns, held-decision durations, event counts, refused / aborted / stale / OOD pipelines (last JDN C line of
  each champion). Wins, faults and fuel-outs come from the run's jdrun report (results.json).
"""
import argparse, glob, json, os, statistics, zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EVAL = Path(os.environ.get('JD_EVAL', str(REPO.parent / 'jd-eval')))
FB = ["nodec", "far", "finished", "unreach", "stale", "ood", "maxdur", "respawn", "model"]
EV = ["first", "respawn", "contact", "finished", "unreach", "claim", "bag", "period", "maxdur"]


def pct(v, p):
    if not v:
        return None
    v = sorted(v)
    return v[min(len(v) - 1, int(p * len(v)))]


def parse_c(tok):
    """JDN C r slot turns T contact C applied A switches S dec D pub P refused R aborted X stale S ood O overrun V
    dur SUM N MAX fb <9> ev <9> [rec F N DROP OVER]"""
    d = {}
    i = 4
    while i < len(tok):
        k = tok[i]
        if k == 'dur':
            d['dur_sum'], d['dur_n'], d['dur_max'] = int(tok[i + 1]), int(tok[i + 2]), int(tok[i + 3])
            i += 4
        elif k == 'fb':
            d['fb'] = [int(x) for x in tok[i + 1:i + 1 + len(FB)]]
            i += 1 + len(FB)
        elif k == 'ev':
            d['ev'] = [int(x) for x in tok[i + 1:i + 1 + len(EV)]]
            i += 1 + len(EV)
        elif k == 'rec':
            d['rec'] = [int(x) for x in tok[i + 1:i + 5]]
            i += 5
        elif k == 'resid':
            d['resid_n'], d['resid_ok'] = int(tok[i + 1]), int(tok[i + 2])
            i += 3
        else:
            d[k] = int(tok[i + 1])
            i += 2
    return d


def run_stats(name):
    out = EVAL / 'runs' / name
    res = json.loads((out / 'results.json').read_text(encoding='utf-8'))
    used, mxstep, turns_per, dec_per, over = [], [], [], [], 0
    agg = dict(turns=0, contact=0, applied=0, switches=0, dec=0, pub=0, refused=0, aborted=0, stale=0, ood=0, overrun=0,
               dur_sum=0, dur_n=0, dur_max=0, fb=[0] * len(FB), ev=[0] * len(EV))
    champs = games = 0
    for b in sorted(glob.glob(str(out / 'games' / 'cand__*.repl26a'))):
        side = b[-9]
        try:
            txt = zipfile.ZipFile(b).read(f'team-{side.lower()}.stdout').replace(b'\0', b'\n').decode('utf-8', 'replace')
        except Exception:  # noqa: BLE001
            continue
        games += 1
        per_slot, last_c = {}, {}
        for l in txt.splitlines():
            if l.startswith('JDN D '):
                t = l.split()
                if len(t) < 9:
                    continue
                per_slot[t[3]] = per_slot.get(t[3], 0) + 1
                if int(t[4]) < 50_000_000:  # the every arm's unsigned difference wraps when a turn resumed with more fuel
                    used.append(int(t[4]))
                    mxstep.append(int(t[5]))
                if t[8] == 'every':
                    over += int(t[7])
                else:
                    turns_per.append(int(t[7]))
            elif l.startswith('JDN O '):
                over += 1 if 'every' not in l else 0
            elif l.startswith('JDN C '):
                t = l.split()
                last_c[t[3]] = parse_c(t)
        for s, c in last_c.items():
            champs += 1
            dec_per.append(per_slot.get(s, 0))
            for k in agg:
                if k == 'dur_max':
                    agg[k] = max(agg[k], c.get(k, 0))
                elif k in ('fb', 'ev'):
                    agg[k] = [a + b for a, b in zip(agg[k], c.get(k, [0] * len(agg[k])))]
                else:
                    agg[k] += c.get(k, 0)
    nc = max(1, agg['turns'] - agg['contact'])
    cand, base = res['arms']['cand'], res['arms'].get('base', res['arms']['cand'])
    return dict(run=name, cand=res['cand'], maps=res['maps'], cells=res['paired']['cells'], played=res['played'],
                missing=res['missing'], failed=res['failed'],
                cand_wins=cand['wins'], base_wins=base['wins'], cand_winrate=res['paired']['cand_winrate'],
                base_winrate=res['paired']['base_winrate'], d_score=res['paired']['d_score'], ci95=res['paired']['ci95'],
                faults=cand['faults'], base_faults=base['faults'], fuel_outs=cand['fuel_outs'], base_fuel_outs=base['fuel_outs'],
                fuel_out_games=cand['fuel_out_games'], base_fuel_out_games=base['fuel_out_games'],
                games_logged=games, champions=champs,
                decisions=len(used), decisions_per_champion=round(statistics.mean(dec_per), 1) if dec_per else 0,
                fuel_per_decision=dict(p50=pct(used, .5), p95=pct(used, .95), max=max(used) if used else None),
                max_step_fuel=dict(p50=pct(mxstep, .5), p95=pct(mxstep, .95), max=max(mxstep) if mxstep else None),
                decision_turns=dict(p50=pct(turns_per, .5), p95=pct(turns_per, .95), max=max(turns_per) if turns_per else None),
                suspended_steps=over,
                out_of_contact_turns=nc, applied_rate=round(agg['applied'] / nc, 3),
                fallback_rate={FB[i]: round(v / nc, 3) for i, v in enumerate(agg['fb']) if v},
                switches_per_100_turns=round(100 * agg['switches'] / max(1, agg['turns']), 2),
                hold_duration=dict(mean=round(agg['dur_sum'] / agg['dur_n'], 1) if agg['dur_n'] else None, max=agg['dur_max'],
                                   n=agg['dur_n']),
                events={EV[i]: v for i, v in enumerate(agg['ev']) if v},
                refused=agg['refused'], aborted=agg['aborted'], stale=agg['stale'], ood=agg['ood'], overrun=agg['overrun'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('runs', nargs='+')
    ap.add_argument('--out', default=str(REPO / 'research' / 'jd-g5070-1104' / 'nn_bench.json'))
    a = ap.parse_args()
    rows = [run_stats(r) for r in a.runs]
    old = json.loads(Path(a.out).read_text(encoding='utf-8')) if Path(a.out).exists() else {}
    old.update({r['run']: r for r in rows})
    Path(a.out).write_text(json.dumps(old, indent=1) + '\n', encoding='utf-8')
    for r in rows:
        print(json.dumps(r))


if __name__ == '__main__':
    main()
