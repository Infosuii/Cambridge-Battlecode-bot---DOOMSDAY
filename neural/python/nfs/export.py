"""PyTorch state -> C++ model header + manifest (agent B).

Usage (library): ``export_model(model, name, out_dir, status=..., provenance=...)`` writes
``<out_dir>/weights.f32`` (little-endian f32 blob in ``layout`` order), ``<out_dir>/manifest.json`` and
``<out_dir>/nn_weights_<name>.h``. ``tools/install_models.py`` copies the header into bot/src.
Floats are written as C++ hex-float literals (exact; no decimal round-trip question). NaN/Inf are refused.
Output is deterministic: same parameters -> byte-identical files.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from .models import PolicyNet, layout, segments
from .models.rt import fnv1a64_f32

STATUSES = ('untrained', 'teacher_initialized', 'trained', 'validated')
ENGINE_VERSION = '1.0.3'
NAME_RE = re.compile(r'^[a-z][a-z0-9_]{0,47}$')
KIND_CPP = {'candidate': 'nnm::Kind::candidate', 'value': 'nnm::Kind::value', 'leaf': 'nnm::Kind::leaf'}
NONE = 0xFFFFFFFF


class ExportError(ValueError):
    pass


def state_to_blob(state, cfg: dict) -> np.ndarray:
    """Concatenate parameters in canonical order; refuses missing/mis-shaped/non-finite tensors."""
    parts = []
    for name, shape in layout(cfg):
        if name not in state:
            raise ExportError(f'missing parameter {name}')
        t = state[name]
        a = t.detach().cpu().numpy() if hasattr(t, 'detach') else np.asarray(t)
        if tuple(a.shape) != tuple(shape):
            raise ExportError(f'{name}: shape {tuple(a.shape)} != {tuple(shape)}')
        a = a.astype(np.float32)
        if not np.all(np.isfinite(a)):
            raise ExportError(f'{name}: NaN/Inf in parameters - refusing to export')
        parts.append(a.reshape(-1))
    return np.concatenate(parts).astype('<f4') if parts else np.zeros(0, '<f4')


def blob_to_state(blob: np.ndarray, cfg: dict) -> dict:
    import torch
    blob = np.asarray(blob, dtype=np.float32)
    out, off = {}, 0
    for name, shape in layout(cfg):
        n = int(np.prod(shape))
        out[name] = torch.from_numpy(blob[off:off + n].reshape(shape).copy())
        off += n
    if off != blob.size:
        raise ExportError(f'blob size {blob.size} != layout {off}')
    return out


def checksum(blob: np.ndarray) -> str:
    return f'0x{fnv1a64_f32(blob):016x}'


def offsets(cfg: dict) -> dict[str, int]:
    out, off = {}, 0
    for name, shape in layout(cfg):
        out[name] = off
        off += int(np.prod(shape))
    return out


def hexf(v) -> str:
    """C++ hex-float literal for an f32 value (exact)."""
    s = float(np.float32(v)).hex()  # e.g. '0x1.8000000000000p+1'
    m = re.match(r'^(-?)0x([01])\.([0-9a-f]*)p([+-]\d+)$', s)
    if not m:
        raise ExportError(f'unexpected hex float {s}')
    sign, lead, frac, exp = m.groups()
    frac = frac.rstrip('0')
    return f'{sign}0x{lead}{"." + frac if frac else ""}p{exp}f'


def architecture(cfg: dict) -> dict:
    return dict(obs=dict((k, cfg['obs'][k]) for k in ('self_global_dim', 'ally_rows', 'ally_dim', 'enemy_rows',
                                                       'enemy_dim', 'obs_dim')),
                encoder=cfg['encoder'],
                heads=[{k: h[k] for k in ('name', 'id', 'kind', 'uses_ctx', 'F', 'hidden', 'n_ctx', 'n_out', 'R',
                                          'action_hash')} for h in cfg['heads']],
                value_outputs=cfg.get('value_outputs'))


def action_schema_hash(cfg: dict) -> int:
    from .models.rt import fnv1a32
    from .models.config import canonical_json
    return fnv1a32(canonical_json([[h['name'], h['action_hash']] for h in cfg['heads']]))


def render_header(name: str, cfg: dict, blob: np.ndarray, status: str, seg_sums: dict, total: str,
                  note: str = '') -> str:
    if not NAME_RE.match(name):
        raise ExportError(f'bad model name {name!r} (lowercase identifier)')
    if status not in STATUSES:
        raise ExportError(f'bad status {status}')
    off = offsets(cfg)
    seg = segments(cfg)
    o, e = cfg['obs'], cfg['encoder']

    def lin(p, n_in, n_out):
        return f'{{{off[p + "_w"]}u, {off[p + "_b"]}u, {n_in}, {n_out}}}'

    def opt(key):
        return f'{off[key]}u' if key in off else 'nnm::kNone'

    heads = []
    by_id = {h['id']: h for h in cfg['heads']}
    for hid in range(13):
        h = by_id.get(hid)
        if h is None:
            heads.append('        {},')
            continue
        q = f'heads.{h["name"]}.'
        b, en = seg[h['name']]
        heads.append(
            f'        {{{KIND_CPP[h["kind"]]}, {int(h["uses_ctx"])}, {h["F"]}, {h["hidden"]}, {h["n_ctx"]}, '
            f'{h["n_out"]}, {hexf(h["R"])}, {opt(q + "wh")}, {opt(q + "wf")}, {opt(q + "emb")}, {off[q + "b1"]}u, '
            f'{off[q + "w2"]}u, {off[q + "b2"]}u, 0x{h["action_hash"]:08x}u, {{{b}u, {en}u, '
            f'{seg_sums[h["name"]]}ull}}}}, // {h["name"]}')
    eb, ee = seg['enc']
    vals = ',\n'.join(','.join(hexf(v) for v in blob[i:i + 8]) for i in range(0, len(blob), 8))
    ns = f'nnw_{name}'
    return f'''// GENERATED by python/nfs/export.py - do not edit. Model "{name}", status {status}.
// {note}
// {len(blob)} f32 parameters, fnv1a64 {total}; layout: python/nfs/models layout() / agents/B/REPORT.md.
#pragma once
#include "nn_model.h"

namespace {ns} {{
alignas(16) inline constexpr float kBlob[{len(blob)}] = {{
{vals}}};

inline constexpr nnm::ModelDesc kDesc = {{
    "{name}", {cfg["arch_version"]}u, nnm::Status::{status}, 0x{o["obs_schema_hash"]:08x}u, 0x{action_schema_hash(cfg):08x}u,
    {o["self_global_dim"]}, {o["ally_rows"]}, {o["ally_dim"]}, {o["enemy_rows"]}, {o["enemy_dim"]},
    {e["global_hidden"]}, {e["entity_hidden"]}, {e["ctx"]},
    {lin("enc.g1", o["self_global_dim"], e["global_hidden"])}, {lin("enc.a1", o["ally_dim"], e["entity_hidden"])},
    {lin("enc.e1", o["enemy_dim"], e["entity_hidden"])}, {lin("enc.c1", e["global_hidden"] + 4 * e["entity_hidden"], e["ctx"])},
    {{{eb}u, {ee}u, {seg_sums["enc"]}ull}},
    {{
{chr(10).join(heads)}
    }},
    {len(blob)}u, {total}ull, kBlob}};
static_assert(nnm::desc_ok(kDesc), "{name}: model descriptor out of runtime limits");
}} // namespace {ns}
'''


def segment_checksums(cfg: dict, blob: np.ndarray) -> dict[str, str]:
    return {k: f'0x{fnv1a64_f32(blob[b:e]):016x}' for k, (b, e) in segments(cfg).items()}


def export_blob(name: str, cfg: dict, blob: np.ndarray, out_dir, status: str, provenance: dict,
                validation: dict | None = None, note: str = '', extra: dict | None = None) -> dict:
    """Write weights.f32, nn_weights_<name>.h and manifest.json for a blob. Returns the manifest."""
    blob = np.asarray(blob, dtype='<f4')
    if not np.all(np.isfinite(blob)):
        raise ExportError('NaN/Inf in parameters - refusing to export')
    n = sum(int(np.prod(s)) for _, s in layout(cfg))
    if blob.size != n:
        raise ExportError(f'blob size {blob.size} != layout {n}')
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    total = checksum(blob)
    segs = segment_checksums(cfg, blob)
    (out / 'weights.f32').write_bytes(blob.tobytes())
    hdr = render_header(name, cfg, blob, status, segs, total, note)
    (out / f'nn_weights_{name}.h').write_text(hdr, encoding='utf-8', newline='\n')
    manifest = dict(
        name=name, head='all', arch_version=cfg['arch_version'], architecture=architecture(cfg),
        obs_schema_hash=f'0x{cfg["obs"]["obs_schema_hash"]:08x}', obs_schema_source=cfg['obs'].get('source'),
        action_schema_hash=f'0x{action_schema_hash(cfg):08x}', n_params=int(blob.size), checksum=total,
        segment_checksums=segs, export_precision='f32', engine_version=ENGINE_VERSION, provenance=provenance,
        status=status, validation=validation or {}, provisional=cfg.get('provisional', []),
        files=dict(weights='weights.f32', header=f'nn_weights_{name}.h'), config=cfg)
    if extra:
        manifest.update(extra)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=False) + '\n', encoding='utf-8',
                                       newline='\n')
    return manifest


def export_model(model: PolicyNet, name: str, out_dir, status: str, provenance: dict, **kw) -> dict:
    return export_blob(name, model.cfg, state_to_blob(model.state_dict(), model.cfg), out_dir, status, provenance,
                       **kw)


def load_blob(model_dir) -> tuple[dict, np.ndarray]:
    """Import side: manifest + blob with checksum and finiteness verified."""
    d = Path(model_dir)
    manifest = json.loads((d / 'manifest.json').read_text(encoding='utf-8'))
    blob = np.frombuffer((d / manifest['files']['weights']).read_bytes(), dtype='<f4').copy()
    if blob.size != manifest['n_params']:
        raise ExportError(f'{d}: {blob.size} floats, manifest says {manifest["n_params"]}')
    if not np.all(np.isfinite(blob)):
        raise ExportError(f'{d}: NaN/Inf in weights')
    if checksum(blob) != manifest['checksum']:
        raise ExportError(f'{d}: checksum {checksum(blob)} != manifest {manifest["checksum"]}')
    return manifest, blob


def load_model(model_dir) -> PolicyNet:
    manifest, blob = load_blob(model_dir)
    model = PolicyNet(manifest['config'])
    model.load_state_dict(blob_to_state(blob, manifest['config']))
    return model
