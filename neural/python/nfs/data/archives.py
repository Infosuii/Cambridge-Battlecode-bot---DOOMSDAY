"""Historical match-summary archive indexing, integrity checks and eligibility filters.

Scope (USER_REQUEST sections 7/8, CONTRACTS section 0):
- Only daily bundles dated 2026-10-21 or later are admitted. The archives carry no per-entry wall-clock timestamp
  (ZIP member times are the 1980 epoch placeholder and the converted summary only has in-game round timestamps),
  so the date is proven at bundle level: the platform bundle filename `summaries-<date>-part<N>.zip` and, when
  available, the platform listing (`archive-links.json` of the first experiment, read-only). Both are recorded.
- Engine 1.0.1 is always excluded. Engine 1.0.3 entries may feed gameplay outcome/value labels. Engine 1.0.2 entries
  are flagged `draft_observational` and are refused by `gameplay_label_records` unless an explicit, tested
  `EngineAdapter` is supplied (none exists yet).
- Integrity: zero-byte, truncated (missing/overrunning end-of-central-directory or member data past the central
  directory), CRC errors (checked for the bounded sample only), duplicate part files, duplicate match IDs across parts.
- Bounded validation only: at most BOUNDED_SAMPLE_CAP entries per part are decompressed/converted.

Nothing here modifies the archives or the previous experiment's files.
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
import re
import struct
import subprocess
import tempfile
import zipfile
import zlib
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable

BOUNDED_SAMPLE_CAP = 200          # hard cap of decompressed/converted entries per part during the build
DATE_FLOOR = '2026-10-21'
GAMEPLAY_ENGINES = ('1.0.3',)
OBSERVATIONAL_ENGINES = ('1.0.2',)
EXCLUDED_ENGINES = ('1.0.1',)     # never admitted, even with an adapter
SCOPE_GAMEPLAY = 'gameplay_1_0_3'
SCOPE_DRAFT_OBS = 'draft_observational'

UUID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
MEMBER_RE = re.compile(rf'^(?:.*/)?(?P<kind>[a-z]+)_(?P<match>{UUID})_(?P<t1>{UUID})_vs_(?P<t2>{UUID})\.camstat$')
ANY_UUID_RE = re.compile(UUID)
ARCHIVE_RE = re.compile(r'^summaries-(?P<date>\d{4}-\d{2}-\d{2})-part(?P<part>\d+)(?: \(\d+\))?\.zip$')

# Draft identifiers = SDK `champion_draft` enum order (sdk/cpp/cambc.h), names as printed in summaries.
CHAMPION_DRAFT_IDS = {'Ryth': 0, 'Vesper Vale': 1, 'Vendetta': 2, 'Cassi & Issac': 3, 'Cassi+Issac': 3,
                      'Cassi and Issac': 3, 'Stellar': 4, 'Prism': 5, 'Marcella': 6, 'Willow': 7, 'Ren': 8,
                      'Varg': 9, 'Tavi': 10, 'Heart of Ruin': 11}


class ArchiveError(RuntimeError):
    pass


class EngineCompatibilityError(RuntimeError):
    """Raised when non-1.0.3 records would be mixed into 1.0.3 gameplay labels without an explicit adapter."""


# --------------------------------------------------------------------------------------------- names and dates
def parse_archive_name(name: str) -> dict:
    m = ARCHIVE_RE.match(Path(name).name)
    if not m:
        return dict(date=None, part=None)
    return dict(date=m['date'], part=int(m['part']))


def parse_member_name(name: str) -> dict | None:
    """`<kind>_<match uuid>_<team uuid>_vs_<team uuid>.camstat`. The two team UUIDs are platform team IDs (verified
    against `teamId` values in the first experiment's recent-match listing); their A/B order is not verified."""
    m = MEMBER_RE.match(name)
    if m:
        return dict(kind=m['kind'], match_id=m['match'], team_ids=[m['t1'], m['t2']], name_parsed=True)
    u = ANY_UUID_RE.search(name)
    if not u:
        return None
    return dict(kind='unknown', match_id=u[0], team_ids=[], name_parsed=False)


def date_ok(date: str | None, floor: str = DATE_FLOOR) -> bool:
    if not date:
        return False
    return dt.date.fromisoformat(date) >= dt.date.fromisoformat(floor)


# --------------------------------------------------------------------------------------------- integrity
def inspect_zip_file(path) -> dict:
    """Cheap structural integrity check (reads only the tail and one local header)."""
    path = Path(path)
    size = path.stat().st_size
    out = dict(path=str(path), size=size)
    if size == 0:
        return dict(out, status='zero_byte')
    with open(path, 'rb') as f:
        head = f.read(4)
        tail_len = min(size, 65557)
        f.seek(size - tail_len)
        tail = f.read(tail_len)
    pos = tail.rfind(b'PK\x05\x06')
    if pos < 0 or len(tail) - pos < 22:
        return dict(out, status='truncated' if head == b'PK\x03\x04' else 'not_zip')
    (_, _, _, _, n_total, cd_size, cd_offset, _) = struct.unpack('<4s4H2IH', tail[pos:pos + 22])
    zip64 = cd_offset == 0xFFFFFFFF or n_total == 0xFFFF
    eocd_abs = size - tail_len + pos
    if not zip64 and cd_offset + cd_size > eocd_abs:
        return dict(out, status='truncated', detail='central directory overruns end record')
    try:
        with zipfile.ZipFile(path) as z:
            infos = z.infolist()
            if infos:
                last = max(infos, key=lambda i: i.header_offset)
                with open(path, 'rb') as f:
                    f.seek(last.header_offset)
                    lh = f.read(30)
                if len(lh) < 30 or lh[:4] != b'PK\x03\x04':
                    return dict(out, status='truncated', detail='last local header missing')
                n_len, x_len = struct.unpack('<2H', lh[26:30])
                end = last.header_offset + 30 + n_len + x_len + last.compress_size
                cd_start = z.start_dir if hasattr(z, 'start_dir') else cd_offset
                if end > cd_start:
                    return dict(out, status='truncated', detail='member data overruns central directory')
    except zipfile.BadZipFile as exc:
        return dict(out, status='corrupt_central_directory', detail=str(exc)[:200])
    return dict(out, status='ok', entries=len(infos), zip64=bool(zip64))


def crc_check(z: zipfile.ZipFile, info: zipfile.ZipInfo) -> tuple[bytes | None, str | None]:
    """Decompress one member fully; zipfile verifies CRC-32 at end of stream."""
    try:
        with z.open(info) as f:
            raw = f.read()
    except zipfile.BadZipFile as exc:
        return None, 'crc_error' if 'CRC' in str(exc) else 'bad_member'
    except (zlib.error, EOFError, OSError) as exc:  # truncated/corrupt deflate stream
        return None, 'decompress_error'
    if len(raw) != info.file_size:
        return None, 'size_mismatch'
    return raw, None


def sha256_cached(path, cache_file) -> str:
    """SHA-256 of a (large) archive, cached by (resolved path, size, mtime_ns) so 800 MB files are hashed once."""
    path = Path(path).resolve()
    st = path.stat()
    key = f'{path}|{st.st_size}|{st.st_mtime_ns}'
    cache_file = Path(cache_file)
    cache = json.loads(cache_file.read_text(encoding='utf-8')) if cache_file.exists() else {}
    if key in cache:
        return cache[key]
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 22), b''):
            h.update(block)
    cache[key] = h.hexdigest()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache_file.with_suffix('.tmp')
    tmp.write_text(json.dumps(cache, indent=1), encoding='utf-8')
    tmp.replace(cache_file)
    return cache[key]


