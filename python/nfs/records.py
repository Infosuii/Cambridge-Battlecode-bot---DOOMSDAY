"""Decoder for NFS1 training records (agent B; format: agents/B/RECORD_FORMAT.md, writer: bot/src/nn_log.h).

    from nfs.records import parse_text
    recs = parse_text(engine.team_stdout(folder, 'A'))     # list of dicts; kind 'turn' | 'decision' | 'episode'

Lines that are not NFS1 records are ignored (other bot output); NUL padding is stripped. Malformed records raise
RecordError unless ``strict=False`` (then they are counted in the returned stats).
"""
from __future__ import annotations

import base64
import binascii
import struct

import numpy as np

MAGIC = 0x3153464E
VERSION = 1
KINDS = {0: 'turn', 1: 'decision', 2: 'episode'}
EVENTS = {0: 'start', 1: 'heartbeat'}
HEADS = ['draft_pick', 'strategy', 'objective', 'role', 'bank', 'shop', 'move', 'combat', 'engage', 'ward', 'belief',
         'value', 'ts_leaf']
MODES = {0: 'off', 1: 'shadow', 2: 'active'}
REASONS = ['ok', 'shadow', 'off', 'budget', 'no_model', 'bad_model', 'model_pending', 'nan', 'empty',
           'teacher_illegal', 'encoder_skipped', 'schema_mismatch', 'bad_input', 'bad_prior', 'capture_failed']
HEADER = struct.Struct('<IHHIiI')  # magic, version, kind, schema_hash, round, champion  (20 bytes)
DEC = struct.Struct('<HHHhhBBBBf')  # head, K, F, teacher, chosen, mode, reason, context, sampled, logp (18 bytes)


class RecordError(ValueError):
    pass


def decode_payload(p: bytes) -> dict:
    if len(p) < HEADER.size:
        raise RecordError('short record')
    magic, version, kind, schema, rnd, champ = HEADER.unpack_from(p, 0)
    if magic != MAGIC:
        raise RecordError(f'bad magic 0x{magic:08x}')
    if version != VERSION:
        raise RecordError(f'unsupported version {version}')
    if kind not in KINDS:
        raise RecordError(f'unknown kind {kind}')
    rec = dict(kind=KINDS[kind], schema_hash=schema, round=rnd, champion=champ)
    o = HEADER.size
    if kind == 0:
        (n,) = struct.unpack_from('<I', p, o)
        o += 4
        if len(p) != o + n:
            raise RecordError(f'turn record length {len(p)} != {o + n}')
        rec['raw'] = p[o:o + n]
    elif kind == 2:
        if len(p) != o + 28:
            raise RecordError('episode record length')
        ev, flags, seed, ck, written, dropped, phash = struct.unpack_from('<HHIQIII', p, o)
        rec.update(event=EVENTS.get(ev, ev), flags=flags, training=bool(flags & 1), fuel_credit=bool(flags & 2),
                   seed=seed, model_checksum=ck, written=written, dropped=dropped, profile_hash=phash)
    else:
        head, K, F, teacher, chosen, mode, reason, context, sampled, logp = DEC.unpack_from(p, o)
        o += DEC.size
        need = o + K * 4 + K + K * 4 + K * F * 4 + 8 + K * 4
        if len(p) != need:
            raise RecordError(f'decision length {len(p)} != {need} (K={K}, F={F})')
        prior = np.frombuffer(p, '<f4', K, o); o += 4 * K
        legal = np.frombuffer(p, 'u1', K, o).astype(bool); o += K
        ids = np.frombuffer(p, '<u4', K, o); o += 4 * K
        feat = np.frombuffer(p, '<f4', K * F, o).reshape(K, F); o += 4 * K * F
        ahash, call, net = struct.unpack_from('<IHh', p, o); o += 8
        logit = np.frombuffer(p, '<f4', K, o)
        rec.update(head=head, head_name=HEADS[head] if head < len(HEADS) else str(head), K=K, F=F, teacher=teacher,
                   chosen=chosen, mode=MODES.get(mode, mode), reason=REASONS[reason] if reason < len(REASONS) else reason,
                   context=context, sampled=bool(sampled), logp=float(logp), prior=prior.copy(), legal=legal,
                   id=ids.copy(), feat=feat.copy(), action_hash=ahash, call=call, net=net, logit=logit.copy())
        if not (0 <= chosen < K) or not legal[chosen]:
            raise RecordError(f'chosen {chosen} not a legal candidate')
    return rec


def decode_line(line: str) -> dict | None:
    line = line.replace('\0', '').strip()
    if not line.startswith('NFS1 '):
        return None
    try:
        payload = base64.b64decode(line[5:], validate=True)
    except (binascii.Error, ValueError) as e:
        raise RecordError(f'bad base64: {e}') from e
    return decode_payload(payload)


def parse_text(text: str, strict: bool = True, stats: dict | None = None) -> list[dict]:
    out = []
    st = stats if stats is not None else {}
    st.setdefault('lines', 0)
    st.setdefault('bad', 0)
    for line in text.replace('\0', '').splitlines():
        if not line.startswith('NFS1 '):
            continue
        st['lines'] += 1
        try:
            r = decode_line(line)
        except RecordError:
            st['bad'] += 1
            if strict:
                raise
            continue
        out.append(r)
    return out


def encode_payload(rec: dict) -> bytes:
    """Python writer (tests, tooling): inverse of decode_payload."""
    kind = {v: k for k, v in KINDS.items()}[rec['kind']]
    b = HEADER.pack(MAGIC, VERSION, kind, rec['schema_hash'], rec['round'], rec['champion'])
    if kind == 0:
        return b + struct.pack('<I', len(rec['raw'])) + bytes(rec['raw'])
    if kind == 2:
        ev = {v: k for k, v in EVENTS.items()}.get(rec['event'], rec['event'])
        return b + struct.pack('<HHIQIII', ev, rec['flags'], rec['seed'], rec['model_checksum'], rec['written'],
                               rec['dropped'], rec['profile_hash'])
    K, F = rec['K'], rec['F']
    mode = {v: k for k, v in MODES.items()}.get(rec['mode'], rec['mode'])
    reason = REASONS.index(rec['reason']) if isinstance(rec['reason'], str) else rec['reason']
    b += DEC.pack(rec['head'], K, F, 0, rec['chosen'], mode, reason, rec['context'], int(rec['sampled']), rec['logp'])
    b += np.asarray(rec['prior'], '<f4').tobytes() + np.asarray(rec['legal'], 'u1').tobytes()
    b += np.asarray(rec['id'], '<u4').tobytes() + np.asarray(rec['feat'], '<f4').reshape(K * F).tobytes()
    b += struct.pack('<IHh', rec['action_hash'], rec['call'], rec['net']) + np.asarray(rec['logit'], '<f4').tobytes()
    return b


def encode_line(rec: dict) -> str:
    return 'NFS1 ' + base64.b64encode(encode_payload(rec)).decode('ascii')
