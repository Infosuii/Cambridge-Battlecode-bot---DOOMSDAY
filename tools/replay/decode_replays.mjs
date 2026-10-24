// Decode official .repl26a replays with the engine shipped in the local cambc visualiser (read-only, in place).
//
// The engine wasm and the visualiser's snapshot decoders are loaded from the installed cambc asset folder and pinned
// by SHA-256; nothing third-party is copied into this repository. Engine 1.0.3 only.
//
// Usage: node --no-warnings tools/replay/decode_replays.mjs --out <file.jsonl | shard directory> [--format jsonl|npz]
//          [--shard-size N] [--assets <visualiser/assets>] [--workers N] [--perspective] [--reference]
//          <replay.repl26a | directory> ...
// jsonl (default): each output line is one replay: final state, per-kind action counts and the ordered champion actions
// ([round, champion, kind, fromX, fromY, toX, toY, abilitySlot]). With --perspective, each champion turn also records
// that champion's own fog-limited view (self + visible entities) at the start of the turn.
// npz: the same content as compact NumPy shards of --shard-size replays (default 256) in a fresh directory; see
// npz_shards.mjs for the layout and replay_shards.py for reading and validating it.
// Where a sibling <name>.summary.json exists (cambc summary output) the final state is checked against it.
//
// Per engine step only the timeline header fields are read (offsets of the visualiser's header decoder); the full
// snapshot is decoded once at the end and, with --perspective, on champion turns. --reference decodes the full
// timeline snapshot at every step instead (slow; the two paths must produce identical rows). --workers runs replays in
// parallel worker threads, one engine each (default: all logical CPUs); JSONL rows are written in completion order,
// npz shards in sorted input order.
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Worker, isMainThread, parentPort, workerData } from 'node:worker_threads';
import { ShardWriter, pack, transferables } from './npz_shards.mjs';

const PINNED = {
  'v1_0_3-DRqNt1t2.wasm': '029ecd290dc400e75418178ec386d72cbd7d9f2fc2a2e451bf594ca23566df48',
  'PanelChrome-BXlTYAwV.js': '960affde6198366d2347bd21f43efec5bc06acc6cb0c53e5f7f96dbf87f027e6',
  'rolldown-runtime-hePW80VL.js': '580ad8c58061a4dde99bde0a56905e382f0568516ee2f5b84dbfb52085709021',
};
// Step kinds as labelled by the visualiser (index bundle `uv`/`mv`); 26/27 are fuel-exhausted / error turn ends.
const ACTION = { 4: 'move', 5: 'attack', 6: 'cast', 9: 'priority', 11: 'recall', 12: 'submit_start', 13: 'buy', 14: 'ward',
                 18: 'submit_bank', 23: 'dash_move', 25: 'sell' };
const PHASE_CHAMPIONS = 10, NO_CHAMPION = 0xFFFFFFFF, NO_SLOT = 0xFFFFFFFF, DRAFT_PICK = 19, ACTOR_CHAMPION = 1;
const SNAPSHOT_MAGIC = 1, OUTCOME = { teamA: 1, teamB: 2 };

function parseArgs(argv) {
  const a = { inputs: [], perspective: false, reference: false, assets: null, out: null, workers: os.availableParallelism(),
              format: 'jsonl', shardSize: 256 };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--out') a.out = argv[++i];
    else if (argv[i] === '--assets') a.assets = argv[++i];
    else if (argv[i] === '--workers') a.workers = Number(argv[++i]);
    else if (argv[i] === '--format') a.format = argv[++i];
    else if (argv[i] === '--shard-size') a.shardSize = Number(argv[++i]);
    else if (argv[i] === '--perspective') a.perspective = true;
    else if (argv[i] === '--reference') a.reference = true;
    else a.inputs.push(argv[i]);
  }
  if (!a.out || !a.inputs.length)
    throw new Error('usage: --out <file.jsonl | dir> [--format jsonl|npz] [--shard-size N] [--assets dir] [--workers N] [--perspective] [--reference] <replays...>');
  if (!Number.isInteger(a.workers) || a.workers < 1) throw new Error('--workers must be a positive integer');
  if (!['jsonl', 'npz'].includes(a.format)) throw new Error('--format must be jsonl or npz');
  if (!Number.isInteger(a.shardSize) || a.shardSize < 1 || a.shardSize > 4096) throw new Error('--shard-size must be 1..4096');
  return a;
}

function defaultAssets() {
  const root = path.join(os.homedir(), 'AppData/Local/cambc/assets');
  for (const d of fs.existsSync(root) ? fs.readdirSync(root) : []) {
    const p = path.join(root, d, 'visualiser/assets');
    if (fs.existsSync(path.join(p, 'v1_0_3-DRqNt1t2.wasm'))) return p;
  }
  throw new Error('cambc visualiser assets not found; pass --assets');
}

