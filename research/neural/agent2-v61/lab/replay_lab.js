// Engine lab, trajectories (from micro_lab.js): with REPLAY_REC=1 the bot's own run records, for every fighter turn
// after setup, the fighters' full state before the turn and the actor's actions in order (replay_sim.js).
// Engine lab, micro labels (from duel_lab.js): every move/spell/attack option of the probe turn scored by the engine
// (all options on variant 0; each distinct executed action re-scored on variant 1; value = mean), plus the full start
// state, for training a move-scorer (micro_fit.py). Original duel_lab header follows.
// Engine lab: are our fights' ability choices good? Duels (1v1) and 2v2s with spells on, set up mid-game inside the
// engine host with the real bots. For each scenario the probe champion's turn is either the bot's own, or forced
// through every combination of move, spell (slot x target x before/after the move) and basic attack (and
// attack-cast-attack for resets); the real bots then play HORIZON more rounds and the fighters' lives and health are
// scored. The engine is deterministic: every option starts from the identical state.
// usage: node duel_lab.js out.jsonl scenarios [size=1|2] [seed=1] [workers=4]
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..", "..");
const BOT = path.join(ROOT, "bots", process.env.DUEL_BOT || "a2c_combo", ".cambc", "build-release", "bot-injected.wasm"); // DUEL_BOT: bots/<name>
const MAPS = path.join(ROOT, "maps_rdev");
const START = 3, HORIZON = 6;
const TYPES = [0, 1, 2, 5, 6, 7, 8, 9, 10, 11]; // all but the Cassi/Issac pair
const TYPE_NAMES = ["ryth", "vesper", "vendetta", "cassi", "issac", "stellar", "prism", "marcella", "willow", "ren", "varg", "tavi"];

