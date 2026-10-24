"""Teacher / self-play episode collection through the official engine (nfs.engine.run_jobs).

- Candidate bot: built from the workspace bot/src copy with a profile via B's tools/install_models.py (`training`
  for RL: active heads, sampling + NFS1 records; a shadow+records profile for teacher labels - see CONTRACT_ISSUES).
  The lead-owned bot/src is never regenerated in place: the tool must accept an output source directory.
- Opponents from the league (pinned SHA-256). Every job folder gets a job.json with both wasm identities and the map,
  which gives the determinism key used by grouped splits (same wasm pair + map = identical game).
- Engine runs are cached by folder (engine.run_match); the GamesLedger counts each folder once.
- Worker count and torch CPU threads are configurable; GPU is used only by the trainer, never by engine workers.
This module runs games but never updates parameters. Collection is bounded by --max-games and the run clock.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .. import engine
from .checkpoint import GamesLedger, RunClock, atomic_json
from .league import League

ROOT = engine.ROOT


class CollectError(RuntimeError):
    pass


@dataclass
class CollectConfig:
    out_dir: str = str(ROOT / 'artifacts/collect')
    maps: list = field(default_factory=list)          # map stems or paths; empty = all local maps
    sides: tuple = ('A', 'B')
    games_per_iteration: int = 24
    max_games: int = 24
    workers: int = 0                                  # 0 = engine.default_workers()
    torch_threads: int = 4
    log_limit: int = 64 * 1024 * 1024                 # NFS1 records go to stdout; keep them untruncated
    timeout: int = 600
    profile: str = 'training'


def resolve_maps(names) -> list[Path]:
    allm = {p.stem: p for p in engine.maps()}
    if not names:
        return list(allm.values())
    out = []
    for n in names:
        p = Path(n)
        out.append(p if p.suffix else allm[n])
    return out


def build_profile_bot(profile: str, out_dir, *, python: str = sys.executable, model: str | None = None,
                      install_tool: Path = ROOT / 'tools/install_models.py') -> dict:
    """Copy bot/src, install models for `profile` into the copy (B's tool), build with the official CLI."""
    out_dir = Path(out_dir)
    if not install_tool.exists():
        raise CollectError('tools/install_models.py (Agent B) is not available; cannot build the profile bot')
    help_text = subprocess.run([python, str(install_tool), '--help'], capture_output=True, text=True,
                               encoding='utf-8', errors='replace', timeout=60).stdout
    work = engine.make_bot_dir(ROOT / 'bot/src', out_dir / f'bot-{profile}')
    opt = next((o for o in ('--src', '--src-dir', '--bot-dir', '--out-src') if o in help_text), None)
    if opt is None:
        raise CollectError('install_models.py offers no output source-directory option; refusing to regenerate the '
                           'lead-owned bot/src in place')
    target = work / 'src' if opt != '--bot-dir' else work
    args = [python, str(install_tool), '--profile', profile, opt, str(target), '--receipt', str(out_dir / f'{profile}.install.json')]
    if model:
        args += ['--model', str(model)]   # in-training export (see agents/G/CONTRACT_ISSUES.md: model dir support)
    r = subprocess.run(args, capture_output=True,
                       text=True, encoding='utf-8', errors='replace', timeout=600, cwd=ROOT)
    if r.returncode:
        raise CollectError('install_models.py failed:\n' + (r.stdout + r.stderr)[-2000:])
    wasm = engine.official_build(work, out_dir / f'{profile}.wasm', release=True)
    man = dict(profile=profile, model=model, wasm=str(wasm), sha256=engine.sha256(wasm), source_tree_sha256=engine.tree_sha256(work / 'src'),
               code_section_sha256=engine.code_section_sha(wasm), install_log=(r.stdout + r.stderr)[-2000:])
    atomic_json(out_dir / f'{profile}.build.json', man)
    return man


def plan_jobs(candidate_wasm, league: League, maps: list[Path], sides, n_games: int, out_dir, iteration: int,
              candidate_name: str = 'candidate') -> list[dict]:
    out_dir = Path(out_dir)
    cand_sha = engine.sha256(candidate_wasm)
    if n_games <= 0:
        return []
    pairs = (n_games + max(1, len(sides)) - 1) // max(1, len(sides))
    opps = league.sample(pairs)
    jobs = []
    for k, opp in enumerate(opps):
        m = maps[(iteration * 7 + k) % len(maps)]
        for side in sides:
            a, b = (candidate_wasm, opp.wasm) if side == 'A' else (opp.wasm, candidate_wasm)
            # content-addressed: a folder can only ever hold the game of this exact wasm pair + map + side
            folder = out_dir / f'it{iteration:05d}' / f'{k:03d}-{opp.name}-{m.stem}-{side}-{cand_sha[:10]}-{opp.sha256[:10]}'
            job = dict(a=str(a), b=str(b), map_path=str(m), folder=str(folder), candidate_side=side)
            meta = dict(job, candidate=candidate_name, candidate_sha256=cand_sha, opponent=opp.name,
                        opponent_kind=opp.kind, opponent_is_proxy=opp.is_proxy, opponent_sha256=opp.sha256,
                        map=m.stem, map_sha256=engine.sha256(m), iteration=iteration,
                        determinism_key=[cand_sha if side == 'A' else opp.sha256,
                                         opp.sha256 if side == 'A' else cand_sha, engine.sha256(m)],
                        team_ids=[cand_sha, opp.sha256])
            jobs.append(dict(job=job, meta=meta))
            if len(jobs) >= n_games:
                return jobs
    return jobs


def run_collection(jobs: list[dict], cfg: CollectConfig, ledger: GamesLedger, clock: RunClock | None = None) -> dict:
    """Run planned jobs (cached by folder) and account each completed folder once."""
    try:
        import torch
        torch.set_num_threads(max(1, cfg.torch_threads))
    except ImportError:
        pass
    todo = []
    for j in jobs:
        if clock is not None and clock.expired(margin=60):
            break
        if len(todo) + len(ledger) >= cfg.max_games and j['job']['folder'] not in ledger:
            break
        folder = Path(j['job']['folder'])
        prev = folder / 'job.json'
        if prev.exists():
            old = json.loads(prev.read_text(encoding='utf-8'))
            for k in ('candidate_sha256', 'opponent_sha256', 'map_sha256', 'candidate_side'):
                if old.get(k) != j['meta'].get(k):
                    raise CollectError(f'{folder} already holds a different game ({k}); refusing to reuse its summary')
        folder.mkdir(parents=True, exist_ok=True)
        atomic_json(prev, j['meta'])
        todo.append(dict(j['job'], log_limit=cfg.log_limit, timeout=cfg.timeout))
    workers = cfg.workers or engine.default_workers()
    results = engine.run_jobs(todo, workers) if todo else []
    new = 0
    for r in results:
        new += ledger.account(r.folder, dict(map=r.map, side=r.side, win=r.win, faults=r.faults))
    ledger.save()
    return dict(planned=len(jobs), run=len(results), newly_accounted=new, accounted_total=len(ledger),
                faults=sum(r.faults for r in results), workers=workers, results=[r.row() for r in results])
