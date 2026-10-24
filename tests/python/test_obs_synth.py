"""Shared synthetic RawTurn generators for the observation tests (agent C). All data here is synthetic."""
from __future__ import annotations

import hashlib
import math
import os
import random
import shutil
import struct
import subprocess
from pathlib import Path

from nfs import obs, schema_gen as S

ROOT = Path(__file__).resolve().parents[2]
GXX = os.environ.get('NFS_GXX', 'C:/msys64/ucrt64/bin/g++.exe')
NATIVE_DIR = ROOT / 'artifacts' / 'tmp' / 'C' / 'native'


def f32(v: float) -> float:
    return struct.unpack('<f', struct.pack('<f', v))[0]


def plausible(rng: random.Random, sym: int | None = None, abs_team: int = 0) -> dict:
    r = obs.empty_raw()
    sym = rng.randrange(3) if sym is None else sym
    W, H = rng.randint(20, 100), rng.randint(20, 100)
    r.update(width=W, height=H, symmetry=sym, abs_team=abs_team, round=rng.randint(1, 1999), max_rounds=2000,
             winning_gems=1000, slot=rng.randint(0, 4), team_size=rng.randint(3, 6), enemy_count=rng.randint(3, 6))
    r.update(n_groups=rng.randint(4, 120))
    r.update(fields_built=rng.randint(0, r['n_groups']), altar_ready=int(rng.random() < .7), enemy_ready=int(rng.random() < .2))
    r.update(own_spawn_x0=1, own_spawn_y0=1, own_spawn_x1=3, own_spawn_y1=3,
             enemy_spawn_x0=W - 4, enemy_spawn_x1=W - 2, enemy_spawn_y0=H - 4, enemy_spawn_y1=H - 2)
    alive = int(rng.random() < .9)
    max_hp = f32(500 + 2000 * rng.random())
    r.update(alive=alive, pos_x=rng.randrange(W), pos_y=rng.randrange(H), gems=rng.randint(0, 120), gold=rng.randint(0, 900),
             attack_range=rng.randint(1, 6), type=rng.randint(0, 12), state_bits=rng.getrandbits(13),
             cast_done=int(rng.random() < .2), heading_home=int(rng.random() < .2),
             target_group=rng.randint(-1, r['n_groups'] - 1), tribute_carry=rng.randint(8, 80),
             ward_charges=rng.randint(0, 2), ward_cooldown=rng.randint(0, 120), spawn_dist=rng.randint(-2, 150),
             altar_dist=rng.randint(-2, 150), enemy_spawn_walk=rng.randint(-2, 150), in_bush=int(rng.random() < .2),
             on_own_spawn=int(rng.random() < .1), in_hot_zone=int(rng.random() < .1), in_enemy_zone=int(rng.random() < .05))
    r['spell_present'] = [int(rng.random() < .85) for _ in range(2)]
    r['spell_kind'] = [rng.randint(1, 7) for _ in range(2)]
    r['spell_cooldown'] = [rng.randint(0, 30) for _ in range(2)]
    r['spell_range'] = [float(rng.randint(0, 8)) for _ in range(2)]
    r.update(max_hp=max_hp, hp=f32(max_hp * rng.random()) if alive else 0.0, prev_hp=f32(max_hp * rng.random()),
             strength=f32(200 * rng.random()), focus=f32(200 * rng.random()), items=f32(40 * rng.random()),
             camp_taken_mult=rng.choice([1.0, f32(0.7), f32(0.63)]), camp_dealt_mult=rng.choice([1.0, f32(1.1)]))
    r.update(hist10_age=rng.choice([-1, rng.randint(10, 14)]), hist10_hp=f32(max_hp * rng.random()), hist10_gems=rng.randint(0, 100),
             ally_score=rng.randint(0, 990), enemy_score=rng.randint(0, 990))
    r.update(hist50_age=rng.choice([-1, rng.randint(50, 59)]), hist50_ally=r['ally_score'] - rng.randint(0, 50),
             hist50_enemy=r['enemy_score'] - rng.randint(0, 50), hist200_age=rng.choice([-1, rng.randint(200, 209)]),
             hist200_ally=r['ally_score'] - rng.randint(0, 200), hist200_enemy=r['enemy_score'] - rng.randint(0, 200))
    r.update(alive_us=rng.randint(0, r['team_size']), alive_them=rng.randint(0, r['enemy_count']),
             ally_deaths_50=rng.randint(0, 3), enemy_deaths_50=rng.randint(0, 3), ally_deaths_total=rng.randint(0, 30),
             enemy_deaths_total=rng.randint(0, 30), vis_enemies=rng.randint(0, 6), vis_allies=rng.randint(0, 5),
             sight_n5=rng.randint(0, 5), sight_n20=rng.randint(0, 9), sight_age=rng.randint(-1, 20), sight_x=rng.randrange(W),
             sight_y=rng.randrange(H), distress_age=rng.randint(-1, 10), distress_x=rng.randrange(W), distress_y=rng.randrange(H),
             enemy_wards=rng.randint(0, 3))
    for o in r['obj']:
        mh = f32(100 + 20000 * rng.random())
        o.update(valid=int(rng.random() < .8), group=rng.randint(0, r['n_groups'] - 1), anchor_x=rng.randrange(W),
                 anchor_y=rng.randrange(H), dist_walk=rng.randint(-2, 200), dist_cheb=rng.randint(0, 100),
                 gems=rng.randint(0, 400), gold=rng.randint(0, 400), state=rng.randint(0, 2), respawn_in=rng.randint(0, 300),
                 harmless=int(rng.random() < .3), ally_claims=rng.randint(0, 3), enemy_age=rng.randint(-1, 300),
                 max_hp=mh, hp_left=f32(mh * rng.random()))
    for i, a in enumerate(r['ally']):
        mh = f32(500 + 2000 * rng.random())
        a.update(present=int(i < r['team_size'] - 1), handle=100 + 7 * i, slot=i, type=rng.randint(0, 12),
                 alive=int(rng.random() < .85), visible=int(rng.random() < .5), known=int(rng.random() < .8),
                 age=rng.randint(0, 60), x=rng.randrange(W), y=rng.randrange(H), range=rng.randint(1, 6),
                 gems=rng.randint(-1, 100), claim_code=rng.choice([-1, rng.randint(0, 127)]), claim_dist=rng.randint(-1, 150),
                 claim_gems=rng.randint(0, 300), max_hp=mh, hp=f32(mh * rng.random()), strength=f32(150 * rng.random()),
                 focus=f32(150 * rng.random()))
    for i, e in enumerate(r['enemy']):
        mh = f32(500 + 2000 * rng.random())
        e.update(present=int(i < r['enemy_count']), handle=200 + 11 * i, type=rng.randint(0, 12), alive=int(rng.random() < .85),
                 visible=int(rng.random() < .4), known=int(rng.random() < .7), age=rng.randint(0, 60), x=rng.randrange(W),
                 y=rng.randrange(H), range=rng.randint(1, 6), gems=rng.randint(0, 100), state_bits=rng.getrandbits(13),
                 max_hp=mh, hp=f32(mh * rng.random()), strength=f32(150 * rng.random()), focus=f32(150 * rng.random()))
    return r


