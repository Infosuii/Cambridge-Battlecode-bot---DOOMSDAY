// Behaviour-cloning rows for the policy-v2 engage, combat and move heads from official replays (engine 1.0.3, read-only).
//
// At each sampled champion turn the acting champion's observation is built from the same Game_API_* calls the bot
// makes at runtime (perspective = that champion), following bot/src/nn_policy_capture.cpp, and its move candidates
// follow bot/src/nn_policy_tactics.cpp (walk tiles from the engine's own movement mask, dash tiles, hold; narrowed to
// 16 by kind x canonical octant, nearest to the goal). The label is the champion's actual first movement that turn.
// Raw (unnormalised) values are written; tools/replay/bc_dataset.py normalises them with the policy-v2 schema.
//
// Bot-internal inputs have no replay equivalent and use fixed rules:
//   goal  = the champion's own position ~GOAL_ROUNDS later (hindsight destination)
//   role  = carrier (carrying gems, submits within 40 rounds) > fighter (attacks a champion within 10 rounds)
//           > farmer (attacks a camp within 10 rounds) > escort (a visible ally carrying gems within 3 tiles) > scout
//   hot_zone = 0; ally shared-claim code = 127 (the bot's own "no mapping" value)
//   engage/context = fight (attacks an enemy champion this turn) -> 1, disengage (moves away from the nearest
//           visible enemy within 8) -> 2, otherwise 0
//
// Usage: node --no-warnings tools/replay/bc_extract.mjs --out <dir> [--rate 0.05] [--workers N] [--shard-size N] <replays|dirs>
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { Worker, isMainThread, parentPort, workerData } from 'node:worker_threads';
import { engine, defaultAssets, verifyAssets, PINNED } from './engine.mjs';
import { RowShardWriter } from './npz_write.mjs';

const FORMAT = 'bc-raw-v3', STRATEGY_HEAD = 1, OBJECTIVE_HEAD = 2, ROLE_HEAD = 3, BANK_HEAD = 4, MOVE_HEAD = 6, COMBAT_HEAD = 7, ENGAGE_HEAD = 8,
  HEAD_LABEL = { 1: 'strategy', 2: 'objective', 3: 'role', 4: 'bank' }, GOAL_ROUNDS = 10, MAX_ROUNDS = 2000, UNREACH = 65535, NONE = 10000;
const PHASE_CHAMPIONS = 10, NO_CHAMPION = 0xFFFFFFFF, DASH = 6, GROUND = 16, CLAIM_IDLE = 127;
const K_WALK = 0, K_HOLD = 3, MAX_K = 16;
const WIDTHS = { obs_self: [40, Float32Array], obs_ally: [50, Float32Array], ally_mask: [5, Uint8Array], obs_enemy: [72, Float32Array],
  enemy_mask: [6, Uint8Array], cand_feat: [MAX_K * 12, Float32Array], cand_id: [MAX_K, Uint32Array], cand_legal: [MAX_K, Uint8Array],
  cand_k: [1, Uint8Array], label: [1, Int16Array], context: [1, Uint8Array], head: [1, Uint8Array], info: [6, Int32Array] };
// info columns: team, champion, round, won (1/0), flags (bit0 relabelled to its octant representative,
// bit1 combat preceded the move this turn), label movement kind (-1 none)

const cheb = (ax, ay, bx, by) => Math.max(Math.abs(ax - bx), Math.abs(ay - by));
function octant(x, y) {
  if (x === 0 && y === 0) return 0;
  const ax = Math.abs(x), ay = Math.abs(y);
  if (2 * ax < ay) return y > 0 ? 0 : 4;
  if (2 * ay < ax) return x > 0 ? 2 : 6;
  return y > 0 ? (x > 0 ? 1 : 7) : (x > 0 ? 3 : 5);
}
function fnv(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619) >>> 0; return h; }

function bfs(w, h, blocked, roots, limit = Infinity) {
  const dist = new Uint16Array(w * h).fill(UNREACH), queue = new Int32Array(w * h); let head = 0, tail = 0;
  for (const i of roots) if (dist[i] === UNREACH) { dist[i] = 0; queue[tail++] = i; }
  while (head < tail) {
    const i = queue[head++], x = i % w, y = (i / w) | 0, d = dist[i] + 1;
    if (d > limit) continue;
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
      const nx = x + dx, ny = y + dy;
      if ((dx || dy) && nx >= 0 && ny >= 0 && nx < w && ny < h) {
        const j = ny * w + nx;
        if (!blocked[j] && dist[j] === UNREACH) { dist[j] = d; queue[tail++] = j; }
      }
    }
  }
  return dist;
}

function readBoard(E, w, h, stride, getter) {
  const { X, dv, check } = E;
  check(getter(E.h, E.out)); const p = dv().getUint32(E.out, true), d = dv(), out = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const word = d.getBigUint64(p + 8 * ((y >> 3) * stride + (x >> 3)), true);
    out[y * w + x] = Number((word >> BigInt((y & 7) * 8 + (x & 7))) & 1n);
  }
  return out;
}

