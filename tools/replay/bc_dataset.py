"""Normalise raw behaviour-cloning rows from bc_extract.mjs into grouped train/validation training arrays.

    python tools/replay/bc_dataset.py --raw <bc_extract dir> [...] --out <fresh dir> [--val-fraction 0.05]
                                      [--winners-only] [--verify 2000]

Normalisation is vectorised but must equal the policy-v2 Python twins exactly: `--verify N` rebuilds N random rows
with nfs.policy.observation.encode and nfs.policy.candidates.build and refuses to write anything on any difference.
Rows without a label are dropped. Train/validation are split by replay (match), so no match is in both.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))
from nfs.policy import candidates as C, observation as O  # noqa: E402

RAW_FORMAT = 'bc-move-raw-v1'
HEAD = 'move'


def load_raw(directories):
    parts, names = [], []
    for directory in map(Path, directories):
        manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
        if manifest['format'] != RAW_FORMAT:
            raise ValueError(f'unsupported raw format {manifest["format"]}')
        for shard in manifest['shards']:
            path = directory / shard['npz']
            if hashlib.sha256(path.read_bytes()).hexdigest() != shard['sha256']:
                raise ValueError(f'shard hash mismatch: {path}')
            side = json.loads((directory / shard['json']).read_text(encoding='utf-8'))
            with np.load(path, allow_pickle=False) as z:
                a = {k: z[k] for k in z.files}
            a['replay_name'] = np.asarray([side['replays'][i]['replay'] for i in a['replay_row']])
            parts.append(a)
            names += [r['replay'] for r in side['replays']]
    keys = parts[0].keys()
    return {k: np.concatenate([p[k] for p in parts]) for k in keys}, names


def normalise_obs(a):
    n = len(a['obs_self'])
    scale = {k: np.asarray([f['scale'] for f in O.SCHEMA[k]], np.float32) for k in ('self', 'ally', 'enemy')}
    obs = np.zeros((n, O.OBS_DIM), np.float32)
    obs[:, :40] = np.clip(a['obs_self'].astype(np.float32) / scale['self'], -4, 4)
    ally = np.clip(a['obs_ally'].reshape(n, 5, 10).astype(np.float32) / scale['ally'], -4, 4)
    enemy = np.clip(a['obs_enemy'].reshape(n, 6, 12).astype(np.float32) / scale['enemy'], -4, 4)
    am, em = a['ally_mask'].reshape(n, 5).astype(bool), a['enemy_mask'].reshape(n, 6).astype(bool)
    obs[:, 40:90] = (ally * am[:, :, None]).reshape(n, 50)
    obs[:, 90:95] = am
    obs[:, 95:167] = (enemy * em[:, :, None]).reshape(n, 72)
    obs[:, 167:173] = em
    return obs


def normalise_feat(a):
    n = len(a['cand_k'])
    spec = C.HEAD_SPECS[HEAD]['features']
    inv = np.asarray(np.float32(1) / np.asarray([f['scale'] for f in spec], np.float32), np.float32)
    low = np.asarray([f['clip'][0] for f in spec], np.float32)
    high = np.asarray([f['clip'][1] for f in spec], np.float32)
    raw = a['cand_feat'].reshape(n, C.MAX_K, C.F).astype(np.float32)
    feat = np.maximum(low, np.minimum(high, np.asarray(raw * inv, np.float32))).astype(np.float32)
    present = np.arange(C.MAX_K)[None, :] < a['cand_k'].reshape(n, 1)
    return feat * present[:, :, None], (a['cand_legal'].reshape(n, C.MAX_K) * present).astype(np.uint8), present


def verify(a, obs, feat, legal, rows):
    n = len(obs)
    for i in rows:
        expect = O.encode(a['obs_self'][i], a['obs_ally'][i].reshape(5, 10), a['ally_mask'][i], a['obs_enemy'][i].reshape(6, 12),
                          a['enemy_mask'][i])
        if not np.array_equal(expect.view(np.uint32), obs[i].view(np.uint32)):
            raise ValueError(f'observation normalisation differs from observation.encode at row {i}')
        k = int(a['cand_k'][i])
        cands = [C.Candidate(int(a['cand_id'][i, j]), int(a['cand_legal'][i, j]), a['cand_feat'][i].reshape(C.MAX_K, C.F)[j])
                 for j in range(k)]
        d = C.build(HEAD, cands, int(a['context'][i]))
        if not (np.array_equal(d.feat.view(np.uint32), feat[i, :k].view(np.uint32)) and np.array_equal(d.legal, legal[i, :k])
                and np.array_equal(d.id, a['cand_id'][i, :k].astype(np.uint32))):
            raise ValueError(f'candidate normalisation/order differs from candidates.build at row {i}')
    return len(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--raw', nargs='+', required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--val-fraction', type=float, default=0.05)
    p.add_argument('--winners-only', action='store_true')
    p.add_argument('--verify', type=int, default=2000)
    p.add_argument('--seed', type=int, default=20261025)
    a = p.parse_args()
    out = a.out.resolve()
    if not out.is_relative_to(ROOT / 'artifacts') or out.exists():
        raise SystemExit('fresh output directory inside artifacts/ required')
    raw, names = load_raw(a.raw)
    info = raw['info'].reshape(-1, 6)
    keep = raw['label'] >= 0
    if a.winners_only:
        keep &= info[:, 3] == 1
    raw = {k: v[keep] for k, v in raw.items()}
    info = info[keep]
    for k, width in (('cand_id', C.MAX_K), ('cand_legal', C.MAX_K)):
        raw[k] = raw[k].reshape(-1, width)
    obs = normalise_obs(raw)
    feat, legal, present = normalise_feat(raw)
    if not np.isfinite(obs).all() or not np.isfinite(feat).all():
        raise ValueError('nonfinite normalised value')
    label = raw['label'].astype(np.int64)
    if not legal[np.arange(len(label)), label].all():
        raise ValueError('label points at an illegal or padded candidate')
    rng = np.random.default_rng(a.seed)
    checked = verify(raw, obs, feat, legal, rng.choice(len(obs), size=min(a.verify, len(obs)), replace=False)) if a.verify else 0
    group = np.asarray([int(hashlib.sha256(n.encode()).hexdigest()[:15], 16) for n in raw['replay_name']], np.int64)
    validation = (group / 2 ** 60) < a.val_fraction
    out.mkdir(parents=True)
    report = dict(format='bc-move-v1', head=HEAD, head_id=C.HEAD_IDS[HEAD], obs_schema_hash=O.OBS_SCHEMA_HASH,
                  action_schema_hash=C.ACTION_SCHEMA_HASH, sources=[str(Path(r).resolve()) for r in a.raw],
                  winners_only=a.winners_only, val_fraction=a.val_fraction, verified_rows=checked, dropped_unlabelled=int((~keep).sum()),
                  split='by replay name (sha256)', rule_inputs='goal=hindsight position 10 rounds later; role rule; hot_zone=0; claim=127')
    for part, mask in (('train', ~validation), ('validation', validation)):
        np.savez(out / f'{part}.npz', obs=obs[mask], feat=feat[mask], legal=legal[mask], label=label[mask],
                 context=raw['context'][mask].astype(np.int64), group=group[mask], won=info[mask, 3].astype(np.uint8),
                 flags=info[mask, 4].astype(np.uint8), k=raw['cand_k'][mask].astype(np.uint8))
        report[part] = dict(rows=int(mask.sum()), replays=int(len(np.unique(group[mask]))),
                            hold_rate=float((info[mask, 5] == -1).mean()) if mask.any() else None,
                            mean_legal=float(legal[mask].sum(1).mean()) if mask.any() else None)
    if set(group[validation]) & set(group[~validation]):
        raise ValueError('train/validation replay overlap')
    (out / 'manifest.json').write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
