// Mimic training rows from engine-2 replays: what each top-team champion saw (its own perspective, through the same
// engine API calls the bot makes) and what it did next.
//
// Pass 1 walks the timeline and records every champion turn: where the champion stood, whether it was alive, and its
// actions (moves, attacks, casts, recall, tribute, cancel), with attack and cast targets resolved to a champion or a
// camp. Hindsight labels follow:
//   objective  = the champion's next event within 60 rounds while it stays alive: attacking a camp (or standing on a
//                camp tile of a group whose reward waits) -> farm that group; tributing -> bank; arriving on its own
//                spawn (later turns only) -> home; attacking an enemy champion -> fight it. Then trips override it:
//                the turns of a walk that keeps closing on the altars (or the own spawn) without hitting anything and
//                ends in a tribute (an arrival) are labelled bank (home) - the next event alone would call a bank trip
//                with a camp on the way "farm" and leave bank only to the last few steps.
//   move       = the turn's first walk or dash destination, else staying put.
//   target     = the turn's first basic attack, else none.
//   recall     = a recall started this turn that is still running at the start of the champion's next turn.
//   tribute    = a tribute started this turn (rows where it stands next to an altar with gems after its moves).
// Pass 2 replays the timeline again, rebuilds each imitated champion's observation with the engine API from its own
// perspective (Game_API_* = the SDK's host calls), feeds it to the mimic kernel (bots/mimic/src/core.cpp compiled to
// wasm), simulates the team's shared memory as the bot writes it, and writes candidate features with the labels.
//
// Usage: NFS_REPLAY_ENGINE=2.0.0 node --no-warnings tools/mimic/extract.mjs --index <index.json> --replays <dir>
//          --teams <duel plan json> --out <dir> [--workers 16] [--limit N] [--obj-rate 16] [--move-rate 4] [--only <match id>]
import fs from 'node:fs';
import path from 'node:path';
import { Worker, isMainThread, parentPort, workerData } from 'node:worker_threads';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '../..');
const KERNEL = path.join(ROOT, 'artifacts/tmp/mimic/kernel.wasm');
const NONE = 0xFFFFFFFF, PHASE_CHAMPIONS = 10, HORIZON = 60, TRIP_MAX = 80;
const K = { MOVE: 4, ATTACK: 5, CAST: 6, END: 8, RECALL: 11, SUBMIT: 12, CANCEL: 16 };
const O = { FARM: 0, BANK: 1, HOME: 2, FIGHT: 3 };
const NF = { obj: 65, move: 36, tgt: 19, recall: 10, trib: 6, cast: 24 }; // must equal core.h NF_* (checked against the kernel)
const DASH = 6;

function args() {
  const a = { workers: 16, objRate: 16, moveRate: 4, castRate: 2, limit: 0, only: null, parity: null, observed: null };
  const v = process.argv.slice(2);
  for (let i = 0; i < v.length; i++) {
    const k = v[i];
    if (k === '--index') a.index = v[++i];
    else if (k === '--replays') a.replays = v[++i];
    else if (k === '--teams') a.teams = v[++i];
    else if (k === '--out') a.out = v[++i];
    else if (k === '--workers') a.workers = +v[++i];
    else if (k === '--limit') a.limit = +v[++i];
    else if (k === '--obj-rate') a.objRate = +v[++i];
    else if (k === '--move-rate') a.moveRate = +v[++i];
    else if (k === '--cast-rate') a.castRate = +v[++i];
    else if (k === '--only') a.only = v[++i];
    else if (k === '--parity') a.parity = v[++i];      // write per-turn kernel hashes instead of rows
    else if (k === '--observed') a.observed = v[++i];  // {champion id: [rounds the bot observed]} (parity)
    else if (k === '--shared-snapshots') a.sharedSnapshots = v[++i]; // actual shared bytes, including suspended writes
    else throw new Error('unknown argument ' + k);
  }
  for (const k of ['index', 'replays', 'teams', 'out']) if (!a[k]) throw new Error('missing --' + k);
  return a;
}

// Deterministic sampling: a hash of (match, champion, round).
function keep(s, rate) {
  if (rate <= 1) return true;
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619) >>> 0;
  return h % rate === 0;
}

async function loadKernel() {
  const { WASI } = await import('node:wasi');
  const wasi = new WASI({ version: 'preview1', args: [], env: {} });
  const { instance } = await WebAssembly.instantiate(fs.readFileSync(KERNEL), { wasi_snapshot_preview1: wasi.wasiImport });
  wasi.initialize(instance);
  return instance.exports;
}

