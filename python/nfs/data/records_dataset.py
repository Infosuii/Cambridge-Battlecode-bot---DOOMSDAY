"""NFS1 training records + match summary -> schema-versioned training shards.

Model inputs and training targets are kept in separate, declared groups and checked by structure:
  inputs  : encoded observation, observation validity, candidate features, legality mask, teacher priors, K, F,
            head id, call-site context code (everything the C++ runtime has when it decides)
  targets : teacher label, chosen action, behaviour log-probability, SMDP interval reward/gap, discounted return,
            outcome, margin, per-component rewards (everything that depends on the action taken or the future)
  meta    : identities and behaviour bookkeeping (match, side, champion, round, reason, mode, sampled, stream id)
`Shard.__post_init__` rejects undeclared fields, input names containing outcome/future tokens and targets in inputs.

Observations come from the team's own stdout (turn-context records written by the bot itself), so they are by
construction the acting team's legal observation; nothing from the replay's full state or the other team's stream is
used as an input. The summary is used only for targets (rewards/outcome).

Decoding: the B-owned decoder `nfs.records` is used when importable; otherwise the reference decoder below
implements CONTRACTS section 3.5 (packed little-endian). Observation encoding uses C-owned `nfs.obs` when importable
(see agents/G/CONTRACT_ISSUES.md for the function names probed) or an injected encoder.
"""
from __future__ import annotations

import base64
import dataclasses
import hashlib
import importlib
import json
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

import numpy as np

from ..train import rewards as R

ROOT = Path(__file__).resolve().parents[3]
MAGIC = 0x3153464E
KIND_TURN, KIND_DECISION, KIND_EPISODE = 0, 1, 2
HEADER = struct.Struct('<IHHIiI')            # magic, version, kind, schema_hash, round, champion_handle (20 bytes)
DECISION = struct.Struct('<HHHhhBBBBf')      # head, K, F, teacher, chosen, mode, reason, context, sampled, logp
K_MAX, F_MAX = 16, 24
SCHEMA = 'nfs.records_dataset.v1'

INPUT_FIELDS = frozenset({'obs', 'obs_valid', 'feat', 'legal', 'prior', 'K', 'F', 'head', 'context'})
TARGET_FIELDS = frozenset({'teacher', 'chosen', 'logp_behaviour', 'reward', 'tau', 'return_mc', 'done', 'outcome',
                           'margin'} | {'r_' + c for c in R.COMPONENTS})
META_FIELDS = frozenset({'match_index', 'side', 'champion', 'round', 'seq', 'reason', 'mode', 'sampled', 'stream',
                         'schema_hash', 'cand_id', 'champion_mapped', 'net', 'logit_behaviour', 'action_hash', 'call'})
FORBIDDEN_INPUT_TOKENS = ('outcome', 'win', 'margin', 'return', 'reward', 'advantage', 'future', 'final', 'logp',
                          'chosen', 'teacher', 'tau', 'done', 'value')


class DatasetError(RuntimeError):
    pass


