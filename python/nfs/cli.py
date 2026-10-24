"""`tools/nfs.py` command-line pipeline (Agent G). Commands are instructions for LATER runs unless noted.

  inspect-data     summarise archive index / split / dataset manifests (read-only)
  index-archives   bounded archive index + eligibility sample (<= 200 converted entries per part)
  build-splits     grouped train/validation/final_eval + map/opponent generalisation splits
  collect          teacher/self-play engine games (requires --i-authorize-collection, --max-games, time limit)
  build-dataset    NFS1 records + summaries -> schema-versioned shards
  pretrain         imitation               } parameter-updating: require --i-authorize-training
  train-value      value/outcome models    } AND --time-limit-minutes; refuse otherwise
  rl               PPO with league         }
  export           checkpoint -> C++ model via B's nfs.export (refuses synthetic/untrained provenance)
  benchmark        delegates to H's tools/eval_run.py
  promote          H's gate (nfs.evaluate.gate.evaluate_files); refuses if the gate is absent or fails
"""
from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
import uuid
from pathlib import Path

from . import engine

ROOT = engine.ROOT
MANIFESTS = ROOT / 'data' / 'manifests'
PREV = Path(engine.PATHS['previous_experiment'])
EXP1_CACHE = PREV / 'historical-training'
PARAM_UPDATING = ('pretrain', 'train-value', 'rl')


def _json(p) -> dict:
    return json.loads(Path(p).read_text(encoding='utf-8'))


def _cfg(path) -> dict:
    return _json(path) if path else {}


def _dc(cls, d: dict | None):
    """Dataclass from a config section: '_'-prefixed doc keys dropped, lists -> tuples for tuple fields."""
    import dataclasses
    names = {f.name: f for f in dataclasses.fields(cls)}
    kw = {k: (tuple(v) if isinstance(v, list) and 'tuple' in str(names[k].type) else v)
          for k, v in (d or {}).items() if k in names}
    return cls(**kw)


def _print(d) -> None:
    print(json.dumps(d, indent=2, default=str))


# --------------------------------------------------------------------------------------------- data commands
def cmd_inspect_data(a) -> int:
    out = {}
    for name in ('archive_index_v1.json', 'splits_v1.json'):
        p = MANIFESTS / name
        if p.exists():
            d = _json(p)
            out[name] = d.get('accounting') or {k: d[k] for k in ('n_records',) if k in d} or list(d)[:10]
            if name == 'splits_v1.json':
                out[name] = {k: d[k].get('counts') for k in ('grouped', 'map_generalisation', 'opponent_generalisation')}
    if a.dataset:
        out['dataset'] = _json(a.dataset).get('accounting')
    _print(out or dict(note='no manifests yet; run index-archives'))
    return 0


def cmd_index_archives(a) -> int:
    from .data import archives as ar
    from .data import splits as sp
    lock = EXP1_CACHE / 'ingestion.lock'
    if lock.exists():
        print(f'refusing: the previous experiment ingestion lock exists ({lock}); an ingestion job may be running')
        return 3
    if a.sample_per_part + a.consistency_checks > ar.BOUNDED_SAMPLE_CAP:
        print(f'refusing: bounded validation is capped at {ar.BOUNDED_SAMPLE_CAP} converted entries per part')
        return 2
    hist = engine.PATHS['historical']
    paths = [Path(hist['part1_zip'])] + sorted(Path(hist['parts_dir']).glob('*.zip'))
    exp1 = ar.load_experiment1_ids(EXP1_CACHE)
    listing = ar.load_platform_listing(PREV / 'data' / 'archive-links.json')
    conv = ar.cambc_summary_converter(engine.CLI, ROOT / 'artifacts' / 'tmp' / 'camstat')
    man = ar.build_index(paths, sample_per_part=a.sample_per_part, converter=conv, experiment1_ids=exp1,
                         consistency_checks_per_part=a.consistency_checks,
                         hash_cache=None if a.no_hash else MANIFESTS / 'sha256_cache.json',
                         platform_listing=listing, workers=a.workers, sample_out_dir=ROOT / 'data' / 'archive_sample_v1',
                         local_map_hashes=sp.local_map_hashes(engine.MAPS))
    engine.write_json(MANIFESTS / 'experiment1_used_ids_v1.json',
                      dict(label='already_used_by_experiment_1', source=str(EXP1_CACHE), read_only=True,
                           count=len(exp1), ids=exp1))
    man['experiment1']['ids_file'] = 'data/manifests/experiment1_used_ids_v1.json'
    engine.write_json(Path(a.out), man)
    _print(dict(out=a.out, accounting=man['accounting']))
    return 0