// Growing typed-array columns for one decision type.
class Rows {
  constructor(nf, metaW) { this.nf = nf; this.metaW = metaW; this.feat = []; this.ncand = []; this.label = []; this.meta = []; this.cand = []; }
  add(feat, n, label, meta, cand) {
    this.feat.push(feat.slice(0, n * this.nf)); this.ncand.push(n); this.label.push(label); this.meta.push(meta);
    this.cand.push(cand ?? new Int32Array(0));
  }
  get size() { return this.ncand.length; }
  write(file) {
    const nr = this.size, total = this.ncand.reduce((a, b) => a + b, 0);
    const feat = new Float32Array(total * this.nf), meta = new Int32Array(nr * this.metaW);
    const ncand = Uint8Array.from(this.ncand), label = Int16Array.from(this.label);
    const candLen = this.cand.reduce((a, b) => a + b.length, 0), cand = new Int32Array(candLen);
    let at = 0, ca = 0;
    for (let i = 0; i < nr; i++) {
      feat.set(this.feat[i], at); at += this.feat[i].length;
      meta.set(this.meta[i], i * this.metaW);
      cand.set(this.cand[i], ca); ca += this.cand[i].length;
    }
    const parts = [feat, ncand, label, meta, cand];
    const header = { rows: nr, cands: total, nf: this.nf, metaW: this.metaW, candInts: candLen,
      parts: ['feat:f4', 'ncand:u1', 'label:i2', 'meta:i4', 'cand:i4'], bytes: parts.map(p => p.byteLength) };
    const fd = fs.openSync(file, 'w');
    const hb = Buffer.from(JSON.stringify(header) + '\n');
    fs.writeSync(fd, hb);
    for (const p of parts) fs.writeSync(fd, Buffer.from(p.buffer, p.byteOffset, p.byteLength));
    fs.closeSync(fd);
    this.feat = []; this.ncand = []; this.label = []; this.meta = []; this.cand = [];
  }
}
// meta columns: imitated team index, hero type, round, champion id, won (1/0), match number, extra
const META_W = 7;

function readBoard(E, w, h, stride, getter) {
  const { dv, check } = E;
  check(getter(E.h, E.out)); const p = dv().getUint32(E.out, true), d = dv(), out = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const word = d.getBigUint64(p + 8 * ((y >> 3) * stride + (x >> 3)), true);
    out[y * w + x] = Number((word >> BigInt((y & 7) * 8 + (x & 7))) & 1n);
  }
  return out;
}

