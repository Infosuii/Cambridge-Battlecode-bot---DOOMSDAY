"""Fit the mimic decision models on rows from tools/mimic/extract.mjs and write bots/mimic/src/weights.h.

  python tools/mimic/train.py --rows <extract out dir> [--rows <dir> ...] [--out bots/mimic/src/weights.h]
         [--report research/mimic/TRAINING.md] [--holdout 10]

Every decision is a linear model over the kernel's candidate features (bots/mimic/src/core.cpp):
  objective, move, target   conditional logit: P(candidate) = softmax over the turn's candidates of w . features
  recall, tribute           logistic: P(yes) = sigmoid(w . features)
Fitting is hierarchical, each level shrunk (L2) toward the level above: all top teams pooled; then per hero (move,
target); then per imitated team (and team x hero). The header holds row 0 = pooled and one row per team, so the bot
imitates one team with MIMIC_TEAM or the pool with -1.

Matches whose number is divisible by --holdout are held out: the report gives held-out accuracy (the model's top
choice is what the top-team champion did) next to simple baselines, per decision.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
KINDS = {'obj': 65, 'move': 36, 'tgt': 19, 'recall': 10, 'trib': 6, 'cast': 24}  # core.h NF_*
HEROES = ['ryth', 'vesper', 'vendetta', 'cassi', 'issac', 'stellar', 'prism', 'marcella', 'willow', 'ren', 'varg', 'tavi',
          'heart']
DEV = 'cuda' if torch.cuda.is_available() else 'cpu'


def load(kind, dirs):
    feats, ncs, labels, metas, cands = [], [], [], [], []
    for d in dirs:
        for f in sorted(Path(d).glob(f'{kind}-w*-*.bin')):
            raw = f.read_bytes()
            nl = raw.index(b'\n')
            hdr = json.loads(raw[:nl])
            if hdr['nf'] != KINDS[kind]:
                raise SystemExit(f'{f}: expected {KINDS[kind]} {kind} features, found {hdr["nf"]}; regenerate rows')
            at = nl + 1
            parts = {}
            for spec, nbytes in zip(hdr['parts'], hdr['bytes']):
                name, dt = spec.split(':')
                parts[name] = np.frombuffer(raw, dtype=np.dtype(dt.replace('f', '<f').replace('i', '<i').replace('u', '<u')),
                                            count=nbytes // int(dt[1:]), offset=at)
                at += nbytes
            feats.append(parts['feat'].reshape(-1, hdr['nf']))
            ncs.append(parts['ncand'])
            labels.append(parts['label'])
            metas.append(parts['meta'].reshape(-1, hdr['metaW']))
            cands.append(parts['cand'])
    if not feats:
        raise SystemExit(f'no {kind} rows under {dirs}')
    return dict(feat=np.concatenate(feats), ncand=np.concatenate(ncs).astype(np.int64),
                label=np.concatenate(labels).astype(np.int64), meta=np.concatenate(metas), cand=np.concatenate(cands))


def subset(data, mask):
    """Rows where mask is true (feature blocks follow their rows)."""
    cmask = np.repeat(mask, data['ncand'])
    return dict(feat=data['feat'][cmask], ncand=data['ncand'][mask], label=data['label'][mask], meta=data['meta'][mask])


class Batch:
    def __init__(self, d):
        self.R = len(d['ncand'])
        self.feat = torch.tensor(d['feat'], dtype=torch.float32, device=DEV)
        nc = torch.tensor(d['ncand'], device=DEV)
        self.seg = torch.repeat_interleave(torch.arange(self.R, device=DEV), nc)
        off = torch.cumsum(nc, 0) - nc
        self.pos = off + torch.tensor(d['label'], device=DEV)
        self.nc = nc


def clogit_nll(w, b):
    s = b.feat @ w
    m = torch.full((b.R,), -1e30, device=DEV).scatter_reduce(0, b.seg, s, 'amax', include_self=True)
    z = torch.zeros(b.R, device=DEV).index_add_(0, b.seg, torch.exp(s - m[b.seg]))
    lse = m + torch.log(z)
    return (lse - s[b.pos]).mean()


def fit(d, binary, prior=None, l2=1e-3, iters=60):
    """Full-batch L-BFGS. Conditional logit, or (binary) logistic where label 1 = yes on the row's one candidate."""
    nf = d['feat'].shape[1]
    if len(d['ncand']) == 0:
        return prior.copy() if prior is not None else np.zeros(nf, np.float32)
    w0 = torch.tensor(prior if prior is not None else np.zeros(nf), dtype=torch.float32, device=DEV)
    w = w0.clone().requires_grad_(True)
    if binary:
        x = torch.tensor(d['feat'], dtype=torch.float32, device=DEV)
        y = torch.tensor(d['label'], dtype=torch.float32, device=DEV)
        loss_fn = lambda: torch.nn.functional.binary_cross_entropy_with_logits(x @ w, y)
    else:
        b = Batch(d)
        loss_fn = lambda: clogit_nll(w, b)
    opt = torch.optim.LBFGS([w], lr=1, max_iter=iters, history_size=20, line_search_fn='strong_wolfe')

    def closure():
        opt.zero_grad()
        loss = loss_fn() + l2 * ((w - w0) ** 2).sum()
        loss.backward()
        return loss
    opt.step(closure)
    return w.detach().cpu().numpy().astype(np.float32)


