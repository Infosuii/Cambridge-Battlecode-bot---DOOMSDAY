"""Pure float32 twins of Wave 2 D candidate builders.

These functions build typed candidate records, not a policy and not trained intelligence.
Teacher labels are always candidate zero. Targets/outcomes never enter runtime inputs.
"""
from __future__ import annotations

import numpy as np

F = 24
COMMON_NAMES = ['round', 'hp_fraction', 'gems', 'gold', 'score_margin', 'slot', 'team_size', 'melee',
                'near_allies', 'near_enemies', 'role', 'long_term_signal']
ROLES = ['farmer', 'carrier', 'fighter', 'escort', 'scout']
PRIORITIES = ['teacher_chain', 'farm_first', 'bank_first', 'home_first', 'hunt_first', 'regroup_first']
f32 = np.float32


def clip(x, lo=-4, hi=4):
    x = f32(x)
    return f32(lo) if x < f32(lo) else f32(hi) if x > f32(hi) else x


def common_features(c):
    """c: round,hp,max_hp,gems,gold,margin,slot,team_size,melee,near_allies,near_enemies,role,long_term."""
    c = np.asarray(c, dtype=np.float32)
    r, hp, maxhp, gems, gold, margin, slot, size, melee, allies, enemies, role, signal = c
    return np.asarray([clip(r / f32(2000)), clip(hp / max(maxhp, f32(1)), 0, 1), clip(gems / f32(100)),
                       clip(gold / f32(1000)), clip(margin / f32(500)), clip(slot / f32(6)), clip(size / f32(6)),
                       melee, clip(allies / f32(6)), clip(enemies / f32(8)), clip(role / f32(4)), clip(signal, -1, 1)], dtype=np.float32)


def _decision(ids, legal, feat, prior):
    return dict(K=len(ids), F=F, id=np.asarray(ids, dtype=np.uint32), legal=np.asarray(legal, dtype=np.uint8),
                feat=np.asarray(feat, dtype=np.float32).reshape(len(ids), F), prior=np.asarray(prior, dtype=np.float32),
                context=0, teacher=0, label_source='computed_teacher_choice')


def build_strategy(c, legal):
    c = np.asarray(c, dtype=np.float32)
    feat = np.zeros((6, F), dtype=np.float32)
    feat[:, :12] = common_features(c)
    prior = np.zeros(6, dtype=np.float32)
    role = int(c[11])
    for k in range(6):
        feat[k, 12 + k] = 1
        if 0 <= role < 5:
            feat[k, 18 + role] = 1
        feat[k, 23] = k == 0
        role_fit = (k == 1 and role == 0) or (k == 2 and role == 1) or (k == 4 and role in (2, 4)) or (k == 5 and role == 3)
        risk_bias = f32(f32(.10) * clip(c[12], 0, 1)) if k == 2 else f32(0)
        prior[k] = 0 if k == 0 else f32(f32(f32(-.25) + (f32(.05) if role_fit else f32(0))) + risk_bias)
    legal = np.asarray(legal, dtype=np.uint8).copy()
    legal[0] = 1
    return _decision(range(6), legal, feat, prior)


def build_role(c, teacher, has_target):
    teacher = teacher if 0 <= teacher < 5 else 0
    ids = [teacher] + [r for r in range(5) if r != teacher]
    feat = np.zeros((5, F), dtype=np.float32)
    feat[:, :12] = common_features(c)
    for k, role in enumerate(ids):
        feat[k, 12 + role] = 1
        feat[k, 17] = bool(has_target)
        feat[k, 18] = feat[k, 2] if role == 1 else 0
        feat[k, 19] = feat[k, 9] if role == 2 else 0
        feat[k, 20] = feat[k, 8] if role == 3 else 0
        feat[k, 21] = f32(f32(1) - clip(feat[k, 9], 0, 1)) if role == 4 else 0
        feat[k, 22] = f32(f32(1) - clip(feat[k, 2], 0, 1)) if role == 0 else 0
        feat[k, 23] = k == 0
    return _decision(ids, [1] * 5, feat, [0] + [-.25] * 4)


def build_objective(c, candidates):
    """rows: id,need,value,cost,score,finish,gems,gold,wait,distance,strength,claimed,legal.

    Candidates were already narrowed by the deterministic teacher, teacher first. Invalid alternatives
    retain their stable id but are masked; no route, visibility, or affordability rule is learned.
    """
    rows = np.asarray(candidates, dtype=np.float32).reshape(-1, 13)[:8]
    feat = np.zeros((len(rows), F), dtype=np.float32)
    feat[:, :12] = common_features(c)
    prior = np.zeros(len(rows), dtype=np.float32)
    for k, row in enumerate(rows):
        _, need, value, cost, score, finish, gems, gold, wait, distance, strength, claimed, _ = row
        feat[k, 12:23] = [clip(value / f32(100)), clip(cost / f32(100)), clip(score / f32(5)),
                          clip(finish / f32(100)), clip(need / f32(6)), clip(gems / f32(100)),
                          clip(gold / f32(1000)), clip(wait / f32(200)), clip(distance / f32(100)),
                          clip(strength / f32(100)), clip(claimed / f32(6))]
        feat[k, 23] = k == 0
        difference = clip(f32(score - rows[0, 4]) / f32(5), -4, 0)
        penalty = f32(f32(f32(.10) * clip(c[12], 0, 1)) * clip(feat[k, 15], 0, 1))
        prior[k] = 0 if k == 0 else f32(f32(f32(-.25) + difference) - penalty)
    legal = (rows[:, 12] != 0).astype(np.uint8)
    if len(rows):
        legal[0] = 1
    return _decision(rows[:, 0].astype(np.uint32), legal, feat, prior)


def build_draft(map_features, scores, taken, teacher, our_melee, their_melee, progress, first):
    if not 0 <= teacher < 12 or (taken & (1 << teacher)):
        return _decision([], [], [], [])
    ids = [teacher] + [c for c in range(12) if c != teacher and not (taken & (1 << c))]
    scores = np.asarray(scores, dtype=np.float32)
    feat = np.zeros((len(ids), F), dtype=np.float32)
    prior = np.zeros(len(ids), dtype=np.float32)
    for k, c in enumerate(ids):
        feat[k, c] = 1
        feat[k, 12] = clip(scores[c] / f32(10))
        feat[k, 13:19] = [clip(x) for x in map_features[:6]]
        feat[k, 19:24] = [clip(f32(our_melee) / f32(6)), clip(f32(their_melee) / f32(6)), clip(progress, 0, 1), f32(first), f32(k == 0)]
        prior[k] = 0 if k == 0 else f32(f32(-.25) + clip(f32(scores[c] - scores[teacher]) / f32(10), -4, 0))
    return _decision(ids, [1] * len(ids), feat, prior)


def bounded_values(values, activation):
    """Ranking signal twin. margin is submitted gem margin /1000, a fixed model output unit.

    The reward configuration's shaping margin_scale is independent of this model unit.
    Values are critic targets, never legality predicates.
    """
    win, margin, risk = map(f32, values)
    w, m, r = f32(activation(win)), f32(activation(margin)), f32(activation(risk))
    return clip(f32(f32(f32(.5) * r - f32(.25) * w) - f32(.25) * m), -1, 1)


def teacher_label(decision):
    if decision['K'] <= 0:
        raise ValueError('empty candidate sets have no action label')
    if not decision['legal'][0]:
        raise ValueError('teacher candidate must be legal')
    return 0