// ---------------------------------------------------------------- worker: plays one (scenario, option)
if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => runJob(job).then((r) => parentPort.postMessage(r), (e) => parentPort.postMessage({ id: job.id, error: String(e) }))); });

  const ex2 = () => H.ex;
  function champInfo(h, full) {
    const ex = H.ex, d = () => H.m, info = H.arena + 2048, ab = H.arena + 2200;
    if (ex.Game_API_Champion_Get(H.g, H.E.persp(2, 0xffffffff), h, info) !== 0) return null;
    const alive = ex.Game_API_Champion_IsAlive(H.g, h, ab) === 0 && d().getUint8(ab) !== 0;
    const u = { h, team: d().getInt32(info, true), type: d().getInt32(info + 4, true), x: d().getInt32(info + 8, true), y: d().getInt32(info + 12, true),
      hp: alive ? d().getFloat32(info + 16, true) : 0, maxhp: d().getFloat32(info + 20, true), str: d().getFloat32(info + 24, true), focus: d().getFloat32(info + 28, true),
      range: d().getInt32(info + 36, true), alive };
    if (full) {
      const P2 = H.E.persp(2, 0xffffffff), o = H.arena + 2300, ap = H.arena + 2600, bd = H.arena + 2400;
      u.cd = [0, 1].map((s) => (ex2().Game_API_Champion_GetCooldown(H.g, P2, h, s, o) === 0 ? d().getInt32(o, true) : -1));
      u.kit = [0, 1].map((s) => {
        if (ex2().Game_API_Champion_GetAbilityProps(H.g, P2, h, s, ap) !== 0) return null;
        const kind = d().getUint32(ap, true), f = (i) => d().getFloat32(ap + 20 + 4 * i, true);
        const p = { kind, targets: d().getUint32(ap + 12, true), attrs: d().getUint32(ap + 16, true) };
        if (kind === 2 || kind === 5) Object.assign(p, { range: f(0), mod: f(1) });
        else if (kind === 3) Object.assign(p, { range: f(0), radius: f(1), mod: f(2) });
        else if (kind === 4 || kind === 7) Object.assign(p, { range: f(0), mod: f(1) });
        else if (kind === 6) Object.assign(p, { range: f(0) });
        return p;
      });
      if (ex2().Game_API_Champion_GetBuffData(H.g, P2, h, bd, 6, o) === 0) {
        const nb = d().getUint32(o, true);
        for (let i = 0; i < nb && i < 6; i++) { const t = d().getUint32(bd + 12 * i, true); if (t === 0) u.shield = d().getFloat32(bd + 12 * i + 8, true); else if (t === 1) u.stun = 1; else if (t === 2) u.enh = 1; }
      }
    }
    return u;
  }
  function setPos(ptr, x, y) { H.m.setInt32(ptr, x, true); H.m.setInt32(ptr + 4, y, true); return ptr; }
  function unitPtr(ptr, h) { H.m.setUint32(ptr, 1, true); H.m.setUint32(ptr + 4, h, true); H.m.setUint32(ptr + 8, 0, true); return ptr; }

  async function runJob(job) {
    const sc = job.sc;
    let fighters = null, probeDone = false, setup = false, actions = [], startState = null;
    const traj = [];
    let curTurn = null;
    const ex = H.ex;
    const U = H.arena + 4096, V = H.arena + 4112, P = H.arena + 4128, O = H.arena + 4144;
    const hooks = {
      draft: (team) => {
        hooks._n = hooks._n || [0, 0];
        return sc.types[team][hooks._n[team]++ % sc.types[team].length];
      },
      beforeTurn: (round) => {
        if (setup || round < START) return;
        setup = true;
        // Fighters: the first `size` champions of each team; everyone else stays near spawn.
        const all = [];
        for (let h = 0; h < 16; h++) { const c = champInfo(h); if (c) all.push(c); }
        const A = all.filter((c) => c.team === 0).slice(0, sc.size), B = all.filter((c) => c.team === 1).slice(0, sc.size);
        fighters = { A: A.map((c) => c.h), B: B.map((c) => c.h) };
        sc.cx = (H.m.getInt32(H.meta, true) >> 1) + sc.ox; sc.cy = (H.m.getInt32(H.meta + 4, true) >> 1) + sc.oy;
        const place = (h, x, y) => {
          for (let t = 0; t < 40; t++) {
            if (ex.Game_Sandbox_Teleport(H.g, unitPtr(U, h), setPos(P, x, y)) === 0) return true;
            x += (t % 3) - 1; y += ((t / 3) | 0) % 3 - 1;
          }
          return false;
        };
        A.forEach((c, i) => place(c.h, sc.cx - Math.ceil(sc.gap / 2), sc.cy + i * 2 - (sc.size - 1)));
        B.forEach((c, i) => place(c.h, sc.cx + Math.floor(sc.gap / 2), sc.cy + i * 2 - (sc.size - 1) + sc.skew));
        [...A, ...B].forEach((c, i) => {
          const frac = sc.hp[i];
          const amt = Math.floor(c.maxhp * (1 - frac));
          const src = (c.team === 0 ? B : A)[0].h;
          if (amt > 0) ex.Game_Sandbox_Damage(H.g, unitPtr(U, src), unitPtr(V, c.h), amt);
        });
      },
      force: (round, champ) => {
        if (process.env.REPLAY_REC && job.opt === null && setup && fighters && [...fighters.A, ...fighters.B].includes(champ)) {
          curTurn = { round, actor: champ, pre: [...fighters.A, ...fighters.B].map((h) => champInfo(h, true)), acts: [] };
        }
        if (!setup || probeDone || !fighters || champ !== fighters.A[0]) return null;
        probeDone = true;
        if (job.opt === null) {
          startState = [...fighters.A, ...fighters.B].map((h) => champInfo(h, true));
          H.onAction = (c, name, a, rc) => { if (c === champ && !probeDone2) actions.push([name, ...a, rc]); if (curTurn && c === curTurn.actor) curTurn.acts.push([name, ...a, rc]); };
          return null;
        }
        return () => play(job.opt, champ);
      },
      // (trajectory recording, REPLAY_REC)
      afterTurn: (round, champ) => {
        if (process.env.REPLAY_REC && curTurn && curTurn.actor === champ) { curTurn.post = [...fighters.A, ...fighters.B].map((h) => champInfo(h, true)); traj.push(curTurn); curTurn = null; }
        if (probeDone && champ === fighters.A[0]) probeDone2 = true;
        return round >= START + (sc.horizon || HORIZON);
      },
      final: () => {
        const val = (hs, sgn) => hs.reduce((s, h) => { const c = champInfo(h); return s + sgn * (c && c.alive ? 25 + 12 * c.hp / Math.max(1, c.maxhp) : 0); }, 0);
        return fighters ? { value: val(fighters.A, 1) + val(fighters.B, -1), types: { A: fighters.A.map((h) => champInfo(h).type), B: fighters.B.map((h) => champInfo(h).type) } } : null;
      },
    };
    let probeDone2 = false;
    // A forced turn: opt = { move: dir 0-8 (8 = stay), cast: null | {slot, tgt, when: "pre"|"post"}, attack: null | enemy index, reset: bool }
    function play(opt, champ) {
      const me = champInfo(champ);
      const enemies = fighters.B.map(champInfo), allies = fighters.A.filter((h) => h !== champ).map(champInfo);
      const done = [];
      const cast = () => {
        if (!opt.cast) return;
        const { slot, tgt } = opt.cast;
        let unit = 0, pos = setPos(P, 0, 0);
        const cur = champInfo(champ);
        if (tgt.startsWith("enemy")) { const e = enemies[+tgt.slice(5)]; if (!e) return; unit = unitPtr(U, e.h); setPos(P, e.x, e.y); }
        else if (tgt.startsWith("ally")) { const a = allies[+tgt.slice(4)]; if (!a) return; unit = unitPtr(U, a.h); setPos(P, a.x, a.y); }
        else if (tgt === "self") { unit = unitPtr(U, champ); setPos(P, cur.x, cur.y); }
        else if (tgt.startsWith("ground")) { const e = enemies[+tgt.slice(6)]; if (!e) return; const ec = champInfo(e.h); setPos(P, ec.x, ec.y); }
        const rc = ex.Game_Action_Cast(H.g, slot, unit, P, O);
        if (rc === 0) done.push(`cast${slot}:${tgt}`);
      };
      if (opt.cast && opt.cast.when === "pre") cast();
      if (opt.move !== 8) {
        const dx = [-1, 0, 1, -1, 1, -1, 0, 1][opt.move], dy = [-1, -1, -1, 0, 0, 1, 1, 1][opt.move];
        const c = champInfo(champ);
        if (ex.Game_Action_Move(H.g, c.x + dx, c.y + dy, O) === 0) done.push(`move${opt.move}`);
      }
      if (opt.cast && opt.cast.when === "post") cast();
      if (opt.attack !== null && enemies[opt.attack]) {
        if (ex.Game_Action_Attack(H.g, unitPtr(V, enemies[opt.attack].h)) === 0) done.push(`attack${opt.attack}`);
        if (opt.cast && opt.cast.when === "reset") { cast(); if (ex.Game_Action_Attack(H.g, unitPtr(V, enemies[opt.attack].h)) === 0) done.push(`attack${opt.attack}`); }
      }
      actions = done;
    }
    // MICRO_FIGHTONLY=1 (lab build as DUEL_BOT): every champion's fight verdict is forced to fight from the first turn an
    // enemy is within 4 (lab.h kind 4) - the continuation has no farming, recalling or regrouping.
    H.labCtlAll = process.env.MICRO_FIGHTONLY ? { kind: 4, round: START, len: 40 } : null;
    const r = await H.play(BOT, BOT, path.join(MAPS, sc.map), START + (sc.horizon || HORIZON) + 1, null, hooks);
    H.labCtlAll = null;
    H.onAction = null;
    return { id: job.id, value: r.final ? r.final.value : null, types: r.final ? r.final.types : null, actions, start: startState, traj };
  }
  return;
}