function extract(E, file, rate) {
  const { X, dv, check, PC } = E;
  E.load(fs.readFileSync(file));
  const name = path.basename(file);
  try {
    check(X.Game_Visualiser_Timeline_GetMain(E.h, E.out)); const main = dv().getBigUint64(E.out, true);
    check(X.Game_Visualiser_Timeline_Info(E.h, main, E.args, E.args + 8, E.args + 16)); const size = dv().getUint32(E.args, true);
    const meta = X.Engine_Malloc(64); check(X.Game_GetBitboardMetadata(E.h, meta));
    const w = dv().getInt32(meta, true), h = dv().getInt32(meta + 4, true), stride = dv().getUint32(meta + 16, true);
    // The metadata record is 20 bytes; a bitboard is chunk_stride x chunked_height 64-bit chunks.
    const maskBytes = Math.max(4096, stride * dv().getUint32(meta + 12, true) * 8), mask = X.Engine_Malloc(maskBytes);
    const wall = readBoard(E, w, h, stride, X.Game_GetWallBuffer), hole = readBoard(E, w, h, stride, X.Game_GetHoleBuffer);
    const altar = readBoard(E, w, h, stride, X.Game_GetAltarBuffer), bush = readBoard(E, w, h, stride, X.Game_GetBushBuffer);
    check(X.Game_API_Map_GetSymmetry(E.h, E.out)); const sym = dv().getInt32(E.out, true);
    const team = [0, 1].map(t => {
      check(X.Game_API_GetSpawnRegion(E.h, t, E.out));
      const [x0, y0, x1, y1] = [0, 4, 8, 12].map(o => dv().getInt32(E.out + o, true));
      return { x0, y0, x1, y1, s2x: x0 + x1 - 1, s2y: y0 + y1 - 1 };
    });
    const inSpawn = (s, x, y) => x >= s.x0 && x < s.x1 && y >= s.y0 && y < s.y1;
    for (const t of [0, 1]) {
      const s = team[t], flip = sym === 0 ? (s.s2x !== w - 1 ? s.s2x > w - 1 : t === 1) : sym === 1 ? (s.s2y !== h - 1 ? s.s2y > h - 1 : t === 1)
        : sym === 2 ? (s.s2x !== w - 1 ? s.s2x > w - 1 : (s.s2y !== h - 1 ? s.s2y > h - 1 : t === 1)) : false;
      s.fx = flip && (sym === 0 || sym === 2); s.fy = flip && (sym === 1 || sym === 2);
      const other = team[1 - t] ?? null; s.blocked = new Uint8Array(w * h);
      for (let i = 0; i < w * h; i++) s.blocked[i] = wall[i] | hole[i] | altar[i];
      s.otherIndex = 1 - t;
    }
    for (const t of [0, 1]) {
      const s = team[t], o = team[1 - t], roots = [];
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { if (inSpawn(o, x, y)) s.blocked[y * w + x] = 1; }
      for (let y = s.y0; y < s.y1; y++) for (let x = s.x0; x < s.x1; x++) if (x >= 0 && y >= 0 && x < w && y < h) roots.push(y * w + x);
      s.spawnField = bfs(w, h, s.blocked, roots);
    }
    const cx = (t, x) => team[t].fx ? w - 1 - x : x, cy = (t, y) => team[t].fy ? h - 1 - y : y;
    const ddx = (t, v) => team[t].fx ? -v : v, ddy = (t, v) => team[t].fy ? -v : v;
    const moveId = (kind, x, y) => kind * 2 ** 30 + y * 2 ** 15 + x;

    const info = E.buf, I = (o) => dv().getInt32(info + o, true), F = (o) => dv().getFloat32(info + o, true);
    const champGet = (P, c) => X.Game_API_Champion_Get(E.h, P, c, info) === 0 ? { team: I(0), type: I(4), x: I(8), y: I(12), hp: F(16),
      max: F(20), str: F(24), focus: F(28), speed: I(32), range: I(36), state: I(40) } : null;
    const u32 = (fn, ...a) => fn(E.h, ...a, E.out) === 0 ? dv().getUint32(E.out, true) : null;
    const handles = (fn, P) => { if (fn(E.h, P, E.buf + 512, 32, E.out)) return []; const n = Math.min(32, dv().getUint32(E.out, true)); return [...new Uint32Array(X.memory.buffer, E.buf + 512, n)]; };

    // Static macro geometry: camp groups (rewards, camps, anchor), camp tiles, altars and game constants.
    check(X.Game_GetNumCamps(E.h, E.out)); const numCamps = dv().getUint32(E.out, true);
    const campInfo = [], campGroup = [], campAt = new Map();
    for (let k = 0; k < numCamps; k++) {
      check(X.Game_API_Map_CampInfo_Get(E.h, k, E.out));
      campInfo.push({ x: dv().getInt32(E.out, true), y: dv().getInt32(E.out + 4, true) });
      check(X.Game_API_Map_CampInfo_GetGroup(E.h, k, E.out)); campGroup.push(dv().getUint32(E.out, true));
      campAt.set(campInfo[k].y * w + campInfo[k].x, k);
    }
    check(X.Game_API_Map_GetNumCampGroups(E.h, E.out)); const numGroups = dv().getUint32(E.out, true);
    if (numGroups > 256) throw new Error('more than 256 camp groups'); // E.buf + 2048 holds 256 handles
    check(X.Game_API_Map_GetCampGroups(E.h, E.buf + 2048, 256, E.out));
    const groupHandles = [...new Uint32Array(X.memory.buffer, E.buf + 2048, numGroups)];
    const groups = groupHandles.map((handle) => {
      check(X.Game_API_Map_CampGroup_Get(E.h, handle, E.out));
      return { handle, gems: dv().getUint32(E.out, true), gold: dv().getUint32(E.out + 4, true),
               camps: campGroup.map((g, k) => g === handle ? k : -1).filter(k => k >= 0) };
    });
    const altars = [];
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (altar[y * w + x]) altars.push({ x, y });
    check(X.Game_Visualiser_GetConstants(E.args)); const K_ = (o, f = 'getInt32') => dv()[f](E.args + o, true);
    const consts = { submitBase: K_(24), submitMin: K_(28), capture: K_(32), submitRange: Math.floor(K_(48, 'getFloat32')), submitMult: K_(56, 'getFloat64') };
    const WINNING_GEMS = 1000;
    const campMem = [[], []], groupSeen = [new Map(), new Map()];
    const posHist = new Map(), acts = new Map(), sight = [new Map(), new Map()], turnsOut = [];
    let prev, steps = 0, current = null, outcome = 0, stats = { turns: 0, sampled: 0, skipped: 0 };
    const closeTurn = () => { current = null; };
    for (;;) {
      check(X.Game_Visualiser_ReadTimelineState(E.h, E.tsnap));
      const d = dv(), T = E.tsnap, u = (o) => d.getUint32(T + o, true), s32 = (o) => d.getInt32(T + o, true);
      const st = { round: u(8), awaiting: u(20) !== 0, phase: u(24), outcome: u(28), input: u(56), current: u(60), kind: u(68),
        actorKind: u(72), actor: u(76), tx: s32(88), ty: s32(92), substep: u(104), slot: u(108) };
      if (prev && st.input === prev.input && st.substep === prev.substep) throw new Error('timeline made no progress');
      // Champion actions: role hindsight, labels and engage.
      if (st.actorKind === 1 && (st.kind === 4 || st.kind === 5 || st.kind === 6 || st.kind === 11 || st.kind === 12)) {
        const c = st.actor, a = { round: st.round, kind: st.kind, x: st.tx, y: st.ty, slot: st.slot, target: 'other' };
        if ((st.kind === 5 || st.kind === 6) && current && current.c === c && current.enemies.some(e => e.x === st.tx && e.y === st.ty))
          a.target = 'champion';
        else if (st.kind === 5) { // basic attacks are hostile only: not an enemy champion means a camp
          a.target = 'camp';
          const k = campAt.get(st.ty * w + st.tx); if (k !== undefined) a.group = campGroup[k];
        }
        if (st.kind === 12 && current && current.c === c) a.from = current.pos;
        if (!acts.has(c)) acts.set(c, []);
        acts.get(c).push(a);
        if (current && current.c === c && current.rec) {
          const r = current.rec, isDash = st.kind === 6 && r.dashSlots.has(st.slot);
          if (!r.move && (st.kind === 4 || isDash)) r.move = { kind: st.kind === 4 ? K_WALK : st.slot + 1, x: st.tx, y: st.ty };
          if (st.kind === 5 || (st.kind === 6 && !isDash)) {
            if (!r.move) r.combatBefore = true;
            if (!r.combat) r.combat = { kind: st.kind === 5 ? 0 : st.slot + 1, x: st.tx, y: st.ty };
          }
          if ((st.kind === 5 || st.kind === 6) && a.target === 'champion') r.fight = true;
          if (st.kind === 12 && !r.submit) r.submit = { x: st.tx, y: st.ty };
        }
      }
      // A new champion turn.
      if (st.phase === PHASE_CHAMPIONS && st.awaiting && st.current !== NO_CHAMPION &&
          !(prev && prev.awaiting && prev.current === st.current && prev.round === st.round)) {
        closeTurn();
        const c = st.current;
        check(X.Game_API_Champion_GetIdentity(E.h, E.perspective(2, NO_CHAMPION), c, E.out));
        const t = dv().getInt32(E.out, true), P = E.perspective(t, c), me = champGet(P, c);
        stats.turns++;
        if (me && (me.state & 1)) {
          if (!posHist.has(c)) posHist.set(c, []);
          posHist.get(c).push({ round: st.round, x: me.x, y: me.y });
          const enemies = [];
          for (const e of handles(X.Game_API_Champion_GetEnemies, P)) {
            const v = champGet(P, e);
            if (v && (v.state & 1) && v.hp > 0) { enemies.push({ id: e, ...v }); sight[t].set(e, { round: st.round, x: v.x, y: v.y }); }
          }
          // Team camp memory (the bot's world model): last seen camp state and group sighting round.
          for (let k = 0; k < numCamps; k++) if (X.Game_API_Camp_Get(E.h, P, k, E.buf + 1024) === 0) {
            campMem[t][k] = { hp: dv().getFloat32(E.buf + 1032, true), str: dv().getFloat32(E.buf + 1040, true), round: st.round };
            groupSeen[t][campGroup[k]] = st.round;
          }
          current = { c, t, enemies, camps: [], rec: null, pos: { x: me.x, y: me.y } };
          const sampled = fnv(`${name}|${c}|${st.round}`) / 2 ** 32 < rate;
          if (sampled) {
            const view = (check(X.Game_Visualiser_ReadState(E.h, P, E.snap)), PC.F(dv(), E.snap));
            const self = view.champions.find(k => k.entity.index === c);
            if (!self || (self.channelTimer ?? 0) > 0) stats.skipped++;
            else {
              current.camps = view.camps.filter(k => k.position && (k.health ?? 0) > 0 && (k.strength?.effective ?? 0) > 0)
                .map(k => ({ x: k.position.x, y: k.position.y, range: k.attackRange ?? 0, str: k.strength.effective }));
              current.rec = sampleTurn(c, t, me, self, enemies, st.round, P);
              turnsOut.push(current.rec); stats.sampled++;
            }
          }
        }
      }
      prev = st; steps++;
      if (st.outcome || (st.awaiting && st.input >= size)) { outcome = st.outcome; break; }
      check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
    }
    X.Engine_Free(meta); X.Engine_Free(mask);
    return finalize(turnsOut, outcome);

    function sampleTurn(c, t, me, self, enemies, round, P) {
      const gems = u32(X.Game_API_Champion_GetGems, P, c) ?? 0, gold = u32(X.Game_API_Champion_GetGold, P, c) ?? 0;
      const ours = (check(X.Game_API_GetSubmittedGemCount(E.h, t, E.out)), Number(dv().getBigUint64(E.out, true)));
      const theirs = (check(X.Game_API_GetSubmittedGemCount(E.h, 1 - t, E.out)), Number(dv().getBigUint64(E.out, true)));
      const o = new Float32Array(40), p = { x: me.x, y: me.y }, maxHp = Math.max(1, me.max);
      o[0] = me.hp / maxHp; o[1] = me.hp; o[2] = me.max; o[3] = gems; o[4] = gold; o[5] = me.str; o[6] = me.focus; o[7] = me.range;
      o[8] = round; o[9] = Math.max(0, MAX_ROUNDS - round); o[10] = ours; o[11] = theirs;
      o[15] = (() => { const v = team[t].spawnField[p.y * w + p.x]; return v === UNREACH ? 10000 : v; })();
      const props = self.abilityProps ?? [], dashSlots = new Set(), cooldowns = [0, 0];
      for (let s = 0; s < 2; s++) {
        const k = props[s]?.type ?? 0, present = k !== 0 ? 1 : 0;
        o[18 + s] = present; o[34 + s] = present ? k : 0;
        if (present) { X.Game_API_Champion_GetCooldown(E.h, P, c, s, E.out); cooldowns[s] = dv().getInt32(E.out, true); o[16 + s] = cooldowns[s]; }
      }
      o[20] = 1; o[21] = (me.state >> 3) & 1; o[22] = (me.state >> 4) & 1; o[23] = (me.state >> 11) & 1; o[26] = 10000;
      let newest = null;
      for (const sg of sight[t].values()) {
        if (sg.round > round) continue;
        const a = cx(t, sg.x), b = cy(t, sg.y);
        if (!newest || sg.round > newest.round || (sg.round === newest.round && (a < newest.a || (a === newest.a && b < newest.b)))) newest = { ...sg, a, b };
      }
      if (newest) { o[24] = ddx(t, newest.x - p.x); o[25] = ddy(t, newest.y - p.y); o[26] = round - newest.round; }
      o[27] = bush[p.y * w + p.x]; o[28] = inSpawn(team[t], p.x, p.y) ? 1 : 0; o[31] = w; o[32] = h; o[33] = me.type;
      if (X.Game_API_Champion_GetWards(E.h, P, c, E.out) === 0) { o[37] = dv().getUint32(E.out, true); o[38] = dv().getInt32(E.out + 4, true); }
      const allies = [];
      for (const a of handles(X.Game_API_Champion_GetAllies, P)) {
        if (a === c) continue;
        const v = champGet(P, a);
        if (v && v.hp > 0) allies.push({ id: a, ...v, gems: u32(X.Game_API_Champion_GetGems, P, a) ?? 0 });
      }
      for (const a of allies) o[29] += cheb(a.x, a.y, p.x, p.y) <= 8;
      for (const e of enemies) o[30] += cheb(e.x, e.y, p.x, p.y) <= 8;
      const nearest = (list) => [...list].sort((a, b) => cheb(a.x, a.y, p.x, p.y) - cheb(b.x, b.y, p.x, p.y) || a.id - b.id);
      const allyRows = new Float32Array(50), allyMask = new Uint8Array(5), enemyRows = new Float32Array(72), enemyMask = new Uint8Array(6);
      nearest(allies).slice(0, 5).forEach((a, i) => {
        allyRows.set([ddx(t, a.x - p.x), ddy(t, a.y - p.y), a.hp / Math.max(1, a.max), a.hp, a.str, a.focus, a.range, a.type, a.gems, CLAIM_IDLE], i * 10);
        allyMask[i] = 1;
      });
      nearest(enemies).slice(0, 6).forEach((e, i) => {
        enemyRows.set([ddx(t, e.x - p.x), ddy(t, e.y - p.y), e.hp / Math.max(1, e.max), e.hp, e.str, e.focus, e.range, e.type,
                       u32(X.Game_API_Champion_GetGems, P, e.id) ?? 0, (e.state >> 1) & 1, (e.state >> 2) & 1, cheb(e.x, e.y, p.x, p.y)], i * 12);
        enemyMask[i] = 1;
      });
      // Movement candidates: engine movement mask (walk) and conservative dash reach (no path through units).
      const walk = [];
      if ((me.state >> 3) & 1) {
        check(X.Game_API_Champion_GetMovementMask(E.h, P, c, mask));
        const dd = dv();
        for (let y = Math.max(0, p.y - 16); y <= Math.min(h - 1, p.y + 16); y++) for (let x = Math.max(0, p.x - 16); x <= Math.min(w - 1, p.x + 16); x++) {
          const word = dd.getBigUint64(mask + 8 * ((y >> 3) * stride + (x >> 3)), true);
          if (((word >> BigInt((y & 7) * 8 + (x & 7))) & 1n) && !(x === p.x && y === p.y)) walk.push({ x, y, kind: K_WALK });
        }
      }
      const dash = [];
      const units = new Uint8Array(w * h);
      for (const k of [...allies, ...enemies]) units[k.y * w + k.x] = 1;
      for (let s = 0; s < 2; s++) {
        const pr = props[s];
        if (!pr || pr.type !== DASH || cooldowns[s] !== 0 || !(pr.target & GROUND)) continue;
        if (pr.maxCharges > 0 && !(self.charges?.[s] > 0)) continue;
        dashSlots.add(s);
        const radius = Math.floor(pr.range ?? 0), blocked = new Uint8Array(w * h);
        for (let i = 0; i < w * h; i++) blocked[i] = team[t].blocked[i] | units[i];
        const reach = bfs(w, h, blocked, [p.y * w + p.x], radius);
        for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (reach[y * w + x] !== UNREACH && !(x === p.x && y === p.y)) dash.push({ x, y, kind: s + 1, cooldown: pr.cooldown ?? 0 });
      }
      // Engage (nn_policy_tactics.cpp engage()): one shared feature vector for the three verdicts.
      let allyHp = me.hp, enemyHp = 0, allyDamage = me.str, enemyDamage = 0, incoming = 0, closest = null, nearestD = NONE;
      for (const a of allies) { allyHp += a.hp; allyDamage += a.str; }
      for (const e of enemies) {
        enemyHp += e.hp; enemyDamage += e.str; const dd = cheb(p.x, p.y, e.x, e.y);
        if (dd < nearestD || (dd === nearestD && (!closest || e.id < closest.id))) { closest = e; nearestD = dd; }
        if (dd <= e.range) incoming += e.str;
      }
      const ready = [0, 1].map(s => !!props[s] && props[s].type !== 0 && cooldowns[s] === 0 && (!(props[s].maxCharges > 0) || self.charges?.[s] > 0));
      const escape = team[t].spawnField[p.y * w + p.x];
      const engageRaw = [0, me.hp / maxHp, closest ? closest.hp / Math.max(1, closest.max) : 0, allyHp, enemyHp, allyDamage, enemyDamage,
                         nearestD, escape, gems, ready.filter(Boolean).length, incoming];
      // Combat (targets()/combat_legal()/combat_row()): visible enemies, allies, self, visible camps, unique handles.
      const campMult = (self.items?.[1] || self.items?.[3] || self.items?.[5]) ? 1.1 : 1.0;
      const channelOf = (id, state) => (state & ((1 << 1) | (1 << 2) | (1 << 12))) && X.Game_API_Champion_GetChannelTime(E.h, P, id, E.out) === 0 ? dv().getInt32(E.out, true) : 0;
      const targets = [];
      for (const e of enemies) targets.push({ cat: 'enemy', handle: e.id, x: e.x, y: e.y, hp: e.hp, max: e.max, str: e.str,
                                              gems: u32(X.Game_API_Champion_GetGems, P, e.id) ?? 0, channel: channelOf(e.id, e.state) });
      for (const a of allies) targets.push({ cat: 'ally', handle: a.id, x: a.x, y: a.y, hp: a.hp, max: a.max, str: a.str, gems: a.gems, channel: channelOf(a.id, a.state) });
      targets.push({ cat: 'self', handle: c, x: p.x, y: p.y, hp: me.hp, max: me.max, str: me.str, gems, channel: 0 });
      check(X.Game_GetNumCamps(E.h, E.out));
      for (let k = 0, nc = dv().getUint32(E.out, true); k < nc; k++) {
        if (X.Game_API_Camp_Get(E.h, P, k, E.buf + 1024) !== 0) continue;
        const hp = dv().getFloat32(E.buf + 1032, true);
        if (hp > 0) targets.push({ cat: 'camp', handle: k, x: dv().getInt32(E.buf + 1024, true), y: dv().getInt32(E.buf + 1028, true), hp,
                                   max: dv().getFloat32(E.buf + 1036, true), str: dv().getFloat32(E.buf + 1040, true), gems: 0, channel: 0 });
      }
      targets.sort((a, b) => a.handle - b.handle);
      const unique = targets.filter((q, i) => !(i && targets[i - 1].handle === q.handle) && !(i + 1 < targets.length && targets[i + 1].handle === q.handle));
      const canAttack = (me.state >> 4) & 1, bucket = new Map();
      const legal = (q, kind) => {
        const hostile = q.cat === 'enemy' || q.cat === 'camp', dist = cheb(p.x, p.y, q.x, q.y);
        if (kind === 0) return hostile && canAttack && dist <= me.range;
        const pr = props[kind - 1];
        if (!pr || !ready[kind - 1] || pr.type === DASH) return false;
        const permits = (pr.target & (q.cat === 'enemy' ? 2 : q.cat === 'camp' ? 1 : q.cat === 'self' ? 8 : 4)) !== 0;
        if (pr.type === 1 || pr.type === 7) return q.cat === 'self' && permits;          // attack reset, shield
        if (pr.type === 5) return !hostile && permits && dist <= (pr.range ?? 0);        // heal
        return hostile && permits && dist <= (pr.range ?? 0);
      };
      for (const q of unique) for (let kind = 0; kind < 3; kind++) {
        if (!(kind === 0 ? canAttack : ready[kind - 1]) || !legal(q, kind)) continue;
        const pick = { q, kind, id: q.handle * 4 + kind, oct: octant(cx(t, q.x) - cx(t, p.x), cy(t, q.y) - cy(t, p.y)) };
        const key = kind * 8 + pick.oct; if (!bucket.has(key)) bucket.set(key, []);
        const list = bucket.get(key); let at = 0;
        while (at < list.length && !((pick.q.channel > 0) !== (list[at].q.channel > 0) ? pick.q.channel > 0 : pick.id < list[at].id)) at++;
        if (at < MAX_K) { list.splice(at, 0, pick); if (list.length > MAX_K) list.pop(); }
      }
      const combatRows = [{ id: 3, kind: 3, q: null, raw: [3, 0, 0, 0, 0, me.hp / maxHp, me.str, 0, 0, 0, 0, 0] }];
      for (let depth = 0; depth < MAX_K && combatRows.length < MAX_K; depth++)
        for (let oct = 0; oct < 8 && combatRows.length < MAX_K; oct++) for (let kind = 0; kind < 3 && combatRows.length < MAX_K; kind++) {
          const pick = bucket.get(kind * 8 + oct)?.[depth];
          if (!pick) continue;
          const q = pick.q, raw = [kind, q.hp, q.max, q.gems, cheb(p.x, p.y, q.x, q.y), me.hp / maxHp, me.str, q.str, 0, 0, q.channel, q.cat === 'enemy' ? 1 : 0];
          if (kind === 0) raw[8] = me.str * (q.cat === 'camp' ? campMult : 1);
          else {
            const pr = props[kind - 1]; raw[9] = pr.cooldown ?? 0;
            if (pr.type === 2 || pr.type === 3 || pr.type === 4) {
              const rc = q.cat === 'camp' ? X.Game_API_Champion_GetAbilityDamage(E.h, P, c, kind - 1, E.out)
                : X.Game_API_Champion_GetAbilityDamageAgainst(E.h, P, c, kind - 1, q.handle, E.out);
              raw[8] = rc === 0 ? dv().getFloat32(E.out, true) * (q.cat === 'camp' ? campMult : 1) : 0;
            }
            if (pr.type === 3) raw[11] = enemies.filter(e => cheb(q.x, q.y, e.x, e.y) <= (pr.radius ?? 0)).length;
          }
          combatRows.push({ id: pick.id, kind, q, raw });
        }
      // Macro heads (nn_policy_strategy.cpp, nn_policy_economy.cpp bank()) over one walk field from this tile.
      const field = bfs(w, h, team[t].blocked, [p.y * w + p.x]), pc = { x: cx(t, p.x), y: cy(t, p.y) };
      const remaining = Math.max(0, MAX_ROUNDS - round), margin = ours - theirs, hpf = me.hp / maxHp;
      let near8a = 0, near8e = 0, strength8 = me.str;
      for (const a of allies) if (cheb(a.x, a.y, p.x, p.y) <= 8) { near8a++; strength8 += a.str; }
      for (const e of enemies) if (cheb(e.x, e.y, p.x, p.y) <= 8) { near8e++; strength8 -= e.str; }
      const liveCamps = (current?.camps ?? []);
      const threat = (q) => !q ? 0 : enemies.reduce((s, e) => s + (cheb(e.x, e.y, q.x, q.y) <= e.range ? e.str : 0), 0)
        + liveCamps.reduce((s, k) => s + (cheb(k.x, k.y, q.x, q.y) <= k.range ? k.str : 0), 0);
      const groupOpt = (gi) => {
        const g = groups[gi]; let distance = UNREACH, anchor = null, key = null;
        for (const k of g.camps) {
          const q = campInfo[k]; distance = Math.min(distance, field[q.y * w + q.x]);
          const kc = { x: cx(t, q.x), y: cy(t, q.y) };
          if (!key || kc.y < key.y || (kc.y === key.y && kc.x < key.x)) { anchor = q; key = kc; }
        }
        return distance === UNREACH || !anchor ? null : { gi, distance, id: g.handle, anchor, key };
      };
      const nearer = (a, b) => a.distance < b.distance || (a.distance === b.distance && a.id < b.id);
      const options = groups.map((g, gi) => groupOpt(gi)).filter(Boolean);
      let nearestGroup = null, oldestGroup = null, oldestSeen = 0;
      for (const q of options) {
        if (!nearestGroup || nearer(q, nearestGroup)) nearestGroup = q;
        const seen = groupSeen[t].get(groups[q.gi].handle) ?? -1;
        if (!oldestGroup || seen < oldestSeen || (seen === oldestSeen && nearer(q, oldestGroup))) { oldestGroup = q; oldestSeen = seen; }
      }
      const ringDistance = (al) => {
        let best = UNREACH;
        for (let y = al.y - consts.submitRange; y <= al.y + consts.submitRange; y++) for (let x = al.x - consts.submitRange; x <= al.x + consts.submitRange; x++)
          if (x >= 0 && y >= 0 && x < w && y < h) best = Math.min(best, field[y * w + x]);
        return best;
      };
      const altarD = altars.map(ringDistance), bankD = altarD.length ? Math.min(...altarD) : UNREACH;
      let home = null, homeKey = null;
      for (let y = team[t].y0; y < team[t].y1; y++) for (let x = team[t].x0; x < team[t].x1; x++) {
        const d0 = cheb(x, y, p.x, p.y), k = { x: cx(t, x), y: cy(t, y) };
        if (!home || d0 < home.d0 || (d0 === home.d0 && (k.y < homeKey.y || (k.y === homeKey.y && k.x < homeKey.x)))) { home = { x, y, d0 }; homeKey = k; }
      }
      const homeGoal = o[15] !== 10000 && home ? { legal: true, pos: home, distance: o[15], group: -1 } : { legal: false };
      const byDistance = (list) => list.reduce((b, q) => !b || cheb(q.x, q.y, p.x, p.y) < cheb(b.x, b.y, p.x, p.y) || (cheb(q.x, q.y, p.x, p.y) === cheb(b.x, b.y, p.x, p.y) && q.id < b.id) ? q : b, null);
      const ally = byDistance(allies), enemy = byDistance(enemies);
      let latest = null;
      for (const sg of sight[t].values()) if (sg.round <= round && round - sg.round <= 100) {
        const k = { x: cx(t, sg.x), y: cy(t, sg.y) };
        if (!latest || sg.round > latest.round || (sg.round === latest.round && (k.y < latest.k.y || (k.y === latest.k.y && k.x < latest.k.x)))) latest = { ...sg, k };
      }
      const groupGoal = (q) => q ? { legal: true, pos: q.anchor, distance: q.distance, group: q.gi } : { legal: false };
      const goals = { farmNearest: groupGoal(nearestGroup), farmScout: groupGoal(oldestGroup),
        bank: gems > 0 && altars.length && bankD !== UNREACH ? { legal: true, pos: p, distance: bankD, group: -1 } : { legal: false },
        home: homeGoal, regroup: ally ? { legal: true, pos: ally, distance: 10000, group: -1 } : { legal: false },
        attack: enemy ? { legal: true, pos: enemy, distance: 10000, group: -1 } : latest ? { legal: true, pos: latest, distance: 10000, group: -1 } : { legal: false } };
      const strategyRow = (i, g) => ({ id: i, legal: g.legal ? 1 : 0, raw: [i, hpf, gems, gold, remaining, g.legal ? g.distance : 10000, near8a, near8e, strength8, margin,
                                                                      g.legal && g.group >= 0 ? groups[g.group].gems : 0, g.legal ? threat(g.pos) : 0] });
      // Objective: best 16 per canonical quadrant, 4 from each, then round-robin (geometry()).
      const quad = [[], [], [], []];
      for (const q of options) quad[(q.key.x >= pc.x ? 1 : 0) | (q.key.y >= pc.y ? 2 : 0)].push(q);
      quad.forEach(l => { l.sort((a, b) => nearer(a, b) ? -1 : 1); l.length = Math.min(l.length, 16); });
      const used = [0, 0, 0, 0], selected = [];
      for (let qd = 0; qd < 4; qd++) for (let i = 0; i < Math.min(4, quad[qd].length); i++) selected.push(quad[qd][used[qd]++]);
      for (let added = true; selected.length < 16 && added;) { added = false; for (let qd = 0; qd < 4 && selected.length < 16; qd++) if (used[qd] < quad[qd].length) { selected.push(quad[qd][used[qd]++]); added = true; } }
      const objectiveRows = selected.map((q) => {
        const g = groups[q.gi]; let hp = 0, str = 0;
        for (const k of g.camps) { const m = campMem[t][k]; if (m && m.hp > 0) { hp += m.hp; str += m.str; } }
        let respawn = 0;
        if (X.Game_API_CampGroup_GetState(E.h, P, g.handle, E.out) === 0 && dv().getUint32(E.out, true) === 3 &&
            X.Game_API_CampGroup_GetCooldown(E.h, P, g.handle, E.out) === 0) respawn = Math.max(0, dv().getInt32(E.out, true));
        const seen = groupSeen[t].get(g.handle);
        return { id: g.handle, raw: [cx(t, q.anchor.x) - pc.x, cy(t, q.anchor.y) - pc.y, q.distance, g.gems, g.gold, hp, str, consts.capture, respawn, 0,
                                     enemies.filter(e => cheb(e.x, e.y, q.anchor.x, q.anchor.y) <= 8).length, seen === undefined ? round + 1 : round - seen] };
      });
      const teamIds = handles(X.Game_API_Champion_GetAllies, P).sort((a, b) => a - b), slot = Math.max(0, teamIds.indexOf(c));
      const roleLegal = [options.length > 0, goals.bank.legal, enemies.length > 0, allies.length > 0, options.length > 0];
      const roleRows = [0, 1, 2, 3, 4].map(i => ({ id: i, legal: roleLegal[i] ? 1 : 0, raw: [i, slot, hpf, gems, gold, me.range, near8a, near8e, 10000, 0, margin, remaining] }));
      // Bank (only scheduled while carrying gems): continue, deposits in range, then destinations (one per quadrant, nearest).
      let bankRows = null;
      if (gems > 0) {
        let visible = 0, damage = 0;
        for (const e of enemies) { visible++; if (cheb(e.x, e.y, p.x, p.y) <= e.range + 1) damage += e.str; }
        const channelRounds = Math.max(consts.submitMin, consts.submitBase + Math.ceil(gems * consts.submitMult));
        const fill = (action, al, distance) => [action, al ? cx(t, al.x) - pc.x : 0, al ? cy(t, al.y) - pc.y : 0, distance, gems, WINNING_GEMS - ours, remaining, hpf, visible, damage, channelRounds, -1];
        bankRows = [{ id: 0, raw: fill(0, null, 0) }];
        const reach = altars.map((al, i) => ({ i, al, distance: altarD[i], quadrant: (cx(t, al.x) >= pc.x ? 1 : 0) | (cy(t, al.y) >= pc.y ? 2 : 0) })).filter(a => a.distance !== UNREACH);
        for (const a of reach) if (a.distance === 0 && cheb(p.x, p.y, a.al.x, a.al.y) <= consts.submitRange && bankRows.length < MAX_K) bankRows.push({ id: 2 + 2 * a.i, raw: fill(2, a.al, 0) });
        const nearestA = [...reach].sort((a, b) => a.distance - b.distance || a.i - b.i), picked = new Set();
        const append = (a) => { if (a && !picked.has(a.i) && bankRows.length < MAX_K) { picked.add(a.i); bankRows.push({ id: 1 + 2 * a.i, raw: fill(1, a.al, a.distance) }); } };
        if (reach.length <= MAX_K - bankRows.length) nearestA.forEach(append);
        else { for (let qd = 0; qd < 4; qd++) append(nearestA.find(a => a.quadrant === qd)); nearestA.forEach(append); }
        bankRows.sort((a, b) => a.id - b.id);
      }
      objectiveRows.sort((a, b) => a.id - b.id); // schema order: ascending stable id (narrowing order is not row order)
      const macro = { goals, strategyRow, objectiveRows, roleRows, bankRows };
      return { c, t, round, p, o, allyRows, allyMask, enemyRows, enemyMask, gems, walk, dash, dashSlots, macro,
               allies: allies.map(a => ({ x: a.x, y: a.y })), enemies: enemies.map(e => ({ x: e.x, y: e.y, range: e.range })),
               enemiesKnown: sight[t].size > 0, canMove: (me.state >> 3) & 1, engageRaw, combatRows: combatRows.sort((a, b) => a.id - b.id),
               camps: null, move: null, combat: null, combatBefore: false, fight: false };
    }

    function finalize(recs, outcome) {
      const rows = [], counts = {};
      const tally = (head, ok) => { const k = `${head}_${ok ? 'labelled' : 'unlabelled'}`; counts[k] = (counts[k] ?? 0) + 1; };
      recs.forEach((r) => {
        r.camps = r.camps ?? [];
        const t = r.t, p = r.p, hist = posHist.get(r.c) ?? [], acts_ = acts.get(r.c) ?? [];
        // Hindsight goal: own position GOAL_ROUNDS later (else the last known one).
        let goal = hist[hist.length - 1];
        for (const q of hist) if (q.round >= r.round + GOAL_ROUNDS) { goal = q; break; }
        const window = (lo, hi, pred) => acts_.some(a => a.round >= lo && a.round <= hi && pred(a));
        let role = 4;
        if (r.gems > 0 && window(r.round, r.round + 40, a => a.kind === 12)) role = 1;
        else if (window(r.round, r.round + 10, a => a.target === 'champion')) role = 2;
        else if (window(r.round, r.round + 10, a => a.target === 'camp')) role = 0;
        else if ([...Array(5).keys()].some(k => r.allyMask[k] && r.allyRows[k * 10 + 8] > 0 && Math.max(Math.abs(r.allyRows[k * 10]), Math.abs(r.allyRows[k * 10 + 1])) <= 3)) role = 3;
        r.o[12] = role; r.o[13] = ddx(t, goal.x - p.x); r.o[14] = ddy(t, goal.y - p.y);
        // Goal field: the goal tile, or its unblocked ring when the goal itself is blocked.
        const blocked = team[t].blocked, gi = goal.y * w + goal.x, roots = [];
        if (!blocked[gi]) roots.push(gi);
        else for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const x = goal.x + dx, y = goal.y + dy; if ((dx || dy) && x >= 0 && y >= 0 && x < w && y < h && !blocked[y * w + x]) roots.push(y * w + x); }
        const field = bfs(w, h, blocked, roots);
        const pick = (q) => ({ ...q, id: moveId(q.kind, cx(t, q.x), cy(t, q.y)), oct: octant(cx(t, q.x) - cx(t, p.x), cy(t, q.y) - cy(t, p.y)),
                               distance: field[q.y * w + q.x] });
        const all = [...r.walk, ...r.dash].map(pick), hold = pick({ x: p.x, y: p.y, kind: K_HOLD });
        const less = (a, b) => a.distance < b.distance || (a.distance === b.distance && a.id < b.id);
        let chosen;
        if (all.length <= MAX_K - 1) chosen = [hold, ...all];
        else {
          const bucket = new Map();
          for (const q of all) { const key = q.kind * 8 + q.oct; if (!bucket.has(key) || less(q, bucket.get(key))) bucket.set(key, q); }
          chosen = [hold];
          for (let oct = 0; oct < 8 && chosen.length < MAX_K; oct++) for (let kind = 0; kind < 3 && chosen.length < MAX_K; kind++) if (bucket.has(kind * 8 + oct)) chosen.push(bucket.get(kind * 8 + oct));
        }
        chosen.sort((a, b) => a.id - b.id);
        // Label: actual movement (or hold); a narrowed-out destination maps to its kind/octant representative.
        const m = r.move ?? { kind: K_HOLD, x: p.x, y: p.y };
        const mid = moveId(m.kind, cx(t, m.x), cy(t, m.y));
        let label = chosen.findIndex(q => q.id === mid), flags = r.combatBefore ? 2 : 0;
        if (label < 0) {
          const target = all.find(q => q.id === mid);
          if (target) { label = chosen.findIndex(q => q.kind === target.kind && q.oct === target.oct); if (label >= 0) flags |= 1; }
        }
        // Engage verdict from this turn's behaviour (runtime: hold suppresses combat and move, disengage suppresses combat).
        let engage = 2;
        if (r.combat) engage = 0;
        else if (r.move) {
          engage = 0;
          if (r.enemies.length) {
            const near = r.enemies.reduce((b, e) => (!b || cheb(e.x, e.y, p.x, p.y) < cheb(b.x, b.y, p.x, p.y) ? e : b), null);
            if (cheb(near.x, near.y, p.x, p.y) <= 8 && cheb(near.x, near.y, m.x, m.y) > cheb(near.x, near.y, p.x, p.y)) engage = 1;
          }
        }
        const context = r.enemiesKnown ? (engage === 0 ? 1 : engage === 1 ? 2 : 0) : 0;
        const base = { r, context, won: outcome === t + 1 ? 1 : 0 };
        // Macro labels (hindsight rules): strategy intent, objective group, role, bank action.
        const M = r.macro, macroContext = r.enemiesKnown ? 1 : 0;
        let intent = 0;
        if (r.gems > 0 && window(r.round, r.round + 40, a => a.kind === 12)) intent = 1;
        else if (window(r.round, r.round + 10, a => a.kind === 11)) intent = 6;
        else if (window(r.round, r.round + 10, a => a.target === 'champion')) intent = 5;
        else if (window(r.round, r.round + 10, a => a.target === 'camp')) intent = 0;
        else if (role === 3) intent = 4;
        const farm = role === 4 ? M.goals.farmScout : M.goals.farmNearest;
        const sRows = [farm, M.goals.bank, M.goals.home, farm, M.goals.regroup, M.goals.attack, M.goals.home].map((g, i) => M.strategyRow(i, g));
        const pushRows = (head, list, label, kind) => {
          rows.push({ ...base, head, context: macroContext, ids: list.map(q => q.id), feats: list.map(q => q.raw), legal: list.map(q => q.legal ?? 1),
                      label, flags: 0, kind });
          tally(HEAD_LABEL[head], label >= 0);
        };
        if (sRows.some(q => q.legal)) pushRows(STRATEGY_HEAD, sRows, sRows[intent].legal ? intent : -1, intent);
        if (M.roleRows.some(q => q.legal)) pushRows(ROLE_HEAD, M.roleRows, M.roleRows[role].legal ? role : -1, role);
        if ((intent === 0 || intent === 3) && M.objectiveRows.length) {
          const nextCamp = acts_.find(a => a.round >= r.round && a.round <= r.round + 30 && a.target === 'camp' && a.group !== undefined);
          pushRows(OBJECTIVE_HEAD, M.objectiveRows, nextCamp ? M.objectiveRows.findIndex(q => q.id === nextCamp.group) : -1, -1);
        }
        if (M.bankRows) {
          const nearestAltar = (q) => altars.reduce((b, al, i) => b < 0 || cheb(al.x, al.y, q.x, q.y) < cheb(altars[b].x, altars[b].y, q.x, q.y) ? i : b, -1);
          let id = 0;
          if (r.submit) id = 2 + 2 * nearestAltar(r.submit);
          else { const s = acts_.find(a => a.round > r.round && a.round <= r.round + 40 && a.kind === 12); if (s) id = 1 + 2 * nearestAltar(s); }
          pushRows(BANK_HEAD, M.bankRows, M.bankRows.findIndex(q => q.id === id), id);
        }
        if (r.enemiesKnown) {
          rows.push({ ...base, head: ENGAGE_HEAD, context: 0, ids: [0, 1, 2], feats: [0, 1, 2].map(v => [v, ...r.engageRaw.slice(1)]), label: engage, flags: 0, kind: engage });
          tally('engage', true);
        }
        if ((!r.enemiesKnown || engage === 0) && r.combatRows.length > 1) {
          let cl = r.combatRows.findIndex(q => q.kind === 3);
          if (r.combat) cl = r.combatRows.findIndex(q => q.q && q.kind === r.combat.kind && q.q.x === r.combat.x && q.q.y === r.combat.y);
          rows.push({ ...base, head: COMBAT_HEAD, ids: r.combatRows.map(q => q.id), feats: r.combatRows.map(q => q.raw), label: cl, flags: 0, kind: r.combat ? r.combat.kind : 3 });
          tally('combat', cl >= 0);
        }
        if (r.canMove && !(r.enemiesKnown && engage === 2)) {
          const feats = chosen.map((q) => {
            let attackers = 0, camps = 0, enemyD = NONE, allyD = NONE;
            for (const e of r.enemies) { const dd = cheb(q.x, q.y, e.x, e.y); enemyD = Math.min(enemyD, dd); attackers += dd <= e.range; }
            for (const cp of r.camps) camps += cheb(q.x, q.y, cp.x, cp.y) <= cp.range;
            for (const a of r.allies) allyD = Math.min(allyD, cheb(q.x, q.y, a.x, a.y));
            return [ddx(t, q.x - p.x), ddy(t, q.y - p.y), q.distance, cheb(q.x, q.y, goal.x, goal.y), attackers, camps,
                    bush[q.y * w + q.x], enemyD, allyD, q.kind, q.kind === 1 || q.kind === 2 ? q.cooldown : 0, r.gems];
          });
          rows.push({ ...base, head: MOVE_HEAD, ids: chosen.map(q => q.id), feats, label, flags, kind: r.move ? r.move.kind : -1 });
          tally('move', label >= 0);
        }
      });
      const n = rows.length, A = Object.fromEntries(Object.entries(WIDTHS).map(([k, [width, Type]]) => [k, new Type(n * width)]));
      rows.forEach((row, i) => {
        const r = row.r;
        A.obs_self.set(r.o, i * 40); A.obs_ally.set(r.allyRows, i * 50); A.ally_mask.set(r.allyMask, i * 5);
        A.obs_enemy.set(r.enemyRows, i * 72); A.enemy_mask.set(r.enemyMask, i * 6);
        row.feats.forEach((f, k) => { A.cand_feat.set(f, (i * MAX_K + k) * 12); A.cand_id[i * MAX_K + k] = row.ids[k]; A.cand_legal[i * MAX_K + k] = row.legal ? row.legal[k] : 1; });
        A.cand_k[i] = row.ids.length; A.label[i] = row.label; A.context[i] = row.context; A.head[i] = row.head;
        A.info.set([r.t, r.c, r.round, row.won, row.flags, row.kind], i * 6);
      });
      return { rows: n, arrays: A, entry: { replay: name, ok: true, rows: n, outcome, steps, ...stats, ...counts } };
    }
  } finally { E.destroy(); }
}

