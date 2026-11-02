"""Branch farm on the x1 team-plan hook (comms/x1 J005; port of lab/box tools/lab/branch_farm.py to this repo).

usage: python tools/x1_farm.py run    --name NAME [--workers N]     resumable; safe to stop and restart
       python tools/x1_farm.py builds --name NAME                    build and check code sections only
Config: research/x1/farm/NAME.json {"bot", "opponents", "kinds", "rounds", "plans", "expect_code"} (defaults below).
Work and rows: artifacts/tmp/x1farm/NAME/ (rows.jsonl, one row per game; base/ keeps baseline summaries).

Baseline: X1_PLAN=1 X1_PLAN_ROUND=5000 X1_PLAN_ID=6 (never switches; non-zero id so it shares the branches' code
section). Branches: every (round, plan); identical to the baseline before the round. Every branch's summary is compared
with its baseline's, timeline by timeline (lab/box tools/lab/branch_prefix.py first_diff), and the first differing round
is kept in the row ('diverge'); 'prefix_ok' is false if it is before the switch round. Branches whose round is at or
after the baseline's last round are recorded as skipped. Baselines run first, then rounds in the configured order,
each tier shuffled across maps, so a partial run is a balanced sample.
"""
import argparse, hashlib, importlib.util, json, random, re, shutil, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('dz', ROOT/'tools/dz.py'); dz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dz)
NEVER = 5000
KINDS = {'ladder': 'maps/local-benchmarks', 'styled': 'maps/x1-unseen', 'maze': 'maps/x1-maze'}
DEFAULT = dict(bot='x1', opponents=['x2', 'x2-s2'], kinds=['ladder', 'styled'], rounds=[250, 150, 350],
               plans=[1, 2, 3, 4, 5, 6, 7, 8], expect_code='be66c8804ef0')
FEAT = ('submittedGems', 'gems', 'gold', 'kills', 'deaths', 'collectedGems', 'earnedGold', 'championDamageDone')


def code_sha(path):
    """sha256 of the wasm code section (id 10)."""
    raw = Path(path).read_bytes(); off = 8
    while off < len(raw):
        kind = raw[off]; off += 1; size = shift = 0
        while True:
            b = raw[off]; off += 1; size |= (b & 127) << shift
            if not b & 128: break
            shift += 7
        if kind == 10: return hashlib.sha256(raw[off:off + size]).hexdigest()
        off += size
    return ''


def features(d, us, op, rounds):
    """Per switch round: for us then them, submitted gems and the champion sums of FEAT[1:] (branch_farm.features)."""
    vals = {}
    for kind in ('teamTimelines', 'championTimelines'):
        for tl in d.get(kind, []):
            o = tl['owner']; team = o if isinstance(o, str) else o.get('team')
            if tl['metric'] not in FEAT or (kind == 'teamTimelines') != (tl['metric'] == 'submittedGems'): continue
            ends, acc = [], 0
            for r in tl['runs']:
                acc += int(r['duration']); ends.append((acc, float(r['value'])))
            vals.setdefault((team, tl['metric']), []).append(ends)
    def at(ends, rd): return next((v for e, v in ends if rd < e), ends[-1][1] if ends else 0)
    return {str(rd): [sum(at(e, rd) for e in vals.get((t, m), [])) for t in (us, op) for m in FEAT] for rd in rounds}


def series(summary):
    s = {}
    for kind in ('teamTimelines', 'championTimelines'):
        for t in summary.get(kind, []):
            o = t['owner']
            key = (kind, t['metric'], o if isinstance(o, str) else (o.get('team'), o.get('id')))
            out = []
            for r in t['runs']: out += [r['value']] * int(r['duration'])
            s[key] = out
    return s


def first_diff(sa, sb):
    """First timeline index where two games differ (lab/box tools/lab/branch_prefix.py), None if identical."""
    first = None
    for k in set(sa) | set(sb):
        x, y = sa.get(k, []), sb.get(k, []); n = min(len(x), len(y))
        d = next((i for i in range(n) if x[i] != y[i]), n if len(x) != len(y) else None)
        if d is not None and (first is None or d < first): first = d
    return first