# --------------------------------------------------------------------------------------------- conversion
def cambc_summary_converter(cli, tmp_root) -> Callable[[bytes], dict]:
    """`cambc summary <camstat> -o <json>` (official CLI; no login). Returns a raw-bytes -> dict callable."""
    tmp_root = Path(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)

    def convert(raw: bytes) -> dict:
        with tempfile.TemporaryDirectory(prefix='camstat-', dir=tmp_root) as td:
            src, dst = Path(td) / 'in.camstat', Path(td) / 'out.json'
            src.write_bytes(raw)
            r = subprocess.run([str(cli), 'summary', str(src), '-o', str(dst)], capture_output=True, text=True,
                               encoding='utf-8', errors='replace', timeout=60)
            if r.returncode or not dst.exists():
                raise ArchiveError('cambc summary failed: ' + (r.stdout + r.stderr)[-300:])
            return json.loads(dst.read_text(encoding='utf-8'))
    return convert


def summary_metadata(d: dict) -> dict:
    """Flat, label-relevant metadata of one converted summary (no per-turn data exists in summaries)."""
    m = d.get('match', {})
    draft = d.get('roster', {}).get('draft', []) or []
    picks = {'teamA': [], 'teamB': []}
    unknown = []
    for row in draft:
        cid = CHAMPION_DRAFT_IDS.get(row.get('champion'))
        if cid is None:
            unknown.append(row.get('champion'))
        elif row.get('team') in picks:
            picks[row['team']].append(cid)
    scores = {t.get('team'): int(t.get('submittedGems', 0)) for t in d.get('teams', [])}
    diag = d.get('diagnostics', {})
    faults = diag.get('botFaults', {}) or {}
    engine = m.get('engineVersion')
    build = m.get('engineBuildHash') or ''
    return dict(
        engine_version=engine, engine_build_hash=build,
        metric_semantics_version=m.get('metricSemanticsVersion'), format_version=d.get('formatVersion'),
        rule_version=f'{engine}+{build[:12]}/metrics{m.get("metricSemanticsVersion")}/fmt{d.get("formatVersion")}',
        outcome=m.get('outcome'), rounds_started=m.get('roundsStarted'), rounds_completed=m.get('roundsCompleted'),
        final_round_partial=m.get('finalRoundPartial'), map_hash=m.get('mapHash'),
        width=m.get('width'), height=m.get('height'), seed=m.get('seed'),
        detailed_capture_complete=diag.get('detailedCaptureComplete'),
        bot_faults={k: int(v) for k, v in faults.items()}, diagnostic_codes=len(diag.get('codes', []) or []),
        submitted_gems=scores, picks=picks, first_pick=draft[0]['team'] if draft else None,
        unknown_champions=unknown, n_champions=len(d.get('champions', []) or []),
        has_timelines=bool(d.get('championTimelines')), has_events=bool(d.get('events')),
        has_heatmaps=bool(d.get('heatmaps')))


