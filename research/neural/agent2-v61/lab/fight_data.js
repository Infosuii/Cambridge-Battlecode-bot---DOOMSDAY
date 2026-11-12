// Engine lab: real fight data for simulator fidelity work. Host games between real bots (a2c_combo against pool
// styles). At every champion turn with an enemy within 6 tiles: the state of every champion within 8 of the actor
// (position, health, strength, focus, range, gems, both cooldowns, stun / shield / enhanced buffs, kit), what the actor
// did (move, attack, cast with targets and return codes), and the same units right after its turn.
// usage: node fight_data.js out.jsonl games [seed=1] [workers=3]
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
const W = (name) => path.join(ROOT, "bots", name, ".cambc", "build-release", "bot-injected.wasm");
const BOTS = ["a2c_combo", "sb_v34c_b1", "sb_sparexp_b1", "sb_spartop_b1", "sb_farm_b1", "sb_aggro_b1"];
const MAPS = path.join(ROOT, "maps_rdev");

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => runJob(job).then((r) => parentPort.postMessage(r), (e) => parentPort.postMessage({ id: job.id, error: String(e) }))); });
  async function runJob(job) {
    const ex = H.ex, P = H.E.persp(2, 0xffffffff), ci = H.arena + 2048, o = H.arena + 2300, bd = H.arena + 2400, ap = H.arena + 2600;
    const kits = new Map(); // type -> [slot props]
    const kit = (h, type) => {
      if (kits.has(type)) return kits.get(type);
      const k = [0, 1].map((s) => {
        if (ex.Game_API_Champion_GetAbilityProps(H.g, P, h, s, ap) !== 0) return null;
        const d = H.m, kind = d.getUint32(ap, true);
        const f = (i) => d.getFloat32(ap + 20 + 4 * i, true), n = (i) => d.getInt32(ap + 20 + 4 * i, true);
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
    const unit = (h) => {
      if (ex.Game_API_Champion_Get(H.g, P, h, ci) !== 0) return null;
      const d = H.m;
      const alive = ex.Game_API_Champion_IsAlive(H.g, h, o) === 0 && d.getUint8(o) !== 0;
      const u = { h, team: d.getInt32(ci, true), type: d.getInt32(ci + 4, true), x: d.getInt32(ci + 8, true), y: d.getInt32(ci + 12, true),
        hp: +d.getFloat32(ci + 16, true).toFixed(1), maxhp: d.getFloat32(ci + 20, true), str: d.getFloat32(ci + 24, true), focus: d.getFloat32(ci + 28, true),
        range: d.getInt32(ci + 36, true), alive };
      u.gems = ex.Game_API_Champion_GetGems(H.g, P, h, o) === 0 ? d.getUint32(o, true) : 0;
      u.cd = [0, 1].map((s) => (ex.Game_API_Champion_GetCooldown(H.g, P, h, s, o) === 0 ? d.getInt32(o, true) : -1));
      if (ex.Game_API_Champion_GetBuffData(H.g, P, h, bd, 6, o) === 0) {
        const nb = d.getUint32(o, true);
        for (let i = 0; i < nb && i < 6; i++) {
          const t = d.getUint32(bd + 12 * i, true), dur = d.getInt32(bd + 12 * i + 4, true);
          if (t === 0) u.shield = [+d.getFloat32(bd + 12 * i + 8, true).toFixed(1), dur];
          else if (t === 1) u.stun = dur;
          else if (t === 2) u.enh = dur;
        }
      }
      return u;
    };
    const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
    const out = [];
    let cur = null;
    H.onAction = (champ, name, args, rc) => { if (cur && champ === cur.actor) cur.acts.push([name.replace("_with_result", ""), ...args, rc]); };
    const hooks = {
      beforeTurn: (round, champ) => {
        cur = null;
        const me = unit(champ);
        if (!me || !me.alive) return;
        // Every champion (dead ones are unreadable: logged as {h, alive: false}), and live camps within 10.
        const all = [];
        for (let h = 0; h < 12; h++) {
          const u = unit(h);
          if (u) all.push(u);
          else if (ex.Game_API_Champion_IsAlive(H.g, h, o) === 0) all.push({ h, alive: false, dead: true });
        }
        if (!all.some((u) => u.alive && u.team !== me.team && cheb(u, me) <= 6)) return;
        all.forEach((u) => { if (!u.dead) u.kit = kit(u.h, u.type); });
        const camps = [];
        const cb = H.arena + 2800, cn = H.arena + 2700;
        if (ex.Game_API_GetCamps(H.g, P, cb, 64, cn) === 0) {
          const nc = Math.min(64, H.m.getUint32(cn, true)), hs = [];
          for (let i = 0; i < nc; i++) hs.push(H.m.getUint32(cb + 4 * i, true));
          for (const ch of [...new Set(hs)]) {
            if (ex.Game_API_Camp_Get(H.g, P, ch, ap) !== 0) continue;
            const c = { h: ch, x: H.m.getInt32(ap, true), y: H.m.getInt32(ap + 4, true), hp: +H.m.getFloat32(ap + 8, true).toFixed(1), maxhp: H.m.getFloat32(ap + 12, true), str: H.m.getFloat32(ap + 16, true) };
            if (c.hp > 0 && cheb(c, me) <= 10) camps.push(c);
          }
        }
        cur = { game: job.gid, map: job.map, round, actor: champ, units: all, camps, acts: [] };
      },
      afterTurn: (round, champ) => {
        if (cur && champ === cur.actor) {
          cur.post = cur.units.map((u) => { const v = unit(u.h); return v ? { h: v.h, x: v.x, y: v.y, hp: v.hp, alive: v.alive, cd: v.cd, gems: v.gems } : { h: u.h, alive: false }; });
          out.push(cur);
          cur = null;
        }
        return false;
      },
    };
    const r = await H.play(W(job.a), W(job.b), path.join(MAPS, job.map), 2000, null, hooks);
    H.onAction = null;
    return { id: job.id, recs: out, round: r.round };
  }
  return;
}

const [outFile, nS, seedS, workersS] = process.argv.slice(2);
const N = +(nS || 20), NW = Math.min(4, +(workersS || 3));
let seed = +(seedS || 1);
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const maps = fs.readdirSync(MAPS).filter((f) => f.endsWith(".map26a")).sort();
// Memory-safe pool (see es_host.js).
const RECYCLE = 15, MAX_RSS = 3e9;
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
  let total = 0, done = 0;
  await Promise.all(Array.from({ length: N }, async (_, g) => {
    const opp = BOTS[1 + (g % (BOTS.length - 1))];
    const side = g % 2;
    const job = { gid: `${seedS || 1}-${g}`, map: maps[Math.floor(rnd() * maps.length)], a: side ? opp : BOTS[0], b: side ? BOTS[0] : opp };
    const r = await run(job);
    if (r.error) { console.log("game error", r.error); return; }
    fs.appendFileSync(outFile, r.recs.map((x) => JSON.stringify(x)).join("\n") + (r.recs.length ? "\n" : ""));
    total += r.recs.length;
    if (++done % 5 === 0) console.log(`${done}/${N} games, ${total} fight turns, memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`);
  }));
  console.log(`done: ${total} fight turns from ${done} games`);
  for (const s of slots) if (s.w) s.w.terminate();
})();
