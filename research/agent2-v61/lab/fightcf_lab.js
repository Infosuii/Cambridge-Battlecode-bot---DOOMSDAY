// Engine lab: fight-or-run counterfactuals. A lab build (team A) plays a pool opponent in the host; from a random
// round, at the first turn champion c has an enemy within 4, the game is played three ways (deterministic up to that
// turn): the bot's own verdict (recorded), forced fight and forced run for 3 rounds. Outcomes: deaths and health 3
// rounds on, the team gem margin 50 rounds on. The start state (all champions, kits, camps) is logged for features.
// usage: node fightcf_lab.js out.jsonl states [seed=1] [workers=3]
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
const W = (name) => path.join(ROOT, "bots", name, ".cambc", "build-release", "bot-injected.wasm");
const OPPS = ["sb_v34c_b1", "sb_sparexp_b1", "sb_spartop_b1", "sb_farm_b1", "sb_aggro_b1", "a2c_combo"];
const MAPS = path.join(ROOT, "maps_rdev");
const LEN = 3, H3 = 3, H50 = 50;

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => runJob(job).then((r) => parentPort.postMessage(r), (e) => parentPort.postMessage({ id: job.id, error: String(e) }))); });
  async function runJob(job) {
    const ex = H.ex, P = H.E.persp(2, 0xffffffff), ci = H.arena + 2048, o = H.arena + 2300, bd = H.arena + 2400, ap = H.arena + 2600;
    const kits = new Map();
    const kit = (h, type) => {
      if (kits.has(type)) return kits.get(type);
      const k = [0, 1].map((s) => {
        if (ex.Game_API_Champion_GetAbilityProps(H.g, P, h, s, ap) !== 0) return null;
        const d = H.m, kind = d.getUint32(ap, true), f = (i) => d.getFloat32(ap + 20 + 4 * i, true), n = (i) => d.getInt32(ap + 20 + 4 * i, true);
        const p = { kind, cd: d.getInt32(ap + 4, true), targets: d.getUint32(ap + 12, true), attrs: d.getUint32(ap + 16, true) };
        if (kind === 2 || kind === 5) Object.assign(p, { range: f(0), mod: f(1) });
        else if (kind === 3) Object.assign(p, { range: f(0), radius: f(1), mod: f(2), dur: n(3) });
        else if (kind === 4 || kind === 7) Object.assign(p, { range: f(0), mod: f(1), dur: n(2) });
        else if (kind === 6) Object.assign(p, { range: f(0) });
        return p;
      });
      kits.set(type, k);
      return k;
    };
    const alive = (h) => ex.Game_API_Champion_IsAlive(H.g, h, o) === 0 && H.m.getUint8(o) !== 0;
    const unit = (h) => {
      if (ex.Game_API_Champion_Get(H.g, P, h, ci) !== 0) return alive(h) ? null : { h, alive: false, dead: true };
      const d = H.m;
      const u = { h, team: d.getInt32(ci, true), type: d.getInt32(ci + 4, true), x: d.getInt32(ci + 8, true), y: d.getInt32(ci + 12, true),
        hp: +d.getFloat32(ci + 16, true).toFixed(1), maxhp: d.getFloat32(ci + 20, true), str: d.getFloat32(ci + 24, true), focus: d.getFloat32(ci + 28, true),
        range: d.getInt32(ci + 36, true), alive: alive(h) };
      u.gems = ex.Game_API_Champion_GetGems(H.g, P, h, o) === 0 ? d.getUint32(o, true) : 0;
      u.cd = [0, 1].map((s) => (ex.Game_API_Champion_GetCooldown(H.g, P, h, s, o) === 0 ? d.getInt32(o, true) : -1));
      if (ex.Game_API_Champion_GetBuffData(H.g, P, h, bd, 6, o) === 0) {
        const nb = d.getUint32(o, true);
        for (let i = 0; i < nb && i < 6; i++) {
          const t = d.getUint32(bd + 12 * i, true), dur = d.getInt32(bd + 12 * i + 4, true);
          if (t === 0) u.shield = [+d.getFloat32(bd + 12 * i + 8, true).toFixed(1), dur]; else if (t === 1) u.stun = dur; else if (t === 2) u.enh = dur;
        }
      }
      u.kit = kit(h, u.type);
      return u;
    };
    const camps = (me) => {
      const out = [], cb = H.arena + 2800, cn = H.arena + 2700;
      if (ex.Game_API_GetCamps(H.g, P, cb, 64, cn) !== 0) return out;
      const nc = Math.min(64, H.m.getUint32(cn, true)), hs = new Set();
      for (let i = 0; i < nc; i++) hs.add(H.m.getUint32(cb + 4 * i, true));
      for (const ch of hs) {
        if (ex.Game_API_Camp_Get(H.g, P, ch, ap) !== 0) continue;
        const c = { h: ch, x: H.m.getInt32(ap, true), y: H.m.getInt32(ap + 4, true), hp: +H.m.getFloat32(ap + 8, true).toFixed(1), maxhp: H.m.getFloat32(ap + 12, true), str: H.m.getFloat32(ap + 16, true) };
        if (c.hp > 0 && Math.max(Math.abs(c.x - me.x), Math.abs(c.y - me.y)) <= 10) out.push(c);
      }
      return out;
    };
    const teamGems = () => {
      const tot = [0, 0];
      for (let t = 0; t < 2; t++) if (ex.Game_API_GetSubmittedGemCount(H.g, t, o) === 0) tot[t] += H.m.getUint32(o, true);
      for (let h = 0; h < 12; h++) {
        if (ex.Game_API_Champion_Get(H.g, P, h, ci) !== 0) continue;
        const t = H.m.getInt32(ci, true);
        if (ex.Game_API_Champion_GetGems(H.g, P, h, o) === 0) tot[t] += H.m.getUint32(o, true);
      }
      return tot;
    };
    H.labCtl = { champ: job.champ, round: job.round, kind: job.kind, len: LEN };
    H.labRead = null;
    let pending = null, start = null, startRound = -1, verdict = null, out3 = null, out50 = null;
    const died = {};
    const hooks = {
      beforeTurn: (round, champ) => {
        if (startRound < 0 && round >= job.round && champ === job.champ) {
          const me = unit(champ);
          if (me && me.alive) {
            const all = [];
            for (let h = 0; h < 12; h++) { const u = unit(h); if (u) all.push(u); }
            pending = { round, units: all, camps: camps(me) };
          }
        }
      },
      afterTurn: (round, champ) => {
        if (startRound < 0 && champ === job.champ && H.labRead) {
          const rec = H.labRead();
          if (rec[9] >= 0 && pending && pending.round === round) { startRound = round; start = pending; verdict = rec[5]; }
        }
        if (startRound >= 0) {
          for (let h = 0; h < 12; h++) if (!died[h] && start.units.some((u) => u.h === h && u.alive) && !alive(h)) died[h] = round;
          if (!out3 && round >= startRound + H3) {
            const me = unit(job.champ);
            out3 = { meAlive: alive(job.champ), meHp: me && !me.dead ? me.hp / me.maxhp : 0, died: { ...died }, gems: teamGems() };
          }
          if (round >= startRound + H50) { out50 = { gems: teamGems() }; return true; }
        }
        return false;
      },
    };
    const lab = W("a2c_lab"), opp = W(job.opp);
    const r = await H.play(lab, opp, path.join(MAPS, job.map), job.round + 400, null, hooks);
    H.labCtl = null;
    return { id: job.id, startRound, verdict, start: job.kind === -4 ? start : null, out3, out50 };
  }
  return;
}