def _sample_rows(path=None) -> list[dict]:
    p = Path(path or ROOT / 'data' / 'archive_sample_v1' / 'sample_rows.jsonl')
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]


def cmd_build_splits(a) -> int:
    from .data import splits as sp
    rows = [r for r in _sample_rows(a.rows) if r.get('accepted')]
    from .data.archives import load_experiment1_ids
    inspected = set()
    for p in sorted(EXP1_CACHE.glob('part-*-v2.jsonl')):
        for l in p.read_text(encoding='utf-8').splitlines():
            h = json.loads(l).get('map_hash')
            if h:
                inspected.add(h)
    protos = [PREV / 'protocol.json', PREV / 'phase2-two-hours' / 'protocol.json']
    man = sp.split_manifest(rows, local=sp.local_map_hashes(engine.MAPS), inspected_maps=inspected,
                            previous_protocols=protos)
    man['source_rows'] = str(a.rows or 'data/archive_sample_v1/sample_rows.jsonl')
    engine.write_json(Path(a.out), man)
    _print({k: man[k]['counts'] for k in ('grouped', 'map_generalisation', 'opponent_generalisation')})
    return 0


# --------------------------------------------------------------------------------------------- collection
def _training_maps(spec) -> list[str]:
    if isinstance(spec, list):
        return spec
    if spec == 'eval_partition:training':
        try:
            from .evaluate import protocol as proto
        except ImportError as exc:
            raise SystemExit(f'evaluation protocol (Agent H) unavailable: {exc}; refusing to guess training maps')
        try:      # H: read the frozen partition file, not a recomputed list (agents/H/CONTRACT_ISSUES.md 1)
            return list(proto.load_schedule('map_partitions')['partitions']['training'])
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(f'frozen map partitions unavailable ({exc}); refusing to guess training maps')
    raise SystemExit(f'unknown map spec {spec!r}')


def cmd_collect(a) -> int:
    if not a.i_authorize_collection or not a.max_games or not a.time_limit_minutes:
        print('refusing: collect runs engine games; pass --i-authorize-collection, --max-games and --time-limit-minutes')
        return 2
    from .train import collect as co
    from .train.checkpoint import GamesLedger, RunClock
    from .train.league import default_league
    cfg = _cfg(a.config)
    run_dir = Path(a.run_dir)
    clock = RunClock.authorize(run_dir, a.time_limit_minutes, a.run_id or run_dir.name)
    ccfg = _dc(co.CollectConfig, cfg.get('collect'))
    ccfg.max_games, ccfg.out_dir = a.max_games, str(run_dir / 'games')
    if a.workers:
        ccfg.workers = a.workers
    cand = Path(a.candidate) if a.candidate else Path(co.build_profile_bot(a.profile or ccfg.profile, run_dir / 'builds')['wasm'])
    league = _league_from_cfg(cfg)
    maps = co.resolve_maps(_training_maps(cfg.get('maps', 'eval_partition:training')))
    ledger = GamesLedger(run_dir)
    jobs = co.plan_jobs(cand, league, maps, ccfg.sides, a.max_games, ccfg.out_dir, iteration=a.iteration)
    rep = co.run_collection(jobs, ccfg, ledger, clock)
    rep.pop('results', None)
    _print(rep)
    return 0


def cmd_build_dataset(a) -> int:
    from .data import records_dataset as rd
    from .train.rewards import RewardConfig
    rcfg = RewardConfig.from_dict(_cfg(a.reward_config).get('reward', {})) if a.reward_config else RewardConfig()
    srcs = []
    for job in sorted(Path(a.games).rglob('job.json')):
        meta = _json(job)
        if (job.parent / 'summary.json').exists():
            srcs.append(rd.MatchSource.from_folder(job.parent, meta['candidate_side']))
    split = _json(a.splits)['grouped']['assignment'] if a.splits else None
    part_of = (lambda s: split.get(s.match_id, 'unassigned')) if split else None
    man = rd.build_dataset(srcs, Path(a.out), name=a.name, reward_cfg=rcfg, partition_of=part_of)
    _print(man['accounting'])
    return 0


