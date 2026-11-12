"""Model registry, manifest schema, lifecycle and compatibility checks (agent B; CONTRACTS section 5).

models/registry.json lists installed models; each has models/<name>/manifest.json. ``resolve_profile`` turns a
profile (configs/profiles/<name>.json) + the registry + the current schemas into a per-head plan
{mode, model, reason}; ``tools/install_models.py`` renders that plan into nn_config.h / nn_registry.h /
nn_weights_*.h. Lifecycle rules enforced here:
  * release: a head may be active only with a 'validated', schema-compatible model named in release_selection;
  * active with any non-validated model only in profiles whose allow_active_status lists that status
    (dev_untrained, training, selftest);
  * shadow needs the status in allow_shadow_status (neutral_* profiles accept untrained zero-residual models);
  * a model that is not exportable to the new schema (draft_net_original) is never installed as a head;
  * any checksum, NaN/Inf, arch or schema-hash mismatch turns the head off (teacher) and is reported.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from .models.config import ROOT, HEAD_NAMES, head_action_hash, load_heads_index, parse_schema_header
from .models.rt import fnv1a64_f32

STATUSES = ('untrained', 'teacher_initialized', 'trained', 'validated')
MODES = ('off', 'shadow', 'active')
REQUIRED = dict(name=str, head=str, arch_version=int, architecture=dict, obs_schema_hash=str, action_schema_hash=str,
                n_params=int, checksum=str, export_precision=str, engine_version=str, provenance=dict, status=str,
                validation=dict)
ENGINE_VERSION = '1.0.3'


class RegistryError(ValueError):
    pass


def load_json(p) -> dict:
    return json.loads(Path(p).read_text(encoding='utf-8'))


def load_registry(root: Path = ROOT) -> dict:
    return load_json(Path(root) / 'models/registry.json')


def load_profile(name: str, root: Path = ROOT) -> dict:
    p = Path(root) / 'configs/profiles' / f'{name}.json'
    if not p.exists():
        raise RegistryError(f'unknown profile {name} ({p})')
    prof = load_json(p)
    for key in ('name', 'mode', 'heads', 'model', 'allow_active_status', 'allow_shadow_status', 'training',
                'telemetry', 'fuel_credit', 'selftest', 'strip_lab', 'seed'):
        if key not in prof:
            raise RegistryError(f'profile {name}: missing {key}')
    if prof['mode'] not in MODES or any(v not in MODES for v in prof['heads'].values()):
        raise RegistryError(f'profile {name}: bad mode')
    unknown = set(prof['heads']) - set(HEAD_NAMES)
    if unknown:
        raise RegistryError(f'profile {name}: unknown heads {sorted(unknown)}')
    return prof


def validate_manifest(m: dict, model_dir: Path | None = None, check_weights: bool = True) -> list[str]:
    """Schema + lifecycle validation of one manifest; with model_dir, the weights are re-hashed."""
    errs = []
    for k, t in REQUIRED.items():
        if k not in m:
            errs.append(f'missing {k}')
        elif not isinstance(m[k], t):
            errs.append(f'{k}: expected {t.__name__}')
    if errs:
        return errs
    if m['status'] not in STATUSES:
        errs.append(f'status {m["status"]!r} not in {STATUSES}')
    if m['export_precision'] != 'f32':
        errs.append('export_precision must be f32')
    if m['engine_version'] != ENGINE_VERSION:
        errs.append(f'engine_version {m["engine_version"]} != {ENGINE_VERSION}')
    for k in ('obs_schema_hash', 'action_schema_hash'):
        if not (m[k].startswith('0x') and len(m[k]) == 10):
            errs.append(f'{k} must be 0x + 8 hex digits')
    if not (m['checksum'].startswith('0x') and len(m['checksum']) == 18):
        errs.append('checksum must be 0x + 16 hex digits')
    if m['status'] == 'validated' and not m['validation'].get('passed'):
        errs.append('status validated requires validation.passed = true')
    if m['status'] in ('trained', 'validated') and not m['provenance'].get('source'):
        errs.append('trained/validated models need provenance.source')
    if m.get('exportable', True) and check_weights and model_dir is not None:
        wf = Path(model_dir) / m.get('files', {}).get('weights', 'weights.f32')
        if not wf.exists():
            errs.append(f'weights file missing: {wf.name}')
        else:
            blob = np.frombuffer(wf.read_bytes(), dtype='<f4')
            if blob.size != m['n_params']:
                errs.append(f'weights: {blob.size} floats != n_params {m["n_params"]}')
            elif not np.all(np.isfinite(blob)):
                errs.append('weights contain NaN/Inf')
            elif f'0x{fnv1a64_f32(blob):016x}' != m['checksum']:
                errs.append(f'checksum mismatch: weights 0x{fnv1a64_f32(blob):016x} != manifest {m["checksum"]}')
    return errs


def current_head_hashes(root: Path = ROOT, head_schema_dir: Path | None = None, cfg_defaults: dict | None = None,
                        manifest_cfg: dict | None = None) -> dict[str, int]:
    """Action schema hash of every candidate/leaf head under the current schemas/heads/*.json (default spec if
    absent, computed from the model's own F/contexts/R exactly as config.resolve_config does)."""
    sdir = Path(head_schema_dir) if head_schema_dir else Path(root) / 'schemas/heads'
    out = {}
    mheads = {h['name']: h for h in (manifest_cfg or {}).get('heads', [])}
    for h in load_heads_index(root):
        p = sdir / f'{h["name"]}.json'
        if p.exists():
            out[h['name']] = head_action_hash(load_json(p))
        elif h['name'] in ('value', 'belief'):
            out[h['name']] = 0
        elif h['name'] in mheads:
            mh = mheads[h['name']]
            out[h['name']] = head_action_hash(dict(name=h['name'], id=h['id'], F=mh['F'], K_max=16,
                                                   contexts=mh['n_ctx'], residual_bound=mh['R'],
                                                   features='provisional-default'))
        else:
            out[h['name']] = None
    return out


def compat_problems(manifest: dict, obs: dict | None, head_hashes: dict[str, int]) -> dict[str, list[str]]:
    """Per-head incompatibilities of a model with the current observation schema and head schemas."""
    cfg = manifest.get('config') or {}
    out = {}
    arch_obs = manifest['architecture'].get('obs', {})
    obs_issue = []
    if obs is None:
        obs_issue.append('no nn_schema.h (agent C) in the target source tree')
    else:
        if int(manifest['obs_schema_hash'], 16) != obs['obs_schema_hash']:
            obs_issue.append(f'obs schema hash {manifest["obs_schema_hash"]} != current 0x{obs["obs_schema_hash"]:08x}')
        for k in ('self_global_dim', 'ally_rows', 'ally_dim', 'enemy_rows', 'enemy_dim'):
            if arch_obs.get(k) != obs[k]:
                obs_issue.append(f'{k} {arch_obs.get(k)} != current {obs[k]}')
    if manifest['arch_version'] != 1:
        obs_issue.append(f'arch_version {manifest["arch_version"]} unsupported')
    for h in cfg.get('heads', manifest['architecture'].get('heads', [])):
        # The observation schema matters for heads reading the shared context; nn_head.cpp needs nn_schema.h always.
        p = list(obs_issue) if h.get('uses_ctx', True) else (['no nn_schema.h (agent C)'] if obs is None else [])
        # Value output units and sector conventions are schema semantics too.
        cur = head_hashes.get(h['name'])
        if cur is None or cur != h['action_hash']:
            p.append(f'action schema hash 0x{h["action_hash"]:08x} != current '
                     f'{"none" if cur is None else f"0x{cur:08x}"}')
        out[h['name']] = p
    return out


def resolve_profile(profile: dict, registry: dict, root: Path = ROOT, src_dir: Path | None = None,
                    head_schema_dir: Path | None = None) -> dict:
    """Per-head plan {mode, model, reason} for a profile. Never raises for a bad model: the head goes off."""
    root = Path(root)
    src = Path(src_dir) if src_dir else root / 'bot/src'
    obs = parse_schema_header(src / 'nn_schema.h')
    obs_iface = (src / 'nn_obs.h').exists()
    plan = dict(profile=profile['name'], heads={}, models=[], notes=[])
    manifests = {}

    def manifest_of(name):
        if name in manifests:
            return manifests[name]
        entry = registry['models'].get(name)
        if entry is None:
            manifests[name] = (None, f'model {name} not in registry')
            return manifests[name]
        mdir = root / entry['path']
        try:
            m = load_json(mdir / 'manifest.json')
        except FileNotFoundError:
            manifests[name] = (None, f'{name}: manifest missing')
            return manifests[name]
        errs = validate_manifest(m, mdir) if m.get('exportable', True) else validate_manifest(m, None, False)
        if m.get('status') != entry.get('status'):
            errs.append(f'registry status {entry.get("status")} != manifest status {m.get("status")}')
        manifests[name] = (m, '; '.join(errs) if errs else None)
        return manifests[name]

    selection = registry.get('release_selection', {}) if profile['model'] == 'release_selection' else None
    for h in load_heads_index(root):
        name = h['name']
        want = profile['heads'].get(name, profile['mode'])
        mname = (selection.get(name) if selection is not None else profile['model']) if want != 'off' else None
        rec = dict(mode='off', model=None, requested=want, reason=None)
        if want == 'off':
            rec['reason'] = 'profile'
        elif not mname:
            rec['reason'] = 'no model selected'
        else:
            m, err = manifest_of(mname)
            status = m.get('status') if m else None
            if m is None or err:
                rec['reason'] = err or 'manifest invalid'
            elif not m.get('exportable', True):
                rec['reason'] = f'{mname} is not exportable to the neural schema (provenance-only entry)'
            elif not obs_iface:
                rec['reason'] = 'nn_obs.h (agent C) missing in the target source tree'
            else:
                probs = compat_problems(m, obs, current_head_hashes(root, head_schema_dir, manifest_cfg=m.get('config')))
                mode = want
                if mode == 'active' and status not in profile['allow_active_status']:
                    mode = 'shadow' if status in profile['allow_shadow_status'] else 'off'
                    rec['reason'] = f'status {status} may not be active in {profile["name"]}'
                if mode == 'shadow' and status not in profile['allow_shadow_status']:
                    mode = 'off'
                    rec['reason'] = f'status {status} may not run in {profile["name"]}'
                if mode != 'off' and profile.get('require_zero_residual') and not m.get('zero_residual'):
                    mode, rec['reason'] = 'off', 'profile requires a zero-residual model'
                if mode != 'off' and name not in probs:
                    mode, rec['reason'] = 'off', f'{mname} has no {name} head'
                if mode != 'off' and probs.get(name):
                    mode, rec['reason'] = 'off', 'incompatible: ' + '; '.join(probs[name])
                if mode != 'off':
                    rec.update(mode=mode, model=mname)
        plan['heads'][name] = rec
    used = sorted({r['model'] for r in plan['heads'].values() if r['model']})
    ctx_models = sorted({plan['heads'][h['name']]['model'] for h in load_heads_index(root)
                         if h.get('uses_shared_context') and plan['heads'][h['name']]['model']})
    if len(ctx_models) > 1:
        keep = ctx_models[0]
        plan['notes'].append(f'shared-context heads must share one encoder; keeping {keep}, turning off {ctx_models[1:]}')
        for hname, r in plan['heads'].items():
            if r['model'] in ctx_models[1:]:
                r.update(mode='off', model=None, reason='second encoder not supported')
        used = sorted({r['model'] for r in plan['heads'].values() if r['model']})
    plan['models'] = used
    plan['ctx_model'] = ctx_models[0] if ctx_models else None
    plan['manifests'] = {n: manifests[n][0] for n in used}
    plan['any_head'] = any(r['mode'] != 'off' for r in plan['heads'].values())
    plan['obs'] = obs
    return plan


# ---------------------------------------------------------------------- fuel cost model (models/budget.json)
def dense_cost(c: dict, n_in: int, n_out: int, density: float = 1.0) -> float:
    rows = math.ceil(n_in * density)
    return c['dense_call'] + rows * (c['dense_row'] + math.ceil(n_out / 4) * c['dense_v4'])


def act_cost(c: dict, n: int) -> float:
    return c['act_call'] + math.ceil(n / 4) * c['act_v4']


def model_costs(cfg: dict, budget: dict) -> dict:
    """Worst-case fuel per component for a resolved config (all rows valid, dense inputs) x safety factor."""
    c = budget['coefficients']
    sf = budget['policy']['safety_factor']
    o, e = cfg['obs'], cfg['encoder']
    G, E, C = e['global_hidden'], e['entity_hidden'], e['ctx']
    enc = (dense_cost(c, o['self_global_dim'], G) + act_cost(c, G)
           + o['ally_rows'] * (dense_cost(c, o['ally_dim'], E) + act_cost(c, E) + c['pool_row'])
           + o['enemy_rows'] * (dense_cost(c, o['enemy_dim'], E) + act_cost(c, E) + c['pool_row'])
           + dense_cost(c, G + 4 * E, C) + act_cost(c, C) + c['finite_v4'] * math.ceil(C / 4)
           + c['finite_v4'] * math.ceil(o['obs_dim'] / 4) + c['encoder_fixed'])
    heads = {}
    for h in cfg['heads']:
        H = h['hidden']
        pre = c['head_fixed'] + H * c['scalar_op'] + (dense_cost(c, C, H) if h['uses_ctx'] else 0) + \
            (math.ceil(H / 4) * c['dense_v4'] if h['n_ctx'] else 0)
        if h['kind'] == 'value':
            fixed = pre + act_cost(c, H) + dense_cost(c, H, h['n_out'])
            per = 0
        else:
            fixed = pre
            per = (c['cand_fixed'] + H * c['scalar_op'] + dense_cost(c, h['F'], H) + act_cost(c, H)
                   + H * c['dot_elem'] + c['bounded'] + c['finite_v4'] * math.ceil(h['F'] / 4) + c['argmax_elem'])
        heads[h['name']] = dict(fixed=int(math.ceil(fixed * sf)), per_cand=int(math.ceil(per * sf)))
    return dict(encoder=int(math.ceil(enc * sf)), heads=heads)