function verifyAssets(dir) {
  for (const [name, digest] of Object.entries(PINNED)) {
    const actual = crypto.createHash('sha256').update(fs.readFileSync(path.join(dir, name))).digest('hex');
    if (actual !== digest) throw new Error(`pinned asset changed: ${name} ${actual}`);
  }
}

async function engine(dir) {
  const PC = await import(pathToFileURL(path.join(dir, 'PanelChrome-BXlTYAwV.js')).href);
  let X;
  const dv = () => new DataView(X.memory.buffer);
  const cstr = (p) => { if (!p) return ''; const b = new Uint8Array(X.memory.buffer); let e = p; while (b[e]) e++; return new TextDecoder().decode(b.subarray(p, e)); };
  // Minimal WASI matching the visualiser's own shim: no files, no environment, stdout/stderr discarded.
  const wasi = {
    random_get(p, n) { crypto.getRandomValues(new Uint8Array(X.memory.buffer, p, n)); return 0; },
    clock_time_get(id, prec, out) { dv().setBigUint64(out, BigInt(Date.now()) * 1000000n, true); return 0; },
    environ_sizes_get(a, b) { dv().setUint32(a, 0, true); dv().setUint32(b, 0, true); return 0; }, environ_get() { return 0; },
    fd_close(fd) { return fd <= 2 ? 0 : 8; },
    fd_fdstat_get(fd, p) { if (fd > 2) return 8; const d = dv(); d.setUint8(p, 2); d.setUint16(p + 2, 0, true); d.setBigUint64(p + 8, 0n, true); d.setBigUint64(p + 16, 0n, true); return 0; },
    fd_prestat_get() { return 8; }, fd_prestat_dir_name() { return 8; },
    fd_read(fd, iov, n, out) { if (fd) return 8; dv().setUint32(out, 0, true); return 0; }, fd_seek(fd) { return fd <= 2 ? 70 : 8; },
    fd_write(fd, iov, n, out) { const d = dv(); let c = 0; for (let i = 0; i < n; i++) c += d.getUint32(iov + i * 8 + 4, true); d.setUint32(out, c, true); return 0; },
    proc_exit(c) { throw new Error('wasm exit ' + c); },
  };
  const { instance } = await WebAssembly.instantiate(fs.readFileSync(path.join(dir, 'v1_0_3-DRqNt1t2.wasm')),
    { wasi_snapshot_preview1: wasi, deep_wasm: { on_assert_fail_impl() { return 1; } } });
  X = instance.exports; X._initialize();
  const check = (rc) => { if (rc !== 0) throw new Error(`engine error ${rc}: ${cstr(X.GetLastErrorMsg())}`); };
  const out = X.Engine_Malloc(32), args = X.Engine_Malloc(128);
  const tsize = X.Game_Visualiser_TimelineSnapshotSize();
  const snap = X.Engine_Malloc(X.Game_Visualiser_SnapshotSize()), tsnap = X.Engine_Malloc(tsize);
  const perspective = (team, champion) => { const q = args + 48; dv().setUint32(q, team, true); dv().setUint32(q + 4, champion, true); return q; };
  return { X, PC, dv, check, out, args, snap, tsnap, tsize, perspective };
}

// Timeline snapshot header, at the offsets used by the visualiser's header decoder (PanelChrome `Tr`).
function fastHeader(d, t) {
  const u = (o) => d.getUint32(t + o, true), s = (o) => d.getInt32(t + o, true);
  const kind = u(68), slot = u(108);
  return { round: u(8), awaiting: u(20) !== 0, phase: u(24), outcome: u(28), input: u(56), current: u(60),
           kind, actorKind: u(72), actor: u(76), fx: s(80), fy: s(84), tx: s(88), ty: s(92), stepRound: u(96), substep: u(104),
           slot: slot !== NO_SLOT && kind !== DRAFT_PICK ? slot : -1 };
}

function referenceHeader(s) {
  const k = s.step;
  return { round: s.round, awaiting: s.awaitingInput, phase: s.phase, outcome: s.outcome, input: s.inputPosition, current: s.currentChampion,
           kind: k.kind, actorKind: k.actor.kind, actor: k.actor.index, fx: k.from.x, fy: k.from.y, tx: k.to.x, ty: k.to.y,
           stepRound: k.round, substep: k.substep, slot: k.abilitySlot ?? -1 };
}