def evaluate(w, d, binary):
    """Held-out top-1 accuracy (logistic: at threshold 0.5) and mean NLL."""
    if len(d['ncand']) == 0:
        return dict(n=0)
    with torch.no_grad():
        wt = torch.tensor(w, device=DEV)
        if binary:
            x = torch.tensor(d['feat'], dtype=torch.float32, device=DEV)
            y = torch.tensor(d['label'], dtype=torch.float32, device=DEV)
            s = x @ wt
            nll = torch.nn.functional.binary_cross_entropy_with_logits(s, y).item()
            acc = ((s > 0).float() == y).float().mean().item()
            p = torch.sigmoid(s)
            return dict(n=len(y), acc=acc, nll=nll, rate=y.mean().item(), pred_rate=p.mean().item())
        b = Batch(d)
        s = b.feat @ wt
        m = torch.full((b.R,), -1e30, device=DEV).scatter_reduce(0, b.seg, s, 'amax', include_self=True)
        # top-1: the label's score equals the row maximum (ties count as hits only if unique; rare with floats)
        acc = (s[b.pos] >= m).float().mean().item()
        return dict(n=b.R, acc=acc, nll=clogit_nll(wt, b).item())


def baseline_acc(d, kind):
    """Simple rules for comparison: objective = nearest candidate (smallest distance feature); move = the candidate
    that most reduces the objective distance (stay on ties); target = none if available... (lowest hp otherwise)."""
    off = np.concatenate([[0], np.cumsum(d['ncand'])])
    hits = 0
    for r in range(len(d['ncand'])):
        f = d['feat'][off[r]:off[r + 1]]
        if kind == 'obj':
            # distance features: OF_D 4, OB_D 38, OH_D 44 (all d/50), OX_D 53 (d/10)
            dist = np.where(f[:, 0] > 0, f[:, 4], np.where(f[:, 1] > 0, f[:, 38], np.where(f[:, 2] > 0, f[:, 44], f[:, 53] * 10 / 50)))
            pick = int(np.argmin(dist))
        elif kind == 'move':
            pick = int(np.argmin(f[:, 2] - 1e-3 * f[:, 0]))
        elif kind == 'tgt':  # attack the objective if possible, else anything, else none
            score = f[:, 6] * 2 + (1 - f[:, 0]) - f[:, 3] * 0.1
            pick = int(np.argmax(score))
        else:  # cast: on an enemy champion if one is a candidate, else nothing
            score = f[:, 7] * 2 + f[:, 0]
            pick = int(np.argmax(score))
        hits += pick == d['label'][r]
    return hits / max(1, len(d['ncand']))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--rows', action='append', required=True)
    ap.add_argument('--out', default=str(ROOT / 'bots/mimic/src/weights.h'))
    ap.add_argument('--report', default=str(ROOT / 'research/mimic/TRAINING.md'))
    ap.add_argument('--holdout', type=int, default=10)
    ap.add_argument('--l2-team', type=float, default=3e-3)
    ap.add_argument('--l2-hero', type=float, default=1e-3)
    a = ap.parse_args()
    manifest = json.loads((Path(a.rows[0]) / 'manifest.json').read_text(encoding='utf8'))
    for directory in a.rows:
        source = json.loads((Path(directory) / 'manifest.json').read_text(encoding='utf8'))
        if source.get('features', KINDS) != KINDS or any(r.get('error') for r in source['stats']):
            raise SystemExit(f'{directory}: incompatible features or failed replay extraction')
    teams = manifest['teamNames']
    NT = len(teams)
    weights, report = {}, []
    for kind, nf in KINDS.items():
        d = load(kind, a.rows)
        binary = kind in ('recall', 'trib')
        test = d['meta'][:, 5] % a.holdout == 0
        tr, te = subset(d, ~test), subset(d, test)
        print(f'{kind}: {len(tr["ncand"])} train rows, {len(te["ncand"])} held out', flush=True)
        pooled = fit(tr, binary, l2=1e-4)
        per_hero = kind in ('move', 'tgt', 'cast')
        if per_hero:
            hero_w = np.stack([fit(subset(tr, tr['meta'][:, 1] == h), binary, prior=pooled, l2=a.l2_hero) for h in range(13)])
            W = np.zeros((NT + 1, 13, nf), np.float32)
            W[0] = hero_w
            for t in range(NT):
                for h in range(13):
                    m = (tr['meta'][:, 0] == t) & (tr['meta'][:, 1] == h)
                    W[t + 1, h] = fit(subset(tr, m), binary, prior=hero_w[h], l2=a.l2_team) if m.sum() >= 200 else hero_w[h]
        else:
            W = np.zeros((NT + 1, nf), np.float32)
            W[0] = pooled
            for t in range(NT):
                m = tr['meta'][:, 0] == t
                W[t + 1] = fit(subset(tr, m), binary, prior=pooled, l2=a.l2_team) if m.sum() >= 200 else pooled
        weights[kind] = W
        # held-out evaluation: pooled-only and full (each row scored by its team's / hero's weights)
        def ev_with(select):
            hits, n, nll = 0.0, 0, 0.0
            for t in range(NT + 1):
                for h in (range(13) if per_hero else [None]):
                    m = np.ones(len(te['ncand']), bool)
                    if t > 0:
                        m &= te['meta'][:, 0] == t - 1
                    if h is not None:
                        m &= te['meta'][:, 1] == h
                    if not m.any():
                        continue
                    if t == 0 and select == 'team':
                        continue
                    if t > 0 and select == 'pool':
                        continue
                    w = W[t] if h is None else W[t, h]
                    r = evaluate(w, subset(te, m), binary)
                    hits += r['acc'] * r['n']
                    nll += r['nll'] * r['n']
                    n += r['n']
            return dict(n=n, acc=hits / max(1, n), nll=nll / max(1, n))
        pool_r = ev_with('pool')
        team_r = ev_with('team')
        base = None if binary else baseline_acc(te, kind)
        line = dict(kind=kind, train=len(tr['ncand']), test=len(te['ncand']), pooled=pool_r, per_team=team_r, baseline=base)
        if binary:
            line['rate'] = float(te['label'].mean()) if len(te['label']) else None
        print(json.dumps(line), flush=True)
        report.append(line)
    write_header(a.out, teams, weights, manifest)
    write_report(a.report, teams, report, a)


