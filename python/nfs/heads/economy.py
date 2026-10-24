"""Economy candidate twins. Synthetic tests exercise the exact float32 C++ feature definitions.

The environment supplies legality. Neither this module nor a model infers SDK legality. Shop choice 0 means the
complete teacher purchase plan as an opaque guarded executor; item, count, cost, owned and projected gold-after
features are zero for that option. No first-purchase preview or duplicate build_for call is made. Alternatives are
save or one guarded purchase. Bank route IDs describe existing reachable fields, avoiding unbounded per-altar paths.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import numpy as np

BANK_F = SHOP_F = 20
MAX_K = 16
BANK_FEATURES = ("teacher", "bank_now", "safe_route", "distance", "carried_gems", "hp_fraction", "gold",
                 "round", "ally_score", "enemy_score", "score_gap", "forced", "winning_bag", "deadline",
                 "end_bank", "rhythm", "edge", "threatened", "channel_turns", "bag_per_trip_turn")
SHOP_FEATURES = ("teacher", "save", "teacher_plan", "shard", "consumable", "item_family", "item_stat", "quantity",
                 "cost", "gold_after", "owned_shard_equivalent", "emblem_progress", "hp_fraction", "carried_gems",
                 "gold", "round", "score_gap", "consumable_kind", "ally_score", "enemy_score")


@dataclass
class State:
    hp: float = 0
    max_hp: float = 1
    gems: int = 0
    gold: int = 0
    round: int = 0
    ally_score: int = 0
    enemy_score: int = 0


@dataclass
class BankTerms:
    go: bool = False
    safe: bool = False
    force: bool = False
    wins: bool = False
    late: bool = False
    end_bank: bool = False
    rhythm: bool = False
    edge: bool = False
    threatened: bool = False
    dist: int = 0
    raw_dist: int = -1


@dataclass(frozen=True)
class BankChoice:
    go: bool
    safe: bool
    dist: int


class BuyKind(IntEnum):
    plan = 0
    save = 1
    shard = 2
    consumable = 3


@dataclass
class Buy:
    kind: BuyKind = BuyKind.save
    item: int = 0
    count: int = 0
    cost: int = 0
    owned: int = 0
    legal: bool = True


def _norm(x, scale, lo=0, hi=1):
    v = np.float32(x) / np.float32(scale)
    return np.float32(lo) if v < lo else np.float32(hi) if v > hi else v


def bank_id(c):
    return 0 if not c.go else 2 if c.safe else 1


def buy_id(b):
    return 0 if b.kind == BuyKind.plan else 1 if b.kind == BuyKind.save else (0x100 if b.kind == BuyKind.shard else 0x200) + b.item


def _decision(head, choices, features, ids, legal):
    return dict(head=head, K=len(choices), F=20, context=0, choices=choices,
                id=np.asarray(ids, dtype=np.uint32), legal=np.asarray(legal, dtype=np.uint8),
                prior=np.asarray([0] + [-.25] * (len(choices)-1), dtype=np.float32),
                feat=np.asarray(features, dtype=np.float32))


def build_bank(s: State, t: BankTerms):
    choices = [BankChoice(t.go, t.safe, t.dist)]

    def add(c):
        if bank_id(c) not in [bank_id(x) for x in choices]:
            choices.append(c)

    if not (t.force or t.wins or t.late):
        add(BankChoice(False, t.safe, t.dist))
    add(BankChoice(True, t.safe, t.dist))
    if t.safe and t.raw_dist >= 0:
        add(BankChoice(True, False, t.raw_dist))
    features = []
    for i, c in enumerate(choices):
        features.append([i == 0, c.go, c.safe, _norm(c.dist, 128), _norm(s.gems, 200),
                         _norm(s.hp, s.max_hp if s.max_hp > 0 else 1), _norm(s.gold, 600), _norm(s.round, 2000),
                         _norm(s.ally_score, 1000), _norm(s.enemy_score, 1000),
                         _norm(np.float32(s.ally_score) - np.float32(s.enemy_score), 1000, -1, 1),
                         t.force, t.wins, t.late, t.end_bank, t.rhythm, t.edge, t.threatened,
                         _norm(s.gems // 10 + (s.gems % 10 > 0), 20),
                         _norm(s.gems, np.float32(10) * (np.float32(c.dist) + np.float32(1)))])
    return _decision("bank", choices, features, [bank_id(c) for c in choices], [1]*len(choices))


def build_shop(s: State, teacher: Buy, options: list[Buy]):
    # Ignore the compatibility preview argument: candidate0 is the opaque complete guarded executor.
    choices = [Buy(BuyKind.plan), Buy()]
    for c in options[:MAX_K-2]:
        if c.kind not in (BuyKind.shard, BuyKind.consumable):
            continue
        if buy_id(c) not in [buy_id(x) for x in choices[2:]]:
            choices.append(c)
    features = []
    for i, b in enumerate(choices):
        shard = b.kind == BuyKind.shard
        features.append([i == 0, b.kind == BuyKind.save, b.kind == BuyKind.plan, shard, b.kind == BuyKind.consumable,
                         _norm(b.item // 6, 6) if shard else 0, _norm((b.item % 6) // 2, 2) if shard else 0,
                         _norm(b.count, 20), _norm(b.cost, 600),
                         0 if b.kind == BuyKind.plan else _norm(np.float32(s.gold) - np.float32(b.cost), 600),
                         _norm(b.owned, 100),
                         _norm(b.owned % 5, 4) if shard else 0, _norm(s.hp, s.max_hp if s.max_hp > 0 else 1),
                         _norm(s.gems, 200), _norm(s.gold, 600), _norm(s.round, 2000),
                         _norm(np.float32(s.ally_score) - np.float32(s.enemy_score), 1000, -1, 1),
                         _norm(b.item, 4) if b.kind == BuyKind.consumable else 0,
                         _norm(s.ally_score, 1000), _norm(s.enemy_score, 1000)])
    return _decision("shop", choices, features, [buy_id(b) for b in choices],
                     [i == 0 or (b.legal and b.cost <= s.gold) for i, b in enumerate(choices)])


def teacher_label(decision):
    """Teacher-label collection always labels the complete original option at candidate index zero."""
    if decision["K"] == 0 or not decision["legal"][0]:
        raise ValueError("teacher candidate missing/illegal")
    return 0