function view(E, team, champion) {
  // The acting champion's own view: everything the engine marks as known to that team at this moment.
  E.check(E.X.Game_Visualiser_ReadState(E.h, E.perspective(team, champion), E.snap));
  const s = E.PC.F(E.dv(), E.snap);
  const unit = (c) => c.position ? [c.entity.index, c.team, c.type, c.position.x, c.position.y, c.health ?? null, c.maxHealth ?? null,
    c.gems ?? null, c.gold ?? null, c.alive ? 1 : 0] : null;
  return { champions: s.champions.map(unit).filter(Boolean),
           camps: s.camps.filter(c => c.position).map(c => [c.entity.index, c.type, c.position.x, c.position.y, c.health ?? null]),
           cooldowns: s.champions.find(c => c.entity.index === champion)?.cooldowns ?? null };
}

function decode(E, file, withPerspective, reference) {
  const bytes = fs.readFileSync(file);
  const p = E.X.Engine_Malloc(bytes.length);
  new Uint8Array(E.X.memory.buffer, p, bytes.length).set(bytes);
  try { E.check(E.X.Game_FromReplayFileBytes(p, bytes.length, E.out)); } finally { E.X.Engine_Free(p); }
  E.h = E.dv().getBigUint64(E.out, true);
  try {
    const { X, check, dv, out, args } = E;
    check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
    check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
    check(X.Game_GetBitboardMetadata(E.h, out)); const width = dv().getInt32(out, true), height = dv().getInt32(out + 4, true);
    check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
    const fullState = () => { check(X.Game_Visualiser_ReadTimelineState(E.h, E.tsnap)); return E.PC.I(dv(), E.tsnap); };
    const teams = new Map();
    const teamOf = (champion) => {
      if (!teams.has(champion)) for (const c of fullState().champions) teams.set(c.entity.index, c.team);
      return teams.get(champion);
    };
    const counts = {}, actions = [], turns = []; let prev, steps = 0, fuelExhausted = 0, errors = 0;
    for (;;) {
      let s;
      if (reference) s = referenceHeader(fullState());
      else {
        check(X.Game_Visualiser_ReadTimelineState(E.h, E.tsnap));
        const d = dv();
        if (!steps && (d.getUint32(E.tsnap, true) !== SNAPSHOT_MAGIC || d.getUint32(E.tsnap + 4, true) !== E.tsize))
          throw new Error('unsupported timeline snapshot ABI');
        s = fastHeader(d, E.tsnap);
      }
      if (prev && s.input === prev.input && s.substep === prev.substep) throw new Error('timeline made no progress');
      if (s.actorKind === ACTOR_CHAMPION && ACTION[s.kind]) {
        counts[ACTION[s.kind]] = (counts[ACTION[s.kind]] ?? 0) + 1;
        actions.push([s.stepRound, s.actor, s.kind, s.fx, s.fy, s.tx, s.ty, s.slot]);
      }
      if (s.kind === 26) fuelExhausted++; else if (s.kind === 27) errors++;
      // A new champion turn: the engine is waiting for this champion's inputs.
      if (withPerspective && s.phase === PHASE_CHAMPIONS && s.awaiting && s.current !== NO_CHAMPION &&
          !(prev && prev.awaiting && prev.current === s.current && prev.round === s.round)) {
        const team = teamOf(s.current);
        if (team !== undefined) turns.push({ round: s.round, champion: s.current, action_index: actions.length, view: view(E, team, s.current) });
      }
      prev = s; steps++;
      if (s.outcome || (s.awaiting && s.input >= size)) break;
      check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
    }
    const last = fullState();
    return { width, height, steps, inputs: last.inputPosition, timeline_size: size, rounds: last.round, outcome: last.outcome,
             submitted_gems: last.submittedGems.map(Number), fuel_exhausted_turns: fuelExhausted, error_turns: errors, counts,
             champions: last.champions.map(c => ({ index: c.entity.index, team: c.team, type: c.type, gold: c.gold, gems: c.gems, kills: c.kills })),
             actions, turns: withPerspective ? turns : undefined };
  } finally { E.X.Game_Destroy(E.h); E.h = undefined; }
}

function compare(result, summaryPath) {
  if (!fs.existsSync(summaryPath)) return null;
  const d = JSON.parse(fs.readFileSync(summaryPath, 'utf8')), m = d.match;
  const gems = ['teamA', 'teamB'].map(t => Number(d.teams.find(x => x.team === t)?.submittedGems ?? 0));
  const want = [...d.champions].sort((a, b) => a.id - b.id)
    .map(c => [c.id, c.team === 'teamA' ? 0 : 1, Number(c.metrics.gold), Number(c.metrics.gems), Number(c.metrics.kills)]);
  const got = result.champions.map(c => [c.index, c.team, c.gold, c.gems, c.kills]);
  const checks = { engine_1_0_3: m.engineVersion === '1.0.3', outcome: (OUTCOME[m.outcome] ?? 0) === result.outcome,
    rounds: m.roundsStarted === result.rounds, final_input: m.finalInput === result.inputs,
    submitted_gems: JSON.stringify(gems) === JSON.stringify(result.submitted_gems),
    champion_gold_gems_kills: JSON.stringify(want) === JSON.stringify(got) };
  return { passed: Object.values(checks).every(Boolean), checks };
}