# --------------------------------------------------------------------------------------------- decoding
def reference_decode_payload(raw: bytes) -> dict:
    if len(raw) < HEADER.size:
        raise DatasetError('record shorter than header')
    magic, version, kind, schema_hash, rnd, champ = HEADER.unpack_from(raw, 0)
    if magic != MAGIC:
        raise DatasetError(f'bad magic {magic:#x}')
    rec = dict(version=version, kind=kind, schema_hash=schema_hash, round=rnd, champion=champ)
    off = HEADER.size
    if kind == KIND_DECISION:
        if len(raw) < off + DECISION.size:
            raise DatasetError('truncated decision header')
        head, K, F, teacher, chosen, mode, reason, context, sampled, logp = DECISION.unpack_from(raw, off)
        off += DECISION.size
        if not (0 <= K <= K_MAX and 0 <= F <= F_MAX):
            raise DatasetError(f'decision K={K} F={F} out of bounds')
        need = off + 4 * K + K + 4 * K + 4 * K * F
        if len(raw) < need:
            raise DatasetError('truncated decision record')
        prior = np.frombuffer(raw, '<f4', K, off).copy(); off += 4 * K
        legal = np.frombuffer(raw, 'u1', K, off).copy(); off += K
        ids = np.frombuffer(raw, '<u4', K, off).copy(); off += 4 * K
        feat = np.frombuffer(raw, '<f4', K * F, off).copy().reshape(K, F); off += 4 * K * F
        rec.update(head=head, K=K, F=F, teacher=teacher, chosen=chosen, mode=mode, reason=reason, context=context,
                   sampled=sampled, logp=float(logp), prior=prior, legal=legal, id=ids, feat=feat)
        if len(raw) >= off + 8 + 4 * K:            # v1 trailer (agents/B nn_log.h): action hash, call, net, logits
            action_hash, call, net = struct.unpack_from('<IHh', raw, off); off += 8
            rec.update(action_hash=action_hash, call=call, net=net,
                       logit=np.frombuffer(raw, '<f4', K, off).copy())
    elif kind == KIND_TURN:
        # B's layout: u32 byte count, then the raw nnobs::RawTurn bytes
        if len(raw) < off + 4:
            raise DatasetError('truncated turn-context record')
        (n,) = struct.unpack_from('<I', raw, off)
        if len(raw) < off + 4 + n:
            raise DatasetError('truncated turn-context payload')
        rec['payload'] = bytes(raw[off + 4:off + 4 + n])
    else:
        rec['payload'] = bytes(raw[off:])
    return rec


