"""Model configuration resolution (agent B).

``configs/model/<name>.json`` gives capacities; observation dimensions come from agent C's generated
``bot/src/nn_schema.h`` (the C++ contract, CONTRACTS 3.3) and per-head candidate widths / context codes / residual
bounds from ``schemas/heads/<name>.json`` (head owners). Missing inputs fall back to documented defaults and are
flagged in ``resolved['provisional']`` so nothing silently pretends to match a schema it was not built against.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .rt import fnv1a32

ROOT = Path(__file__).resolve().parents[3]
ARCH_VERSION = 1
HEAD_NAMES = ['draft_pick', 'strategy', 'objective', 'role', 'bank', 'shop', 'move', 'combat', 'engage', 'ward',
              'belief', 'value', 'ts_leaf']
VALUE_OUTPUTS = ['win_logit', 'margin', 'carry_risk']
MAX = dict(hidden=64, ctx=64, entity=32, rows=32, entity_dim=64, self_dim=256, out=16, F=24, ctx_codes=16)

_SCHEMA_KEYS = {'kObsSchemaHash': 'obs_schema_hash', 'kSelfGlobalDim': 'self_global_dim', 'kAllyRows': 'ally_rows',
                'kAllyDim': 'ally_dim', 'kEnemyRows': 'enemy_rows', 'kEnemyDim': 'enemy_dim', 'kObsDim': 'obs_dim'}


def parse_schema_header(path: Path) -> dict | None:
    """Read the integer constants of nn_schema.h (literal values only). None if absent or incomplete."""
    path = Path(path)
    if not path.exists():
        return None
    text = path.read_text(encoding='utf-8', errors='replace')
    out = {}
    for cname, key in _SCHEMA_KEYS.items():
        m = re.search(r'\b' + cname + r'\s*=\s*(0[xX][0-9a-fA-F]+|\d+)\s*[uUlL]*\s*[;,]', text)
        if m:
            out[key] = int(m.group(1), 0)
    need = set(_SCHEMA_KEYS.values()) - {'obs_dim'}
    if not need <= set(out):
        return None
    out.setdefault('obs_dim', obs_dim(out))
    return out


def obs_dim(o: dict) -> int:
    return (o['self_global_dim'] + o['ally_rows'] * o['ally_dim'] + o['ally_rows'] + o['enemy_rows'] * o['enemy_dim']
            + o['enemy_rows'])


def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')


def head_action_hash(spec: dict) -> int:
    """fnv1a32 of the canonical JSON of the semantically relevant head-schema fields."""
    keep = {k: spec.get(k) for k in ('name', 'id', 'version', 'F', 'K_max', 'contexts', 'residual_bound', 'R',
                                    'outputs', 'n_sectors', 'semantics', 'candidate_ids', 'legality')}
    keep['features'] = [{k: f.get(k) for k in ('name', 'scale', 'clip', 'description')} for f in spec.get('features', [])
                        if isinstance(f, dict)] if isinstance(spec.get('features'), list) else spec.get('features')
    return fnv1a32(canonical_json(keep))


def load_heads_index(root: Path = ROOT) -> list[dict]:
    heads = json.loads((Path(root) / 'schemas/heads.json').read_text(encoding='utf-8'))['heads']
    names = [h['name'] for h in sorted(heads, key=lambda h: h['id'])]
    if names != HEAD_NAMES:
        raise ValueError(f'schemas/heads.json head order {names} != runtime order {HEAD_NAMES}')
    return sorted(heads, key=lambda h: h['id'])


def load_raw_config(name_or_path, root: Path = ROOT) -> dict:
    p = Path(name_or_path)
    if not p.suffix:
        p = Path(root) / 'configs/model' / f'{name_or_path}.json'
    return json.loads(p.read_text(encoding='utf-8'))


def resolve_config(raw: dict, root: Path = ROOT, schema_header: Path | None = None,
                   head_schema_dir: Path | None = None) -> dict:
    """Concrete dimensions for PolicyNet / export / C++ (see module doc)."""
    root = Path(root)
    provisional = []
    obs_cfg = raw.get('obs', {})
    hdr = Path(schema_header) if schema_header else root / obs_cfg.get('schema_header', 'bot/src/nn_schema.h')
    obs = parse_schema_header(hdr)
    if obs is None:
        fb = obs_cfg.get('fallback')
        if not fb:
            raise ValueError(f'no observation schema at {hdr} and no fallback in the model config')
        obs = {k: int(fb[k]) for k in ('self_global_dim', 'ally_rows', 'ally_dim', 'enemy_rows', 'enemy_dim',
                                       'obs_schema_hash')}
        obs['obs_dim'] = obs_dim(obs)
        obs['source'] = 'fallback (no nn_schema.h)'
        provisional.append('obs: fallback dimensions, not agent C schema')
    else:
        obs['source'] = str(hdr)
        if obs['obs_dim'] != obs_dim(obs):
            raise ValueError(f'{hdr}: kObsDim {obs["obs_dim"]} != layout sum {obs_dim(obs)}')
    enc = raw['encoder']
    G, E, C = int(enc['global_hidden']), int(enc['entity_hidden']), int(enc['ctx'])
    sdir = Path(head_schema_dir) if head_schema_dir else root / raw.get('head_schema_dir', 'schemas/heads')
    cand_d, leaf_d = raw['candidate_defaults'], raw['leaf_defaults']
    overrides = raw.get('head_overrides', {})
    heads = []
    for h in load_heads_index(root):
        name, hid = h['name'], h['id']
        ov = overrides.get(name, {})
        spec_path = sdir / f'{name}.json'
        spec = json.loads(spec_path.read_text(encoding='utf-8')) if spec_path.exists() else None
        uses_ctx = bool(h.get('uses_shared_context', True))
        if name in ('value', 'belief'):
            vd = raw['value'] if name == 'value' else raw['belief']
            n_out = len(vd['outputs']) if name == 'value' else int(vd['n_sectors'])
            if spec and name == 'belief' and spec.get('n_sectors'):
                n_out = int(spec['n_sectors'])
            heads.append(dict(name=name, id=hid, kind='value', uses_ctx=uses_ctx, F=0, hidden=int(ov.get('hidden', vd['hidden'])),
                              n_ctx=0, n_out=n_out, R=0.0, action_hash=head_action_hash(spec) if spec else 0,
                              schema=str(spec_path) if spec else None))
            continue
        d = leaf_d if name == 'ts_leaf' else cand_d
        if spec:
            F = int(spec.get('F', d['F']))
            n_ctx = len(spec.get('contexts', [])) if 'contexts' in spec else int(d['n_contexts'])
            R = float(spec.get('residual_bound', spec.get('R', d['residual_bound'])))
            ahash = head_action_hash(spec)
        else:
            F, n_ctx, R = int(d['F']), int(d['n_contexts']), float(d['residual_bound'])
            ahash = head_action_hash(dict(name=name, id=hid, F=F, K_max=16, contexts=n_ctx, residual_bound=R,
                                          features='provisional-default'))
            provisional.append(f'{name}: no schemas/heads/{name}.json, default F={F}')
        F, n_ctx, R = int(ov.get('F', F)), int(ov.get('n_contexts', n_ctx)), float(ov.get('residual_bound', R))
        heads.append(dict(name=name, id=hid, kind='leaf' if name == 'ts_leaf' else 'candidate', uses_ctx=uses_ctx,
                          F=F, hidden=int(ov.get('hidden', d['hidden'])), n_ctx=n_ctx, n_out=1, R=R,
                          action_hash=ahash, schema=str(spec_path) if spec else None))
    cfg = dict(name=raw['name'], arch_version=int(raw.get('arch_version', ARCH_VERSION)), obs=obs,
               encoder=dict(global_hidden=G, entity_hidden=E, ctx=C), heads=heads,
               value_outputs=list(raw['value']['outputs']), provisional=provisional)
    check_limits(cfg)
    return cfg


def check_limits(cfg: dict) -> None:
    o, e = cfg['obs'], cfg['encoder']
    errs = []
    if cfg['arch_version'] != ARCH_VERSION:
        errs.append(f'arch_version {cfg["arch_version"]} != {ARCH_VERSION}')
    if not 0 < o['self_global_dim'] <= MAX['self_dim']:
        errs.append('self_global_dim')
    if o['ally_rows'] > MAX['rows'] or o['enemy_rows'] > MAX['rows']:
        errs.append('entity rows > 32')
    if o['ally_dim'] > MAX['entity_dim'] or o['enemy_dim'] > MAX['entity_dim']:
        errs.append('entity dim > 64')
    if not 0 < e['global_hidden'] <= MAX['hidden'] or not 0 < e['entity_hidden'] <= MAX['entity'] \
            or not 0 < e['ctx'] <= MAX['ctx']:
        errs.append('encoder sizes')
    for h in cfg['heads']:
        if not 0 < h['hidden'] <= MAX['hidden'] or not 0 < h['n_out'] <= MAX['out'] or h['F'] > MAX['F'] \
                or h['n_ctx'] > MAX['ctx_codes']:
            errs.append(f'head {h["name"]} sizes')
        if h['kind'] != 'value' and (h['F'] <= 0 or h['R'] <= 0):
            errs.append(f'head {h["name"]} needs F > 0 and R > 0')
    if errs:
        raise ValueError('model config exceeds runtime limits: ' + ', '.join(errs))


def load_config(name_or_path, root: Path = ROOT, **kw) -> dict:
    return resolve_config(load_raw_config(name_or_path, root), root, **kw)
