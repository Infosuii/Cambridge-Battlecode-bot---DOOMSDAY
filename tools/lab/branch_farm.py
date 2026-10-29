"""Plan-branch farm: baseline games of a plan-hook bot plus copies that switch team plan at a given round.

Usage: python branch_farm.py --pack DIR [--workers N]      run (resumable; safe to stop and restart)
       python branch_farm.py --pack DIR --zip               write DIR/results_<name>.zip from DIR/results

Bots ship prebuilt in DIR/workspace/wasm (missing ones are built with the CLI). Stdlib only, so it runs on an embeddable Python with no installs (the 5060 package, docs/HANDOVER_5060.txt). Layout:
  DIR/tools/cambc.exe         official CLI (downloads its compiler on the first build)
  DIR/workspace/              cambc.toml, sdk/, cmake/, bots/<name>/src, maps/*.map26a
  DIR/farm/farm.json          {"name", "bot", "opponents", "seeds", "rounds", "plans", "log_limit"}
  DIR/results/rows.jsonl      one row per game (written here; nothing else is kept)

The bot must read PLAN_ROUND / PLAN_ID from src/common.h (bots/v76p). For each seed, opponent, map and side it plays the
baseline (PLAN_ROUND 5000, never reached) and every (round, plan) branch; a branch is identical to the baseline before its round, so only
its result row is kept. NOVA_SEED is set to the seed for every bot, as tools/lab/screen120.py does. Branches whose round
is at or after the baseline's last round are recorded as skipped without playing. Jobs run seed by seed, baselines
first, then rounds in the configured order, shuffled across maps, so a partial run is still a balanced sample.
"""
import argparse
import ctypes
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Baseline switch round: never reached (games end by round 2000) but positive, so the baseline compiles to the same
# code section as the branches (PLAN_ROUND -1 does not, and code size changes fuel use and so the game).
NEVER = 5000  # with PLAN_ID 6 (no such plan): a non-zero initialiser keeps the memory layout too


def code_sha(path):
    """sha256 of the wasm code section (id 10): equal across machines when the build is reproducible."""
    raw = Path(path).read_bytes()
    off = 8
    while off < len(raw):
        kind = raw[off]
        off += 1
        size = shift = 0
        while True:
            b = raw[off]
            off += 1
            size |= (b & 127) << shift
            if not b & 128:
                break
            shift += 7
        if kind == 10:
            return hashlib.sha256(raw[off:off + size]).hexdigest()
        off += size
    return ''