def fmt(v):
    return f'{float(v):.6g}f'


def write_header(path, teams, W, manifest):
    NT = len(teams)
    lines = ['// Generated by tools/mimic/train.py; do not edit by hand.',
             f'// Rows: {len(manifest["items"])} replays. Row 0 = all top teams pooled, then one row per team (kTeamNames).',
             '#pragma once', '#include "core.h"', '', 'namespace mc {', f'constexpr int kNumTeams = {NT};',
             'inline constexpr const char* kTeamNames[kNumTeams] = {' + ', '.join(json.dumps(t) for t in teams) + '};']
    if manifest.get('kernelSha256'):
        lines.insert(2, '// Training kernel SHA256: ' + manifest['kernelSha256'])
    def arr(name, a, dims):
        flat = a.reshape(-1, a.shape[-1])
        body = ',\n'.join('    {' + ', '.join(fmt(x) for x in row) + '}' for row in flat)
        lines.append(f'inline constexpr float {name}{dims}[{a.shape[-1]}] = {{\n{body}}};')
    arr('kObjW', W['obj'], f'[{NT + 1}]')
    lines.append(f'inline constexpr float kMoveW[{NT + 1}][13][{W["move"].shape[-1]}] = {{')
    for t in range(NT + 1):
        lines.append('  {' + ',\n   '.join('{' + ', '.join(fmt(x) for x in W['move'][t, h]) + '}' for h in range(13)) + '},')
    lines.append('};')
    for name, kind in (('kTgtW', 'tgt'), ('kCastW', 'cast')):
        lines.append(f'inline constexpr float {name}[{NT + 1}][13][{W[kind].shape[-1]}] = {{')
        for t in range(NT + 1):
            lines.append('  {' + ',\n   '.join('{' + ', '.join(fmt(x) for x in W[kind][t, h]) + '}' for h in range(13)) + '},')
        lines.append('};')
    arr('kRecallW', W['recall'], f'[{NT + 1}]')
    arr('kTribW', W['trib'], f'[{NT + 1}]')
    lines += ['static_assert(sizeof(kObjW[0]) / sizeof(float) == NF_OBJ);',
              'static_assert(sizeof(kMoveW[0][0]) / sizeof(float) == NF_MOVE);',
              'static_assert(sizeof(kTgtW[0][0]) / sizeof(float) == NF_TGT);',
              'static_assert(sizeof(kCastW[0][0]) / sizeof(float) == NF_CAST);',
              'static_assert(sizeof(kRecallW[0]) / sizeof(float) == NF_RECALL);',
              'static_assert(sizeof(kTribW[0]) / sizeof(float) == NF_TRIB);', '} // namespace mc', '']
    Path(path).write_text('\n'.join(lines), encoding='utf8', newline='\n')
    print('wrote', path)


def write_report(path, teams, report, a):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    out = ['# Mimic training report', '', f'Rows: {", ".join(a.rows)}; held out: matches with number % {a.holdout} == 0.', '',
           '| Decision | Train rows | Held-out rows | Accuracy, pooled | Accuracy, per team | NLL pooled / per team | Rule baseline |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for r in report:
        base = '' if r['baseline'] is None else f'{r["baseline"]:.3f}'
        if r['kind'] in ('recall', 'trib'):
            base = f'always no: {1 - r["rate"]:.3f}' if r.get('rate') is not None else ''
        out.append(f'| {r["kind"]} | {r["train"]} | {r["test"]} | {r["pooled"]["acc"]:.3f} | {r["per_team"]["acc"]:.3f} | '
                   f'{r["pooled"]["nll"]:.3f} / {r["per_team"]["nll"]:.3f} | {base} |')
    Path(path).write_text('\n'.join(out) + '\n', encoding='utf8', newline='\n')
    print('wrote', path)


if __name__ == '__main__':
    main()