# --------------------------------------------------------------------------------------------- training
def _require(a, what) -> float:
    from .train.auth import require_authorization
    return require_authorization(a.i_authorize_training, a.time_limit_minutes, what)


def _build_model(model_cfg_path):
    try:
        models = importlib.import_module('nfs.models')
    except ImportError as exc:
        raise SystemExit(f'nfs.models (Agent B) unavailable: {exc}')
    # PolicyNet allocates zeros. Starting every layer at zero leaves candidate scores symmetric and the
    # hidden layers without a learning signal. Match the seeded, zero-output UNTRAINED runtime initialization.
    model = models.build_model(_json(model_cfg_path))
    return models.init_untrained(model, seed=20261024, zero_residual=True)


def cmd_pretrain(a) -> int:
    minutes = _require(a, 'pretrain')
    from .data.records_dataset import Shard
    from .train import imitation
    from .train.checkpoint import RunClock, save_checkpoint
    from .train.common import Deadline
    cfg = _cfg(a.config)
    clock = RunClock.authorize(a.run_dir, minutes, a.run_id or Path(a.run_dir).name)
    model = _build_model(a.model_config)
    icfg = _dc(imitation.ImitationConfig, cfg.get('imitation'))
    tr, va = Shard.load(a.train), Shard.load(a.validation)
    rep = imitation.pretrain(model, tr, va, icfg, authorized=True, time_limit_minutes=minutes,
                             deadline=Deadline(clock.deadline_epoch))
    save_checkpoint(Path(a.run_dir) / 'pretrain.pt', actor=model, clock=clock, status='pretrained_unvalidated',
                    provenance=dict(stage='pretrain', train=tr.manifest, validation=va.manifest,
                                    synthetic=bool(tr.manifest.get('synthetic'))))
    engine.write_json(Path(a.run_dir) / 'pretrain_report.json', rep)
    return 0


def cmd_train_value(a) -> int:
    minutes = _require(a, 'train-value')
    from .train import value as V
    from .train.checkpoint import RunClock, save_checkpoint
    from .train.common import Deadline
    cfg = _cfg(a.config)
    clock = RunClock.authorize(a.run_dir, minutes, a.run_id or Path(a.run_dir).name)
    vcfg = _dc(V.ValueConfig, cfg.get('value'))
    if a.draft:
        from .data.archives import draft_observational_records
        rows = draft_observational_records([r for r in _sample_rows(a.rows) if r.get('accepted')])
        assignment = _json(a.splits)['grouped']['assignment']
        model = V.DraftOutcomeModel()
        rep = V.train_draft_outcome(rows, assignment, vcfg, model=model, authorized=True,
                                    time_limit_minutes=minutes, deadline=Deadline(clock.deadline_epoch))
        provenance = dict(stage='draft_outcome', confounded=True, exportable_to_runtime=False,
                          source_rows=str(a.rows), splits=str(a.splits), synthetic=False)
    else:
        from .data.records_dataset import Shard
        model = _build_model(a.model_config)
        train, validation = Shard.load(a.train), Shard.load(a.validation)
        rep = V.train_value(model, train, validation, vcfg, authorized=True,
                            time_limit_minutes=minutes, deadline=Deadline(clock.deadline_epoch))
        provenance = dict(stage='team_value', train=train.manifest, validation=validation.manifest,
                          synthetic=bool(train.manifest.get('synthetic')))
    save_checkpoint(Path(a.run_dir) / 'value.pt', actor=model, clock=clock,
                    status='trained_unvalidated', provenance=provenance)
    engine.write_json(Path(a.run_dir) / 'value_report.json', rep)
    return 0


def _league_from_cfg(cfg: dict):
    from .train.league import default_league
    lg = default_league()
    lc = cfg.get('league', {})
    if lc.get('opponents'):
        keep = set(lc['opponents'])
        lg.opponents = [o for o in lg.opponents if o.name in keep]
    for p in lc.get('draft_proxies', []):
        lg.add(Path(p).stem, 'draft_proxy', p, 0.5)
    if 'min_reference_share' in lc:
        lg.min_reference_share = float(lc['min_reference_share'])
    return lg


