"""Official-engine helpers shared by every tool in this workspace.

Only the official CLI is used: `cambc build --release` (the platform's CMake path, GLOB_RECURSE src/*.cpp, -O3)
and `cambc run --release` at default fuel. Nothing here changes fuel, rounds or rules.
"""
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import os
import shutil
import subprocess
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATHS = json.loads((ROOT / 'config/paths.json').read_text(encoding='utf-8'))
CLI = Path(PATHS['cli'])
MAPS = Path(PATHS['maps'])
if not MAPS.is_dir():  # another machine: the 40 official maps are vendored in the repository
    MAPS = ROOT / 'maps' / 'local-benchmarks'


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree_sha256(src: Path, pattern: str = '*') -> str:
    """Order-independent digest of a flat or nested source tree (relative names + contents)."""
    src = Path(src)
    h = hashlib.sha256()
    for p in sorted(x for x in src.rglob(pattern) if x.is_file() and '.cambc' not in x.parts):
        h.update(p.relative_to(src).as_posix().encode() + b'\0' + p.read_bytes() + b'\0')
    return h.hexdigest()


def write_json(path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str) + '\n', encoding='utf-8')
    tmp.replace(path)


def _run(args, timeout=600, cwd=ROOT) -> str:
    r = subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=timeout)
    out = (r.stdout or '') + (r.stderr or '')
    if r.returncode:
        raise RuntimeError(f'command failed ({r.returncode}): {args[:3]}\n{out[-4000:]}')
    return out


def cli_version() -> str:
    return _run([CLI, '--version'], timeout=30).strip()


def official_build(bot_dir, out_wasm, release: bool = True, timeout: int = 900) -> Path:
    """Build `bot_dir` (containing src/) with the official CLI from this workspace (cambc.toml, cmake/, sdk/)."""
    bot_dir = Path(bot_dir).resolve()
    out_wasm = Path(out_wasm).resolve()
    out_wasm.parent.mkdir(parents=True, exist_ok=True)
    args = [CLI, 'build', bot_dir, '--output', out_wasm]
    if release:
        args.insert(3, '--release')
    log = _run(args, timeout=timeout)
    if not out_wasm.exists():
        raise RuntimeError('official build produced no wasm\n' + log[-3000:])
    out_wasm.with_suffix('.build.log').write_text(log, encoding='utf-8')
    return out_wasm


def make_bot_dir(src_dir, dest_bot_dir, overrides: dict[str, str] | None = None) -> Path:
    """Copy a flat source tree into dest/src (fresh), then overwrite files given in `overrides` (name -> text)."""
    dest = Path(dest_bot_dir)
    if (dest / 'src').exists():
        shutil.rmtree(dest / 'src')
    shutil.copytree(src_dir, dest / 'src', ignore=shutil.ignore_patterns('.cambc'))
    for name, text in (overrides or {}).items():
        (dest / 'src' / name).write_text(text, encoding='utf-8', newline='\n')
    return dest


def wasm_sections(path) -> list[tuple[int, str]]:
    """(section id, sha256) of every non-custom section: a rebuild check that ignores name/debug custom sections."""
    raw = Path(path).read_bytes()
    if raw[:8] != b'\0asm\x01\0\0\0':
        raise ValueError('not a wasm module: ' + str(path))
    off, out = 8, []
    while off < len(raw):
        kind = raw[off]; off += 1
        size = shift = 0
        while True:
            b = raw[off]; off += 1
            size |= (b & 127) << shift
            if not b & 128:
                break
            shift += 7
        if kind:
            out.append((kind, hashlib.sha256(raw[off:off + size]).hexdigest()))
        off += size
    return out


def code_section_sha(path) -> str:
    return dict(wasm_sections(path)).get(10, '')


@dataclass
class MatchResult:
    folder: str
    map: str
    side: str
    win: float
    gems: int
    opponent_gems: int
    faults: int
    fuel_exhausted: int
    opponent_fuel_exhausted: int
    deaths: int
    collected: int
    gold: int
    rounds: int
    outcome: str
    engine: str

    def row(self) -> dict:
        return dict(self.__dict__)


