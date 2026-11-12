// Simulator fidelity benchmark on real fights (fight_data.js output) with simharness2.wasm (the bot's ts:: code).
// Test M (mechanics): the actor's real actions applied in the simulator; post-turn health, deaths and cooldowns
// against the engine's. Test P (policy): the simulator's own choice for the actor against what the real bot did.
// usage: node bench_sim.js fights.jsonl [max=10000] [--vis] [--dump N]
process.env.ENGWASM = require("path").join(__dirname, "..", "..", "tools", "viz", "v0_0_3.wasm");
const fs = require("fs");
const path = require("path");
const { WASI } = require("wasi");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));

const args = process.argv.slice(2);
const file = args[0], MAX = +(args[1] && !args[1].startsWith("--") ? args[1] : 10000);
const VIS = args.includes("--vis"), DUMP = args.includes("--dump") ? +args[args.indexOf("--dump") + 1] : 0;
const TYPE = ["ryth", "vesper", "vendetta", "cassi", "issac", "stellar", "prism", "marcella", "willow", "ren", "varg", "tavi"];
const KIND = ["none", "reset", "damage", "aoe", "cc", "heal", "dash", "shield"];

function loadSim() {
  const wasi = new WASI({ version: "preview1", args: [], env: {}, returnOnExit: true });
  const mod = new WebAssembly.Module(fs.readFileSync(path.join(__dirname, "simharness2.wasm")));
  const env = {};
  for (const i of WebAssembly.Module.imports(mod)) if (i.module === "env" && i.kind === "function") env[i.name] = () => 0;
  env.__cpp_exception = new WebAssembly.Tag({ parameters: ["i32"] });
  const inst = new WebAssembly.Instance(mod, { env, wasi_snapshot_preview1: wasi.wasiImport });
  wasi.initialize(inst);
  return inst.exports;
}
const S = loadSim();
const KF = 28;
const sio = () => new Float32Array(S.memory.buffer, S.io(), 4 + KF * 8);
const sops = () => new Float32Array(S.memory.buffer, S.ops(), 40);

// Map boards (blocked = walls, holes, altars; vision boards) per map, from the engine.
const E = load(), ex = E.ex;
let curMap = null, W = 0, H = 0;
function mapBoards(mapName) {
  if (curMap === mapName) return;
  curMap = mapName;
  const bytes = fs.readFileSync(path.join(__dirname, "..", "..", "maps_rdev", mapName));
  const p = ex.Engine_Malloc(bytes.length);
  new Uint8Array(ex.memory.buffer, p, bytes.length).set(bytes);
  E.check(ex.Game_FromMapFileBytes(p, bytes.length, E.outBuf, 0), "map");
  const g = E.mem.getBigUint64(E.outBuf, true);
  const meta = E.alloc(64);
  ex.Game_API_Map_GetBitboardMetadata(g, meta);
  W = E.mem.getInt32(meta, true); H = E.mem.getInt32(meta + 4, true);
  const stride = E.mem.getInt32(meta + 16, true);
  const bit = (ptr, x, y) => { const b = ((y & 7) << 3) | (x & 7); return (E.mem.getUint8(ptr + ((y >> 3) * stride + (x >> 3)) * 8 + (b >> 3)) >> (b & 7)) & 1; };
  const buf = (fn) => { fn(g, E.outBuf); return E.mem.getUint32(E.outBuf, true); };
  const wp = buf(ex.Game_GetWallBuffer), hp = buf(ex.Game_GetHoleBuffer), bp = buf(ex.Game_GetBushBuffer), ap = buf(ex.Game_GetAltarBuffer);
  const hs = (W + 7) >> 3;
  const blk = new BigUint64Array(S.memory.buffer, S.board(), 64 * 64), wb = new BigUint64Array(S.memory.buffer, S.walls(), 64 * 64),
    bb = new BigUint64Array(S.memory.buffer, S.bushes(), 64 * 64), lb = new Uint16Array(S.memory.buffer, S.labels(), 512 * 512);
  blk.fill(0n); wb.fill(0n); bb.fill(0n);
  const bush = new Uint8Array(W * H), cl = new Int32Array(W * H).fill(-1);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const k = (y >> 3) * hs + (x >> 3), m = 1n << BigInt(((y & 7) << 3) | (x & 7));
      if (bit(wp, x, y) || bit(hp, x, y) || bit(ap, x, y)) blk[k] |= m;
      if (bit(wp, x, y)) wb[k] |= m;
      if (bit(bp, x, y)) { bb[k] |= m; bush[y * W + x] = 1; }
    }
  let id = 0;
  for (let i = 0; i < W * H; i++) {
    if (!bush[i] || cl[i] >= 0) continue;
    const st = [i]; cl[i] = id;
    while (st.length) { const c = st.pop(), cx = c % W, cy = (c / W) | 0; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const qx = cx + dx, qy = cy + dy, q = qy * W + qx; if ((dx || dy) && qx >= 0 && qy >= 0 && qx < W && qy < H && bush[q] && cl[q] < 0) { cl[q] = id; st.push(q); } } }
    id++;
  }
  for (let i = 0; i < W * H; i++) if (cl[i] >= 0) lb[i] = cl[i];
  ex.Game_Destroy(g);
  S.set_vis(VIS ? 1 : 0);
}