function processFile(E, file, opts) {
  const t0 = performance.now();
  try {
    const r = decode(E, file, opts.perspective, opts.reference);
    return { replay: path.basename(file), ok: true, ms: Math.round(performance.now() - t0), ...r,
             summary_check: compare(r, file.replace(/\.repl26a$/, '.summary.json')) };
  } catch (e) { return { replay: path.basename(file), ok: false, error: String(e.message ?? e) }; }
}

// npz rows are packed where they were decoded, so only typed-array buffers cross threads (transferred, not copied).
function packed(row) {
  try { return pack(row); } catch (e) { return pack({ replay: row.replay, ok: false, error: 'pack: ' + String(e.message ?? e) }); }
}

async function runParallel(files, opts, result) {
  // A pool of engines; each worker takes the next file when it finishes one. A crashed worker is replaced.
  let next = 0;
  await new Promise((resolve) => {
    let live = 0;
    const spawn = () => {
      if (next >= files.length) { if (!live) resolve(); return; }
      const w = new Worker(new URL(import.meta.url), { workerData: { assets: opts.assets, perspective: opts.perspective,
                                                                    reference: opts.reference, format: opts.format } });
      let current = null; live++;
      const feed = () => {
        if (next < files.length) { current = next++; w.postMessage({ index: current, file: files[current] }); }
        else { current = null; w.postMessage(null); }
      };
      w.on('message', (m) => { if (m === 'ready') return feed(); result(m.index, m); feed(); });
      w.on('error', (e) => {
        if (current !== null) {
          const row = { replay: path.basename(files[current]), ok: false, error: 'worker crashed: ' + String(e.message ?? e) };
          result(current, opts.format === 'npz' ? { packed: packed(row) } : { row });
        }
        current = null;
      });
      w.on('exit', () => { live--; if (next < files.length) spawn(); else if (!live) resolve(); });
    };
    for (let i = 0; i < Math.min(opts.workers, files.length); i++) spawn();
  });
}

function jsonlOutput(file) {
  const stream = fs.createWriteStream(file);
  let passed = 0, failed = 0;
  return {
    result(index, { row }) { if (row.ok && row.summary_check?.passed !== false) passed++; else failed++; stream.write(JSON.stringify(row) + '\n'); },
    async close() { await new Promise((r) => stream.end(r)); return { passed, failed }; },
  };
}

function npzOutput(dir, files, a) {
  const writer = new ShardWriter(dir, files, { shardSize: a.shardSize, perspective: a.perspective, run: {
    created: new Date().toISOString(), assets: a.assets, pinned: PINNED, reference_decoder: a.reference,
    inputs: files.map(f => path.basename(f)) } });
  return {
    result(index, m) { writer.add(index, m.packed ?? packed(m.row)); },
    async close() { const manifest = writer.finish(); return { passed: manifest.passed, failed: manifest.failed, shards: manifest.shards.length, bytes: manifest.bytes }; },
  };
}

if (isMainThread) {
  const a = parseArgs(process.argv.slice(2));
  a.assets = a.assets ?? defaultAssets();
  verifyAssets(a.assets);
  const files = a.inputs.flatMap(p => fs.statSync(p).isDirectory()
    ? fs.readdirSync(p).filter(f => f.endsWith('.repl26a')).sort().map(f => path.join(p, f)) : [p]);
  const output = a.format === 'npz' ? npzOutput(a.out, files, a) : jsonlOutput(a.out);
  const t0 = performance.now();
  const workers = Math.min(a.workers, files.length);
  if (workers <= 1) {
    const E = await engine(a.assets);
    files.forEach((f, i) => { const row = processFile(E, f, a); output.result(i, a.format === 'npz' ? { packed: packed(row) } : { row }); });
  } else await runParallel(files, a, output.result);
  const totals = await output.close();
  console.log(JSON.stringify({ replays: files.length, ...totals, workers, seconds: Math.round((performance.now() - t0) / 100) / 10,
                               format: a.format, out: a.out, assets: a.assets, perspective: a.perspective, reference: a.reference }));
  if (totals.failed) process.exitCode = 1;
} else {
  const E = await engine(workerData.assets);
  parentPort.on('message', (job) => {
    if (job === null) { parentPort.close(); return; }
    const row = processFile(E, job.file, workerData);
    if (workerData.format !== 'npz') return parentPort.postMessage({ index: job.index, row });
    const p = packed(row);
    parentPort.postMessage({ index: job.index, packed: p }, transferables(p));
  });
  parentPort.postMessage('ready');
}
