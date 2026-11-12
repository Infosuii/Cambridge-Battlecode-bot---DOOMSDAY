"""Create the synthetic, seeded, UNTRAINED models and the inherited draft-net registry entry (agent B).

    python -m nfs.models.untrained            (PYTHONPATH=python)

* fs_v1_untrained - status 'untrained'; seeded synthetic init (no data); residual output layers of every candidate
  and leaf head are exactly zero, so it is teacher-neutral by construction (logit == prior). Used by neutral_*,
  training (behaviour = softmax(prior)).
* fs_v1_dev       - status 'untrained'; same encoder init but NON-zero residual layers: plumbing only
  (dev_untrained / selftest profiles), never playable.
* draft_net_original - provenance-only entry for the inherited trained draft network in bot/src/draft_net.h
  (status 'trained', used unchanged by the teacher; NOT exported into the new schema).
Dimensions follow the current schemas (bot/src/nn_schema.h when agent C's header exists, else the documented
fallback with obs_schema_hash 0). Re-run after a schema change; output is deterministic in the seed.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import torch

from . import PolicyNet, init_untrained, load_config
from .config import ROOT
from .rt import fnv1a32, fnv1a64_f32

SEEDS = {'fs_v1_untrained': 20261024, 'fs_v1_dev': 20261025}


def make(name: str, zero_residual: bool, root: Path = ROOT, config: str = 'fs_v1', out_dir: Path | None = None,
         seed: int | None = None, **cfg_kw) -> dict:
    """Export one synthetic untrained model. cfg_kw go to load_config (e.g. schema_header for test stubs)."""
    from .. import export
    cfg = load_config(config, root, **cfg_kw)
    seed = SEEDS.get(name, 1) if seed is None else seed
    model = init_untrained(PolicyNet(cfg), seed, zero_residual=zero_residual)
    if not zero_residual:
        # Plumbing variant: residual output layers drawn so r is O(1) -> logits move by up to +-R from the priors.
        g = torch.Generator().manual_seed(seed + 1)
        with torch.no_grad():
            for h in cfg['heads']:
                if h['kind'] in ('candidate', 'leaf'):
                    p = model.heads[h['name']]
                    p['w2'].copy_((torch.rand(p['w2'].shape, generator=g) * 2 - 1) * 1.5)
                    p['b2'].copy_((torch.rand(p['b2'].shape, generator=g) * 2 - 1) * 0.1)
    note = ('SYNTHETIC seeded init, untrained, zero residual (teacher-neutral)' if zero_residual else
            'SYNTHETIC seeded init, untrained, non-zero residual: PLUMBING ONLY, never a release')
    prov = dict(source='synthetic seeded initialisation (python/nfs/models/untrained.py)', seed=seed,
                data='none - synthetic, no match data, no training', config=f'configs/model/{config}.json',
                label='synthetic', created_by='agent B (wave 1)')
    return export.export_model(model, name, Path(out_dir) if out_dir else root / 'models' / name, status='untrained',
                               provenance=prov,
                               validation=dict(passed=False, note='untrained: nothing to validate'), note=note,
                               extra=dict(zero_residual=zero_residual, note=note))


def draft_net_entry(root: Path = ROOT) -> dict:
    """Manifest for the inherited draft network (parsed from bot/src/draft_net.h; never re-exported)."""
    path = root / 'bot/src/draft_net.h'
    text = path.read_text(encoding='utf-8')
    k_in = int(re.search(r'kIn\s*=\s*(\d+)', text).group(1))
    k_hid = int(re.search(r'kHid\s*=\s*(\d+)', text).group(1))
    arrays = []
    for name in ('W1', 'b1', 'w2'):
        m = re.search(r'\b' + name + r'\s*\[[^\]]*\]\s*=\s*\{([^}]*)\}', text)
        arrays.append(np.array([np.float32(v.strip().rstrip('f')) for v in m.group(1).split(',') if v.strip()],
                               np.float32))
    b2 = np.float32(re.search(r'\bb2\s*=\s*([-0-9.eE+]+)f', text).group(1))
    blob = np.concatenate(arrays + [np.array([b2], np.float32)])
    assert blob.size == k_in * k_hid + 2 * k_hid + 1, blob.size
    import hashlib
    man = dict(
        name='draft_net_original', head='draft_pick (teacher-internal)', arch_version=0,
        architecture=dict(type='mlp', inputs=k_in, hidden=k_hid, outputs=1, activation='tanh',
                          note='P(win | map features, picks, team size, first pick, progress); see draft_net.h'),
        obs_schema_hash=f'0x{fnv1a32(path.read_bytes()):08x}',
        obs_schema_note='own 53-feature draft input schema (draft.cpp); hash = fnv1a32(bot/src/draft_net.h bytes)',
        action_schema_hash='0x00000000', n_params=int(blob.size), checksum=f'0x{fnv1a64_f32(blob):016x}',
        checksum_note='fnv1a64 over little-endian f32 of W1, b1, w2, b2 as parsed from bot/src/draft_net.h',
        export_precision='f32', engine_version='1.0.3',
        provenance=dict(source='inherited from original source bot/src/draft_net.h (mld_fuel35_engine103.zip)',
                        trainer='agent2/lab/draft_fit.py on random-lineup lab games (per the header comment)',
                        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        used_by='teacher (original draft logic), unchanged'),
        status='trained', exportable=False,
        validation=dict(passed=False, note='not re-validated in this build; inherited network kept bit-identical'),
        files={})
    out = root / 'models/draft_net_original'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'manifest.json').write_text(json.dumps(man, indent=2) + '\n', encoding='utf-8', newline='\n')
    return man


def write_registry(root: Path = ROOT) -> dict:
    reg = dict(
        _doc=('Installed models (agent B). status: untrained | teacher_initialized | trained | validated. '
              'release_selection maps heads to models for the release profile; only validated, schema-compatible '
              'models are ever activated there (tools/install_models.py). Untrained models run only in '
              'dev_untrained/training/selftest (active) or neutral_* (shadow, zero residual).'),
        version=1,
        models={
            'fs_v1_untrained': dict(path='models/fs_v1_untrained', status='untrained', exportable=True,
                                    label='synthetic seeded init, zero residual (teacher-neutral)'),
            'fs_v1_dev': dict(path='models/fs_v1_dev', status='untrained', exportable=True,
                              label='synthetic seeded init, non-zero residual, plumbing only'),
            'draft_net_original': dict(path='models/draft_net_original', status='trained', exportable=False,
                                       label='inherited original draft network, used by the teacher'),
        },
        release_selection={})
    (root / 'models/registry.json').write_text(json.dumps(reg, indent=2) + '\n', encoding='utf-8', newline='\n')
    return reg


def main() -> int:
    for name, zr in (('fs_v1_untrained', True), ('fs_v1_dev', False)):
        m = make(name, zr)
        print(name, m['n_params'], m['checksum'], 'provisional:' if m['provisional'] else '', *m['provisional'][:2])
    print('draft_net_original', draft_net_entry()['checksum'])
    write_registry()
    return 0


if __name__ == '__main__':
    sys.exit(main())