def _export_for_training(model, run_dir: Path, iteration: int, profile: str = 'training') -> Path:
    """Export the current actor through B's exporter and build the `training` profile bot from it."""
    try:
        exp = importlib.import_module('nfs.export')
    except ImportError as exc:
        raise SystemExit(f'nfs.export (Agent B) unavailable: {exc}')
    import re
    run_name = re.sub('[^a-z0-9_]', '_', run_dir.name.lower())
    if not run_name or not run_name[0].isalpha():
        run_name = 'run_' + run_name
    name = f'{run_name}_it{iteration:05d}'
    out = run_dir / 'exports' / name                    # never models/: in-training weights are not registered
    exp.export_model(model, name, out, status='trained',
                     provenance=dict(stage='rl_in_training', run=str(run_dir), iteration=iteration, validated=False))
    from .train import collect as co
    return Path(co.build_profile_bot(profile, run_dir / 'builds' / name, model=str(out))['wasm'])


def cmd_rl(a) -> int:
    minutes = _require(a, 'rl')
    import torch
    from .data import records_dataset as rd
    from .train import collect as co
    from .train import ppo
    from .train.checkpoint import GamesLedger, RunClock, resume, save_checkpoint
    from .train.common import Deadline
    from .train.league import League, default_league
    from .train.rewards import RewardConfig
    from .train.value import Critic
    cfg = _cfg(a.config)
    run_dir = Path(a.run_dir)
    clock = RunClock.authorize(run_dir, minutes, a.run_id or run_dir.name)   # persisted; never extended on resume
    model = _build_model(a.model_config)
    obs_dim = int(cfg.get('obs_dim') or getattr(model, 'obs_dim'))
    critic = Critic(obs_dim, int(cfg.get('critic_hidden', 64)))
    pcfg = _dc(ppo.PPOConfig, cfg.get('ppo'))
    dev = torch.device('cuda' if torch.cuda.is_available() and pcfg.device != 'cpu' else 'cpu')
    model.to(dev); critic.to(dev)
    aopt = torch.optim.Adam(model.parameters(), lr=pcfg.lr)
    copt = torch.optim.Adam(critic.parameters(), lr=pcfg.critic_lr)
    rcfg = RewardConfig.from_dict(cfg.get('reward', {}))
    ccfg = _dc(co.CollectConfig, cfg.get('collect'))
    maps = co.resolve_maps(_training_maps(cfg.get('maps', 'eval_partition:training')))
    counters = dict(iteration=0, games=0, decisions=0)
    league = _league_from_cfg(cfg)
    ledger = GamesLedger(run_dir)
    if (run_dir / 'latest.pt').exists() or a.actor_from:
        st = resume(run_dir, actor=model, critic=critic, actor_opt=aopt, critic_opt=copt, actor_from=a.actor_from,
                    obs_schema_hash=model.cfg['obs']['obs_schema_hash'], action_schema_hash=rd.action_schema_hash(),
                    reset_critic_optimizer=a.reset_critic_optimizer)
        counters.update(st['counters'])
        ledger = st['ledger']
        if st['league']:
            league = League.from_state(st['league'])
    league.verify()
    deadline = Deadline(clock.deadline_epoch)
    max_games = int(cfg.get('max_games', 0)) or None
    while not clock.expired(margin=120) and (max_games is None or len(ledger) < max_games):
        it = counters['iteration'] + 1
        wasm = _export_for_training(model, run_dir, it, cfg.get('profile', 'training'))
        remaining_games = max_games - len(ledger) if max_games is not None else ccfg.games_per_iteration
        ccfg.max_games = max_games if max_games is not None else len(ledger) + ccfg.games_per_iteration
        jobs = co.plan_jobs(wasm, league, maps, ccfg.sides, min(ccfg.games_per_iteration, remaining_games), run_dir / 'games', it)
        before = set(ledger.games)
        rep = co.run_collection(jobs, ccfg, ledger, clock)
        if rep['faults']:
            engine.write_json(run_dir / 'stopped.json', dict(reason='bot faults in rollout', collection=rep))
            raise RuntimeError('stopping before parameter updates: bot fault in rollout')
        fresh = [r for r in rep['results'] if GamesLedger.key(r['folder']) not in before]
        if not fresh:
            break
        srcs = [rd.MatchSource.from_folder(r['folder'], r['side']) for r in fresh]
        shard = rd.concat([rd.convert_match(s, reward_cfg=rcfg, match_index=k) for k, s in enumerate(srcs)])
        _, rollout_stats = ppo.ratio_mask_np(shard, pcfg)
        limits = cfg.get('rollout_stop', dict(invalid_action_rate=0.0, fallback_rate=0.2, missing_obs_rate=0.2))
        violations = [name for name, limit in limits.items() if rollout_stats.get(name, 0) > limit]
        if violations or not rollout_stats['ratio_rows']:
            engine.write_json(run_dir / 'stopped.json', dict(reason='rollout quality before update',
                              violations=violations, stats=rollout_stats))
            raise RuntimeError(f'stopping before parameter updates: rollout quality {violations}')
        metrics = ppo.ppo_update(model, critic, aopt, copt, shard, pcfg, authorized=True,
                                 time_limit_minutes=minutes, deadline=deadline)
        counters.update(iteration=it, games=len(ledger), decisions=counters['decisions'] + len(shard))
        save_checkpoint(run_dir / 'latest.pt', actor=model, critic=critic, actor_opt=aopt, critic_opt=copt,
                        league_state=league.state_dict(), ledger=ledger, clock=clock, counters=counters,
                        obs_schema_hash=model.cfg['obs']['obs_schema_hash'],
                        action_schema_hash=rd.action_schema_hash(),
                        provenance=dict(stage='rl', config=cfg, reward=rcfg.to_dict(), synthetic=False))
        engine.write_json(run_dir / 'updates' / f'it{it:05d}.json', dict(metrics=metrics, collection={k: v for k, v in rep.items() if k != 'results'}))
        if it % int(cfg.get('freeze_every', 10)) == 0:
            league.add(f'self-it{it:05d}', 'frozen_self', wasm, 0.5, 'frozen own checkpoint')
    return 0