// ---------------------------------------------------------------- main
const [outFile, nS, sizeS, seedS, workersS] = process.argv.slice(2);
const N = +(nS || 10), SIZE = +(sizeS || 1), NW = Math.min(4, +(workersS || 4));
let seed = +(seedS || 1);
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const maps = fs.readdirSync(MAPS).filter((f) => f.endsWith(".map26a")).sort();

// Memory-safe pool (see es_host.js): one job at a time per worker, workers recycled, abort over 3 GB.
const RECYCLE = 60, MAX_RSS = 3e9; // ~6 MB leaked per game inside a worker: 60 games keeps 4 workers near 1.5 GB
const queue = [];
const slots = Array.from({ length: NW }, () => ({ w: null, games: 0, busy: null }));
function abort(why) { console.log("ABORT:", why); fs.appendFileSync(outFile, JSON.stringify({ abort: why }) + "\n"); for (const s of slots) if (s.w) s.w.terminate(); process.exit(2); }
function spawn(slot) {
  slot.w = new Worker(__filename); slot.games = 0;
  slot.w.on("message", (m) => {
    const job = slot.busy; slot.busy = null; job.res(m);
    if (++slot.games >= RECYCLE) { const old = slot.w; slot.w = null; old.terminate().then(() => { spawn(slot); pump(); }); return; }
    pump();
  });
  slot.w.on("error", (e) => abort("worker error " + String(e)));
}
function pump() {
  if (process.memoryUsage().rss > MAX_RSS) abort("memory over 3 GB");
  for (const s of slots) { if (!s.w || s.busy || !queue.length) continue; s.busy = queue.shift(); s.w.postMessage(s.busy.job); }
}
let nextId = 0;
const run = (job) => new Promise((res) => { queue.push({ job: { ...job, id: nextId++ }, res }); pump(); });
for (const s of slots) spawn(s);

