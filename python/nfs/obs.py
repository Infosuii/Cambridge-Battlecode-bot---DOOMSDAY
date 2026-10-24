"""Canonical observation (agent C): RawTurn packing/unpacking and the encoder, identical to bot/src/nn_obs.cpp.

    raw = unpack(raw_bytes)          # dict (nested lists/dicts for arrays and rows)
    x = encode(raw_bytes or raw)     # np.float32[OBS_DIM]
    data = pack(raw)                 # bytes, exactly RAW_TURN_SIZE

All arithmetic is float32 in the same order as the C++ (parity is bit-exact; tests/python/test_obs_parity.py).
Layout and normalisation constants come from the generated nfs.schema_gen (tools/gen_schema.py).
"""
from __future__ import annotations

import struct
from typing import Any

import numpy as np

from . import schema_gen as S
from .transforms import Frame, make_frame

F32 = np.float32
BIG = F32(10000.0)
_ZERO = F32(0.0)

SG_INV = np.array(S.SG_INV_SCALE, dtype=np.float32)
SG_LO = np.array(S.SG_LO, dtype=np.float32)
SG_HI = np.array(S.SG_HI, dtype=np.float32)
ALLY_INV = np.array(S.ALLY_INV_SCALE, dtype=np.float32)
ALLY_LO = np.array(S.ALLY_LO, dtype=np.float32)
ALLY_HI = np.array(S.ALLY_HI, dtype=np.float32)
ENEMY_INV = np.array(S.ENEMY_INV_SCALE, dtype=np.float32)
ENEMY_LO = np.array(S.ENEMY_LO, dtype=np.float32)
ENEMY_HI = np.array(S.ENEMY_HI, dtype=np.float32)

SG = {n: i for i, n in enumerate(S.SG_NAMES)}
OBJ = {n: i for i, n in enumerate(S.OBJ_NAMES)}
AL = {n: i for i, n in enumerate(S.ALLY_NAMES)}
EN = {n: i for i, n in enumerate(S.ENEMY_NAMES)}
ROW_STRUCTS = {'objective': S.RAW_OBJ_FIELDS, 'ally': S.RAW_ALLY_FIELDS, 'enemy': S.RAW_ENEMY_FIELDS}


# ---------------------------------------------------------------- RawTurn struct

def _fmt(fields) -> str:
    out = ''
    for name, code, count, _ in fields:
        if code in ROW_STRUCTS:
            out += _fmt(ROW_STRUCTS[code]) * count
        else:
            out += code * count
    return out


TURN_FORMAT = '<' + _fmt(S.RAW_TURN_FIELDS)
_TURN = struct.Struct(TURN_FORMAT)
assert _TURN.size == S.RAW_TURN_SIZE, (_TURN.size, S.RAW_TURN_SIZE)


def _unflat(fields, vals, pos):
    out: dict[str, Any] = {}
    for name, code, count, _ in fields:
        if code in ROW_STRUCTS:
            rows = []
            for _k in range(count):
                row, pos = _unflat(ROW_STRUCTS[code], vals, pos)
                rows.append(row)
            out[name] = rows
        elif count == 1:
            out[name] = vals[pos]
            pos += 1
        else:
            out[name] = list(vals[pos:pos + count])
            pos += count
    return out, pos


def _flat(fields, d, out):
    for name, code, count, _ in fields:
        if code in ROW_STRUCTS:
            rows = d[name]
            assert len(rows) == count, name
            for row in rows:
                _flat(ROW_STRUCTS[code], row, out)
        elif count == 1:
            out.append(d[name])
        else:
            v = list(d[name])
            assert len(v) == count, name
            out.extend(v)


def unpack(data: bytes) -> dict:
    if len(data) != S.RAW_TURN_SIZE:
        raise ValueError(f'RawTurn must be {S.RAW_TURN_SIZE} bytes, got {len(data)}')
    vals = _TURN.unpack(data)
    d, pos = _unflat(S.RAW_TURN_FIELDS, vals, 0)
    assert pos == len(vals)
    return d


def pack(d: dict) -> bytes:
    out: list = []
    _flat(S.RAW_TURN_FIELDS, d, out)
    return _TURN.pack(*out)