def reference_decode_stdout(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith('NFS1 '):
            continue
        try:
            out.append(reference_decode_payload(base64.b64decode(line[5:], validate=True)))
        except (ValueError, DatasetError, struct.error):
            out.append(dict(kind=-1, error='undecodable'))
    return out


def _normalise(rec) -> dict:
    if isinstance(rec, dict):
        d = dict(rec)
    elif dataclasses.is_dataclass(rec):
        d = dataclasses.asdict(rec)
    elif hasattr(rec, '_asdict'):
        d = dict(rec._asdict())
    else:
        d = dict(vars(rec))
    alias = {'champion_handle': 'champion', 'logp_behaviour': 'logp', 'ids': 'id', 'features': 'feat',
             'teacher_index': 'teacher', 'raw': 'payload'}
    for a, b in alias.items():
        if a in d and b not in d:
            d[b] = d.pop(a)
    if isinstance(d.get('kind'), str):
        d['kind'] = {'turn': 0, 'turn_context': 0, 'decision': 1, 'episode': 2, 'episode_marker': 2}.get(d['kind'], -1)
    return d


def decoder() -> tuple[Callable[[str], list[dict]], str]:
    """B's decoder when importable, else the CONTRACTS 3.5 reference decoder."""
    try:
        mod = importlib.import_module('nfs.records')
    except ImportError:
        return reference_decode_stdout, 'reference(CONTRACTS 3.5)'
    for name in ('decode_stdout', 'parse_stdout', 'decode_text', 'iter_records', 'decode_lines'):
        fn = getattr(mod, name, None)
        if callable(fn):
            return (lambda text, fn=fn: [_normalise(r) for r in fn(text)]), f'nfs.records.{name}'
    return reference_decode_stdout, 'reference(CONTRACTS 3.5; nfs.records has no known entry point)'


def obs_encoder() -> tuple[Callable[[bytes], np.ndarray] | None, int | None, str]:
    """C's observation encoder (raw RawTurn bytes -> float32[kObsDim]) when importable."""
    try:
        mod = importlib.import_module('nfs.obs')
    except ImportError:
        return None, None, 'unavailable'
    dim = None
    for n in ('OBS_DIM', 'kObsDim', 'K_OBS_DIM'):
        if hasattr(mod, n):
            dim = int(getattr(mod, n))
    for name in ('encode_bytes', 'encode_raw_bytes', 'encode_record'):
        fn = getattr(mod, name, None)
        if callable(fn):
            return (lambda b, fn=fn: np.asarray(fn(b), np.float32)), dim, f'nfs.obs.{name}'
    raw_t = getattr(mod, 'RawTurn', None)
    if raw_t is not None and hasattr(raw_t, 'from_bytes') and callable(getattr(mod, 'encode', None)):
        return (lambda b: np.asarray(mod.encode(raw_t.from_bytes(b)), np.float32)), dim, 'nfs.obs.encode(RawTurn.from_bytes)'
    return None, dim, 'nfs.obs has no known byte encoder'


def head_names() -> dict[int, str]:
    d = json.loads((ROOT / 'schemas/heads.json').read_text(encoding='utf-8'))
    return {h['id']: h['name'] for h in d['heads']}


def action_schema_hash() -> str:
    # Include feature meaning/normalisation, not just the frozen head inventory and dimensions.
    paths = [ROOT / 'schemas/heads.json', *sorted((ROOT / 'schemas/heads').glob('*.json'))]
    canonical = {p.relative_to(ROOT).as_posix(): json.loads(p.read_text(encoding='utf-8')) for p in paths}
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


# --------------------------------------------------------------------------------------------- shard structure
@dataclass
class Shard:
    inputs: dict
    targets: dict
    meta: dict
    manifest: dict = field(default_factory=dict)

    def __post_init__(self):
        for group, allowed, name in ((self.inputs, INPUT_FIELDS, 'inputs'), (self.targets, TARGET_FIELDS, 'targets'),
                                     (self.meta, META_FIELDS, 'meta')):
            extra = set(group) - allowed
            if extra:
                raise DatasetError(f'undeclared {name} fields: {sorted(extra)}')
        for k in self.inputs:
            if any(tok in k.lower() for tok in FORBIDDEN_INPUT_TOKENS):
                raise DatasetError(f'input field {k} looks like a target/future field')
        if set(self.inputs) & (TARGET_FIELDS | META_FIELDS):
            raise DatasetError('target/meta field placed in inputs')
        n = {len(v) for g in (self.inputs, self.targets, self.meta) for v in g.values()}
        if len(n) > 1:
            raise DatasetError(f'inconsistent row counts {sorted(n)}')

    def __len__(self):
        return len(next(iter(self.inputs.values()))) if self.inputs else 0

    def save(self, path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        arrays = {f'{g}/{k}': v for g, d in (('inputs', self.inputs), ('targets', self.targets), ('meta', self.meta))
                  for k, v in d.items()}
        tmp = path.with_name(path.name + '.tmp.npz')
        np.savez_compressed(tmp, **arrays)
        tmp.replace(path)
        man = dict(self.manifest, file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), rows=len(self))
        mpath = path.with_suffix('.manifest.json')
        mtmp = mpath.with_suffix('.tmp')
        mtmp.write_text(json.dumps(man, indent=2, default=str) + '\n', encoding='utf-8')
        mtmp.replace(mpath)
        return path

    @classmethod
    def load(cls, path) -> 'Shard':
        path = Path(path)
        z = np.load(path, allow_pickle=False)
        groups = {'inputs': {}, 'targets': {}, 'meta': {}}
        for k in z.files:
            g, name = k.split('/', 1)
            groups[g][name] = z[k]
        mpath = path.with_suffix('.manifest.json')
        man = json.loads(mpath.read_text(encoding='utf-8')) if mpath.exists() else {}
        return cls(groups['inputs'], groups['targets'], groups['meta'], man)


def concat(shards: list[Shard]) -> Shard:
    if not shards:
        raise DatasetError('no shards')
    cat = lambda g: {k: np.concatenate([getattr(s, g)[k] for s in shards]) for k in getattr(shards[0], g)}
    return Shard(cat('inputs'), cat('targets'), cat('meta'), dict(parts=[s.manifest for s in shards]))


# --------------------------------------------------------------------------------------------- conversion
@dataclass
class MatchSource:
    """One completed engine match: summary dict, the team's stdout text and identity of the acting side."""
    match_id: str
    side: str                         # 'A' or 'B'
    summary: dict
    stdout: str
    folder: str = ''
    provenance: dict = field(default_factory=dict)

    @classmethod
    def from_folder(cls, folder, side: str) -> 'MatchSource':
        from .. import engine
        folder = Path(folder)
        raw = (folder / 'summary.json').read_bytes()
        prov = {}
        job = folder / 'job.json'
        if job.exists():
            prov = json.loads(job.read_text(encoding='utf-8'))
        bundle = engine.replay_bundle(folder)
        prov.update(summary_sha256=hashlib.sha256(raw).hexdigest(),
                    replay_sha256=engine.sha256(bundle) if bundle else None)
        return cls(match_id='local:' + hashlib.sha256(raw).hexdigest()[:20], side=side,
                   summary=json.loads(raw), stdout=engine.team_stdout(folder, side), folder=str(folder),
                   provenance=prov)


def _resolve_champions(handles: list[int], summary: dict, team: str) -> tuple[dict, str]:
    ids = sorted(int(c['id']) for c in summary.get('roster', {}).get('champions', []) if c.get('team') == team)
    if handles and all(h in ids for h in handles):
        return {h: h for h in handles}, 'identity'
    if handles and len(set(handles)) == len(ids):
        return dict(zip(sorted(set(handles)), ids)), 'order_assumed'
    return {}, 'team_level'


def _team_series(summary: dict, team: str) -> R.AgentSeries:
    ids = [int(c['id']) for c in summary.get('roster', {}).get('champions', []) if c.get('team') == team]
    parts = [R.series_from_summary(summary, team, i) for i in ids]
    s0 = parts[0]
    agg = lambda f: sum(getattr(p, f) for p in parts)
    return R.AgentSeries(submitted=agg('submitted'), carried=agg('carried'), gold=agg('gold'), deaths=agg('deaths'),
                         damage=agg('damage'), objective=agg('objective'), team_submitted=s0.team_submitted,
                         outcome=s0.outcome, final_team_gems=s0.final_team_gems,
                         final_opponent_gems=s0.final_opponent_gems)


def convert_match(src: MatchSource, *, reward_cfg: R.RewardConfig | None = None,
                  encode: Callable[[bytes], np.ndarray] | None = None, obs_dim: int | None = None,
                  decode: Callable[[str], list[dict]] | None = None, expected_obs_schema: int | None = None,
                  expected_action_hashes: dict | None = None,
                  engine_version: str = '1.0.3', synthetic: bool = False, match_index: int = 0) -> Shard:
    cfg = (reward_cfg or R.RewardConfig()).validate()
    eng = src.summary.get('match', {}).get('engineVersion')
    if eng != engine_version:
        raise DatasetError(f'summary engine {eng} != {engine_version}: refusing gameplay labels')
    if decode is None:
        decode, dec_name = decoder()
    else:
        dec_name = 'injected'
    if encode is None:
        encode, dim, enc_name = obs_encoder()
        obs_dim = obs_dim or dim
    else:
        enc_name = 'injected'
    team = 'team' + src.side.upper()
    recs = decode(src.stdout)
    bad = sum(1 for r in recs if r.get('kind') == -1)
    if not synthetic:
        from ..obs import OBS_SCHEMA_HASH
        from ..registry import current_head_hashes
        expected_obs_schema = OBS_SCHEMA_HASH if expected_obs_schema is None else expected_obs_schema
        if expected_action_hashes is None:
            expected_action_hashes = current_head_hashes()
        if bad:
            raise DatasetError(f'{bad} undecodable NFS1 records: refusing partially corrupt gameplay data')
    contexts = {}
    decisions = []
    schema_hashes = Counter()
    for i, r in enumerate(recs):
        if r.get('kind') == KIND_TURN:
            contexts[(int(r['champion']), int(r['round']))] = r.get('payload', b'')
            schema_hashes[int(r['schema_hash'])] += 1
        elif r.get('kind') == KIND_DECISION:
            if expected_obs_schema is not None and int(r['schema_hash']) != expected_obs_schema:
                raise DatasetError('decision observation schema hash mismatch')
            if expected_action_hashes is not None:
                name = head_names().get(int(r['head']))
                want = expected_action_hashes.get(name)
                if want is None or int(r.get('action_hash', -1)) != int(want):
                    raise DatasetError(f'{name}: action schema hash mismatch or absent')
            decisions.append((i, r))
    if expected_obs_schema is not None:
        wrong = [h for h in schema_hashes if h != expected_obs_schema]
        if wrong:
            raise DatasetError(f'turn-context schema hash {wrong} != expected {expected_obs_schema}')
    rounds = int(src.summary['match']['roundsStarted'])
    handles = sorted({int(r['champion']) for _, r in decisions})
    cmap, cmethod = _resolve_champions(handles, src.summary, team)
    series = {}
    for h in handles:
        series[h] = R.series_from_summary(src.summary, team, cmap[h], rounds) if h in cmap else _team_series(src.summary, team)
    comps = {h: R.per_round_components(s, cfg) for h, s in series.items()}
    # streams: (champion, head); SMDP intervals between that stream's consecutive decisions
    streams = defaultdict(list)
    for seq, (i, r) in enumerate(decisions):
        streams[(int(r['champion']), int(r['head']))].append((seq, r))
    N = len(decisions)
    D = obs_dim or 0
    if D == 0:
        for p in contexts.values():
            if encode is not None:
                D = len(encode(p)); break
    inp = dict(obs=np.zeros((N, D), np.float32), obs_valid=np.zeros(N, np.uint8),
               feat=np.zeros((N, K_MAX, F_MAX), np.float32), legal=np.zeros((N, K_MAX), bool),
               prior=np.zeros((N, K_MAX), np.float32), K=np.zeros(N, np.int16), F=np.zeros(N, np.int16),
               head=np.zeros(N, np.int16), context=np.zeros(N, np.uint8))
    tg = {k: np.zeros(N, np.float32) for k in TARGET_FIELDS}
    tg['teacher'] = np.zeros(N, np.int16); tg['chosen'] = np.zeros(N, np.int16); tg['done'] = np.zeros(N, np.uint8)
    mt = dict(match_index=np.full(N, match_index, np.int32), side=np.full(N, ord(src.side.upper()), np.uint8),
              champion=np.zeros(N, np.uint32), round=np.zeros(N, np.int32), seq=np.zeros(N, np.int32),
              reason=np.zeros(N, np.uint8), mode=np.zeros(N, np.uint8), sampled=np.zeros(N, np.uint8),
              stream=np.zeros(N, np.int32), schema_hash=np.zeros(N, np.uint32),
              cand_id=np.zeros((N, K_MAX), np.uint32), champion_mapped=np.zeros(N, np.uint8),
              net=np.full(N, -1, np.int16), logit_behaviour=np.zeros((N, K_MAX), np.float32),
              action_hash=np.zeros(N, np.uint32), call=np.zeros(N, np.uint16))
    missing_obs = 0
    for sid, (key, items) in enumerate(sorted(streams.items())):
        h = key[0]
        bounds = [max(0, min(int(r['round']), rounds - 1)) for _, r in items]
        ints = R.interval_rewards(comps[h], bounds, cfg.gamma)
        ret = 0.0
        rets = [0.0] * len(items)
        for j in reversed(range(len(items))):
            ret = ints[j]['reward'] + (cfg.gamma ** ints[j]['tau']) * (0.0 if ints[j]['terminal'] else ret)
            rets[j] = ret
        s = series[h]
        for j, (seq, r) in enumerate(items):
            K, F = int(r['K']), int(r['F'])
            inp['K'][seq], inp['F'][seq], inp['head'][seq], inp['context'][seq] = K, F, int(r['head']), int(r['context'])
            inp['feat'][seq, :K, :F] = np.asarray(r['feat'], np.float32).reshape(K, F)
            inp['legal'][seq, :K] = np.asarray(r['legal'][:K]).astype(bool)
            inp['prior'][seq, :K] = np.asarray(r['prior'][:K], np.float32)
            payload = contexts.get((h, int(r['round'])))
            if payload is not None and encode is not None:
                x = encode(payload)
                inp['obs'][seq, :len(x)] = x
                inp['obs_valid'][seq] = 1
            else:
                missing_obs += 1
            tg['teacher'][seq] = int(r.get('teacher', 0))
            tg['chosen'][seq] = int(r['chosen'])
            tg['logp_behaviour'][seq] = float(r['logp'])
            tg['reward'][seq] = ints[j]['reward']
            tg['tau'][seq] = ints[j]['tau']
            tg['done'][seq] = int(ints[j]['terminal'])
            tg['return_mc'][seq] = rets[j]
            tg['outcome'][seq] = {'win': 1.0, 'loss': 0.0}.get(s.outcome, 0.5)
            # Fixed model-output unit, independent of an experiment's reward shaping scale.
            tg['margin'][seq] = (s.final_team_gems - s.final_opponent_gems) / 1000.0
            for c in R.COMPONENTS:
                tg['r_' + c][seq] = ints[j]['components'][c]
            mt['champion'][seq], mt['round'][seq], mt['seq'][seq] = h, int(r['round']), seq
            mt['reason'][seq], mt['mode'][seq], mt['sampled'][seq] = int(r['reason']), int(r['mode']), int(r['sampled'])
            mt['stream'][seq] = match_index * 4096 + sid
            mt['schema_hash'][seq] = int(r['schema_hash'])
            mt['cand_id'][seq, :K] = np.asarray(r['id'][:K], np.uint32)
            mt['champion_mapped'][seq] = int(h in cmap)
            if r.get('logit') is not None:
                lg = np.asarray(r['logit'][:K], np.float32)
                mt['logit_behaviour'][seq, :K] = np.where(np.isfinite(lg), lg, 0.0)
                mt['net'][seq] = int(r.get('net', -1))
                mt['action_hash'][seq] = int(r.get('action_hash', 0))
                mt['call'][seq] = int(r.get('call', 0))
    names = head_names()
    manifest = dict(
        schema=SCHEMA, synthetic=bool(synthetic), match_id=src.match_id, side=src.side, folder=src.folder,
        engine_version=eng, provenance=src.provenance, decoder=dec_name, obs_encoder=enc_name, obs_dim=D,
        obs_schema_hashes={str(k): v for k, v in schema_hashes.items()},
        decision_schema_hashes=dict(Counter(str(int(r['schema_hash'])) for _, r in decisions)),
        action_schema_hash=action_schema_hash(), reward=cfg.to_dict(), champion_mapping=cmethod,
        counts=dict(records=len(recs), undecodable=bad, turn_contexts=len(contexts), decisions=N,
                    decisions_missing_obs=missing_obs, streams=len(streams),
                    per_head={names.get(int(k), str(k)): v for k, v in Counter(int(r['head']) for _, r in decisions).items()},
                    sampled=int(mt['sampled'].sum()), fallback_reason_nonzero=int((mt['reason'] != 0).sum())),
        separation=dict(inputs=sorted(inp), targets=sorted(tg), meta=sorted(mt)))
    return Shard(inp, tg, mt, manifest)


def build_dataset(sources: Iterable[MatchSource], out_dir, *, name: str, reward_cfg: R.RewardConfig | None = None,
                  partition_of: Callable[[MatchSource], str] | None = None, **kw) -> dict:
    """Convert matches into one shard per partition plus a dataset manifest."""
    out_dir = Path(out_dir)
    per_part = defaultdict(list)
    sources_rep = []
    seen = set()
    for idx, src in enumerate(sources):
        key = (src.match_id, src.side)
        if key in seen:
            sources_rep.append(dict(match_id=src.match_id, side=src.side, skipped='duplicate_match_side'))
            continue
        seen.add(key)
        part = partition_of(src) if partition_of else 'train'
        sh = convert_match(src, reward_cfg=reward_cfg, match_index=idx, **kw)
        per_part[part].append(sh)
        sources_rep.append(dict(match_id=src.match_id, side=src.side, partition=part, folder=src.folder,
                                rows=len(sh), provenance=src.provenance))
    files = {}
    for part, shards in sorted(per_part.items()):
        merged = concat(shards)
        merged.manifest = dict(schema=SCHEMA, dataset=name, partition=part, synthetic=kw.get('synthetic', False),
                               matches=[s.manifest['match_id'] for s in shards],
                               obs_schema_hashes=sorted({h for s in shards for h in s.manifest['obs_schema_hashes']}),
                               action_schema_hash=action_schema_hash())
        p = merged.save(out_dir / f'{name}-{part}.npz')
        files[part] = dict(file=p.name, rows=len(merged), matches=len(shards))
    man = dict(schema=SCHEMA, dataset=name, synthetic=kw.get('synthetic', False), files=files, sources=sources_rep,
               accounting=dict(independent_matches=len({s['match_id'] for s in sources_rep if 'skipped' not in s}),
                               match_sides=len(seen), per_turn_observations=sum(f['rows'] for f in files.values()),
                               augmented_samples=0, epochs=0))
    tmp = out_dir / f'{name}.manifest.json.tmp'
    tmp.write_text(json.dumps(man, indent=2, default=str) + '\n', encoding='utf-8')
    tmp.replace(out_dir / f'{name}.manifest.json')
    return man