function options(size) {
  const tgts = ["self", "enemy0", "ground0"];
  for (let i = 1; i < size; i++) tgts.push("enemy" + i, "ground" + i);
  for (let i = 0; i < size - 1; i++) tgts.push("ally" + i);
  const casts = [null];
  for (const slot of [0, 1]) for (const tgt of tgts) for (const when of ["pre", "post", "reset"]) casts.push({ slot, tgt, when });
  const attacks = [null]; for (let i = 0; i < size; i++) attacks.push(i);
  const out = [];
  for (let move = 0; move <= 8; move++)
    for (const cast of casts)
      for (const attack of attacks) {
        if (cast && cast.when === "reset" && attack === null) continue;
        out.push({ move, cast, attack });
      }
  return out;
}

(async () => {
  console.log(`${N} scenarios (sizes 1 and 2), options per scenario: 1v1 ${options(1).length}, 2v2 ${options(2).length}`);
  const jitter = (sc) => ({ ...sc, hp: sc.hp.map((x) => Math.min(1, Math.max(0.2, x + (rnd() - 0.5) * 0.06))), horizon: 6 });
  let done = 0;
  // Scenarios are drawn up front (deterministic), then labelled 6 at a time so the workers never idle.
  const todo = Array.from({ length: N }, (_, k) => k);
  const scen = todo.map((k) => {
    const size = rnd() < 0.7 ? 1 : 2;
    const pick = () => TYPES[Math.floor(rnd() * TYPES.length)];
    const sc = { map: maps[Math.floor(rnd() * maps.length)], size, types: [[pick(), pick(), pick(), pick()], [pick(), pick(), pick(), pick()]],
      gap: 1 + Math.floor(rnd() * 3), skew: Math.floor(rnd() * 3) - 1, hp: Array.from({ length: 2 * size }, () => 0.3 + 0.7 * rnd()),
      ox: Math.floor(rnd() * 9) - 4, oy: Math.floor(rnd() * 9) - 4 };
    return { k, sc, sc1: jitter(sc) };
  });
  const SKIP = +(process.env.MICRO_SKIP || 0);
  async function label({ k, sc }) {
    const own = await run({ sc, opt: null });
    if (own.value === null || !own.start || !own.traj || !own.traj.length) return;
    fs.appendFileSync(outFile, JSON.stringify({ k, size: sc.size, map: sc.map, start: own.start, traj: own.traj, value: own.value }) + "\n");
    if (++done % 25 === 0) console.log(`${done} trajectories, memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`);
  }  let next = SKIP;
  await Promise.all(Array.from({ length: 6 }, async () => { while (next < scen.length) await label(scen[next++]); }));
  console.log(`done: ${done} labelled scenarios`);
  for (const s of slots) if (s.w) s.w.terminate();
})();