async function workerMain() {
  const { files, opts, teamNames } = workerData;
  const { engine, defaultAssets, verifyAssets } = await import('../replay/engine.mjs');
  const dir = defaultAssets(); verifyAssets(dir);
  const E = await engine(dir);
  const X = E.X;
  const M = await loadKernel();
  const kmem = () => M.memory.buffer;
  // The kernel's feature lists must have the widths this file writes.
  for (const [i, k] of ['obj', 'move', 'tgt', 'recall', 'trib', 'cast'].entries()) {
    const ptr = M.mk_names(i), b = new Uint8Array(M.memory.buffer);
    let e = ptr; while (b[e]) e++;
    const n = new TextDecoder().decode(b.subarray(ptr, e)).split(',').length;
    if (n !== NF[k]) throw new Error(`kernel ${k} has ${n} features, extract.mjs expects ${NF[k]}`);
  }
  const cstrK = (ptr) => { const b = new Uint8Array(kmem()); let e = ptr; while (b[e]) e++; return new TextDecoder().decode(b.subarray(ptr, e)); };
  const rows = { obj: new Rows(NF.obj, META_W), move: new Rows(NF.move, META_W), tgt: new Rows(NF.tgt, META_W),
    recall: new Rows(NF.recall, META_W), trib: new Rows(NF.trib, META_W), cast: new Rows(NF.cast, META_W) };
  let shard = 0;
  const flush = () => {
    for (const [k, r] of Object.entries(rows)) if (r.size) r.write(path.join(opts.out, `${k}-w${workerData.id}-${shard}.bin`));
    shard++;
  };
  const stats = [];
  for (const [fi, item] of files.entries()) {
    try {
      stats.push(processReplay(item));
    } catch (e) {
      stats.push({ match: item.match, error: String(e && e.stack || e) });
    }
    if ((fi + 1) % 20 === 0) flush();
    parentPort.postMessage({ progress: 1 });
  }
  flush();
  parentPort.postMessage({ done: stats });

  function processReplay(item) {
    E.load(fs.readFileSync(item.file));
    const { dv, check } = E;
    const u32 = o => dv().getUint32(o, true), i32 = o => dv().getInt32(o, true), f32 = o => dv().getFloat32(o, true);
    try {
      // ---- static map ----
      const meta = X.Engine_Malloc(64); check(X.Game_GetBitboardMetadata(E.h, meta));
      const w = i32(meta), h = i32(meta + 4), stride = u32(meta + 16);
      X.Engine_Free(meta);
      const wall = readBoard(E, w, h, stride, X.Game_GetWallBuffer), hole = readBoard(E, w, h, stride, X.Game_GetHoleBuffer);
      const altar = readBoard(E, w, h, stride, X.Game_GetAltarBuffer), bush = readBoard(E, w, h, stride, X.Game_GetBushBuffer);
      check(X.Game_API_Map_GetSymmetry(E.h, E.out)); const sym = i32(E.out);
      const spawn = [0, 1].map(t => { check(X.Game_API_GetSpawnRegion(E.h, t, E.out)); return [0, 4, 8, 12].map(o => i32(E.out + o)); });
      const inSpawn = (t, x, y) => x >= spawn[t][0] && x < spawn[t][2] && y >= spawn[t][1] && y < spawn[t][3];
      // Camps through the map API, group by group (Game_GetNumCamps counts only part of them on some maps).
      check(X.Game_API_Map_GetNumCampGroups(E.h, E.out)); const nGroups = u32(E.out);
      if (nGroups > 96) throw new Error('too many groups ' + nGroups);
      check(X.Game_API_Map_GetCampGroups(E.h, E.buf + 2048, 256, E.out));
      const ghandles = [...new Uint32Array(X.memory.buffer, E.buf + 2048, nGroups)];
      const gindex = new Map(ghandles.map((hd, i) => [hd, i]));
      const camps = [];
      const groups = ghandles.map(hd => {
        check(X.Game_API_Map_CampGroup_Get(E.h, hd, E.out)); const gems = u32(E.out), gold = u32(E.out + 4);
        check(X.Game_API_Map_CampGroup_GetRespawnTime(E.h, hd, E.out)); const respawn = i32(E.out);
        check(X.Game_API_Map_CampGroup_GetNumCamps(E.h, hd, E.out)); const n = u32(E.out);
        check(X.Game_API_Map_CampGroup_GetCampInfo(E.h, hd, E.buf + 3072, 256, E.out));
        if (u32(E.out) !== n) throw new Error('camp list size');
        for (const k of [...new Uint32Array(X.memory.buffer, E.buf + 3072, n)]) {
          check(X.Game_API_Map_CampInfo_Get(E.h, k, E.out));
          camps.push({ k, x: i32(E.out), y: i32(E.out + 4), type: i32(E.out + 8), gh: hd });
        }
        return { hd, gems, gold, respawn };
      });
      if (camps.length > 200) throw new Error('too many camps ' + camps.length);
      // Kernel camp order: by group, then (y, x) inside a group (the bot sorts the same way).
      const order = [];
      for (let g = 0; g < nGroups; g++)
        order.push(...camps.filter(c => gindex.get(c.gh) === g).sort((a, b) => a.y - b.y || a.x - b.x));
      const myIdx = new Map(order.map((c, i) => [c.k, i]));
      const campAt = new Map(camps.map(c => [c.y * w + c.x, c])), campByK = new Map(camps.map(c => [c.k, c]));
      for (const t of [0, 1]) {
        M.mk_map_begin(t, w, h, sym);
        const terr = new Uint8Array(kmem(), M.mk_terr(t), w * h);
        for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
          const i = y * w + x;
          terr[i] = (wall[i] ? 1 : 0) | (hole[i] ? 2 : 0) | (altar[i] ? 4 : 0) | (bush[i] ? 8 : 0) |
            (inSpawn(t, x, y) ? 16 : 0) | (inSpawn(1 - t, x, y) ? 32 : 0);
        }
        for (const c of order) M.mk_add_camp(t, gindex.get(c.gh), c.x, c.y, c.type);
        for (let g = 0; g < nGroups; g++) M.mk_set_group(t, g, groups[g].gold, groups[g].gems, groups[g].respawn);
        M.mk_map_finish(t);
      }

      // ---- who is imitated ----
      const info = item.info;
      const names = info.source === 'top' ? [info.teamA, info.teamB]
        : (info.ourSide === 'a' ? ['DOOMSDAY', info.opponent] : [info.opponent, 'DOOMSDAY']);
      const teamId = names.map(n => teamNames.indexOf(n));
      const won = info.source === 'top' ? [info.winner === 'a' ? 1 : 0, info.winner === 'b' ? 1 : 0]
        : (info.ourSide === 'a' ? [info.win ? 1 : 0, info.win ? 0 : 1] : [info.win ? 0 : 1, info.win ? 1 : 0]);
      const imitated = opts.parity ? [true, true] : [0, 1].map(t => names[t] !== 'DOOMSDAY' && teamId[t] >= 0);
      const observed = opts.observed ? JSON.parse(fs.readFileSync(opts.observed, 'utf8')) : null;
      const sharedSnapshots = opts.sharedSnapshots ? JSON.parse(fs.readFileSync(opts.sharedSnapshots, 'utf8')) : null;
      const parityOut = [];
      if (opts.parity) {
        for (const t of [0, 1]) {
          M.mk_hash_map_parts(t);
          parityOut.push({ team: t, map: M.mk_hash_map(t) >>> 0, parts: [...new Uint32Array(kmem(), M.mk_ibuf(), 4)], dump: cstrK(M.mk_dump_map(t)) });
          for (let g = -2; g < nGroups; g++) parityOut.push({ team: t, field: g, hash: M.mk_hash_field(t, g) >>> 0 });
        }
      }

      const P = (team, c) => E.perspective(team, c);
      const champGet = (team, viewer, id) => {
        if (X.Game_API_Champion_Get(E.h, P(team, viewer), id, E.buf) !== 0) return null;
        return { team: i32(E.buf), type: i32(E.buf + 4), x: i32(E.buf + 8), y: i32(E.buf + 12), hp: f32(E.buf + 16),
          max: f32(E.buf + 20), str: f32(E.buf + 24), focus: f32(E.buf + 28), range: i32(E.buf + 36), state: u32(E.buf + 40) };
      };
      const teamOf = new Map();
      const idOf = (c) => {
        if (!teamOf.has(c)) { check(X.Game_API_Champion_GetIdentity(E.h, P(2, NONE), c, E.out)); teamOf.set(c, i32(E.out)); }
        return teamOf.get(c);
      };

      // ---- pass 1: turns and actions ----
      const timeline = () => {
        check(X.Game_Visualiser_Timeline_GetMain(E.h, E.out)); const main = dv().getBigUint64(E.out, true);
        check(X.Game_Visualiser_Timeline_Info(E.h, main, E.args, E.args + 8, E.args + 16));
        const size = u32(E.args);
        check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
        return size;
      };
      const read = () => {
        check(X.Game_Visualiser_ReadTimelineState(E.h, E.tsnap));
        const T = E.tsnap;
        return { round: u32(T + 8), awaiting: u32(T + 20) !== 0, phase: u32(T + 24), outcome: u32(T + 28), input: u32(T + 56),
          current: u32(T + 60), kind: u32(T + 68), actorKind: u32(T + 72), actor: u32(T + 76), tx: i32(T + 88), ty: i32(T + 92),
          substep: u32(T + 104), slot: u32(T + 108) };
      };
      const turns = [], turnKey = new Map(), byChamp = new Map(), abil = new Map(), dbg = [];
      let size = timeline(), cur = null, lastKey = '', drafts = null;
      for (;;) {
        const st = read();
        if (st.phase === PHASE_CHAMPIONS && st.awaiting && st.current !== NONE && `${st.round}:${st.current}` !== lastKey) {
          lastKey = `${st.round}:${st.current}`;
          const c = st.current, team = idOf(c), me = champGet(team, c, c);
          const full = E.PC.I(dv(), E.tsnap);
          if (!drafts) drafts = full.drafts;
          if (!abil.has(c)) {
            check(X.Game_Visualiser_ReadState(E.h, P(team, c), E.snap));
            const view = E.PC.F(dv(), E.snap), v = view.champions.find(o => o.entity.index === c);
            abil.set(c, (v?.abilityProps ?? []).map(p => ({ kind: p.type, excl: (p.attributes & 1) !== 0, range: p.range ?? 0, radius: p.radius ?? 0 })));
          }
          const where = new Map();
          for (const o of full.champions) if (o.alive && o.position) where.set(o.position.y * w + o.position.x, { id: o.entity.index, team: o.team });
          const alive = !!me && (me.state & 1) === 1 && me.x >= 0;
          let capture = -1;
          if (alive) {
            const ct = campAt.get(me.y * w + me.x);
            if (ct) { const g = gindex.get(ct.gh); if (full.groups[g]?.rewardAvailable) capture = g; }
          }
          cur = { i: turns.length, c, team, round: st.round, alive, x: me?.x ?? -1, y: me?.y ?? -1, state: me?.state ?? 0,
            onSpawn: alive && inSpawn(team, me.x, me.y), capture, acts: [], where };
          turns.push(cur); turnKey.set(lastKey, cur.i);
          if (!byChamp.has(c)) byChamp.set(c, []);
          byChamp.get(c).push(cur.i);
        }
        if (cur && st.actorKind === 1 && st.actor === cur.c && st.phase === PHASE_CHAMPIONS &&
            [K.MOVE, K.ATTACK, K.CAST, K.RECALL, K.SUBMIT, K.CANCEL].includes(st.kind)) {
          if (st.kind === K.CANCEL) cur.cancelState = champGet(cur.team, cur.c, cur.c)?.state;
          const a = { kind: st.kind, x: st.tx, y: st.ty, slot: st.slot };
          if (st.kind === K.ATTACK || st.kind === K.CAST) {
            const u = cur.where.get(st.ty * w + st.tx);
            if (u && u.team !== cur.team) a.champ = u.id;
            else if (u) a.ally = u.id;
            else if (!u) { const ct = campAt.get(st.ty * w + st.tx); if (ct) a.camp = ct.k; }
            if (st.kind === K.ATTACK && a.champ === undefined && a.camp === undefined && dbg.length < 6)
              dbg.push({ round: st.round, c: cur.c, team: cur.team, tile: [st.tx, st.ty], u, me: [cur.x, cur.y],
                camps: camps.filter(q => Math.max(Math.abs(q.x - st.tx), Math.abs(q.y - st.ty)) <= 2).map(q => [q.k, q.x, q.y, q.type]),
                tl: E.PC.I(dv(), E.tsnap).camps.filter(q => q.position && Math.max(Math.abs(q.position.x - st.tx), Math.abs(q.position.y - st.ty)) <= 1).map(q => [q.entity.index, q.position.x, q.position.y, q.health]),
                near: [...cur.where.entries()].map(([k, v]) => [k % w, Math.floor(k / w), v.id, v.team]).filter(q => Math.max(Math.abs(q[0] - st.tx), Math.abs(q[1] - st.ty)) <= 2) });
          }
          cur.acts.push(a);
        }
        if (st.outcome || (st.awaiting && st.input >= size)) break;
        check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
      }
      for (const t of turns) t.where = null;
      // Side check: team 0 is side a.
      if (info.source === 'top' && drafts && JSON.stringify(drafts[0].filter(x => x >= 0)) !== JSON.stringify(info.picksA)) throw new Error('side mismatch: drafts ' + JSON.stringify(drafts) + ' vs picksA ' + JSON.stringify(info.picksA));

      // ---- events and labels ----
      const isDash = (c, slot) => abil.get(c)?.[slot]?.kind === DASH;
      for (const t of turns) {
        t.events = [];
        if (!t.alive) continue;
        if (t.capture >= 0) t.events.push({ o: O.FARM, arg: t.capture });
        for (const a of t.acts) {
          if (a.kind === K.ATTACK || (a.kind === K.CAST && !isDash(t.c, a.slot))) {
            if (a.champ !== undefined) t.events.push({ o: O.FIGHT, arg: a.champ });
            else if (a.camp !== undefined) t.events.push({ o: O.FARM, arg: gindex.get(campByK.get(a.camp).gh) });
          } else if (a.kind === K.SUBMIT) t.events.push({ o: O.BANK, arg: -1 });
        }
      }
      for (const list of byChamp.values()) {
        for (let k = 1; k < list.length; k++) {
          const t = turns[list[k]], p = turns[list[k - 1]];
          t.prev = p;
          p.next = t;
          if (t.alive && p.alive && t.onSpawn && !p.onSpawn) t.home = true;
        }
        // Next event, scanning forward.
        let nextEv = null, nextRound = 0, nextIdx = -1;
        for (let k = list.length - 1; k >= 0; k--) {
          const t = turns[list[k]];
          if (!t.alive) { nextEv = null; t.label = null; continue; }
          // label at t: own events first, else the home arrival or events of later turns
          if (t.events.length) t.label = t.events[0];
          else if (nextEv && nextRound - t.round <= HORIZON) t.label = nextEv;
          else t.label = null;
          // what earlier turns see from t onwards
          if (t.events.length) { nextEv = t.events[0]; nextRound = t.round; nextIdx = k; }
          else if (t.home) { nextEv = { o: O.HOME, arg: -1 }; nextRound = t.round; nextIdx = k; }
        }
        for (const i of list) {
          const t = turns[i];
          const first = t.acts[0];
          t.trick = !!(first && first.kind === K.CANCEL && (t.state & 2));
          if (t.trick && t.cancelState === undefined) throw new Error(`missing post-cancel state ${t.round}:${t.c}`);
          t.actionState = t.trick ? t.cancelState : t.state;
          t.realRecall = t.acts.some(a => a.kind === K.RECALL) && !!t.next && t.next.alive && (t.next.state & 2) !== 0 &&
            !(t.next.acts[0] && t.next.acts[0].kind === K.CANCEL);
        }
        // Trips: a walk that keeps getting closer to the altars and ends in a tribute is a bank trip, and one that ends
        // on the own spawn a trip home, even where the next event alone would say otherwise. Walking back from the
        // arrival, every turn whose distance is not below the next one's (and that hits no camp or champion) gets the
        // trip's label, up to TRIP_MAX steps of distance.
        const hits = t => t.acts.some(a => a.kind === K.ATTACK || (a.kind === K.CAST && !isDash(t.c, a.slot)));
        const dist = (t, kind) => (t.alive ? M.mk_static_distance(t.team, kind, t.x, t.y) : 300);
        for (let k = 0; k < list.length; k++) {
          const end = turns[list[k]];
          const kind = end.acts.some(a => a.kind === K.SUBMIT) ? O.BANK : (end.home ? O.HOME : -1);
          if (kind < 0) continue;
          const dEnd = dist(end, kind);
          let dNext = dEnd;
          for (let j = k - 1; j >= 0; j--) {
            const t = turns[list[j]];
            if (!t.alive || hits(t) || t.acts.some(a => a.kind === K.SUBMIT)) break;
            const d = dist(t, kind);
            if (d < dNext || d - dEnd > TRIP_MAX || end.round - t.round > HORIZON) break;
            t.label = { o: kind, arg: -1 };
            t.trip = true;
            dNext = d;
          }
        }
      }

      // ---- pass 2: observations, kernel features, rows ----
      for (let s = 0; s < 16; s++) M.mk_mem_reset(s);
      M.mk_shared_reset();
      const allyIds = [0, 1].map(t => [...teamOf.entries()].filter(([, tm]) => tm === t).map(([c]) => c).sort((a, b) => a - b));
      // Every champion that ever took a turn is known; make sure the full roster is there.
      for (const t of [0, 1]) {
        const any = allyIds[t][0];
        if (any === undefined) continue;
        check(X.Game_API_Champion_GetAllies(E.h, P(t, any), E.buf + 512, 32, E.out));
        allyIds[t] = [...new Uint32Array(X.memory.buffer, E.buf + 512, u32(E.out))].sort((a, b) => a - b);
      }
      const rank = (t, c) => allyIds[t].indexOf(c);
      const counters = { turns: 0, obj: 0, objMiss: 0, move: 0, moveMiss: 0, tgt: 0, tgtMiss: 0, recall: 0, trib: 0, cast: 0, castMiss: 0, slotWrites: 0 };
      const feat = () => new Float32Array(kmem(), M.mk_feat(), 107 * NF.obj); // kMaxObj x NF_OBJ, the largest block
      const ibuf = () => new Int32Array(kmem(), M.mk_ibuf(), 107 * 5);
      size = timeline(); lastKey = '';
      let curT = null, lastEnd = '';
      for (;;) {
        const st = read();
        if (st.phase === PHASE_CHAMPIONS && st.awaiting && st.current !== NONE && `${st.round}:${st.current}` !== lastKey) {
          lastKey = `${st.round}:${st.current}`;
          const ti = turnKey.get(lastKey);
          curT = ti === undefined ? null : turns[ti];
          if (curT && imitated[curT.team] && curT.alive && (!observed || (observed[curT.c] ?? []).includes(curT.round))) {
            emit(curT); counters.turns++;
          }
        }
        // End of a champion's turn: it writes its shared-memory slot (as the bot does at the end of every turn).
        if (st.actorKind === 1 && st.kind === K.END && `${st.round}:${st.actor}` !== lastEnd) {
          lastEnd = `${st.round}:${st.actor}`;
          const c = st.actor, team = idOf(c), me = champGet(team, c, c);
          const alive = !!me && (me.state & 1) === 1 && me.x >= 0;
          const r = rank(team, c);
          if (r >= 0 && r < 6) { M.mk_write_slot(team, r, alive ? me.x : 0, alive ? me.y : 0, alive ? 1 : 0); counters.slotWrites++; }
        }
        if (st.outcome || (st.awaiting && st.input >= size)) break;
        check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
      }
      const submits = turns.filter(t => t.acts.some(a => a.kind === K.SUBMIT)).length;
      if (opts.parity) fs.writeFileSync(opts.parity, parityOut.map(r => JSON.stringify(r)).join('\n') + '\n');
      return { match: item.match, map: info.map, turns: turns.length, submits, dbg, ...counters, teams: names, imitated };

      function emit(t) {
        const team = t.team, c = t.c, Pc = P(team, c);
        const me = champGet(team, c, c);
        check(X.Game_API_Champion_GetGems(E.h, Pc, c, E.out)); const gems = u32(E.out);
        check(X.Game_API_Champion_GetGold(E.h, Pc, c, E.out)); const gold = u32(E.out);
        const ab = abil.get(c) ?? [];
        const cd = [0, 1].map(s => (X.Game_API_Champion_GetCooldown(E.h, Pc, c, s, E.out) === 0 ? i32(E.out) : 0));
        M.mk_obs_self(t.round, c, me.type, me.x, me.y, me.hp, me.max, me.str, me.focus, me.range, gems, gold, t.actionState,
          ab[0]?.kind ?? 0, ab[1]?.kind ?? 0, cd[0], cd[1]);
        M.mk_obs_abilities(ab[0]?.range ?? 0, ab[0]?.radius ?? 0, ab[0]?.excl ? 1 : 0, ab[1]?.range ?? 0, ab[1]?.radius ?? 0,
          ab[1]?.excl ? 1 : 0);
        for (const [fn, enemy] of [[X.Game_API_Champion_GetAllies, 0], [X.Game_API_Champion_GetEnemies, 1]]) {
          check(fn(E.h, Pc, E.buf + 512, 32, E.out));
          const ids = [...new Uint32Array(X.memory.buffer, E.buf + 512, u32(E.out))];
          for (const id of ids) {
            if (id === c) continue;
            const u = champGet(team, c, id);
            if (!u || (u.state & 1) === 0 || u.x < 0) continue;
            const g = X.Game_API_Champion_GetGems(E.h, Pc, id, E.out) === 0 ? u32(E.out) : 0;
            M.mk_obs_unit(enemy, id, u.type, u.x, u.y, u.hp, u.max, u.str, u.range, g, u.state);
          }
        }
        for (const cp of order) {
          if (X.Game_API_Camp_Get(E.h, Pc, cp.k, E.buf) !== 0) continue;
          const hp = f32(E.buf + 8);
          check(X.Game_API_Camp_GetState(E.h, Pc, cp.k, E.out)); const s = u32(E.out);
          if (s === 0) continue;
          M.mk_obs_camp(myIdx.get(cp.k), hp, s === 1 ? 1 : 0);
        }
        for (let g = 0; g < nGroups; g++) {
          if (X.Game_API_CampGroup_GetState(E.h, Pc, ghandles[g], E.out) !== 0) continue;
          const s = u32(E.out);
          if (s < 1 || s > 3) continue;
          let timer = 0;
          if (s === 3 && X.Game_API_CampGroup_GetCooldown(E.h, Pc, ghandles[g], E.out) === 0) timer = i32(E.out);
          M.mk_obs_group(g, s, timer);
        }
        const ids = allyIds[team];
        if (opts.sharedSnapshots) {
          const snapshot = sharedSnapshots[`${t.round}:${c}`];
          if (!snapshot) throw new Error(`missing shared snapshot ${t.round}:${c}`);
          M.mk_shared_snapshot(team, snapshot[0], snapshot[1]);
        }
        M.mk_add_remembered(team, Math.min(6, ids.length), ...[0, 1, 2, 3, 4, 5].map(k => ids[k] ?? -1));
        M.mk_observe(team, c);
        if (opts.parity) {
          M.mk_hash_obs_parts();
          const parts = [...new Uint32Array(kmem(), M.mk_ibuf(), 5)];
          const dump = t.round <= 150 ? cstrK(M.mk_dump_obs()) : undefined;
          parityOut.push({ round: t.round, c, obs: M.mk_hash_obs() >>> 0, mem: M.mk_hash_memory(team, c) >>> 0, dec: M.mk_hash_decisions(team, c) >>> 0, parts, dump });
          M.mk_end_observe(c);
          return;
        }

        const metaRow = (extra = 0) => Int32Array.from([teamId[team], me.type, t.round, c, won[team], item.n, extra]);
        const channel = (t.state & 6) !== 0 && !t.trick;
        const canMove = (t.actionState & 8) !== 0, canAttack = (t.actionState & 16) !== 0, canCast = (t.actionState & 2048) !== 0;
        let L = t.label;
        // A fight label needs the enemy in view now; otherwise the objective is unknown for this turn's features.
        const Lvis = L && (L.o !== O.FIGHT || M.mk_objective_distance(team, O.FIGHT, L.arg, t.x, t.y) < 300);
        const tag = `${item.match}:${c}:${t.round}`;
        // objective
        if (!channel && L && keep(tag + ':o', opts.objRate)) {
          const n = M.mk_objectives(team, c), ib = ibuf();
          let lab = -1;
          const cand = new Int32Array(2 * n);
          for (let i = 0; i < n; i++) {
            cand[2 * i] = ib[2 * i]; cand[2 * i + 1] = ib[2 * i + 1];
            if (ib[2 * i] === L.o && (L.o === O.BANK || L.o === O.HOME || ib[2 * i + 1] === L.arg)) lab = i;
          }
          if (lab >= 0) { rows.obj.add(feat(), n, lab, metaRow(L.o), cand); counters.obj++; } else { counters.objMiss++; counters['objMiss' + L.o] = (counters['objMiss' + L.o] ?? 0) + 1; }
        }
        // first movement and first basic attack of the turn
        let px = t.x, py = t.y, move = null, attack = null, blocked = false;
        for (const a of t.acts) {
          if (a.kind === K.RECALL || a.kind === K.SUBMIT) { if (!move) blocked = true; continue; }
          const dash = a.kind === K.CAST && ab[a.slot]?.kind === DASH;
          if (a.kind === K.MOVE || dash) {
            if (!move) move = { x: a.x, y: a.y, dash, afterAttack: !!attack };
            px = a.x; py = a.y;
          } else if (a.kind === K.ATTACK) {
            if (!attack) attack = { champ: a.champ, camp: a.camp, x: px, y: py, beforeMove: !move };
          } else if (a.kind === K.CAST && ab[a.slot]?.excl && !move) blocked = true;
        }
        const ranged = me.range > 1;
        const dashReady = canCast && ab.some((p, s) => p.kind === DASH && cd[s] <= 0) ? 1 : 0;
        // move
        if (!channel && canMove && L && Lvis && !blocked && !(ranged && attack && attack.beforeMove) && keep(tag + ':m', opts.moveRate)) {
          const n = M.mk_moves(team, c, L.o, L.arg, dashReady), ib = ibuf();
          const tx = move ? move.x : t.x, ty = move ? move.y : t.y;
          let lab = -1;
          for (let i = 0; i < n; i++) {
            if (ib[3 * i] !== tx || ib[3 * i + 1] !== ty) continue;
            if (lab < 0 || (!!ib[3 * i + 2] === !!move?.dash)) lab = i;
          }
          if (lab >= 0) { rows.move.add(feat(), n, lab, metaRow(move ? (move.dash ? 2 : 1) : 0)); counters.move++; } else counters.moveMiss++;
        }
        // target
        if (!channel && canAttack && L && Lvis) {
          const ax = attack ? attack.x : t.x, ay = attack ? attack.y : t.y;
          const n = M.mk_targets(team, c, L.o, L.arg, ax, ay), ib = ibuf();
          if (n > 1) {
            let lab = -1;
            if (!attack) lab = 0;
            else for (let i = 1; i < n; i++) {
              if (ib[2 * i] === 1 && attack.champ !== undefined && ib[2 * i + 1] === attack.champ) lab = i;
              if (ib[2 * i] === 2 && attack.camp !== undefined && ib[2 * i + 1] === myIdx.get(attack.camp)) lab = i;
            }
            if (lab >= 0) { rows.tgt.add(feat(), n, lab, metaRow(attack ? 1 : 0)); counters.tgt++; }
            else {
              counters.tgtMiss++;
              const why = attack.champ !== undefined ? 'champ' : attack.camp !== undefined ? 'camp' : 'other';
              counters['tgtMiss_' + why] = (counters['tgtMiss_' + why] ?? 0) + 1;
              if (why === 'camp' && !counters.ex) counters.ex = { round: t.round, c, at: [ax, ay], camp: campByK.get(attack.camp), n, start: [t.x, t.y], acts: t.acts };
            }
          }
        }
        // cast: the turn's first spell other than the dash, from where the champion stood when it cast
        if (!channel && canCast && L && Lvis && keep(tag + ':c', opts.castRate)) {
          let cx = t.x, cy = t.y, cast = null;
          for (const a of t.acts) {
            const isDashCast = a.kind === K.CAST && ab[a.slot]?.kind === DASH;
            if (a.kind === K.MOVE || isDashCast) { cx = a.x; cy = a.y; continue; }
            if (a.kind === K.CAST) { cast = { ...a, px: cx, py: cy }; break; }
          }
          const ox = cast ? cast.px : t.x, oy = cast ? cast.py : t.y;
          const n = M.mk_casts(team, c, L.o, L.arg, ox, oy), ib = ibuf();
          if (n > 1) {
            let lab = cast ? -1 : 0, best = 99;
            if (cast) for (let i = 1; i < n; i++) {
              if (ib[5 * i] !== cast.slot) continue;
              const tk = ib[5 * i + 1], id = ib[5 * i + 2];
              if (ab[cast.slot]?.kind === 3) { // area: the candidate tile nearest the aimed tile, within the radius
                const dd = Math.max(Math.abs(ib[5 * i + 3] - cast.x), Math.abs(ib[5 * i + 4] - cast.y));
                if (dd <= (ab[cast.slot].radius ?? 0) && dd < best) { best = dd; lab = i; }
              } else if (tk === 4 || (tk === 1 && cast.champ === id) || (tk === 3 && cast.ally === id) ||
                         (tk === 2 && cast.camp !== undefined && myIdx.get(cast.camp) === id)) { lab = i; break; }
            }
            if (lab >= 0) { rows.cast.add(feat(), n, lab, metaRow(cast ? ab[cast.slot]?.kind ?? 0 : 0)); counters.cast++; }
            else counters.castMiss++;
          }
        }
        // recall
        if (!channel && !t.onSpawn && canMove) {
          M.mk_recall(team, c);
          rows.recall.add(feat(), 1, t.realRecall ? 1 : 0, metaRow()); counters.recall++;
        }
        // tribute
        // tribute: where the champion stands after its moves (it usually walks next to the altar and tributes at once)
        if (!channel && gems > 0 && nextToAltar(px, py)) {
          M.mk_tribute(team, c);
          rows.trib.add(feat(), 1, t.acts.some(a => a.kind === K.SUBMIT) ? 1 : 0, metaRow()); counters.trib++;
        }
        M.mk_end_observe(c);
      }
      function nextToAltar(x, y) {
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          const nx = x + dx, ny = y + dy;
          if (nx >= 0 && ny >= 0 && nx < w && ny < h && altar[ny * w + nx]) return true;
        }
        return false;
      }
    } finally {
      E.destroy();
    }
  }
}