const [outFile, nS, seedS, workersS] = process.argv.slice(2);
const N = +(nS || 50), NW = Math.min(4, +(workersS || 3));
let seed = +(seedS || 1);
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const maps = fs.readdirSync(MAPS).filter((f) => f.endsWith(".map26a")).sort();
const RECYCLE = 30, MAX_RSS = 3e9;
const queue = [];
const slots = Array.from({ length: NW }, () => ({ w: null, games: 0, busy: null }));
function abort(why) { console.log("ABORT:", why); for (const s of slots) if (s.w) s.w.terminate(); process.exit(2); }
function spawn(slot) {
  slot.w = new Worker(__filename); slot.games = 0;
  slot.w.on("message", (m) => { const job = slot.busy; slot.busy = null; job.res(m); if (++slot.games >= RECYCLE) { const old = slot.w; slot.w = null; old.terminate().then(() => { spawn(slot); pump(); }); return; } pump(); });
  slot.w.on("error", (e) => abort("worker error " + String(e)));
}
function pump() {
  if (process.memoryUsage().rss > MAX_RSS) abort("memory over 3 GB");
  for (const s of slots) { if (!s.w || s.busy || !queue.length) continue; s.busy = queue.shift(); s.w.postMessage(s.busy.job); }
}
let nextId = 0;
const run = (job) => new Promise((res) => { queue.push({ job: { ...job, id: nextId++ }, res }); pump(); });
for (const s of slots) spawn(s);

(async () => {
  let done = 0, kept = 0;
  await Promise.all(Array.from({ length: N }, async () => {
    const s = { map: maps[Math.floor(rnd() * maps.length)], opp: OPPS[Math.floor(rnd() * OPPS.length)], round: 20 + Math.floor(rnd() * 300), champ: Math.floor(rnd() * 4) };
    const [base, fight, run_] = await Promise.all([-4, 4, 5].map((kind) => run({ ...s, kind })));
    done++;
    if (base.error || base.startRound < 0 || fight.startRound !== base.startRound || run_.startRound !== base.startRound || !base.out3 || !fight.out3 || !run_.out3) return;
    const pack = (r) => ({ meAlive: r.out3.meAlive, meHp: +r.out3.meHp.toFixed(3), died: r.out3.died, g3: r.out3.gems, g50: r.out50 ? r.out50.gems : null });
    fs.appendFileSync(outFile, JSON.stringify({ ...s, startRound: base.startRound, verdict: base.verdict, start: base.start, base: pack(base), fight: pack(fight), run: pack(run_) }) + "\n");
    kept++;
    if (done % 50 === 0) console.log(`${done}/${N} states, ${kept} kept, memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`);
  }));
  console.log(`done: ${kept} counterfactual states of ${done}`);
  for (const s of slots) if (s.w) s.w.terminate();
})();