# --------------------------------------------------------------------------------------------- export / eval
def cmd_export(a) -> int:
    from .train.checkpoint import load_checkpoint
    d = load_checkpoint(a.checkpoint)
    prov = d['meta'].get('provenance', {})
    if prov.get('exportable_to_runtime') is False:
        print('refusing: observational draft-outcome checkpoint has no runtime-compatible head adapter')
        return 2
    if prov.get('synthetic') or d['meta'].get('status') in ('in_training',) and not a.allow_in_training:
        print('refusing: checkpoint is synthetic or mid-training; export requires a selected, non-synthetic checkpoint')
        return 2
    try:
        exp = importlib.import_module('nfs.export')
    except ImportError as exc:
        print(f'refusing: nfs.export (Agent B) unavailable: {exc}')
        return 2
    model = _build_model(a.model_config)
    model.load_state_dict(d['actor'])
    name = a.name or Path(a.out).name
    man = exp.export_model(model, name, Path(a.out), status='trained',
                           provenance=dict(checkpoint=str(a.checkpoint), checkpoint_meta=d['meta'], validated=False))
    print(f'exported {name} (status trained, NOT validated) to {a.out}; checksum {man.get("checksum")}. '
          'Promotion requires `promote` (H gate) and tools/install_models.py.')
    return 0


def cmd_benchmark(a) -> int:
    tool = ROOT / 'tools' / 'eval_run.py'
    if not tool.exists():
        print('refusing: tools/eval_run.py (Agent H) not available')
        return 2
    return subprocess.call([sys.executable, str(tool), *a.rest], cwd=ROOT)


def cmd_promote(a) -> int:
    try:
        gate = importlib.import_module('nfs.evaluate.gate')
    except ImportError as exc:
        print(f'refusing: evaluation gate (python/nfs/evaluate/gate.py) unavailable: {exc}')
        return 2
    if not hasattr(gate, 'evaluate_files'):
        print('refusing: nfs.evaluate.gate has no evaluate_files')
        return 2
    res = gate.evaluate_files(a.candidate_results, a.baseline_results, a.incumbent_results, mode=a.mode)
    out = res.as_dict() if hasattr(res, 'as_dict') else dict(passed=bool(getattr(res, 'passed', False)))
    receipt = dict(model=a.model_name, gate=out, promoted=bool(out.get('passed')))
    engine.write_json(MANIFESTS / 'promotions' / f'{a.model_name}-{uuid.uuid4().hex[:8]}.json', receipt)
    if not out.get('passed'):
        print('gate FAILED; model not promoted:', out.get('reasons'))
        return 1
    print('gate passed. Set status "validated" in models/<name>/manifest.json via B\'s registry and run '
          'tools/install_models.py --profile release (single install switch).')
    return 0