def free_ram_gb():
    class MS(ctypes.Structure):
        _fields_ = [('len', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in (
            'total', 'avail', 'tpage', 'apage', 'tvirt', 'avirt', 'aext')]
    try:
        m = MS()
        m.len = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.avail / 2 ** 30
    except Exception:
        return 8.0


def keep_awake():
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    except Exception:
        pass


class Farm:
    def __init__(self, pack, workers):
        self.pack = Path(pack).resolve()
        self.ws = self.pack / 'workspace'
        self.cli = str(self.pack / 'tools' / 'cambc.exe')
        self.cfg = json.loads((self.pack / 'farm' / 'farm.json').read_text(encoding='utf-8'))
        self.res = self.pack / 'results'
        self.res.mkdir(exist_ok=True)
        self.tmp = self.ws / 'tmp'
        self.tmp.mkdir(exist_ok=True)
        self.workers = workers
        self.lock = threading.Lock()
        self.rows_path = self.res / 'rows.jsonl'
        self.done, self.base_rounds = {}, {}
        if self.rows_path.exists():
            for line in self.rows_path.read_text(encoding='utf-8').splitlines():
                try:
                    r = json.loads(line)
                except ValueError:
                    continue  # a line cut by a crash
                self.note(r)
        self.maps = sorted(p for p in (self.ws / 'maps').glob('*.map26a'))

    def note(self, r):
        self.done[r['key']] = r
        if r['round'] < 0 and 'rounds' in r:
            self.base_rounds[(r['seed'], r['opp'], r['map'], r['side'])] = r['rounds']

    def log(self, msg):
        print(time.strftime('%H:%M:%S'), msg, flush=True)

    # builds -------------------------------------------------------------------------------------------------------
    def variant(self, bot, defs):
        name = bot + ''.join(f'_{k[0] if k != "PLAN_ID" else "I"}{v}' for k, v in defs)
        return name.replace('-', 'm')

    def build(self, bot, defs):
        name = self.variant(bot, defs)
        wasm = self.ws / 'wasm' / f'{name}.wasm'
        if wasm.exists():
            return wasm
        work = self.ws / 'build' / name
        shutil.rmtree(work, ignore_errors=True)
        shutil.copytree(self.ws / 'bots' / bot / 'src', work / 'src')
        common = work / 'src' / 'common.h'
        text = common.read_bytes().decode('utf-8')
        head = ''
        for k, v in defs:
            pat = re.compile(rf'^#define {re.escape(k)}\b.*$', re.M)
            if pat.search(text):
                text = pat.sub(lambda _m: f'#define {k} {v}', text, count=1)
            else:
                head += f'#define {k} {v}\n'
        common.write_bytes((head + text).encode('utf-8'))
        wasm.parent.mkdir(exist_ok=True)
        part = wasm.with_suffix('.part')
        r = subprocess.run([self.cli, 'build', str(work), '--release', '--output', str(part)], cwd=self.ws,
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode or not part.exists():
            raise RuntimeError(f'build {name} failed:\n{((r.stdout or "") + (r.stderr or ""))[-3000:]}')
        part.replace(wasm)
        shutil.rmtree(work, ignore_errors=True)
        return wasm

    def build_all(self):
        c = self.cfg
        todo = []
        for s in c['seeds']:
            seed = [('NOVA_SEED', s)]
            for o in c['opponents']:
                todo.append((o, seed))
            todo.append((c['bot'], [('PLAN_ROUND', NEVER), ('PLAN_ID', 6)] + seed))
            for rd in c['rounds']:
                for p in c['plans']:
                    todo.append((c['bot'], [('PLAN_ROUND', rd), ('PLAN_ID', p)] + seed))
        missing = [t for t in todo if not (self.ws / 'wasm' / f'{self.variant(*t)}.wasm').exists()]
        if missing:
            self.log(f'building {len(missing)} bots (the first build downloads the compiler, about 600 MB, once)')
            self.build(*missing[0])
            with ThreadPoolExecutor(max(1, min(self.workers, 8))) as ex:
                for i, _ in enumerate(ex.map(lambda t: self.build(*t), missing[1:]), 2):
                    if i % 10 == 0 or i == len(missing):
                        self.log(f'built {i} / {len(missing)}')
        builds = {self.variant(*t): code_sha(self.ws / 'wasm' / f'{self.variant(*t)}.wasm') for t in todo}
        (self.res / 'builds.json').write_text(json.dumps(builds, indent=1), encoding='utf-8')

    # games --------------------------------------------------------------------------------------------------------
    def jobs(self):
        c, out = self.cfg, []
        rng = random.Random(0)
        for s in c['seeds']:
            groups = [(s, o, m.stem, side) for o in c['opponents'] for m in self.maps for side in 'AB']
            tier = [g + (-1, 0) for g in groups]
            rng.shuffle(tier)
            out += tier
            for rd in c['rounds']:
                tier = [g + (rd, p) for g in groups for p in c['plans']]
                rng.shuffle(tier)
                out += tier
        return out

    def play(self, job):
        s, o, m, side, rd, p = job
        key = f'{s}|{o}|{m}|{side}|{rd}|{p}'
        if key in self.done:
            return False
        row = dict(key=key, seed=s, opp=o, map=m, side=side, round=rd, plan=p)
        last = self.base_rounds.get((s, o, m, side))
        if rd >= 0 and last is not None and rd >= last:
            row['skipped'] = 'game over before round'
            self.add(row)
            return False
        c = self.cfg
        seed = [('NOVA_SEED', s)]
        me = self.ws / 'wasm' / f'{self.variant(c["bot"], [("PLAN_ROUND", rd if rd >= 0 else NEVER), ("PLAN_ID", p if rd >= 0 else 6)] + seed)}.wasm'
        them = self.ws / 'wasm' / f'{self.variant(o, seed)}.wasm'
        a, b = (me, them) if side == 'A' else (them, me)
        folder = self.tmp / hashlib.sha1(key.encode()).hexdigest()[:16]
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)
        stats = folder / 'summary.json'
        for attempt in (1, 2):
            r = subprocess.run([self.cli, 'run', str(a), str(b), '--map', str(self.ws / 'maps' / f'{m}.map26a'),
                                '--out-dir', str(folder), '--statistics', str(stats), '--json', '--release',
                                '--log-limit', str(c.get('log_limit', 1048576))], cwd=self.ws, capture_output=True,
                               text=True, encoding='utf-8', errors='replace', timeout=900)
            if not r.returncode and stats.exists():
                break
            if attempt == 2:
                with self.lock, open(self.res / 'errors.jsonl', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(dict(key=key, out=((r.stdout or '') + (r.stderr or ''))[-2000:])) + '\n')
                shutil.rmtree(folder, ignore_errors=True)
                return False
        d = json.loads(stats.read_text(encoding='utf-8'))
        shutil.rmtree(folder, ignore_errors=True)
        us, op = 'team' + side, 'team' + ('B' if side == 'A' else 'A')
        gems = {t['team']: int(t['submittedGems']) for t in d['teams']}
        fuel = {t: sum(len(e['entries']) for e in d['events'] if e['kind'] == 'fuelExhausted'
                       and e['owner']['team'] == t) for t in (us, op)}
        outcome = d['match']['outcome']
        row.update(win=1.0 if outcome == us else 0.0 if outcome == op else 0.5, gems=gems[us], opp_gems=gems[op],
                   rounds=int(d['match']['roundsStarted']), faults=int(d['diagnostics']['botFaults'][us]),
                   fuel=fuel[us], opp_fuel=fuel[op])
        self.add(row)
        return True

    def add(self, row):
        with self.lock:
            with open(self.rows_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(row, separators=(',', ':')) + '\n')
            self.note(row)

    def run(self):
        keep_awake()
        self.log(f'{os.cpu_count()} threads, {free_ram_gb():.1f} GB free RAM, {self.workers} games at once')
        self.build_all()
        jobs = self.jobs()
        total = len(jobs)
        played, t0 = 0, time.time()
        self.log(f'games {sum(1 for j in jobs if self.key(j) in self.done)} / {total}')
        with ThreadPoolExecutor(self.workers) as ex:
            futs = [ex.submit(self.play, j) for j in jobs]
            for i, f in enumerate(futs):
                try:
                    played += bool(f.result())
                except Exception as e:  # noqa: BLE001 (one bad game must not stop the farm)
                    with self.lock, open(self.res / 'errors.jsonl', 'a', encoding='utf-8') as fh:
                        fh.write(json.dumps(dict(key=self.key(jobs[i]), out=repr(e)[-2000:])) + '\n')
                if played and (i % 200 == 0 or i == total - 1):
                    n = sum(1 for j in jobs if self.key(j) in self.done)
                    rate = played / (time.time() - t0)
                    left = (total - n) / max(rate, 1e-9) / 3600
                    self.log(f'games {n} / {total}   ({rate * 3600:.0f} per hour, about {left:.1f} h left)')
        n = sum(1 for j in jobs if self.key(j) in self.done)
        errs = self.res / 'errors.jsonl'
        self.log(f'games {n} / {total}')
        if n == total:
            print('\n==================  ALL DONE: run ZIP_RESULTS.bat and send results_*.zip  ==================')
        else:
            print(f'\n{total - n} games failed (see results/errors.jsonl{"" if errs.exists() else ", none logged"}); '
                  'run RUN_ME.bat again to retry them, or send the results as they are.')

    @staticmethod
    def key(j):
        return '|'.join(str(x) for x in j)

    def zip(self):
        out = self.pack / f'results_{self.cfg["name"]}.zip'
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in sorted(self.res.glob('*')):
                if p.is_file():
                    z.write(p, p.name)
        print(f'wrote {out} ({out.stat().st_size / 2 ** 20:.1f} MB). Send this one file.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pack', default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument('--workers', type=int, default=0, help='0 = all threads but 2, capped by free RAM (0.5 GB a game)')
    ap.add_argument('--zip', action='store_true')
    ap.add_argument('--build-only', action='store_true', help='prebuild the bots (done before packing)')
    a = ap.parse_args()
    workers = a.workers or max(2, min((os.cpu_count() or 4) - 2, int(free_ram_gb() / 0.5)))
    farm = Farm(a.pack, workers)
    if a.zip:
        farm.zip()
    elif a.build_only:
        farm.build_all()
    else:
        farm.run()


if __name__ == '__main__':
    sys.exit(main())