// Spell slot -> harness fields (as the bot's kit_of in tsearch.cpp).
function spellFields(k, type, focus) {
  if (!k) return [0, 99, 0, 0, 0, 0];
  let flags = 0;
  if (k.attrs & 1) flags |= 1;          // SF_EXCL_WALK
  if (k.targets & 2) flags |= 4;        // SF_ENEMY
  if (k.targets & 4) flags |= 8;        // SF_ALLY
  if (k.kind === 4 || (k.kind === 3 && type === 0)) flags |= 2; // SF_STUN (cc; Ryth's area stun)
  if (k.kind === 1 && type === 7) flags |= 16; // SF_ENH (Marcella)
  let range = Math.round(k.range || 0);
  if (k.kind === 6 && range <= 0) range = 2;
  return [k.kind, -1, range, Math.round(k.radius || 0), (k.mod || 0) * focus, flags];
}
const RADIUS = args.includes("--radius") ? +args[args.indexOf("--radius") + 1] : 8, CAMPS = args.includes("--camps");
function fill(rec) {
  const actor = rec.units.find((u) => u.h === rec.actor);
  const dist = (u) => Math.max(Math.abs(u.x - actor.x), Math.abs(u.y - actor.y));
  const others = rec.units.filter((u) => u.h !== rec.actor && !u.dead && u.alive && dist(u) <= RADIUS).sort((a, b) => dist(a) - dist(b));
  const order = [actor, ...others].slice(0, 8);
  const cf = new Float32Array(S.memory.buffer, S.camps(), 25);
  cf[0] = 0;
  if (CAMPS && rec.camps) {
    const cs = rec.camps.filter((c) => c.str > 0 && Math.max(Math.abs(c.x - actor.x), Math.abs(c.y - actor.y)) <= 8).slice(0, 6);
    cf[0] = cs.length;
    cs.forEach((c, i) => { cf[1 + 4 * i] = c.x; cf[2 + 4 * i] = c.y; cf[3 + 4 * i] = c.str; cf[4 + 4 * i] = 3; });
  }
  const f = sio();
  f[0] = order.length; f[1] = W; f[2] = H; f[3] = 0;
  order.forEach((u, i) => {
    const o = 4 + KF * i, s0 = spellFields(u.kit && u.kit[0], u.type, u.focus), s1 = spellFields(u.kit && u.kit[1], u.type, u.focus);
    s0[1] = Math.max(0, u.cd[0]); s1[1] = Math.max(0, u.cd[1]);
    const vals = [u.team === actor.team ? 0 : 1, u.x, u.y, u.alive ? u.hp : 0, u.maxhp, u.str, Math.max(1, u.range), u.alive ? 1 : 0, u.type, u.focus,
      u.shield ? u.shield[0] : 0, u.shield ? u.shield[1] : 0, u.stun ? 1 : 0, u.enh ? 1 : 0, u.gems, ...s0, ...s1, 0];
    for (let k = 0; k < KF; k++) f[o + k] = vals[k];
  });
  return order;
}
const read = (n) => { const f = sio(); return Array.from({ length: n }, (_, i) => { const o = 4 + KF * i; return { x: f[o + 1], y: f[o + 2], hp: f[o + 3], alive: f[o + 7] > 0, cd: [f[o + 16], f[o + 22]] }; }); };