SPECIAL_F = [math.nan, math.inf, -math.inf, 3.4e38, -3.4e38, 0.0, -0.0, 1e-38, 1e-45]
SPECIAL_I = [0, -1, -2, 1, 2 ** 31 - 1, -2 ** 31, 126, 127]


def hostile_bytes(rng: random.Random) -> bytes:
    """Random 4-byte words, a third of them replaced by special floats/ints: exercises NaN/Inf/extreme handling."""
    words = []
    for _ in range(S.RAW_TURN_SIZE // 4):
        roll = rng.random()
        if roll < 0.15:
            words.append(struct.pack('<f', rng.choice(SPECIAL_F)))
        elif roll < 0.3:
            words.append(struct.pack('<i', rng.choice(SPECIAL_I)))
        else:
            words.append(struct.pack('<I', rng.getrandbits(32)))
    return b''.join(words)


def native_harness() -> Path | None:
    """Build tests/cpp/obs_parity.cpp + bot/src/nn_obs.cpp natively (cached by source digest); None without g++."""
    if not Path(GXX).exists() and not shutil.which('g++'):
        return None
    gxx = GXX if Path(GXX).exists() else shutil.which('g++')
    srcs = [ROOT / 'tests/cpp/obs_parity.cpp', ROOT / 'bot/src/nn_obs.cpp']
    heads = [ROOT / 'bot/src/nn_obs.h', ROOT / 'bot/src/nn_schema.h', ROOT / 'bot/src/nn_config.h']
    digest = hashlib.sha256(b''.join(p.read_bytes() for p in srcs + heads)).hexdigest()[:12]
    NATIVE_DIR.mkdir(parents=True, exist_ok=True)
    exe = NATIVE_DIR / f'obs_parity_{digest}.exe'
    if not exe.exists():
        env = dict(os.environ)
        env['PATH'] = str(Path(gxx).parent) + os.pathsep + env.get('PATH', '')
        subprocess.run([gxx, '-std=c++20', '-O2', '-Wall', '-Wextra', '-DNNOBS_NATIVE', '-I', str(ROOT / 'bot/src'),
                        *map(str, srcs), '-o', str(exe)], check=True, env=env, capture_output=True, text=True)
    return exe


def run_native(exe: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env['PATH'] = str(Path(GXX).parent) + os.pathsep + env.get('PATH', '')
    return subprocess.run([str(exe), *args], env=env, capture_output=True, text=True)