def _zero_fields(fields) -> dict:
    d: dict[str, Any] = {}
    for name, code, count, _ in fields:
        if code in ROW_STRUCTS:
            d[name] = [_zero_fields(ROW_STRUCTS[code]) for _ in range(count)]
        else:
            z = 0.0 if code == 'f' else 0
            d[name] = z if count == 1 else [z] * count
    return d


def empty_raw() -> dict:
    """A zeroed RawTurn dict with a valid header (useful for synthetic tests)."""
    d = _zero_fields(S.RAW_TURN_FIELDS)
    d.update(magic=S.RAW_MAGIC, version=S.RAW_VERSION, schema_hash=S.OBS_SCHEMA_HASH, size=S.RAW_TURN_SIZE)
    return d


def check_header(d: dict) -> bool:
    return (d['magic'] == S.RAW_MAGIC and d['version'] == S.RAW_VERSION and d['schema_hash'] == S.OBS_SCHEMA_HASH
            and d['size'] == S.RAW_TURN_SIZE)


# ---------------------------------------------------------------- encoder

def _f(v) -> np.float32:
    return F32(v)


def _cheb(dx: int, dy: int) -> int:
    return max(abs(dx), abs(dy))


def _norm(block: np.ndarray, inv: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> np.ndarray:
    y = (block * inv).astype(np.float32)
    y[~np.isfinite(y)] = 0.0
    y = np.where(y < lo, lo, np.where(y > hi, hi, y)).astype(np.float32)
    return (y + _ZERO).astype(np.float32)


def _onehot(s: np.ndarray, base: int, n: int, k: int) -> None:
    if 0 <= k < n:
        s[base + k] = 1.0


def _tiles(d: int) -> np.float32:
    return _f(d) if d >= 0 else (BIG if d == -2 else _ZERO)


def _base(table: dict, prefix: str) -> tuple[int, int]:
    idx = [i for n, i in table.items() if n.startswith(prefix + '.')]
    return min(idx), len(idx)


_SELF_TYPE = _base(SG, 'self.type')
_SPELL_KIND = (_base(SG, 'self.spell0.kind'), _base(SG, 'self.spell1.kind'))
_SYM = _base(SG, 'glob.symmetry')
_OBJ_STATE = _base(OBJ, 'state')
_AL_TYPE = _base(AL, 'type')
_EN_TYPE = _base(EN, 'type')


def encode(raw) -> np.ndarray:
    """RawTurn bytes or dict -> float32[OBS_DIM]; bit-identical to nnobs::encode."""
    r = unpack(raw) if isinstance(raw, (bytes, bytearray, memoryview)) else raw
    with np.errstate(all='ignore'):
        return _encode(r)


def _encode(r: dict) -> np.ndarray:
    x = np.zeros(S.OBS_DIM, dtype=np.float32)
    s = np.zeros(S.SELF_GLOBAL_DIM, dtype=np.float32)
    F = frame_of(r)
    px, py = r['pos_x'], r['pos_y']
    alive = r['alive'] != 0
    hp, max_hp = _f(r['hp']), _f(r['max_hp'])

    # ---- self
    s[SG['self.alive']] = 1.0 if alive else 0.0
    s[SG['self.hp_frac']] = hp / max_hp if alive else _ZERO
    s[SG['self.max_hp']] = max_hp
    s[SG['self.strength']] = _f(r['strength'])
    s[SG['self.focus']] = _f(r['focus'])
    s[SG['self.gems']] = _f(r['gems'])
    s[SG['self.gems_vs_carry']] = _f(r['gems']) / _f(r['tribute_carry'])
    s[SG['self.gold']] = _f(r['gold'])
    s[SG['self.attack_range']] = _f(r['attack_range'])
    s[SG['self.melee']] = 1.0 if r['attack_range'] <= 1 else 0.0
    _onehot(s, *_SELF_TYPE, r['type'])
    for k in range(2):
        if not r['spell_present'][k]:
            continue
        b = SG[f'self.spell{k}.present']
        s[b] = 1.0
        s[b + 1] = 1.0 if (r['spell_cooldown'][k] == 0 and not r['cast_done']) else 0.0
        s[b + 2] = _f(r['spell_cooldown'][k])
        s[b + 3] = _f(r['spell_range'][k])
        _onehot(s, *_SPELL_KIND[k], r['spell_kind'][k] - 1)
    s[SG['self.cast_done']] = 1.0 if r['cast_done'] else 0.0
    b = r['state_bits'] & 0xFFFFFFFF
    s[SG['self.state.recalling']] = (b >> 1) & 1
    s[SG['self.state.submitting_gems']] = (b >> 2) & 1
    s[SG['self.state.teleporting']] = (b >> 12) & 1
    s[SG['self.state.can_move']] = (b >> 3) & 1
    s[SG['self.state.can_attack']] = (b >> 4) & 1
    s[SG['self.state.can_cast']] = (b >> 11) & 1
    s[SG['self.items']] = _f(r['items'])
    s[SG['self.camp_taken_mult']] = _f(r['camp_taken_mult'])
    s[SG['self.camp_dealt_mult']] = _f(r['camp_dealt_mult'])
    s[SG['self.ward_charges']] = _f(r['ward_charges'])
    s[SG['self.ward_cooldown']] = _f(r['ward_cooldown'])
    s[SG['self.pos_x']] = _f(F.canon_x(px)) / _f(F.w - 1)
    s[SG['self.pos_y']] = _f(F.canon_y(py)) / _f(F.h - 1)
    s[SG['self.spawn_dist']] = _tiles(r['spawn_dist'])
    s[SG['self.altar_known']] = 1.0 if (r['altar_ready'] and r['altar_dist'] != -1) else 0.0
    s[SG['self.altar_dist']] = _tiles(r['altar_dist']) if r['altar_ready'] else _ZERO
    s[SG['self.enemy_spawn_cheb']] = _f(_cheb(2 * px - (r['enemy_spawn_x0'] + r['enemy_spawn_x1']),
                                             2 * py - (r['enemy_spawn_y0'] + r['enemy_spawn_y1']))) * F32(0.5)
    s[SG['self.enemy_spawn_walk_known']] = 1.0 if (r['enemy_ready'] and r['enemy_spawn_walk'] != -1) else 0.0
    s[SG['self.enemy_spawn_walk']] = _tiles(r['enemy_spawn_walk']) if r['enemy_ready'] else _ZERO
    s[SG['self.in_bush']] = 1.0 if r['in_bush'] else 0.0
    s[SG['self.on_own_spawn']] = 1.0 if r['on_own_spawn'] else 0.0
    s[SG['self.in_hot_zone']] = 1.0 if r['in_hot_zone'] else 0.0
    s[SG['self.in_enemy_zone']] = 1.0 if r['in_enemy_zone'] else 0.0
    s[SG['self.heading_home']] = 1.0 if r['heading_home'] else 0.0
    s[SG['self.has_target']] = 1.0 if r['target_group'] >= 0 else 0.0
    s[SG['self.hp_delta_turn']] = (hp - _f(r['prev_hp'])) / max_hp if alive else _ZERO
    if r['hist10_age'] >= 10:
        s[SG['self.hist10_valid']] = 1.0
        s[SG['self.hp_delta_10']] = (hp - _f(r['hist10_hp'])) / max_hp
        s[SG['self.gems_delta_10']] = _f(r['gems'] - r['hist10_gems'])
        s[SG['self.hist10_age']] = _f(r['hist10_age'])

    # ---- global
    win = _f(r['winning_gems'])
    s[SG['glob.round_frac']] = _f(r['round']) / _f(r['max_rounds'])
    s[SG['glob.ally_score']] = _f(r['ally_score']) / win
    s[SG['glob.enemy_score']] = _f(r['enemy_score']) / win
    s[SG['glob.score_diff']] = _f(r['ally_score'] - r['enemy_score']) / win
    s[SG['glob.gems_to_win']] = _f(r['winning_gems'] - r['ally_score'] - r['gems']) / win
    s[SG['glob.win_now']] = 1.0 if (r['winning_gems'] > 0 and r['ally_score'] + r['gems'] >= r['winning_gems']) else 0.0
    if r['hist50_age'] >= 50:
        s[SG['glob.rate50_valid']] = 1.0
        s[SG['glob.ally_rate50']] = _f(r['ally_score'] - r['hist50_ally']) / _f(r['hist50_age'])
        s[SG['glob.enemy_rate50']] = _f(r['enemy_score'] - r['hist50_enemy']) / _f(r['hist50_age'])
    if r['hist200_age'] >= 200:
        s[SG['glob.rate200_valid']] = 1.0
        s[SG['glob.ally_rate200']] = _f(r['ally_score'] - r['hist200_ally']) / _f(r['hist200_age'])
        s[SG['glob.enemy_rate200']] = _f(r['enemy_score'] - r['hist200_enemy']) / _f(r['hist200_age'])
    s[SG['glob.alive_us']] = _f(r['alive_us']) / _f(r['team_size'])
    s[SG['glob.alive_them']] = _f(r['alive_them']) / _f(r['enemy_count'])
    s[SG['glob.team_size']] = _f(r['team_size'])
    s[SG['glob.enemy_count']] = _f(r['enemy_count'])
    for k in ('ally_deaths_50', 'enemy_deaths_50', 'ally_deaths_total', 'enemy_deaths_total'):
        s[SG['glob.' + k]] = _f(r[k])
    s[SG['glob.map_w']] = _f(r['width'])
    s[SG['glob.map_h']] = _f(r['height'])
    area = r['width'] * r['height']
    s[SG['glob.size_class.small' if area <= S.SMALL_MAX_AREA else
         'glob.size_class.medium' if area <= S.MEDIUM_MAX_AREA else 'glob.size_class.large']] = 1.0
    _onehot(s, *_SYM, r['symmetry'])
    s[SG['glob.n_groups']] = _f(r['n_groups'])
    s[SG['glob.fields_frac']] = _f(r['fields_built']) / _f(r['n_groups'])
    s[SG['glob.vis_enemies']] = _f(r['vis_enemies'])
    s[SG['glob.vis_allies']] = _f(r['vis_allies'])
    s[SG['glob.sight_n5']] = _f(r['sight_n5'])
    s[SG['glob.sight_n20']] = _f(r['sight_n20'])
    if r['sight_age'] >= 0:
        dx, dy = r['sight_x'] - px, r['sight_y'] - py
        s[SG['glob.sight_valid']] = 1.0
        s[SG['glob.sight_dx']] = _f(F.canon_dx(dx))
        s[SG['glob.sight_dy']] = _f(F.canon_dy(dy))
        s[SG['glob.sight_dist']] = _f(_cheb(dx, dy))
        s[SG['glob.sight_age']] = _f(r['sight_age'])
    if r['distress_age'] >= 0:
        s[SG['glob.distress_valid']] = 1.0
        s[SG['glob.distress_dx']] = _f(F.canon_dx(r['distress_x'] - px))
        s[SG['glob.distress_dy']] = _f(F.canon_dy(r['distress_y'] - py))
        s[SG['glob.distress_age']] = _f(r['distress_age'])
    s[SG['glob.enemy_wards']] = _f(r['enemy_wards'])

    # ---- objective slots
    for k in range(S.OBJ_SLOTS):
        o = r['obj'][k]
        if not o['valid']:
            continue
        q = S.OBJ_BASE + k * S.OBJ_DIM
        dx, dy = o['anchor_x'] - px, o['anchor_y'] - py
        s[q + OBJ['valid']] = 1.0
        s[q + OBJ['dx']] = _f(F.canon_dx(dx))
        s[q + OBJ['dy']] = _f(F.canon_dy(dy))
        s[q + OBJ['dist']] = _f(o['dist_walk']) if o['dist_walk'] >= 0 else _f(o['dist_cheb'])
        s[q + OBJ['dist_is_walk']] = 1.0 if o['dist_walk'] >= 0 else 0.0
        s[q + OBJ['unreachable']] = 1.0 if o['dist_walk'] == -2 else 0.0
        s[q + OBJ['gems']] = _f(o['gems'])
        s[q + OBJ['gold']] = _f(o['gold'])
        if 0 <= o['state'] < _OBJ_STATE[1]:
            s[q + _OBJ_STATE[0] + o['state']] = 1.0
        s[q + OBJ['respawn_in']] = _f(o['respawn_in'])
        s[q + OBJ['hp_left_frac']] = _f(o['hp_left']) / _f(o['max_hp'])
        s[q + OBJ['max_hp']] = _f(o['max_hp'])
        s[q + OBJ['harmless']] = 1.0 if o['harmless'] else 0.0
        s[q + OBJ['ally_claims']] = _f(o['ally_claims'])
        s[q + OBJ['enemy_seen']] = 1.0 if o['enemy_age'] >= 0 else 0.0
        s[q + OBJ['enemy_age']] = _f(o['enemy_age']) if o['enemy_age'] >= 0 else BIG
    x[:S.SELF_GLOBAL_DIM] = _norm(s, SG_INV, SG_LO, SG_HI)

    # ---- ally rows
    keys = []
    for i, a in enumerate(r['ally'][:S.ALLY_ROWS]):
        if not a['present']:
            continue
        known = a['known'] != 0
        dist = _cheb(a['x'] - px, a['y'] - py) if known else 2 ** 63 - 1
        keys.append((-(1 if (a['visible'] and known) else 0), -(1 if known else 0), dist, a['handle'] & 0xFFFFFFFF, i))
    keys.sort()
    for j, key in enumerate(keys):
        a = r['ally'][key[4]]
        q = np.zeros(S.ALLY_DIM, dtype=np.float32)
        known = a['known'] != 0
        q[AL['alive']] = 1.0 if a['alive'] else 0.0
        q[AL['visible']] = 1.0 if (a['visible'] and known) else 0.0
        q[AL['known']] = 1.0 if known else 0.0
        q[AL['age']] = (_ZERO if a['visible'] else _f(a['age'])) if known else BIG
        if known:
            dx, dy = a['x'] - px, a['y'] - py
            q[AL['dx']] = _f(F.canon_dx(dx))
            q[AL['dy']] = _f(F.canon_dy(dy))
            q[AL['dist']] = _f(_cheb(dx, dy))
            q[AL['hp_frac']] = _f(a['hp']) / _f(a['max_hp'])
            q[AL['max_hp']] = _f(a['max_hp'])
            q[AL['strength']] = _f(a['strength'])
            q[AL['focus']] = _f(a['focus'])
            q[AL['range']] = _f(a['range'])
            if a['gems'] >= 0:
                q[AL['gems_known']] = 1.0
                q[AL['gems']] = _f(a['gems'])
        else:
            q[AL['dist']] = BIG
        _onehot(q, *_AL_TYPE, a['type'])
        c = a['claim_code']
        is_group = 0 <= c < r['n_groups'] and c < 126
        if c == 127:
            q[AL['claim.idle']] = 1.0
        elif c == 126:
            q[AL['claim.dead']] = 1.0
        elif is_group:
            q[AL['claim.group']] = 1.0
        elif c >= 0:
            q[AL['claim.other']] = 1.0
        if is_group:
            q[AL['claim_is_my_target']] = 1.0 if c == r['target_group'] else 0.0
            if a['claim_dist'] >= 0 and known:
                q[AL['claim_dist_known']] = 1.0
                q[AL['claim_dist']] = _f(a['claim_dist'])
            q[AL['claim_gems']] = _f(a['claim_gems'])
        q[AL['acts_before_me']] = 1.0 if a['slot'] < r['slot'] else 0.0
        off = S.ALLY_ROWS_OFF + j * S.ALLY_DIM
        x[off:off + S.ALLY_DIM] = _norm(q, ALLY_INV, ALLY_LO, ALLY_HI)
        x[S.ALLY_MASK_OFF + j] = 1.0

    # ---- enemy rows
    keys = []
    for i, e in enumerate(r['enemy'][:S.ENEMY_ROWS]):
        if not e['present']:
            continue
        known = e['known'] != 0
        dist = _cheb(e['x'] - px, e['y'] - py) if known else 2 ** 63 - 1
        keys.append((-(1 if (e['visible'] and known) else 0), -(1 if known else 0), dist, e['handle'] & 0xFFFFFFFF, i))
    keys.sort()
    for j, key in enumerate(keys):
        e = r['enemy'][key[4]]
        q = np.zeros(S.ENEMY_DIM, dtype=np.float32)
        known = e['known'] != 0
        vis = known and bool(e['visible'])
        q[EN['alive']] = 1.0 if e['alive'] else 0.0
        q[EN['visible']] = 1.0 if vis else 0.0
        q[EN['known']] = 1.0 if known else 0.0
        q[EN['age']] = (_ZERO if vis else _f(e['age'])) if known else BIG
        if known:
            dx, dy = e['x'] - px, e['y'] - py
            d = _cheb(dx, dy)
            q[EN['dx']] = _f(F.canon_dx(dx))
            q[EN['dy']] = _f(F.canon_dy(dy))
            q[EN['dist']] = _f(d)
            q[EN['hp_frac']] = _f(e['hp']) / _f(e['max_hp'])
            q[EN['max_hp']] = _f(e['max_hp'])
            q[EN['strength']] = _f(e['strength'])
            q[EN['focus']] = _f(e['focus'])
            q[EN['range']] = _f(e['range'])
            q[EN['gems']] = _f(e['gems'])
            b = e['state_bits'] & 0xFFFFFFFF
            q[EN['recalling']] = (b >> 1) & 1
            q[EN['tributing']] = (b >> 2) & 1
            if vis and alive:
                q[EN['in_my_range']] = 1.0 if d <= r['attack_range'] else 0.0
                q[EN['threatens_me']] = 1.0 if d <= e['range'] + 1 else 0.0
        else:
            q[EN['dist']] = BIG
        _onehot(q, *_EN_TYPE, e['type'])
        off = S.ENEMY_ROWS_OFF + j * S.ENEMY_DIM
        x[off:off + S.ENEMY_DIM] = _norm(q, ENEMY_INV, ENEMY_LO, ENEMY_HI)
        x[S.ENEMY_MASK_OFF + j] = 1.0
    return x


def frame_of(r: dict) -> Frame:
    return make_frame(r['width'], r['height'], r['symmetry'], r['own_spawn_x0'] + r['own_spawn_x1'],
                      r['own_spawn_y0'] + r['own_spawn_y1'], r['abs_team'])


def obs_hash(x: np.ndarray) -> int:
    """FNV-1a-32 over the float32 bit patterns (nnobs::obs_hash)."""
    h = 0x811C9DC5
    for b in np.ascontiguousarray(x, dtype='<f4').tobytes():
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def split(x: np.ndarray) -> dict:
    """View an encoded observation (or a batch [..., OBS_DIM]) as its blocks."""
    x = np.asarray(x)
    lead = x.shape[:-1]
    return {
        'self_global': x[..., :S.SELF_GLOBAL_DIM],
        'ally': x[..., S.ALLY_ROWS_OFF:S.ALLY_MASK_OFF].reshape(*lead, S.ALLY_ROWS, S.ALLY_DIM),
        'ally_mask': x[..., S.ALLY_MASK_OFF:S.ENEMY_ROWS_OFF],
        'enemy': x[..., S.ENEMY_ROWS_OFF:S.ENEMY_MASK_OFF].reshape(*lead, S.ENEMY_ROWS, S.ENEMY_DIM),
        'enemy_mask': x[..., S.ENEMY_MASK_OFF:S.OBS_DIM],
    }


def feature_names() -> list[str]:
    """Flat names of all OBS_DIM features, in layout order."""
    out = list(S.SG_NAMES)
    for k in range(S.ALLY_ROWS):
        out += [f'ally{k}.{n}' for n in S.ALLY_NAMES]
    out += [f'ally_mask{k}' for k in range(S.ALLY_ROWS)]
    for k in range(S.ENEMY_ROWS):
        out += [f'enemy{k}.{n}' for n in S.ENEMY_NAMES]
    out += [f'enemy_mask{k}' for k in range(S.ENEMY_ROWS)]
    assert len(out) == S.OBS_DIM
    return out