# --------------------------------------------------------------------------------------------- eligibility
@dataclass
class EligibilityPolicy:
    date_floor: str = DATE_FLOOR
    gameplay_engines: tuple = GAMEPLAY_ENGINES
    observational_engines: tuple = OBSERVATIONAL_ENGINES
    excluded_engines: tuple = EXCLUDED_ENGINES
    min_rounds: int = 50                       # shorter games are forfeits/resignations, not played outcomes
    allowed_outcomes: tuple = ('teamA', 'teamB')
    require_detailed_capture: bool = True
    reject_bot_faults: bool = True
    reject_zero_score: bool = True             # 0:0 decided only by engine tiebreak: no outcome information
    draft_sizes: tuple = (3, 4, 5)


def classify(meta: dict, archive_date: str | None, policy: EligibilityPolicy | None = None) -> dict:
    """Return {'accepted': bool, 'reason': str|None, 'label_scope': str|None, 'flags': [...]}. First failing
    reason wins (order documented in DATA_AUDIT.md)."""
    p = policy or EligibilityPolicy()
    flags = []
    if not archive_date:
        return dict(accepted=False, reason='date_unproven', label_scope=None, flags=flags)
    if not date_ok(archive_date, p.date_floor):
        return dict(accepted=False, reason='date_before_floor', label_scope=None, flags=flags)
    eng = meta.get('engine_version')
    if eng in p.excluded_engines:
        return dict(accepted=False, reason=f'engine_{eng}_excluded', label_scope=None, flags=flags)
    if eng in p.gameplay_engines:
        scope = SCOPE_GAMEPLAY
    elif eng in p.observational_engines:
        scope = SCOPE_DRAFT_OBS
        flags.append(SCOPE_DRAFT_OBS)
    else:
        return dict(accepted=False, reason=f'engine_{eng}_unknown', label_scope=None, flags=flags)
    if p.require_detailed_capture and meta.get('detailed_capture_complete') is not True:
        return dict(accepted=False, reason='incomplete_capture', label_scope=None, flags=flags)
    if (meta.get('rounds_started') or 0) < p.min_rounds:
        return dict(accepted=False, reason='too_few_rounds', label_scope=None, flags=flags)
    if meta.get('outcome') not in p.allowed_outcomes:
        return dict(accepted=False, reason='outcome_not_decisive', label_scope=None, flags=flags)
    if p.reject_bot_faults and any(v for v in (meta.get('bot_faults') or {}).values()):
        return dict(accepted=False, reason='bot_fault', label_scope=None, flags=flags)
    gems = meta.get('submitted_gems') or {}
    if p.reject_zero_score and sum(gems.values()) == 0:
        return dict(accepted=False, reason='zero_score_tiebreak', label_scope=None, flags=flags)
    if meta.get('unknown_champions'):
        return dict(accepted=False, reason='unknown_champion', label_scope=None, flags=flags)
    pa, pb = (meta.get('picks') or {}).get('teamA', []), (meta.get('picks') or {}).get('teamB', [])
    if len(pa) not in p.draft_sizes or len(pa) != len(pb):
        return dict(accepted=False, reason='draft_size', label_scope=None, flags=flags)
    if meta.get('final_round_partial'):
        flags.append('final_round_partial')    # normal for a gem-target win mid-round; informational
    return dict(accepted=True, reason=None, label_scope=scope, flags=flags)