# --------------------------------------------------------------------------------------------- parser
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='tools/nfs.py', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)

    def train_flags(s):
        s.add_argument('--i-authorize-training', action='store_true', help='explicit authorization (required)')
        s.add_argument('--time-limit-minutes', type=float, help='wall-clock limit (required); persisted, never extended')
        s.add_argument('--run-dir', required=True)
        s.add_argument('--run-id')
        s.add_argument('--config')
        s.add_argument('--model-config', help='configs/model/<name>.json (Agent B)')

    s = sub.add_parser('inspect-data'); s.add_argument('--dataset'); s.set_defaults(fn=cmd_inspect_data)
    s = sub.add_parser('index-archives')
    s.add_argument('--sample-per-part', type=int, default=190)
    s.add_argument('--consistency-checks', type=int, default=10)
    s.add_argument('--no-hash', action='store_true')
    s.add_argument('--workers', type=int, default=8)
    s.add_argument('--out', default=str(MANIFESTS / 'archive_index_v1.json'))
    s.set_defaults(fn=cmd_index_archives)
    s = sub.add_parser('build-splits'); s.add_argument('--rows'); s.add_argument('--out', default=str(MANIFESTS / 'splits_v1.json'))
    s.set_defaults(fn=cmd_build_splits)
    s = sub.add_parser('collect')
    s.add_argument('--i-authorize-collection', action='store_true'); s.add_argument('--max-games', type=int)
    s.add_argument('--time-limit-minutes', type=float); s.add_argument('--run-dir', required=True); s.add_argument('--run-id')
    s.add_argument('--config'); s.add_argument('--candidate'); s.add_argument('--profile'); s.add_argument('--workers', type=int)
    s.add_argument('--iteration', type=int, default=0)
    s.set_defaults(fn=cmd_collect)
    s = sub.add_parser('build-dataset'); s.add_argument('--games', required=True); s.add_argument('--out', required=True)
    s.add_argument('--name', required=True); s.add_argument('--reward-config'); s.add_argument('--splits')
    s.set_defaults(fn=cmd_build_dataset)
    s = sub.add_parser('pretrain'); train_flags(s); s.add_argument('--train'); s.add_argument('--validation')
    s.set_defaults(fn=cmd_pretrain)
    s = sub.add_parser('train-value'); train_flags(s); s.add_argument('--train'); s.add_argument('--validation')
    s.add_argument('--draft', action='store_true', help='observational draft-outcome model from archive sample rows')
    s.add_argument('--rows'); s.add_argument('--splits', default=str(MANIFESTS / 'splits_v1.json'))
    s.set_defaults(fn=cmd_train_value)
    s = sub.add_parser('rl'); train_flags(s); s.add_argument('--actor-from'); s.add_argument('--reset-critic-optimizer', action='store_true')
    s.set_defaults(fn=cmd_rl)
    s = sub.add_parser('export'); s.add_argument('--checkpoint', required=True); s.add_argument('--out', required=True)
    s.add_argument('--model-config'); s.add_argument('--name'); s.add_argument('--allow-in-training', action='store_true')
    s.set_defaults(fn=cmd_export)
    s = sub.add_parser('benchmark'); s.add_argument('rest', nargs=argparse.REMAINDER); s.set_defaults(fn=cmd_benchmark)
    s = sub.add_parser('promote'); s.add_argument('--candidate-results', required=True)
    s.add_argument('--baseline-results', required=True); s.add_argument('--incumbent-results')
    s.add_argument('--mode', default='final'); s.add_argument('--model-name', required=True); s.set_defaults(fn=cmd_promote)
    return p


def main(argv=None) -> int:
    a = parser().parse_args(argv)
    if a.cmd in PARAM_UPDATING:
        from .train.auth import TrainingNotAuthorized, require_authorization
        try:
            require_authorization(a.i_authorize_training, a.time_limit_minutes, a.cmd)
        except TrainingNotAuthorized as exc:
            print(f'refusing: {exc}')
            return 2
    return int(a.fn(a) or 0)


if __name__ == '__main__':
    sys.exit(main())
