"""Opponent league for collection and RL.

Entries are pinned by SHA-256. Kinds:
- reference: the unchanged original (teacher) - always present with a minimum share (anti-regression anchor);
- historical_release: v47 (user-supplied), first-hour release, v50 (uploaded phase-2 release);
- frozen_self: frozen checkpoints of the run itself (added during RL, capped);
- draft_proxy: baseline gameplay with a recent-meta draft order. These are PROXIES of draft preferences only, never
  real top-team executables, and are labelled so in every report.
Sampling is deterministic given the league RNG state (saved in checkpoints). `anti_regression` checks every reference
opponent separately, so a pooled improvement cannot hide a regression against the original.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROXY_LABEL = 'draft-preference proxy (baseline gameplay + recent-meta draft order); NOT a real top-team executable'
KINDS = ('reference', 'historical_release', 'frozen_self', 'draft_proxy')


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@dataclass
class Opponent:
    name: str
    kind: str
    wasm: str
    sha256: str
    weight: float = 1.0
    label: str = ''
    is_proxy: bool = False

    def verify(self) -> None:
        if sha256_file(self.wasm) != self.sha256:
            raise ValueError(f'opponent {self.name} identity changed ({self.wasm})')


@dataclass
class League:
    opponents: list = field(default_factory=list)
    min_reference_share: float = 0.3
    max_frozen_self: int = 4
    seed: int = 20261024
    draws: int = 0

    def add(self, name, kind, wasm, weight=1.0, label='') -> Opponent:
        if kind not in KINDS:
            raise ValueError(f'unknown opponent kind {kind}')
        if any(o.name == name for o in self.opponents):
            raise ValueError(f'duplicate opponent {name}')
        o = Opponent(name=name, kind=kind, wasm=str(wasm), sha256=sha256_file(wasm), weight=float(weight),
                     label=PROXY_LABEL if kind == 'draft_proxy' else label, is_proxy=kind == 'draft_proxy')
        self.opponents.append(o)
        frozen = [x for x in self.opponents if x.kind == 'frozen_self']
        while len(frozen) > self.max_frozen_self:
            self.opponents.remove(frozen.pop(0))
        return o

    def sample(self, n: int) -> list[Opponent]:
        """n opponents; at least ceil(min_reference_share * n) are reference opponents. Deterministic."""
        if not self.opponents:
            raise ValueError('empty league')
        rng = random.Random(f'{self.seed}:{self.draws}')
        self.draws += 1
        refs = [o for o in self.opponents if o.kind == 'reference']
        need = math.ceil(self.min_reference_share * n - 1e-9) if refs else 0
        out = [refs[i % len(refs)] for i in range(min(n, need))]
        w = [o.weight for o in self.opponents]
        out += rng.choices(self.opponents, weights=w, k=n - len(out))
        rng.shuffle(out)
        return out

    def state_dict(self) -> dict:
        return dict(opponents=[asdict(o) for o in self.opponents], min_reference_share=self.min_reference_share,
                    max_frozen_self=self.max_frozen_self, seed=self.seed, draws=self.draws)

    @classmethod
    def from_state(cls, d: dict) -> 'League':
        lg = cls(min_reference_share=d['min_reference_share'], max_frozen_self=d['max_frozen_self'],
                 seed=d['seed'], draws=d['draws'])
        lg.opponents = [Opponent(**o) for o in d['opponents']]
        return lg

    def verify(self) -> None:
        for o in self.opponents:
            o.verify()


def default_league(builds_dir=None, proxies: list[Path] = ()) -> League:
    """original, v47, first-hour, v50 from references/builds (built by the lead with the official CLI)."""
    b = Path(builds_dir or ROOT / 'references/builds')
    lg = League()
    lg.add('original', 'reference', b / 'original.wasm', 2.0, 'unchanged original bot (teacher)')
    for name, label in (('v47', 'user-supplied v47'), ('first-hour', 'first-hour neural release'),
                        ('v50', 'phase-2 release uploaded as version 50')):
        if (b / f'{name}.wasm').exists():
            lg.add(name, 'historical_release', b / f'{name}.wasm', 1.0, label)
    for p in proxies:
        lg.add(Path(p).stem, 'draft_proxy', p, 0.5)
    return lg


def anti_regression(candidate: dict, baseline: dict, references: list[str], max_drop: float = 0.0) -> dict:
    """Per-opponent check: candidate win rate vs each reference opponent must not fall more than `max_drop` below the
    baseline's (same maps/sides). Pooled totals are reported but never sufficient. Final promotion uses H's gate."""
    rows, ok = {}, True
    for name in references:
        c, b = candidate.get(name), baseline.get(name)
        if c is None or b is None:
            rows[name] = dict(ok=False, reason='missing results')
            ok = False
            continue
        cw, bw = c['wins'] / max(1, c['games']), b['wins'] / max(1, b['games'])
        good = cw >= bw - max_drop
        rows[name] = dict(ok=good, candidate=cw, baseline=bw, drop=bw - cw)
        ok = ok and good
    pooled = lambda d: sum(v['wins'] for v in d.values()) / max(1, sum(v['games'] for v in d.values()))
    return dict(ok=ok, per_opponent=rows, pooled_candidate=pooled(candidate), pooled_baseline=pooled(baseline),
                rule='every reference opponent separately; pooled score is informational only')
