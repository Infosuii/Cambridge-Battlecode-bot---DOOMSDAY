"""Complete, atomic training checkpoints and safe resume.

A checkpoint holds actor, critic, both optimizers, scheduler, RNG states (python, numpy, torch, cuda), observation and
action schema hashes, league state, data/split provenance, the games ledger and counters, plus a `pairing_id` that ties
actor, critic and optimizer states written together.

Resume rules:
- The authorized wall-clock deadline is an absolute time persisted once in <run>/clock.json; resume reads it and never
  extends it (a new authorization needs a new run id).
- Games are accounted by match folder in <run>/games.json; a folder already accounted is never re-counted, so a
  restarted collection (whose engine runs are cached by folder) cannot inflate game counts.
- Resuming from a *selected* actor checkpoint (e.g. best.pt) requires its critic/optimizer to belong to the same
  pairing; otherwise resume refuses (stale critic/optimizer) unless `reset_critic_optimizer=True` is passed explicitly,
  in which case critic and optimizers are re-initialised and that fact is recorded in provenance.
- Observation/action schema hashes must match the running code.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import random
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch

SCHEMA = 'nfs.checkpoint.v1'


class CheckpointError(RuntimeError):
    pass


def _atomic_bytes_write(path: Path, writer) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    with open(tmp, 'wb') as f:
        writer(f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_json(path, data) -> None:
    _atomic_bytes_write(Path(path), lambda f: f.write((json.dumps(data, indent=2, default=str) + '\n').encode()))


def rng_state() -> dict:
    st = dict(python=random.getstate(), numpy=np.random.get_state(), torch=torch.get_rng_state())
    if torch.cuda.is_available():
        st['cuda'] = torch.cuda.get_rng_state_all()
    return st


def set_rng_state(st: dict) -> None:
    random.setstate(st['python'])
    np.random.set_state(st['numpy'])
    torch.set_rng_state(st['torch'])
    if 'cuda' in st and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(st['cuda'])


def param_hash(module) -> str | None:
    if module is None:
        return None
    h = hashlib.sha256()
    for k, v in module.state_dict().items():
        h.update(k.encode())
        h.update(v.detach().cpu().contiguous().numpy().astype('<f4' if v.is_floating_point() else v.cpu().numpy().dtype).tobytes())
    return h.hexdigest()


# --------------------------------------------------------------------------------------------- clock / ledger
@dataclass
class RunClock:
    run_id: str
    authorized_minutes: float
    started_epoch: float
    deadline_epoch: float

    @classmethod
    def authorize(cls, run_dir, minutes: float, run_id: str) -> 'RunClock':
        """Create the clock once. If it exists (resume), the persisted deadline is kept unchanged."""
        p = Path(run_dir) / 'clock.json'
        if p.exists():
            c = cls(**{k: v for k, v in json.loads(p.read_text(encoding='utf-8')).items() if k in cls.__annotations__})
            if c.run_id != run_id:
                raise CheckpointError(f'run dir belongs to run {c.run_id}, not {run_id}; use a new run dir')
            return c
        now = time.time()
        c = cls(run_id=run_id, authorized_minutes=float(minutes), started_epoch=now, deadline_epoch=now + 60.0 * minutes)
        atomic_json(p, dict(asdict(c), deadline_utc=dt.datetime.fromtimestamp(c.deadline_epoch, dt.timezone.utc).isoformat()))
        return c

    @classmethod
    def load(cls, run_dir) -> 'RunClock':
        p = Path(run_dir) / 'clock.json'
        if not p.exists():
            raise CheckpointError('no clock.json: run was never authorized')
        return cls(**{k: v for k, v in json.loads(p.read_text(encoding='utf-8')).items() if k in cls.__annotations__})

    def remaining(self) -> float:
        return self.deadline_epoch - time.time()

    def expired(self, margin: float = 0.0) -> bool:
        return self.remaining() <= margin


class GamesLedger:
    """Games accounted by match folder; persisted atomically in <run>/games.json."""

    def __init__(self, run_dir):
        self.path = Path(run_dir) / 'games.json'
        self.games: dict[str, dict] = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {}

    @staticmethod
    def key(folder) -> str:
        return Path(folder).resolve().as_posix().lower()

    def account(self, folder, info: dict | None = None) -> bool:
        k = self.key(folder)
        if k in self.games:
            return False
        self.games[k] = dict(info or {}, accounted_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'))
        return True

    def __contains__(self, folder) -> bool:
        return self.key(folder) in self.games

    def __len__(self) -> int:
        return len(self.games)

    def merge(self, games: dict) -> None:
        for k, v in games.items():
            self.games.setdefault(k, v)

    def save(self) -> None:
        atomic_json(self.path, self.games)


# --------------------------------------------------------------------------------------------- save / load
def save_checkpoint(path, *, actor, critic=None, actor_opt=None, critic_opt=None, scheduler=None, league_state=None,
                    obs_schema_hash=None, action_schema_hash=None, provenance: dict | None = None,
                    ledger: GamesLedger | None = None, clock: RunClock | None = None, counters: dict | None = None,
                    pairing_id: str | None = None, status: str = 'in_training') -> dict:
    meta = dict(schema=SCHEMA, pairing_id=pairing_id or uuid.uuid4().hex, status=status,
                saved_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                actor_hash=param_hash(actor), critic_hash=param_hash(critic),
                obs_schema_hash=obs_schema_hash, action_schema_hash=action_schema_hash,
                provenance=provenance or {}, counters=counters or {},
                clock=asdict(clock) if clock else None, games_accounted=len(ledger) if ledger else 0)
    payload = dict(meta=meta, actor=actor.state_dict(),
                   critic=critic.state_dict() if critic is not None else None,
                   actor_opt=actor_opt.state_dict() if actor_opt is not None else None,
                   critic_opt=critic_opt.state_dict() if critic_opt is not None else None,
                   scheduler=scheduler.state_dict() if scheduler is not None else None,
                   league=league_state, rng=rng_state(), games=dict(ledger.games) if ledger else {})
    _atomic_bytes_write(Path(path), lambda f: torch.save(payload, f))
    if ledger is not None:
        ledger.save()
    atomic_json(Path(path).with_suffix('.json'), meta)
    return meta


def load_checkpoint(path, map_location='cpu') -> dict:
    d = torch.load(Path(path), map_location=map_location, weights_only=False)  # own files only
    if d.get('meta', {}).get('schema') != SCHEMA:
        raise CheckpointError(f'{path}: not an {SCHEMA} checkpoint')
    return d


def resume(run_dir, *, actor, critic=None, actor_opt=None, critic_opt=None, scheduler=None,
           actor_from=None, obs_schema_hash=None, action_schema_hash=None, reset_critic_optimizer: bool = False,
           restore_rng: bool = True) -> dict:
    """Restore a run. Returns {'meta', 'league', 'ledger', 'clock', 'counters', 'reset_critic_optimizer'}."""
    run_dir = Path(run_dir)
    clock = RunClock.load(run_dir)
    latest_p = run_dir / 'latest.pt'
    src_p = Path(actor_from) if actor_from else latest_p
    if not src_p.exists():
        raise CheckpointError(f'no checkpoint at {src_p}')
    d = load_checkpoint(src_p)
    meta = d['meta']
    for name, want, got in (('observation', obs_schema_hash, meta.get('obs_schema_hash')),
                            ('action', action_schema_hash, meta.get('action_schema_hash'))):
        if want is not None and got != want:
            raise CheckpointError(f'{name} schema hash mismatch: checkpoint {got} vs code {want}')
    actor.load_state_dict(d['actor'])
    if param_hash(actor) != meta['actor_hash']:
        raise CheckpointError('actor parameters do not match the recorded hash (corrupt checkpoint)')
    has_pair = d.get('critic') is not None and d.get('actor_opt') is not None
    reset = False
    if actor_from and not has_pair:
        if not reset_critic_optimizer:
            raise CheckpointError(f'{src_p} is an actor-only selection; refusing to pair it with a stale critic/'
                                  'optimizer. Pass reset_critic_optimizer=True to re-initialise them explicitly.')
        reset = True
    elif actor_from and latest_p.exists() and reset_critic_optimizer:
        reset = True
    if not reset:
        if critic is not None:
            if d.get('critic') is None:
                raise CheckpointError('checkpoint has no critic')
            critic.load_state_dict(d['critic'])
            if param_hash(critic) != meta['critic_hash']:
                raise CheckpointError('critic does not match its pairing hash')
        if actor_opt is not None and d.get('actor_opt') is not None:
            actor_opt.load_state_dict(d['actor_opt'])
        if critic_opt is not None and d.get('critic_opt') is not None:
            critic_opt.load_state_dict(d['critic_opt'])
        if scheduler is not None and d.get('scheduler') is not None:
            scheduler.load_state_dict(d['scheduler'])
        if restore_rng:
            set_rng_state(d['rng'])
    ledger = GamesLedger(run_dir)
    ledger.merge(d.get('games', {}))
    return dict(meta=meta, league=d.get('league'), ledger=ledger, clock=clock, counters=dict(meta.get('counters', {})),
                reset_critic_optimizer=reset, source=str(src_p))