@dataclass(frozen=True)
class EngineAdapter:
    """Explicit, tested compatibility adapter. None exists for 1.0.2 -> 1.0.3; this type is the only way in."""
    name: str
    source_version: str
    target_version: str
    tested: bool
    description: str
    transform: Callable[[dict], dict] | None = None

    def apply(self, record: dict) -> dict:
        out = dict(self.transform(record) if self.transform else record)
        out['engine_adapter'] = self.name
        out['label_scope'] = SCOPE_GAMEPLAY + '_adapted'
        return out


def gameplay_label_records(records: Iterable[dict], target_engine: str = '1.0.3',
                           adapter: EngineAdapter | None = None) -> list[dict]:
    """Records allowed as engine-`target_engine` gameplay labels/rewards. Refuses anything else unless an explicit
    tested adapter for exactly that source version is supplied; excluded engines are refused unconditionally."""
    out = []
    for r in records:
        eng = r.get('engine_version')
        if eng == target_engine and r.get('label_scope') == SCOPE_GAMEPLAY:
            out.append(r)
            continue
        if eng in EXCLUDED_ENGINES:
            raise EngineCompatibilityError(f'engine {eng} is excluded from all use ({r.get("match_id")})')
        if adapter is None:
            raise EngineCompatibilityError(
                f'record {r.get("match_id")} has engine {eng} / scope {r.get("label_scope")}; refusing to mix it '
                f'into {target_engine} gameplay labels without an explicit adapter')
        if not adapter.tested or adapter.source_version != eng or adapter.target_version != target_engine:
            raise EngineCompatibilityError(f'adapter {adapter.name} does not cover {eng}->{target_engine} or untested')
        out.append(adapter.apply(r))
    return out


def draft_observational_records(records: Iterable[dict]) -> list[dict]:
    """Accepted records usable for observational draft analysis (1.0.2 and 1.0.3). Labels are confounded."""
    return [dict(r, confounded=True) for r in records if r.get('label_scope') in (SCOPE_GAMEPLAY, SCOPE_DRAFT_OBS)]