function parseArgs(argv) {
  const a = { inputs: [], out: null, rate: 0.05, workers: os.availableParallelism(), shardSize: 256, assets: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--out') a.out = argv[++i]; else if (argv[i] === '--rate') a.rate = Number(argv[++i]);
    else if (argv[i] === '--workers') a.workers = Number(argv[++i]); else if (argv[i] === '--shard-size') a.shardSize = Number(argv[++i]);
    else if (argv[i] === '--assets') a.assets = argv[++i]; else a.inputs.push(argv[i]);
  }
  if (!a.out || !a.inputs.length || !(a.rate > 0 && a.rate <= 1)) throw new Error('usage: --out <dir> [--rate r] [--workers N] [--shard-size N] <replays...>');
  return a;
}

function run(E, file, rate) {
  try { return extract(E, file, rate); }
  catch (e) {
    // A wasm trap's message is only "unreachable": keep the calling line of this file.
    const where = String(e.stack ?? '').split('\n').find(l => l.includes('bc_extract.mjs'))?.trim();
    return { rows: 0, arrays: null, entry: { replay: path.basename(file), ok: false, error: String(e.message ?? e) + (where ? ` @ ${where}` : '') } };
  }
}

if (isMainThread) {
  const a = parseArgs(process.argv.slice(2));
  a.assets = a.assets ?? defaultAssets(); verifyAssets(a.assets);
  const files = a.inputs.flatMap(p => fs.statSync(p).isDirectory() ? fs.readdirSync(p).filter(f => f.endsWith('.repl26a')).sort().map(f => path.join(p, f)) : [p]);
  const writer = new RowShardWriter(a.out, files, { shardSize: a.shardSize, format: FORMAT,
    widths: Object.fromEntries(Object.entries(WIDTHS).map(([k, [width, type]]) => [k, { width, type }])),
    run: { created: new Date().toISOString(), rate: a.rate, goal_rounds: GOAL_ROUNDS, assets: a.assets, pinned: PINNED } });
  const t0 = performance.now();
  if (Math.min(a.workers, files.length) <= 1) { const E = await engine(a.assets); files.forEach((f, i) => writer.add(i, run(E, f, a.rate))); }
  else {
    let next = 0;
    await new Promise((resolve) => {
      let live = 0;
      const spawn = () => {
        if (next >= files.length) { if (!live) resolve(); return; }
        const w = new Worker(new URL(import.meta.url), { workerData: { assets: a.assets, rate: a.rate } }); let cur = null; live++;
        const feed = () => { if (next < files.length) { cur = next++; w.postMessage({ index: cur, file: files[cur] }); } else { cur = null; w.postMessage(null); } };
        w.on('message', (m) => { if (m === 'ready') return feed(); writer.add(m.index, m.result); feed(); });
        w.on('error', (e) => { if (cur !== null) writer.add(cur, { rows: 0, arrays: null, entry: { replay: path.basename(files[cur]), ok: false, error: 'worker crashed: ' + e.message } }); cur = null; });
        w.on('exit', () => { live--; if (next < files.length) spawn(); else if (!live) resolve(); });
      };
      for (let i = 0; i < Math.min(a.workers, files.length); i++) spawn();
    });
  }
  const m = writer.finish();
  console.log(JSON.stringify({ replays: files.length, passed: m.passed, failed: m.failed, rows: m.rows, bytes: m.bytes, shards: m.shards.length,
                               seconds: Math.round((performance.now() - t0) / 100) / 10, out: a.out }));
  if (m.failed) process.exitCode = 1;
} else {
  const E = await engine(workerData.assets);
  parentPort.on('message', (job) => {
    if (job === null) { parentPort.close(); return; }
    const result = run(E, job.file, workerData.rate);
    parentPort.postMessage({ index: job.index, result }, result.arrays ? Object.values(result.arrays).map(x => x.buffer) : []);
  });
  parentPort.postMessage('ready');
}