async function main() {
  const opts = args();
  if (fs.existsSync(opts.out) && fs.readdirSync(opts.out).length) throw new Error('use a fresh output directory: ' + opts.out);
  fs.mkdirSync(opts.out, { recursive: true });
  const kernelSha256 = createHash('sha256').update(fs.readFileSync(KERNEL)).digest('hex');
  const index = JSON.parse(fs.readFileSync(opts.index, 'utf8'));
  const plan = JSON.parse(fs.readFileSync(opts.teams, 'utf8'));
  const tops = Object.values(index).filter(v => v.source === 'top').flatMap(v => [v.teamA, v.teamB]);
  const teamNames = [...new Set([...plan.groups.map(g => g.opponent), ...tops])].sort();
  let items = Object.entries(index).filter(([m]) => fs.existsSync(path.join(opts.replays, m + '.repl26a')))
    .filter(([m]) => !opts.only || m === opts.only).sort(([a], [b]) => a.localeCompare(b))
    .map(([match, info], n) => ({ match, info, n, file: path.join(opts.replays, match + '.repl26a') }));
  if (opts.limit) items = items.slice(0, opts.limit);
  const nw = Math.max(1, Math.min(opts.workers, items.length));
  const parts = Array.from({ length: nw }, () => []);
  items.forEach((it, i) => parts[i % nw].push(it));
  let done = 0;
  const all = [];
  await Promise.all(parts.map((files, id) => new Promise((resolve, reject) => {
    const wk = new Worker(fileURLToPath(import.meta.url), { workerData: { files, opts, teamNames, id } });
    wk.on('message', m => {
      if (m.progress) { done++; if (done % 50 === 0) console.log(`replays ${done}/${items.length}`); }
      if (m.done) { all.push(...m.done); resolve(); }
    });
    wk.on('error', reject);
    wk.on('exit', code => { if (code) reject(new Error('worker exit ' + code)); });
  })));
  all.sort((a, b) => a.match.localeCompare(b.match));
  fs.writeFileSync(path.join(opts.out, 'manifest.json'), JSON.stringify({ teamNames, features: NF, kernelSha256,
    items: items.map(i => ({ match: i.match, n: i.n, map: i.info.map, source: i.info.source })), stats: all }, null, 1));
  const err = all.filter(s => s.error);
  const sum = k => all.reduce((a, s) => a + (s[k] ?? 0), 0);
  console.log(JSON.stringify({ replays: all.length, errors: err.length, turns: sum('turns'), obj: sum('obj'), objMiss: sum('objMiss'),
    move: sum('move'), moveMiss: sum('moveMiss'), tgt: sum('tgt'), tgtMiss: sum('tgtMiss'), recall: sum('recall'), trib: sum('trib'), cast: sum('cast'), castMiss: sum('castMiss') }));
  if (err.length) console.log('first error:', err[0].match, err[0].error.slice(0, 800));
  if (err.length) process.exitCode = 1;
}

if (isMainThread) await main(); else await workerMain();