# --------------------------------------------------------------------------------------------- experiment 1
def load_experiment1_ids(cache_dir) -> dict[str, dict]:
    """Read-only: match IDs sampled by the first experiment (historical-training/part-*.jsonl)."""
    out: dict[str, dict] = {}
    cache_dir = Path(cache_dir)
    if not cache_dir.exists():
        return out
    for p in sorted(cache_dir.glob('part-*.jsonl')):
        m = re.match(r'part-(\d+)(-v2)?\.jsonl$', p.name)
        if not m:
            continue
        with open(p, encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                mid = r.get('match_id')
                if not mid:
                    continue
                e = out.setdefault(mid, dict(part=int(m[1]), files=[], accepted_v2=None, engine_version=None))
                e['files'].append(p.name)
                if m[2]:
                    e['accepted_v2'] = 'rejected' not in r
                    e['engine_version'] = r.get('engine_version') or e['engine_version']
                    if 'rejected' in r:
                        e['rejected_v2'] = r['rejected']
    return out


def load_platform_listing(path) -> dict[str, str]:
    """Read-only platform listing (archive name -> date) recorded by the first experiment."""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        rows = json.loads(path.read_text(encoding='utf-8'))
    except ValueError:
        return {}
    return {r['name']: r['date'] for r in rows if isinstance(r, dict) and 'name' in r and 'date' in r}


# --------------------------------------------------------------------------------------------- index
@dataclass
class ArchiveSource:
    path: str
    part: int | None
    date: str | None
    size: int
    status: str
    detail: str = ''
    selected: bool = False
    skip_reason: str | None = None
    sha256: str | None = None
    entries: int = 0
    listing_date: str | None = None


def discover(paths: Iterable) -> list[ArchiveSource]:
    """Inspect candidate archive files and choose one valid file per part number (deterministic)."""
    srcs = []
    for p in paths:
        p = Path(p)
        if not p.is_file():
            continue
        info = parse_archive_name(p.name)
        chk = inspect_zip_file(p)
        srcs.append(ArchiveSource(path=str(p), part=info['part'], date=info['date'], size=chk['size'],
                                  status=chk['status'], detail=chk.get('detail', ''), entries=chk.get('entries', 0)))
    by_part = defaultdict(list)
    for s in srcs:
        by_part[(s.date, s.part)].append(s)
    for key, group in by_part.items():
        if key[1] is None:
            for s in group:
                s.skip_reason = 'unrecognised_archive_name'
            continue
        ok = sorted((s for s in group if s.status == 'ok'), key=lambda s: (-s.entries, s.path))
        for s in group:
            if s.status != 'ok':
                s.skip_reason = s.status + ('_duplicate_part' if len(group) > 1 else '')
        if ok:
            ok[0].selected = True
            for s in ok[1:]:
                s.skip_reason = 'duplicate_part_skipped'
    return sorted(srcs, key=lambda s: (s.date or '', s.part or 0, s.path))


def sample_order_key(match_id: str) -> bytes:
    return hashlib.sha256(match_id.encode()).digest()


def build_index(paths: Iterable, *, sample_per_part: int, converter: Callable[[bytes], dict] | None,
                policy: EligibilityPolicy | None = None, experiment1_ids: dict | None = None,
                consistency_checks_per_part: int = 0, hash_cache: str | Path | None = None,
                platform_listing: dict | None = None, workers: int = 8, sample_out_dir: str | Path | None = None,
                local_map_hashes: dict | None = None) -> dict:
    """Index archives: central directories in full; CRC + conversion + eligibility for a bounded sample per part.

    The sample per part is the first `sample_per_part` member IDs in SHA-256(match_id) order that the first
    experiment did NOT sample (fresh), plus `consistency_checks_per_part` IDs it did sample (re-checked against
    its cache). Total converted per part is capped at BOUNDED_SAMPLE_CAP.
    """
    policy = policy or EligibilityPolicy()
    exp1 = experiment1_ids or {}
    listing = platform_listing or {}
    if sample_per_part + consistency_checks_per_part > BOUNDED_SAMPLE_CAP:
        raise ArchiveError(f'bounded sample cap is {BOUNDED_SAMPLE_CAP} entries per part')
    sources = discover(paths)
    seen: dict[str, dict] = {}
    duplicates = []
    parts = []
    sample_rows = []
    for s in sources:
        s.listing_date = listing.get(Path(s.path).name)
        if not s.selected:
            parts.append(dict(asdict(s)))
            continue
        if hash_cache is not None:
            s.sha256 = sha256_cached(s.path, hash_cache)
        part_rep = dict(asdict(s))
        if not date_ok(s.date, policy.date_floor):
            part_rep.update(admitted=False, reject_reason='date_before_floor' if s.date else 'date_unproven')
            parts.append(part_rep)
            continue
        if s.listing_date and s.listing_date != s.date:
            part_rep.update(admitted=False, reject_reason='date_listing_mismatch')
            parts.append(part_rep)
            continue
        part_rep['admitted'] = True
        kinds, unparsed, local_dups = Counter(), 0, 0
        members = []
        with zipfile.ZipFile(s.path) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                parsed = parse_member_name(info.filename)
                if parsed is None:
                    unparsed += 1
                    continue
                mid = parsed['match_id']
                kinds[parsed['kind']] += 1
                if mid in seen:
                    first = seen[mid]
                    same_part = first['part'] == s.part
                    local_dups += same_part
                    duplicates.append(dict(match_id=mid, first_part=first['part'], dup_part=s.part,
                                           same_crc=first['crc'] == info.CRC, same_size=first['size'] == info.file_size))
                    continue
                seen[mid] = dict(part=s.part, crc=info.CRC, size=info.file_size, member=info.filename,
                                 team_ids=parsed['team_ids'], kind=parsed['kind'])
                members.append((info, parsed))
            exp1_in_part = [m for m in members if m[1]['match_id'] in exp1]
            fresh = sorted((m for m in members if m[1]['match_id'] not in exp1),
                           key=lambda m: sample_order_key(m[1]['match_id']))
            checks = sorted(exp1_in_part, key=lambda m: sample_order_key(m[1]['match_id']))
            chosen = [(m, 'fresh') for m in fresh[:sample_per_part]] + \
                     [(m, 'experiment1_consistency') for m in checks[:consistency_checks_per_part]]
            raws = []
            for (info, parsed), role in chosen:
                raw, err = crc_check(z, info)
                raws.append((info, parsed, role, raw, err))

        def work(item):
            info, parsed, role, raw, err = item
            row = dict(match_id=parsed['match_id'], member=info.filename, part=s.part, archive=Path(s.path).name,
                       archive_date=s.date, kind=parsed['kind'], team_ids=parsed['team_ids'], sample_role=role,
                       used_by_experiment1=parsed['match_id'] in exp1, crc32=f'{info.CRC:08x}',
                       compressed_bytes=info.compress_size, bytes=info.file_size)
            if err:
                return dict(row, accepted=False, reason=err, label_scope=None)
            if converter is None:
                return dict(row, accepted=None, reason='not_converted', label_scope=None)
            try:
                d = converter(raw)
            except Exception as exc:  # noqa: BLE001 - recorded as a rejection reason
                return dict(row, accepted=False, reason='conversion_error', label_scope=None, detail=str(exc)[:200])
            meta = summary_metadata(d)
            verdict = classify(meta, s.date, policy)
            row.update(meta)
            row.update(verdict)
            if local_map_hashes is not None:
                row['local_map'] = local_map_hashes.get(meta.get('map_hash'))
            if role == 'experiment1_consistency':
                e = exp1[parsed['match_id']]
                row['experiment1_engine_version'] = e.get('engine_version')
                row['experiment1_accepted_v2'] = e.get('accepted_v2')
            return row

        with cf.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
            rows = list(ex.map(work, raws))
        rows.sort(key=lambda r: sample_order_key(r['match_id']))
        sample_rows.extend(rows)
        fresh_rows = [r for r in rows if r['sample_role'] == 'fresh']
        part_rep.update(
            archive_entries=s.entries, unique_new_match_ids=len(members), unparsed_member_names=unparsed,
            duplicate_ids_within_part=local_dups, kinds=dict(kinds),
            experiment1_ids_in_part=len(exp1_in_part), sampled_entries=len(rows),
            sampled_fresh=len(fresh_rows), sampled_consistency=len(rows) - len(fresh_rows),
            accepted_fresh=sum(1 for r in fresh_rows if r.get('accepted')),
            rejected_fresh_by_reason=dict(Counter(r['reason'] for r in fresh_rows if r.get('accepted') is False)),
            accepted_fresh_by_scope=dict(Counter(r['label_scope'] for r in fresh_rows if r.get('accepted'))),
            engine_versions_fresh=dict(Counter(r.get('engine_version') for r in fresh_rows)))
        parts.append(part_rep)
    if sample_out_dir is not None:
        out = Path(sample_out_dir)
        out.mkdir(parents=True, exist_ok=True)
        tmp = out / 'sample_rows.jsonl.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            for r in sample_rows:
                f.write(json.dumps(r, sort_keys=True) + '\n')
        tmp.replace(out / 'sample_rows.jsonl')
    return _index_manifest(sources, parts, sample_rows, duplicates, seen, exp1, policy)


def _index_manifest(sources, parts, rows, duplicates, seen, exp1, policy) -> dict:
    fresh = [r for r in rows if r['sample_role'] == 'fresh']
    accepted = [r for r in fresh if r.get('accepted')]
    consistency = [r for r in rows if r['sample_role'] == 'experiment1_consistency']
    cons_engine_agree = sum(1 for r in consistency
                            if r.get('engine_version') and r.get('experiment1_engine_version') in (None, r['engine_version']))
    admitted = [p for p in parts if p.get('admitted')]
    exp1_overlap = sum(1 for mid in seen if mid in exp1)
    build_hashes = defaultdict(set)
    for r in rows:
        if r.get('engine_version'):
            build_hashes[r['engine_version']].add(r.get('engine_build_hash'))
    return dict(
        schema='nfs.archive_index.v1',
        created_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        policy=asdict(policy),
        bounded_sample_cap_per_part=BOUNDED_SAMPLE_CAP,
        date_evidence=dict(
            per_entry_wall_clock='absent: ZIP member times are the 1980 placeholder; summaries contain only in-game '
                                 'round/substep timestamps',
            method='bundle-level: platform bundle filename summaries-<date>-partN.zip, cross-checked with the '
                   'platform listing date when available; archives dated before the floor are rejected whole',
            parts={Path(p['path']).name: dict(name_date=p.get('date'), listing_date=p.get('listing_date'))
                   for p in parts if p.get('selected')}),
        sources=[dict(path=p['path'], part=p['part'], date=p['date'], size=p['size'], status=p['status'],
                      detail=p.get('detail', ''), selected=p['selected'], skip_reason=p.get('skip_reason'),
                      sha256=p.get('sha256')) for p in parts],
        parts=[p for p in parts if p.get('selected')],
        accounting=dict(
            archive_entries=sum(p.get('archive_entries', 0) for p in admitted),
            unique_match_ids=len(seen),
            duplicate_entries_dropped=len(duplicates),
            sampled_entries=len(rows),
            sampled_fresh_entries=len(fresh),
            sampled_experiment1_consistency_entries=len(consistency),
            accepted_independent_matches=len({r['match_id'] for r in accepted}),
            accepted_gameplay_1_0_3=sum(1 for r in accepted if r['label_scope'] == SCOPE_GAMEPLAY),
            accepted_draft_observational_1_0_2=sum(1 for r in accepted if r['label_scope'] == SCOPE_DRAFT_OBS),
            rejected_by_reason=dict(Counter(r['reason'] for r in fresh if r.get('accepted') is False)),
            engine_versions_in_sample=dict(Counter(r.get('engine_version') for r in fresh)),
            engine_build_hashes={k: sorted(v) for k, v in build_hashes.items()},
            per_turn_observations=0,
            augmented_samples=0,
            epochs=0,
            note='Only the bounded sample was decompressed/converted. archive_entries are not compatible games; '
                 'acceptance rates apply to the sample only. Summaries contain no per-turn observations.'),
        experiment1=dict(
            ids_known=len(exp1), ids_found_in_archives=exp1_overlap,
            accepted_by_experiment1=sum(1 for e in exp1.values() if e.get('accepted_v2')),
            engine_versions_of_experiment1_accepted=dict(Counter(e.get('engine_version') for e in exp1.values()
                                                                 if e.get('accepted_v2'))),
            label='already_used_by_experiment_1',
            consistency_checked=len(consistency), consistency_engine_agree=cons_engine_agree,
            rule='IDs sampled by experiment 1 are labelled already_used_by_experiment_1; they are excluded from the '
                 'fresh sample and may only enter train partitions, never final_eval.'),
        duplicates=duplicates[:200],
    )
