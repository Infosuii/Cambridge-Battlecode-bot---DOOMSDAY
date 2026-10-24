"""Test-only fakes for Agent G's tests (synthetic data only; nothing here is match evidence).

- NFS1 record encoder following CONTRACTS 3.5 (so the reference decoder AND B's nfs.records decoder can be checked).
- FakeObs: RawTurn payload = float32[OBS_DIM] little-endian; encode = identity copy.
- FakePolicyNet: the CONTRACTS 4 PolicyNet API (encode, head_logits, values, belief) with logit = prior + R*tanh(r/R).
- policy_net(): the REAL nfs.models.build_model when importable and probe-compatible, else FakePolicyNet.
- make_summary(): engine-summary-shaped dicts; synthetic_zip(): archives with controllable defects.
"""
from __future__ import annotations

import base64
import importlib
import json
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))

MAGIC = 0x3153464E
OBS_DIM = 12
K_MAX, F_MAX = 16, 24
R_BOUND = 2.0
HEADS = json.loads((ROOT / 'schemas/heads.json').read_text(encoding='utf-8'))['heads']
HEAD_ID = {h['name']: h['id'] for h in HEADS}
HEAD_NAME = {h['id']: h['name'] for h in HEADS}


# --------------------------------------------------------------------------------------------- NFS1 encoding
def _header(kind, rnd, champ, schema_hash=0xABCD1234):
    return struct.pack('<IHHIiI', MAGIC, 1, kind, schema_hash, rnd, champ)


def turn_payload(rnd, champ, obs: np.ndarray, schema_hash=0xABCD1234) -> bytes:
    raw = np.asarray(obs, '<f4').tobytes()
    return _header(0, rnd, champ, schema_hash) + struct.pack('<I', len(raw)) + raw   # B layout: u32 bytes + RawTurn


def decision_payload(rnd, champ, head, prior, legal, feat, chosen, logp, mode=2, reason=0, context=0, sampled=1,
                     ids=None, schema_hash=0xABCD1234, logits=None, net=-1, action_hash=0, call=0) -> bytes:
    K, F = feat.shape
    ids = np.arange(K, dtype='<u4') if ids is None else np.asarray(ids, '<u4')
    return (_header(1, rnd, champ, schema_hash)
            + struct.pack('<HHHhhBBBBf', head, K, F, 0, chosen, mode, reason, context, sampled, logp)
            + np.asarray(prior, '<f4').tobytes() + np.asarray(legal, 'u1').tobytes() + ids.tobytes()
            + np.asarray(feat, '<f4').tobytes()
            + struct.pack('<IHh', action_hash, call, net)                                   # v1 trailer (nn_log.h)
            + np.asarray(np.zeros(K) if logits is None else logits, '<f4').tobytes())


def line(payload: bytes) -> str:
    return 'NFS1 ' + base64.b64encode(payload).decode()


def fake_encode(payload: bytes) -> np.ndarray:
    return np.frombuffer(payload, '<f4').copy()


# --------------------------------------------------------------------------------------------- model
class FakePolicyNet(nn.Module):
    def __init__(self, obs_dim=OBS_DIM, ctx=8, R=R_BOUND, seed=0):
        super().__init__()
        g = torch.Generator().manual_seed(seed)
        self.obs_dim, self.R = obs_dim, R
        self.enc = nn.Linear(obs_dim, ctx)
        self.res = nn.Sequential(nn.Linear(ctx + F_MAX, 16), nn.Tanh(), nn.Linear(16, 1))
        self.head_emb = nn.Embedding(len(HEADS), ctx)
        self.v = nn.Linear(ctx, 3)
        self.b = nn.Linear(ctx, 4)
        with torch.no_grad():
            for p in self.parameters():
                p.copy_(torch.randn(p.shape, generator=g) * 0.3)

    def encode(self, obs):
        return torch.tanh(self.enc(obs))

    def residual(self, head, h, feat):
        B, K, F = feat.shape
        f = nn.functional.pad(feat, (0, F_MAX - F))
        hh = (h + self.head_emb.weight[HEAD_ID[head]])[:, None, :].expand(B, K, -1)
        return self.res(torch.cat([hh, f], -1)).squeeze(-1)

    def head_logits(self, head, h, feat, legal, prior):
        z = prior + self.R * torch.tanh(self.residual(head, h, feat) / self.R)
        return z.masked_fill(~legal.bool(), float('-inf'))

    def values(self, h):
        v = self.v(h)
        return {'win_logit': v[:, 0], 'margin': v[:, 1], 'carry_risk': v[:, 2]}

    def belief(self, h):
        return self.b(h)


def policy_net(obs_dim=OBS_DIM, seed=0):
    """(model, obs_dim, is_real). Uses B's nfs.models when it builds and passes an API probe."""
    try:
        models = importlib.import_module('nfs.models')
        cfgs = sorted((ROOT / 'configs/model').glob('*.json'))
        if cfgs and hasattr(models, 'build_model'):
            cfg = json.loads(cfgs[0].read_text(encoding='utf-8'))
            m = models.build_model(cfg)
            d = int(getattr(m, 'obs_dim', 0) or cfg.get('obs_dim', 0))
            if d:
                h = m.encode(torch.zeros(2, d))
                m.values(h)
                return m, d, True
    except Exception as exc:  # noqa: BLE001 - fall back to the contract fake
        print(f'[_fakes] real nfs.models not usable ({type(exc).__name__}: {exc}); using FakePolicyNet', file=sys.stderr)
    return FakePolicyNet(obs_dim, seed=seed), obs_dim, False


