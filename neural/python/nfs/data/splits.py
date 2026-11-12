"""Deterministic grouped partitions (train / validation / final_eval) and generalisation splits.

Grouping (a group is never split across partitions):
- match identity (`match_id`), match series (`group_id` when the source provides one; archive summaries do not),
- team/bot provenance: the unordered pair of team IDs (archive member names) or bot identities (own rollouts),
  which also places every game of the same series/pairing - the near-duplicates - in one partition,
- determinism key (wasm A sha, wasm B sha, map): the official engine is deterministic, so such games are identical.
Partition = SHA-256(seed | canonical component key) bucket; independent of input order.

Generalisation splits partition entities instead of matches: maps (map-generalisation) or teams/opponents
(opponent-generalisation). A record goes to the held-out side only if ALL its entities are held out, to train only if
none are, and is otherwise `excluded_mixed` (never silently assigned).

Map provenance labels: every local map (40 in the arena) and every map seen in previous experiments or inspected
results is `reused_benchmark`; `fresh_holdout` is only possible for a map in none of those sets.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable

PARTITIONS = ('train', 'validation', 'final_eval')
REUSED = 'reused_benchmark'
FRESH = 'fresh_holdout'
NOT_LOCAL = 'archive_map_not_locally_benchmarked'


@dataclass
class SplitConfig:
    seed: str = 'nfs-split-v1'
    fractions: dict = field(default_factory=lambda: {'train': 0.8, 'validation': 0.1, 'final_eval': 0.1})
    keys: tuple = ('match_id', 'group_id', 'team_pair', 'determinism_key')
    experiment1_never_final_eval: bool = True   # matches already used by experiment 1 cannot be final evaluation


class _UF:
    def __init__(self):
        self.p: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            if rb < ra:
                ra, rb = rb, ra
            self.p[rb] = ra   # root = lexicographically smallest node -> canonical, order-independent


def record_nodes(r: dict, keys: Iterable[str]) -> list[str]:
    nodes = []
    for k in keys:
        if k == 'team_pair':
            teams = [t for t in (r.get('team_ids') or []) if t]
            if len(teams) == 2:
                nodes.append('p:' + '|'.join(sorted(teams)))
        elif r.get(k):
            v = r[k]
            nodes.append(f'{k[0]}:{"|".join(map(str, v)) if isinstance(v, (list, tuple)) else v}')
    if not nodes:
        raise ValueError('record has no grouping key: ' + json.dumps(r, default=str)[:200])
    return nodes


def components(records: list[dict], keys: Iterable[str]) -> dict[str, str]:
    """match_id -> canonical component key (union-find over shared grouping keys)."""
    keys = tuple(keys)
    uf = _UF()
    per = {}
    for r in records:
        nodes = record_nodes(r, keys)
        for n in nodes[1:]:
            uf.union(nodes[0], n)
        per[r['match_id']] = nodes[0]
    return {mid: uf.find(n) for mid, n in per.items()}


def bucket(seed: str, key: str) -> float:
    return int(hashlib.sha256(f'{seed}|{key}'.encode()).hexdigest()[:16], 16) / float(1 << 64)


def _pick(u: float, fractions: dict) -> str:
    total = sum(fractions.values())
    acc = 0.0
    for name in PARTITIONS:
        acc += fractions.get(name, 0.0) / total
        if u < acc:
            return name
    return PARTITIONS[-1] if fractions.get(PARTITIONS[-1], 0) else 'train'


def grouped_split(records: list[dict], cfg: SplitConfig | None = None) -> dict:
    cfg = cfg or SplitConfig()
    comp = components(records, cfg.keys)
    exp1_groups = {comp[r['match_id']] for r in records if r.get('used_by_experiment1')}
    assignment, reassigned = {}, 0
    group_part = {}
    for g in sorted(set(comp.values())):
        part = _pick(bucket(cfg.seed, g), cfg.fractions)
        if part == 'final_eval' and cfg.experiment1_never_final_eval and g in exp1_groups:
            part = 'train'
            reassigned += 1
        group_part[g] = part
    for r in records:
        assignment[r['match_id']] = group_part[comp[r['match_id']]]
    verify_grouping(records, assignment, cfg.keys)
    sizes = Counter(comp.values())
    return dict(kind='grouped', config=asdict(cfg), assignment=assignment,
                counts=dict(Counter(assignment.values())),
                groups=dict(Counter(group_part.values())), n_groups=len(group_part),
                largest_group=max(sizes.values()) if sizes else 0,
                experiment1_groups_reassigned_from_final_eval=reassigned)


def verify_grouping(records: list[dict], assignment: dict, keys: Iterable[str]) -> None:
    """Invariant: any two records sharing a grouping key are in the same partition."""
    seen: dict[str, str] = {}
    for r in records:
        part = assignment[r['match_id']]
        for n in record_nodes(r, keys):
            if seen.setdefault(n, part) != part:
                raise AssertionError(f'group {n} split across {seen[n]} and {part}')


def entity_holdout_split(records: list[dict], entities: Callable[[dict], list[str]], holdout_fraction: float,
                         seed: str, name: str, validation_fraction: float = 0.0) -> dict:
    """Hold out whole entities (maps, teams, opponents). all-held-out -> final_eval, none -> train/validation
    (validation = a held-out entity subset of the remaining ones if validation_fraction > 0), mixed -> excluded."""
    ents = sorted({e for r in records for e in entities(r)})
    held = {e for e in ents if bucket(seed + '|eval', e) < holdout_fraction}
    val = {e for e in ents if e not in held and bucket(seed + '|val', e) < validation_fraction}
    assignment = {}
    for r in records:
        es = set(entities(r))
        if not es:
            assignment[r['match_id']] = 'excluded_no_entity'
        elif es <= held:
            assignment[r['match_id']] = 'final_eval'
        elif not es & held and es <= val:
            assignment[r['match_id']] = 'validation'
        elif not es & held and not es & val:
            assignment[r['match_id']] = 'train'
        else:
            assignment[r['match_id']] = 'excluded_mixed'
    return dict(kind=name, seed=seed, holdout_fraction=holdout_fraction, validation_fraction=validation_fraction,
                held_out_entities=sorted(held), validation_entities=sorted(val), n_entities=len(ents),
                assignment=assignment, counts=dict(Counter(assignment.values())))


def map_split(records, holdout_fraction=0.2, validation_fraction=0.1, seed='nfs-map-split-v1') -> dict:
    return entity_holdout_split(records, lambda r: [r['map_hash']] if r.get('map_hash') else [],
                                holdout_fraction, seed, 'map_generalisation', validation_fraction)


def opponent_split(records, holdout_fraction=0.2, validation_fraction=0.1, seed='nfs-opponent-split-v1',
                   own_identity: str | None = None) -> dict:
    """Teams/bots as entities. For own rollouts pass `own_identity` so only the opponent is an entity."""
    def ents(r):
        return [t for t in (r.get('team_ids') or []) if t and t != own_identity]
    return entity_holdout_split(records, ents, holdout_fraction, seed, 'opponent_generalisation',
                                validation_fraction)


# --------------------------------------------------------------------------------------------- map provenance
def local_map_hashes(maps_dir) -> dict[str, str]:
    """sha256(map file) -> map stem for the local arena maps (summary `mapHash` is the SHA-256 of the map file)."""
    out = {}
    for p in sorted(Path(maps_dir).glob('*.map26a')):
        out[hashlib.sha256(p.read_bytes()).hexdigest()] = p.stem
    return out


def map_provenance(map_hashes: Iterable[str], local: dict[str, str], inspected: Iterable[str] = ()) -> dict:
    """Label each map hash. Local or previously inspected maps are reused benchmarks, never fresh holdouts."""
    inspected = set(inspected)
    out = {}
    for h in sorted(set(map_hashes)):
        if h in local:
            out[h] = dict(label=REUSED, local_name=local[h])
        elif h in inspected:
            out[h] = dict(label=REUSED, local_name=None, reason='seen in previous experiment data/results')
        else:
            out[h] = dict(label=FRESH, local_name=None,
                          caveat='not a local map and not in any recorded previous sample; fresh only until used')
    return out


def local_map_labels(local: dict[str, str], previous_protocols: Iterable[Path] = ()) -> dict:
    """All local maps -> reused_benchmark, with their previous-experiment roles (training/selection/final)."""
    roles = defaultdict(list)
    for proto in previous_protocols:
        proto = Path(proto)
        if not proto.exists():
            continue
        d = json.loads(proto.read_text(encoding='utf-8'))
        for role in ('training_maps', 'selection_maps', 'final_holdout_maps'):
            for m in d.get(role, []):
                roles[Path(m).stem].append(f'{proto.parent.name}/{proto.name}:{role}')
    return {name: dict(label=REUSED, map_hash=h, previous_roles=roles.get(name, []))
            for h, name in sorted(local.items(), key=lambda kv: kv[1])}


def split_manifest(records: list[dict], *, local: dict[str, str], inspected_maps: Iterable[str] = (),
                   previous_protocols: Iterable[Path] = (), cfg: SplitConfig | None = None) -> dict:
    g = grouped_split(records, cfg)
    m = map_split(records)
    o = opponent_split(records)
    prov = map_provenance([r['map_hash'] for r in records if r.get('map_hash')], local, inspected_maps)
    for split in (g, m, o):
        eval_maps = {r.get('map_hash') for r in records if split['assignment'][r['match_id']] == 'final_eval'}
        split['final_eval_map_labels'] = dict(Counter(prov[h]['label'] for h in eval_maps if h in prov))
    return dict(schema='nfs.splits.v1', n_records=len(records), grouped=g, map_generalisation=m,
                opponent_generalisation=o, map_provenance=prov,
                local_maps=local_map_labels(local, previous_protocols),
                rule='local and previously inspected maps are reused_benchmark, never fresh_holdout')
