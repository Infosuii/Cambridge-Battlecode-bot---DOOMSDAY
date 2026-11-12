// Engine lab: what is a life, a health bar and a carried gem worth in final gems? Real bot games in the host; at a
// random round one champion is (a) killed, (b) cut by half its maximum health, or (c) given 20 gems, and the game is
// played to the end. The change in that champion's team gem margin against the identical untouched game (the host is
// deterministic) is the value of the perturbation. Calibrates the simulator's value weights (alive 25, hp 12, gem 1).
// usage: node calib_lab.js out.jsonl states [seed=1] [workers=2]
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
const BOT = path.join(ROOT, "bots", "a2c_combo", ".cambc", "build-release", "bot-injected.wasm");
const MAPS = path.join(ROOT, "maps_rdev");

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => runJob(job).then((r) => parentPort.postMessage(r), (e) => parentPort.postMessage({ id: job.id, error: String(e) }))); });
  async function runJob(job) {
    const ex = H.ex, U = H.arena + 4096, V = H.arena + 4112;
    const unitPtr = (ptr, h) => { H.m.setUint32(ptr, 1, true); H.m.setUint32(ptr + 4, h, true); H.m.setUint32(ptr + 8, 0, true); return ptr; };
    let done = false, info = null;
    const hooks = {
      beforeTurn: (round) => {
        if (done || round < job.round) return;
        done = true;
        const ci = H.arena + 2048, ab = H.arena + 2200;
        const get = (h) => {
          if (ex.Game_API_Champion_Get(H.g, H.E.persp(2, 0xffffffff), h, ci) !== 0) return null;
          const alive = ex.Game_API_Champion_IsAlive(H.g, h, ab) === 0 && H.m.getUint8(ab) !== 0;
          const gems = ex.Game_API_Champion_GetGems(H.g, H.E.persp(2, 0xffffffff), h, ab) === 0 ? H.m.getUint32(ab, true) : 0;
          return { h, team: H.m.getInt32(ci, true), hp: H.m.getFloat32(ci + 16, true), maxhp: H.m.getFloat32(ci + 20, true), alive, gems };
        };
        const c = get(job.champ), foe = [0, 1, 2, 3, 4, 5, 6, 7].map(get).find((x) => x && x.team !== (c && c.team));
        if (!c || !c.alive || !foe) { info = { skipped: true }; return; }
        info = { team: c.team, hpf: c.hp / c.maxhp, gems: c.gems };
        if (job.kind === "kill") ex.Game_Sandbox_Damage(H.g, unitPtr(U, foe.h), unitPtr(V, c.h), c.hp + 50);
        else if (job.kind === "half") { if (c.hp > c.maxhp * 0.55) ex.Game_Sandbox_Damage(H.g, unitPtr(U, foe.h), unitPtr(V, c.h), c.maxhp * 0.5); else info.skipped = true; }
        else if (job.kind === "gems") ex.Game_Sandbox_GiveGems(H.g, c.h, 20);
        const after = get(c.h); info.after = after ? { hpf: +(after.hp / after.maxhp).toFixed(2), alive: after.alive, gems: after.gems } : null;
      },
    };
    // Horizon: 100 rounds after the change; team gems = submitted + carried by living champions.
    hooks.final = () => {
      const tot = [0, 0];
      for (let t = 0; t < 2; t++) if (ex.Game_API_GetSubmittedGemCount(H.g, t, H.arena + 2300) === 0) tot[t] += H.m.getUint32(H.arena + 2300, true);
      for (let h = 0; h < 8; h++) {
        const ci = H.arena + 2048;
        if (ex.Game_API_Champion_Get(H.g, H.E.persp(2, 0xffffffff), h, ci) !== 0) continue;
        const team = H.m.getInt32(ci, true);
        if (ex.Game_API_Champion_GetGems(H.g, H.E.persp(2, 0xffffffff), h, H.arena + 2300) === 0) tot[team] += H.m.getUint32(H.arena + 2300, true);
      }
      return tot;
    };
    const r = await H.play(BOT, BOT, path.join(MAPS, job.map), job.round + 100, null, hooks);
    return { id: job.id, gems: r.final || r.gems, round: r.round, info };
  }
  return;
}

const [outFile, nS, seedS, workersS] = process.argv.slice(2);
const N = +(nS || 50), NW = Math.min(4, +(workersS || 2));
let seed = +(seedS || 1);
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const maps = fs.readdirSync(MAPS).filter((f) => f.endsWith(".map26a")).sort();
const RECYCLE = 40, MAX_RSS = 3e9;
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
  const states = Array.from({ length: N }, () => ({ map: maps[Math.floor(rnd() * maps.length)], round: 60 + Math.floor(rnd() * 240), champ: Math.floor(rnd() * 8) }));
  await Promise.all(states.map(async (s, k) => {
    const [base, kill, half, gems] = await Promise.all(["none", "kill", "half", "gems"].map((kind) => run({ ...s, kind })));
    if (!kill.info || kill.info.skipped || base.error) return;
    const t = kill.info.team, margin = (r) => r.gems[t] - r.gems[1 - t];
    if (process.env.CALIB_DEBUG) console.log(JSON.stringify({ base: [base.gems, base.round], kill: [kill.gems, kill.round], half: [half.gems, half.round], gems: [gems.gems, gems.round] }));
    const rec = { ...s, team: t, hpf: +kill.info.hpf.toFixed(2), carried: kill.info.gems, baseRound: base.round,
      dKill: margin(kill) - margin(base), dHalf: half.info && !half.info.skipped ? margin(half) - margin(base) : null, dGems: margin(gems) - margin(base) };
    fs.appendFileSync(outFile, JSON.stringify(rec) + "\n");
  }));
  const rows = fs.readFileSync(outFile, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
  const mean = (a) => a.reduce((x, y) => x + y, 0) / Math.max(1, a.length);
  const se = (a) => { const m = mean(a); return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / Math.max(1, a.length - 1) / Math.max(1, a.length)); };
  const k = rows.map((r) => r.dKill), h = rows.filter((r) => r.dHalf !== null).map((r) => r.dHalf), g = rows.map((r) => r.dGems);
  console.log(`${rows.length} states. Final gem-margin change: death ${mean(k).toFixed(1)} Â± ${se(k).toFixed(1)}; half a health bar ${mean(h).toFixed(1)} Â± ${se(h).toFixed(1)} (n ${h.length}); +20 carried gems ${mean(g).toFixed(1)} Â± ${se(g).toFixed(1)}`);
  for (const s of slots) if (s.w) s.w.terminate();
})();