def head_F(name: str, model=None) -> int:
    hc = getattr(model, 'head_cfg', {}).get(name) if model is not None else None
    if hc is not None and hc.get('F'):
        return int(hc['F'])
    p = ROOT / 'schemas' / 'heads' / f'{name}.json'
    if p.exists():
        try:
            return int(json.loads(p.read_text(encoding='utf-8'))['F'])
        except (KeyError, ValueError):
            pass
    return 6


# --------------------------------------------------------------------------------------------- summaries
def _runs(values):
    out, prev, n = [], None, 0
    for v in values:
        if v == prev:
            n += 1
        else:
            if prev is not None:
                out.append(dict(duration=n, value=str(prev)))
            prev, n = v, 1
    out.append(dict(duration=n, value=str(prev)))
    return out


def make_summary(engine='1.0.3', outcome='teamA', rounds=100, gems=(300, 200), faults=(0, 0), capture=True,
                 picks=None, per_team=2, series=None, partial=True):
    """series: {(team, champ_id): {metric: list of length rounds+1}} cumulative timelines."""
    picks = picks or {'teamA': ['Ryth', 'Prism', 'Ren'], 'teamB': ['Varg', 'Tavi', 'Willow']}
    champs, tls, draft = [], [], []
    for a, b in zip(picks['teamA'], picks['teamB']):
        draft += [dict(champion=a, team='teamA'), dict(champion=b, team='teamB')]
    n = rounds + 1
    for ti, team in enumerate(('teamA', 'teamB')):
        for k in range(per_team):
            cid = ti * per_team + k
            champs.append(dict(id=cid, name=f'C{cid}', team=team, draftPick=k))
            s = (series or {}).get((team, cid), {})
            for metric in ('submittedGems', 'gems', 'earnedGold', 'deaths', 'championDamageDone', 'collectedGems'):
                vals = s.get(metric, [0] * n)
                tls.append(dict(metric=metric, owner=dict(id=cid, kind='champion', name=f'C{cid}', team=team),
                                runs=_runs(vals), sampleCount=n))
    return dict(
        formatVersion='1.0', jsonFormatVersion='1.0',
        match=dict(engineVersion=engine, engineBuildHash='0' * 64, metricSemanticsVersion=1, outcome=outcome,
                   roundsStarted=rounds, roundsCompleted=rounds, finalRoundPartial=partial, mapHash='ab' * 32,
                   width=40, height=40, seed='1'),
        roster=dict(champions=[dict(id=c['id'], name=c['name'], team=c['team'], draftPick=c['draftPick']) for c in champs],
                    draft=draft),
        champions=[dict(id=c['id'], name=c['name'], team=c['team'], metrics={}) for c in champs],
        championTimelines=tls,
        teamTimelines=[dict(metric='submittedGems', owner='teamA', runs=_runs([0] * rounds + [gems[0]]), sampleCount=n),
                       dict(metric='submittedGems', owner='teamB', runs=_runs([0] * rounds + [gems[1]]), sampleCount=n)],
        teams=[dict(team='teamA', submittedGems=str(gems[0])), dict(team='teamB', submittedGems=str(gems[1]))],
        events=[], heatmaps=[],
        diagnostics=dict(botFaults=dict(teamA=faults[0], teamB=faults[1]), codes=[], detailedCaptureComplete=capture))


# --------------------------------------------------------------------------------------------- archives
def member_name(match_id, t1='11111111-1111-4111-8111-111111111111', t2='22222222-2222-4222-8222-222222222222',
                kind='ranked'):
    return f'{kind}_{match_id}_{t1}_vs_{t2}.camstat'


def uuid_n(i: int) -> str:
    h = f'{i:032x}'
    return f'{h[:8]}-{h[8:12]}-4{h[13:16]}-8{h[17:20]}-{h[20:32]}'


def synthetic_zip(path, entries: dict[str, dict], stored=True) -> Path:
    """entries: member name -> summary dict (stored as JSON; tests use json.loads as the converter)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED) as z:
        for name, d in entries.items():
            z.writestr(name, json.dumps(d))
    return path


def corrupt_member(path, member: str) -> None:
    """Flip one data byte of a STORED member so its CRC no longer matches (central directory intact)."""
    with zipfile.ZipFile(path) as z:
        info = z.getinfo(member)
    raw = bytearray(Path(path).read_bytes())
    n_len, x_len = struct.unpack('<2H', raw[info.header_offset + 26:info.header_offset + 30])
    pos = info.header_offset + 30 + n_len + x_len + 2
    raw[pos] ^= 0xFF
    Path(path).write_bytes(bytes(raw))


def json_converter(raw: bytes) -> dict:
    return json.loads(raw.decode())