class Farm:
    def __init__(self, name, workers):
        self.name, self.workers = name, workers
        cfg_path = ROOT/'research/x1/farm'/f'{name}.json'
        self.cfg = dict(DEFAULT, **(json.loads(cfg_path.read_text()) if cfg_path.exists() else {}))
        self.dir = ROOT/'artifacts/tmp/x1farm'/name
        for sub in ('wasm', 'base', 'tmp'): (self.dir/sub).mkdir(parents=True, exist_ok=True)
        self.rows_path = self.dir/'rows.jsonl'
        self.lock = threading.Lock(); self.done, self.base_rounds, self.base_series = {}, {}, {}
        if self.rows_path.exists():
            for line in self.rows_path.read_text(encoding='utf-8').splitlines():
                try: self.note(json.loads(line))
                except ValueError: continue  # a line cut by a crash
        self.maps = [(k, p) for k in self.cfg['kinds'] if (ROOT/KINDS[k]).is_dir()
                     for p in sorted((ROOT/KINDS[k]).glob('*.map26a'))]

    def note(self, r):
        self.done[r['key']] = r
        if r['round'] < 0 and 'rounds' in r: self.base_rounds[(r['opp'], r['kind'], r['map'], r['side'])] = r['rounds']

    def log(self, msg): print(time.strftime('%H:%M:%S'), msg, flush=True)

    # builds -------------------------------------------------------------------------------------------------------
    @staticmethod
    def variant(rd, p): return 'base' if rd < 0 else f'r{rd}p{p}'

    def wasm(self, rd, p): return self.dir/'wasm'/f'{self.variant(rd, p)}.wasm'

    def build_x1(self, rd, p):
        out = self.wasm(rd, p)
        if out.exists(): return out
        work = self.dir/'build'/self.variant(rd, p); shutil.rmtree(work, ignore_errors=True)
        shutil.copytree(ROOT/'bots'/self.cfg['bot']/'src', work/'src')
        config = work/'src/x1_config.h'; text = config.read_text(encoding='utf-8')
        for k, v in (('X1_PLAN', 1), ('X1_PLAN_ROUND', NEVER if rd < 0 else rd), ('X1_PLAN_ID', 6 if rd < 0 else p)):
            text, n = re.subn(r'^#define ' + k + r'\s+[^\n]+', f'#define {k} {v}', text, flags=re.MULTILINE)
            if n != 1: raise ValueError('define not found once: ' + k)
        config.write_text(text, encoding='utf-8', newline='\n')
        part = out.with_suffix('.part'); dz.build(work, part); part.replace(out)
        shutil.rmtree(work, ignore_errors=True)
        return out

    def build_opp(self, o):
        out = self.dir/'wasm'/f'opp-{o}.wasm'
        if out.exists(): return out
        work = self.dir/'build'/f'opp-{o}'; shutil.rmtree(work, ignore_errors=True)
        shutil.copytree(ROOT/'bots'/o/'src', work/'src')
        part = out.with_suffix('.part'); dz.build(work, part); part.replace(out)
        shutil.rmtree(work, ignore_errors=True)
        return out

    def build_all(self):
        c = self.cfg
        x1 = [(-1, 0)] + [(rd, p) for rd in c['rounds'] for p in c['plans']]
        with ThreadPoolExecutor(min(self.workers, 6)) as ex:
            list(ex.map(lambda t: self.build_x1(*t), x1)); list(ex.map(self.build_opp, c['opponents']))
        builds = {self.variant(*t): dict(sha256=dz.sha(self.wasm(*t)), code=code_sha(self.wasm(*t))) for t in x1}
        builds.update({f'opp-{o}': dict(sha256=dz.sha(self.dir/'wasm'/f'opp-{o}.wasm')) for o in c['opponents']})
        (self.dir/'builds.json').write_text(json.dumps(builds, indent=1))
        codes = {v['code'] for k, v in builds.items() if not k.startswith('opp-')}
        shas = {v['sha256'] for k, v in builds.items() if not k.startswith('opp-')}
        self.log(f'{len(x1)} x1 builds, {len(shas)} distinct binaries, code sections {sorted(x[:12] for x in codes)}')
        if len(codes) != 1 or not next(iter(codes)).startswith(c['expect_code']):
            raise SystemExit(f'code sections differ or do not match {c["expect_code"]}: see {self.dir/"builds.json"}')
        if len(shas) != len(x1): raise SystemExit('two plan builds share a binary: a define did not take')

    # games --------------------------------------------------------------------------------------------------------
    def tiers(self):
        c, rng = self.cfg, random.Random(0)
        groups = [(o, k, m.stem, side) for o in c['opponents'] for k, m in self.maps for side in 'AB']
        tier = [g + (-1, 0) for g in groups]; rng.shuffle(tier); out = [tier]
        for rd in c['rounds']:
            tier = [g + (rd, p) for g in groups for p in c['plans']]; rng.shuffle(tier); out.append(tier)
        return out

    @staticmethod
    def key(j): return '|'.join(str(x) for x in j)

    def play(self, job):
        o, kind, m, side, rd, p = job; key = self.key(job)
        if key in self.done: return False
        row = dict(key=key, opp=o, kind=kind, map=m, side=side, round=rd, plan=p)
        last = self.base_rounds.get((o, kind, m, side))
        if rd >= 0 and last is not None and rd >= last:
            row['skipped'] = 'game over before round'; self.add(row); return False
        me, them = self.wasm(rd, p), self.dir/'wasm'/f'opp-{o}.wasm'
        a, b = (me, them) if side == 'A' else (them, me)
        folder = self.dir/'tmp'/hashlib.sha1(key.encode()).hexdigest()[:16]
        shutil.rmtree(folder, ignore_errors=True); folder.mkdir(parents=True)
        stats = folder/'summary.json'
        for attempt in (1, 2, 3):  # Windows can refuse a process start under load
            r = subprocess.run([str(dz.CLI), 'run', str(a), str(b), '--map', str(ROOT/KINDS[kind]/f'{m}.map26a'),
                                '--out-dir', str(folder), '--statistics', str(stats), '--json', '--release'], cwd=ROOT,
                               capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=900)
            if not r.returncode and stats.exists(): break
            if attempt == 3:
                with self.lock, open(self.dir/'errors.jsonl', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(dict(key=key, out=((r.stdout or '') + (r.stderr or ''))[-2000:])) + '\n')
                shutil.rmtree(folder, ignore_errors=True); return False
            time.sleep(5)
        raw = stats.read_text(encoding='utf-8'); d = json.loads(raw)
        us, op = 'team' + side, 'team' + ('B' if side == 'A' else 'A')
        gems = {t['team']: int(t['submittedGems']) for t in d['teams']}
        fuel = {t: sum(len(e['entries']) for e in d['events'] if e['kind'] == 'fuelExhausted' and e['owner']['team'] == t)
                for t in (us, op)}
        champ = lambda t, k: sum(int(c['metrics'][k]) for c in d['champions'] if c['team'] == t)
        outcome = d['match']['outcome']
        row.update(win=1.0 if outcome == us else 0.0 if outcome == op else 0.5, gems=gems[us], opp_gems=gems[op],
                   rounds=int(d['match']['roundsStarted']), deaths=champ(us, 'deaths'), kills=champ(us, 'kills'),
                   opp_deaths=champ(op, 'deaths'), faults=int(d['diagnostics']['botFaults'][us]),
                   opp_faults=int(d['diagnostics']['botFaults'][op]), fuel=fuel[us], opp_fuel=fuel[op])
        if rd < 0:
            row['feat'] = features(d, us, op, self.cfg['rounds'])
            (self.dir/'base'/f'{o}-{kind}-{m}-{side}.json').write_text(raw, encoding='utf-8')
        else:
            base = self.dir/'base'/f'{o}-{kind}-{m}-{side}.json'
            if base.exists():
                div = first_diff(series(json.loads(base.read_text(encoding='utf-8'))), series(d))
                row.update(diverge=div, prefix_ok=div is None or div >= rd)
        shutil.rmtree(folder, ignore_errors=True)
        self.add(row); return True

    def add(self, row):
        with self.lock:
            with open(self.rows_path, 'a', encoding='utf-8') as f: f.write(json.dumps(row, separators=(',', ':')) + '\n')
            self.note(row)

    def run(self):
        self.build_all()
        tiers = self.tiers(); total = sum(map(len, tiers)); played, t0 = 0, time.time()
        self.log(f'{len(self.maps)} maps, {total} games, {sum(1 for t in tiers for j in t if self.key(j) in self.done)} done')
        for tier in tiers:  # a tier finishes before the next starts: branches need their baseline's summary
            with ThreadPoolExecutor(self.workers) as ex:
                for i, f in enumerate([ex.submit(self.play, j) for j in tier]):
                    try: played += bool(f.result())
                    except Exception as e:  # one bad game must not stop the farm
                        with self.lock, open(self.dir/'errors.jsonl', 'a', encoding='utf-8') as fh:
                            fh.write(json.dumps(dict(key=self.key(tier[i]), out=repr(e)[-2000:])) + '\n')
                    if played and i % 200 == 0:
                        n = len(self.done); rate = played / (time.time() - t0)
                        self.log(f'games {n} / {total}  ({rate * 60:.0f}/min, ~{(total - n) / max(rate, 1e-9) / 3600:.1f} h left)')
        self.log(f'games {len(self.done)} / {total}' + ('  X1FARM_DONE' if len(self.done) == total else '  (some failed: errors.jsonl)'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('command', choices=['run', 'builds']); ap.add_argument('--name', required=True)
    ap.add_argument('--workers', type=int, default=6)
    a = ap.parse_args()
    farm = Farm(a.name, a.workers)
    farm.build_all() if a.command == 'builds' else farm.run()


if __name__ == '__main__': sys.exit(main())