def maps(pattern: str = '*.map26a') -> list[Path]:
    return sorted(MAPS.glob(pattern))


def run_match(a, b, map_path, folder, candidate_side: str = 'A', log_limit: int = 1048576,
              timeout: int = 300) -> MatchResult:
    """One official match at default fuel. Cached by folder: a completed match is never re-run or re-counted."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    stats = folder / 'summary.json'
    identity = dict(wasm_a=sha256(a), wasm_b=sha256(b), map=sha256(map_path),
                    release=True, fuel='official default', log_limit=int(log_limit))
    receipt = folder / 'engine_identity.json'
    if receipt.exists():
        if json.loads(receipt.read_text(encoding='utf-8')) != identity:
            raise ValueError(f'{folder}: cached match identity differs; use a new folder')
    elif stats.exists():
        raise ValueError(f'{folder}: legacy summary has no engine identity; use a new folder')
    else:
        write_json(receipt, identity)
    if not stats.exists():
        log = _run([CLI, 'run', a, b, '--map', map_path, '--out-dir', folder, '--statistics', stats,
                    '--json', '--release', '--log-limit', str(log_limit)], timeout=timeout)
        (folder / 'runner.log').write_text(log, encoding='utf-8')
    return parse_summary(json.loads(stats.read_text(encoding='utf-8')), folder, Path(map_path).stem, candidate_side)


def parse_summary(d: dict, folder, map_name: str, side: str) -> MatchResult:
    me, them = 'team' + side, 'team' + ('B' if side == 'A' else 'A')
    scores = {t['team']: int(t['submittedGems']) for t in d['teams']}

    def fuel(team):
        return sum(len(e['entries']) for e in d['events'] if e['kind'] == 'fuelExhausted' and e['owner']['team'] == team)

    cs = [c for c in d['champions'] if c['team'] == me]
    outcome = d['match']['outcome']
    return MatchResult(folder=str(folder), map=map_name, side=side,
                       win=1.0 if outcome == me else 0.0 if outcome == them else 0.5,
                       gems=scores[me], opponent_gems=scores[them], faults=int(d['diagnostics']['botFaults'][me]),
                       fuel_exhausted=fuel(me), opponent_fuel_exhausted=fuel(them),
                       deaths=sum(int(c['metrics']['deaths']) for c in cs),
                       collected=sum(int(c['metrics']['collectedGems']) for c in cs),
                       gold=sum(int(c['metrics']['earnedGold']) for c in cs),
                       rounds=int(d['match']['roundsStarted']), outcome=outcome, engine=d['match']['engineVersion'])


def replay_bundle(folder) -> Path | None:
    files = sorted(Path(folder).glob('*.repl26a'))
    return files[0] if files else None


def read_bundle_member(folder, member: str) -> bytes:
    bundle = replay_bundle(folder)
    if bundle is None:
        return b''
    with zipfile.ZipFile(bundle) as z:
        return z.read(member) if member in z.namelist() else b''


def team_stdout(folder, side: str) -> str:
    """A team's stdout from the replay bundle. The engine pads per-turn output with NUL bytes; they are removed."""
    return read_bundle_member(folder, f'team-{side.lower()}.stdout').replace(b'\0', b'').decode('utf-8', 'replace')


def run_jobs(jobs: list[dict], workers: int) -> list[MatchResult]:
    out = []
    with cf.ThreadPoolExecutor(max_workers=max(1, min(4, workers))) as ex:
        futs = {ex.submit(run_match, **j): j for j in jobs}
        for f in cf.as_completed(futs):
            try:
                out.append(f.result())
            except Exception:
                time.sleep(0.5)
                out.append(run_match(**futs[f]))  # one retry of an incomplete (uncached) job
    return out


def default_workers() -> int:
    return max(1, min(4, (os.cpu_count() or 4) - 2))
