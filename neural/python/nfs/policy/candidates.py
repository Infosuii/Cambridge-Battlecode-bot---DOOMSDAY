"""Direct-policy v2 candidate schema, canonical builder and stable-ID label lookup.

This layer has no teacher preference, residual prior, model or SDK dependency. Callers generate
legal bounded options independently. Teacher labels are optional annotations after construction.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import copy
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / 'schemas/policy_v2.json'
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
F = 12
MAX_K = 16
INTERPRETATION_VERSION = 2
HEAD_NAMES = tuple(h['name'] for h in SCHEMA['heads'])
HEAD_IDS = {h['name']: h['id'] for h in SCHEMA['heads']}
HEAD_SPECS = {h['name']: h for h in SCHEMA['heads']}
FEATURE_NAMES = {h['name']: tuple(f['name'] for f in h['features']) for h in SCHEMA['heads']}
_BY_ID = {h['id']: h for h in SCHEMA['heads']}


def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')


def fnv1a32(data: bytes) -> int:
    value = 2166136261
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xFFFFFFFF
    return value


def head_spec(head: str | int) -> dict:
    try:
        return copy.deepcopy(HEAD_SPECS[head] if isinstance(head, str) else _BY_ID[int(head)])
    except (KeyError, ValueError, TypeError):
        raise ValueError(f'unsupported direct-policy head: {head!r}') from None


def head_action_hash(head: str | int | dict) -> int:
    value = copy.deepcopy(head) if isinstance(head, dict) else head_spec(head)
    value.pop('action_hash', None)
    return fnv1a32(canonical_json(value))


def schema_hash(schema: dict | None = None) -> int:
    value = copy.deepcopy(SCHEMA if schema is None else schema)
    value.pop('action_schema_hash', None)
    for head in value['heads']:
        head.pop('action_hash', None)
    return fnv1a32(canonical_json(value))


ACTION_HASHES = {h['name']: head_action_hash(h) for h in SCHEMA['heads']}
ACTION_HASH_BY_ID = {h['id']: ACTION_HASHES[h['name']] for h in SCHEMA['heads']}
ACTION_SCHEMA_HASH = schema_hash()
if SCHEMA.get('interpretation_version') != 2 or SCHEMA.get('schema_version') != 2:
    raise ValueError('direct candidate schema must use interpretation/schema version2')
if ACTION_SCHEMA_HASH != SCHEMA.get('action_schema_hash') or any(h['action_hash'] != ACTION_HASHES[h['name']] for h in SCHEMA['heads']):
    raise ValueError('policy_v2 semantic hash mismatch; regenerate rather than reinterpret artifacts')


class Error(IntEnum):
    OK = 0
    UNSUPPORTED_HEAD = 1
    BAD_COUNT = 2
    BAD_CONTEXT = 3
    DUPLICATE_ID = 4
    BAD_MASK = 5
    NON_FINITE = 6
    EMPTY = 7
    NO_LEGAL = 8


class CandidateBuildError(ValueError):
    def __init__(self, code: Error):
        self.code = code
        super().__init__(f'direct candidate build failed: {code.name.lower()}')


@dataclass(frozen=True)
class Candidate:
    id: int
    legal: int | bool
    raw: tuple | list | np.ndarray


@dataclass
class Decision:
    head: int
    context: int
    feat: np.ndarray
    legal: np.ndarray
    id: np.ndarray
    F: int = F

    @property
    def K(self):
        return len(self.id)


def _empty(head, context):
    return Decision(head, context, np.empty((0, F), dtype=np.float32), np.empty(0, dtype=np.uint8), np.empty(0, dtype=np.uint32))


def try_build(head: str | int, candidates: list[Candidate], context: int = 0) -> tuple[Error, Decision]:
    try:
        hid = HEAD_IDS[head] if isinstance(head, str) else int(head)
    except (KeyError, ValueError, TypeError):
        return Error.UNSUPPORTED_HEAD, _empty(-1, context)
    empty = _empty(hid, context)
    if hid not in _BY_ID:
        return Error.UNSUPPORTED_HEAD, empty
    if len(candidates) > MAX_K:
        return Error.BAD_COUNT, empty
    if not isinstance(context, (int, np.integer)) or not 0 <= context <= 3:
        return Error.BAD_CONTEXT, empty
    if not candidates:
        return Error.EMPTY, empty
    # IDs are uint32 in C++. Reject Python overflow instead of wrapping and creating aliases.
    for row in candidates:
        if not isinstance(row.id, (int, np.integer)) or not 0 <= row.id <= 0xFFFFFFFF:
            raise ValueError('candidate id must be an unsigned32-bit integer')
        if row.legal not in (0, 1):
            return Error.BAD_MASK, empty
        if len(row.raw) != F:
            return Error.BAD_COUNT, empty
        with np.errstate(over='ignore', invalid='ignore'):
            raw = np.asarray(row.raw, dtype=np.float32)
        if raw.shape != (F,):
            return Error.BAD_COUNT, empty
        if not np.isfinite(raw).all():
            return Error.NON_FINITE, empty
    rows = sorted(candidates, key=lambda x: int(x.id))
    if any(a.id == b.id for a, b in zip(rows, rows[1:])):
        return Error.DUPLICATE_ID, empty
    if not any(row.legal for row in rows):
        return Error.NO_LEGAL, empty
    spec = _BY_ID[hid]
    scales = np.asarray([f['scale'] for f in spec['features']], dtype=np.float32)
    inv = np.asarray(np.float32(1) / scales, dtype=np.float32)
    low = np.asarray([f['clip'][0] for f in spec['features']], dtype=np.float32)
    high = np.asarray([f['clip'][1] for f in spec['features']], dtype=np.float32)
    raw = np.asarray([row.raw for row in rows], dtype=np.float32)
    normalized = np.asarray(raw * inv, dtype=np.float32)
    normalized = np.maximum(low, np.minimum(high, normalized)).astype(np.float32)
    return Error.OK, Decision(hid, int(context), normalized, np.asarray([row.legal for row in rows], dtype=np.uint8),
                              np.asarray([row.id for row in rows], dtype=np.uint32))


def build(head: str | int, candidates: list[Candidate], context: int = 0) -> Decision:
    error, decision = try_build(head, candidates, context)
    if error != Error.OK:
        raise CandidateBuildError(error)
    return decision


def teacher_index(decision: Decision, stable_action_id: int = -1) -> int:
    """Optional collection label. Does not reorder or alter candidate features/masks."""
    if not isinstance(stable_action_id, (int, np.integer)) or not 0 <= stable_action_id <= 0xFFFFFFFF:
        return -1
    matches = np.flatnonzero(decision.id == stable_action_id)
    return int(matches[0]) if len(matches) == 1 and decision.legal[matches[0]] else -1


def move_id(kind: int, canonical_x: int, canonical_y: int) -> int:
    if any(not isinstance(v, (int, np.integer)) for v in (kind, canonical_x, canonical_y)) or not (
        0 <= kind <= 3 and 0 <= canonical_x <= 32767 and 0 <= canonical_y <= 32767
    ):
        raise ValueError('move id requires kind0..3 and canonical coordinates0..32767')
    return (int(kind) << 30) | (int(canonical_y) << 15) | int(canonical_x)


def combat_id(kind: int, target_handle: int) -> int:
    if any(not isinstance(v, (int, np.integer)) for v in (kind, target_handle)) or not (
        0 <= kind <= 3 and 0 <= target_handle <= 0x3FFFFFFF
    ):
        raise ValueError('combat id requires kind0..3 and target handle0..0x3FFFFFFF')
    return (int(target_handle) << 2) | int(kind)