const lines = fs.readFileSync(file, "utf8").split("\n").filter(Boolean);

// --- Test R (rollout): from a real fight state, simulate the rest of the round and two more; compare with the real
// game's units at round r + 3 (first logged turn of that round that contains them). Policies: static (nobody acts),
// greedy (the playout policy), learned (behaviour network for both teams; harness built with A2_ENEMY_NET).
if (args.includes("--rollout")) {
  const recs = lines.map((l) => JSON.parse(l));
  const byGame = new Map();
  for (const r of recs) { if (!byGame.has(r.game)) byGame.set(r.game, []); byGame.get(r.game).push(r); }
  // Deaths: dead champions are not readable, so they vanish from later logs; their death turns are in the records
  // where a unit is alive before the actor's turn and dead after it.
  const deaths = new Map(); // game -> [[handle, round]]
  for (const r of recs) r.units.forEach((u, i) => { const p2 = r.post[i]; if (u.alive && p2 && !p2.alive) { if (!deaths.has(r.game)) deaths.set(r.game, []); deaths.get(r.game).push([u.h, r.round]); } });
  const diedBy = (game, h, from, to) => (deaths.get(game) || []).some(([hh, rr]) => hh === h && rr >= from && rr <= to);
  const res = { static: [], greedy: [], learned: [] };
  let used2 = 0;
  for (const rec of recs) {
    if (used2 >= MAX) break;
    if (rec.units.length > 8 || !rec.units.some((u) => u.h === rec.actor)) continue;
    // Each unit's state at round r + 3 from any logged turn of that round (a dead champion is often far from the
    // next actor, so one record alone would drop exactly the fights where someone died).
    const lu = new Map();
    for (const x of byGame.get(rec.game)) if (x.round === rec.round + 3) for (const u of x.units) if (!lu.has(u.h)) lu.set(u.h, u);
    if (!lu.size) continue;
    for (const u of rec.units) if (u.alive && diedBy(rec.game, u.h, rec.round, rec.round + 3)) lu.set(u.h, { ...u, alive: false, hp: 0 });
    const order0 = rec.units.filter((u) => u.alive && !u.dead);
    if (order0.filter((u) => lu.has(u.h)).length < 2) continue;
    if (args.includes("--engaged")) {
      // Real fights only: an enemy pair within 3 tiles, and someone loses 10% of their health within the 3 rounds.
      const me0 = rec.units.find((u) => u.h === rec.actor);
      const close = order0.some((u) => u.team !== me0.team && order0.some((v) => v.team === me0.team && Math.max(Math.abs(u.x - v.x), Math.abs(u.y - v.y)) <= 3));
      const hurt = order0.some((u) => { const r2 = lu.get(u.h); return r2 && (u.hp - (r2.alive ? r2.hp : 0)) >= 0.1 * u.maxhp; });
      if (!close || !hurt) continue;
    }
    used2++;
    mapBoards(rec.map);
    for (const [name, pol] of [["static", null], ["greedy", [0, 0]], ["learned", [1, 1]]]) {
      const order = fill(rec);
      let pred;
      if (!pol) pred = read(order.length);
      else {
        const pp = new Float32Array(S.memory.buffer, S.pol(), 8);
        pp[5] = rec.round; pp[6] = pol[0]; pp[7] = pol[1];
        S.roll(2);
        pred = read(order.length);
      }
      let hpErr = 0, posErr = 0, aliveBad = 0, n = 0, tp = 0, fp = 0, fn = 0;
      order.forEach((u, j) => {
        if (!u.alive || !lu.has(u.h)) return;
        const real = lu.get(u.h);
        if (real.dead) { real.alive = false; real.hp = 0; }
        n++;
        if (real.alive !== pred[j].alive) aliveBad++;
        if (!real.alive && !pred[j].alive) tp++; else if (real.alive && !pred[j].alive) fp++; else if (!real.alive && pred[j].alive) fn++;
        hpErr += Math.abs((real.alive ? real.hp : 0) - (pred[j].alive ? pred[j].hp : 0)) / Math.max(1, u.maxhp);
        if (real.alive && pred[j].alive) posErr += Math.max(Math.abs(real.x - pred[j].x), Math.abs(real.y - pred[j].y));
      });
      res[name].push({ hp: hpErr / n, pos: posErr / n, alive: aliveBad, tp, fp, fn });
    }
  }
  const mean = (a, k) => a.reduce((s, x) => s + x[k], 0) / a.length;
  console.log(`rollout test: ${used2} real fight states, 3 rounds ahead`);
  for (const k of Object.keys(res)) {
    { const s = (f) => res[k].reduce((a, x) => a + x[f], 0); console.log(`  ${k.padEnd(8)} deaths caught ${s("tp")}/${s("tp") + s("fn")} real, false alarms ${s("fp")}`); }
    console.log(`  ${k.padEnd(8)} health error ${(100 * mean(res[k], "hp")).toFixed(1)}% of max per unit | position error ${mean(res[k], "pos").toFixed(2)} tiles | wrong deaths ${(mean(res[k], "alive")).toFixed(3)} per state`);
  }
  process.exit(0);
}
const M = { n: 0, ok: 0, hpBad: 0, aliveBad: 0, cdBad: 0, skipped: 0, byCause: {}, ex: [] };
const P = { n: 0, cls: 0, tgt: [0, 0], dir: [0, 0], conf: {} };
const note = (k, e) => { M.byCause[k] = (M.byCause[k] || 0) + 1; if (DUMP && M.ex.filter((x) => x.startsWith(k)).length < DUMP && e) M.ex.push(k + " | " + e); };
const cls = (moved, att, cast) => (cast ? "C" : "") + (att ? "A" : "") + (moved ? "M" : "") || "-";
let used = 0;
for (const line of lines) {
  if (used >= MAX) break;
  const rec = JSON.parse(line);
  if (rec.units.length > 8 || !rec.units.some((u) => u.h === rec.actor)) continue; // handles 8+ (Cassi/Issac teams) were not logged
  used++;
  mapBoards(rec.map);
  const acts = rec.acts.filter((a) => a[a.length - 1] === 0);
  if (acts.some((a) => a[0] === "recall" || a[0] === "use_consumable" || a[0] === "submit_gems")) { M.skipped++; continue; }
  const order = fill(rec);
  const idxOf = (h) => order.findIndex((u) => u.h === h);
  const actor = order[0];
  // --- Test P: the simulator's choice.
  if (!actor.stun) {
    const before = read(order.length);
    S.act_unit(0);
    const pred = read(order.length);
    const pMoved = pred[0].x !== before[0].x || pred[0].y !== before[0].y;
    let pAtt = -1, drop = 0.5;
    pred.forEach((u, j) => { if (j && order[j].team !== actor.team && before[j].hp - u.hp > drop) { drop = before[j].hp - u.hp; pAtt = j; } });
    const pCast = pred[0].cd[0] > before[0].cd[0] || pred[0].cd[1] > before[0].cd[1] || (before[0].cd[0] === 0 && pred[0].cd[0] > 0) || (before[0].cd[1] === 0 && pred[0].cd[1] > 0);
    const rMoved = acts.some((a) => a[0] === "move_to"), rCast = acts.some((a) => a[0] === "cast");
    const ra = acts.find((a) => a[0] === "attack" && a[1] === 1), rAtt = ra ? idxOf(ra[2]) : -1;
    const pc = cls(pMoved, pAtt >= 0, pCast), rc = cls(rMoved, rAtt >= 0 || acts.some((a) => a[0] === "attack"), rCast);
    P.n++; if (pc === rc) P.cls++;
    P.conf[rc + "->" + pc] = (P.conf[rc + "->" + pc] || 0) + 1;
    if (pAtt >= 0 && rAtt >= 0) { P.tgt[1]++; if (pAtt === rAtt) P.tgt[0]++; }
    if (pMoved && rMoved) {
      const mv = acts.filter((a) => a[0] === "move_to").pop();
      P.dir[1]++; if (Math.sign(mv[1] - actor.x) === Math.sign(pred[0].x - actor.x) && Math.sign(mv[2] - actor.y) === Math.sign(pred[0].y - actor.y)) P.dir[0]++;
    }
    fill(rec);
  }
  // --- Test M: the real actions in the simulator.
  const ops = sops();
  let n = 0, camp = false;
  for (const a of acts) {
    if (n >= 8) break;
    if (a[0] === "move_to") { ops.set([1, a[1], a[2], 0, 0], 5 * n++); }
    else if (a[0] === "attack") { if (a[1] !== 1) { camp = true; continue; } ops.set([2, idxOf(a[2]), 0, 0, 0], 5 * n++); }
    else if (a[0] === "cast") { const t = a[2] === 1 ? idxOf(a[3]) : -1; if (a[2] && a[2] !== 1) camp = true; ops.set([3, a[1], t, a[4], a[5]], 5 * n++); }
  }
  S.apply_ops(0, n);
  const got = read(order.length);
  M.n++;
  let bad = false;
  order.forEach((u, j) => {
    const post = rec.post[rec.units.indexOf(u)];
    if (!post) return;
    const g = got[j];
    if (g.alive !== post.alive) { bad = true; M.aliveBad++; note(`alive:${TYPE[actor.type]}`, `unit ${TYPE[u.type]} sim ${g.alive} eng ${post.alive} acts ${JSON.stringify(acts)}`); return; }
    if (post.alive && Math.abs(g.hp - post.hp) > 1.0) {
      bad = true; M.hpBad++;
      const d = post.hp - g.hp;
      const castK = acts.filter((a) => a[0] === "cast").map((a) => KIND[(actor.kit[a[1]] || {}).kind || 0]).join("+") || "none";
      const why = j === 0 ? (Math.abs(d) <= 4 && d > 0 ? "self-regen" : `self(${castK})`) : `other(${castK}${acts.some((a) => a[0] === "attack") ? "+atk" : ""})`;
      note(`hp:${why}`, `${TYPE[actor.type]} -> ${TYPE[u.type]} sim ${g.hp.toFixed(0)} eng ${post.hp} pre ${u.hp} acts ${JSON.stringify(acts)}`);
    }
  });
  const pa = rec.post[rec.units.indexOf(actor)];
  if (pa && pa.alive) for (let s = 0; s < 2; s++) if (actor.kit[s] && Math.max(0, pa.cd[s]) !== got[0].cd[s]) { bad = true; M.cdBad++; note(`cd:${TYPE[actor.type]}:${KIND[actor.kit[s].kind]}`, `pre ${actor.cd[s]} sim ${got[0].cd[s]} eng ${pa.cd[s]} acts ${JSON.stringify(acts)}`); }
  if (!bad) M.ok++;
  if (camp) note("camp-involved", null);
}
console.log(`records ${used} (skipped recall/consumable/bank ${M.skipped})`);
console.log(`M mechanics: exact ${M.ok}/${M.n} (${(100 * M.ok / M.n).toFixed(1)}%); health wrong ${M.hpBad}, deaths wrong ${M.aliveBad}, cooldowns wrong ${M.cdBad}`);
for (const [k, v] of Object.entries(M.byCause).sort((a, b) => b[1] - a[1]).slice(0, 25)) console.log(`   ${k}: ${v}`);
console.log(`P policy: action class right ${(100 * P.cls / P.n).toFixed(1)}% of ${P.n}; attack target right ${(100 * P.tgt[0] / Math.max(1, P.tgt[1])).toFixed(1)}% (${P.tgt[1]}); move direction right ${(100 * P.dir[0] / Math.max(1, P.dir[1])).toFixed(1)}% (${P.dir[1]})`);
console.log("   real -> simulated (top):");
for (const [k, v] of Object.entries(P.conf).sort((a, b) => b[1] - a[1]).slice(0, 14)) console.log(`     ${k}: ${v}`);
if (DUMP) for (const e of M.ex) console.log("  EX " + e);
