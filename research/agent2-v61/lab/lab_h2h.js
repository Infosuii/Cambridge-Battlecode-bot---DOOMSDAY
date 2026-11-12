// Head-to-head in the engine host (engine 1.0.1, ~1 s per game, no fuel meter): bot A vs bot B on every map of a
// directory, both sides. Bots are cambc build folders (bots/<name>). Prints A's score, gem margin and per-size split.
// usage: node lab_h2h.js A B MAPDIR [nmaps=all] [workers=6] [skip=0]
// H2H_POLW=file.json: bot A is a policy lab build playing these weights greedily (ppo2_lab.js output, field w).
// H2H_KNOBS=k0,..,k23: bot A is a knob lab build (a2c_klab) playing these knobs.
// H2H_PER_MAP=3: three games per map - A on side 0 and 1 against B, then side 0 against B with seed 2 (sb_<B>_c1 -> c2),
// since the lab is deterministic and a repeated pairing replays the same game.
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v1_0_1.wasm");
const wasm = (b) => path.join(process.env.BOTS_DIR || path.join(ROOT, "v3", "bots"), b, ".cambc", "build-release", "bot-injected.wasm"); // BOTS_DIR: another workspace (v4/bots)

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    const files = job.side === 0 ? [job.a, job.b] : [job.b, job.a];
    H.polW = job.w ? (job.side === 0 ? [job.w, null] : [null, job.w]) : null;
    H.polMode = [0, 0];
    H.knobs = job.k ? (job.side === 0 ? [job.k, null] : [null, job.k]) : null;
    H.macroW = job.mw ? (job.side === 0 ? [job.mw, null] : [null, job.mw]) : null; // H2H_MACROW: bot A's A2_MACRO weights
    // H2H_BOOST=g: bot B's champions get g sandbox gold a turn (fractions spread over rounds) (a stand-in for an opponent that out-earns us, E65).
    const boost = +(process.env.H2H_BOOST || 0), bTeam = 1 - job.side;
    const hooks = boost > 0 ? { beforeTurn: (round, champ, team) => { const g = Math.floor(round * boost) - Math.floor((round - 1) * boost); if (team === bTeam && g > 0) H.ex.Game_Sandbox_GiveGold(H.g, champ, g); } } : {};
    // H2H_GIFT=round:gold:gems (E73): once, at its first turn from that round, each of bot A's champions gets that much
    // sandbox gold and carried gems (the value of each resource in wins, against the untouched games).
    // H2H_KILL=round:n (E73): once at that round, n living enemy champions die, credited to one of bot A's living ones.
    if (process.env.H2H_KILL) {
      const [kr, kn] = process.env.H2H_KILL.split(":").map(Number);
      let done = false;
      hooks.beforeTurn = (round) => {
        if (done || round < kr) return;
        done = true;
        const ex = H.ex, ci = H.arena + 2048, ab = H.arena + 2200, U = H.arena + 4096, V = H.arena + 4112;
        const unit = (ptr, h) => { H.m.setUint32(ptr, 1, true); H.m.setUint32(ptr + 4, h, true); H.m.setUint32(ptr + 8, 0, true); return ptr; };
        const champs = [];
        for (let h = 0; h < 12; h++) {
          if (ex.Game_API_Champion_Get(H.g, H.E.persp(2, 0xffffffff), h, ci) !== 0) continue;
          const alive = ex.Game_API_Champion_IsAlive(H.g, h, ab) === 0 && H.m.getUint8(ab) !== 0;
          champs.push({ h, team: H.m.getInt32(ci, true), hp: H.m.getFloat32(ci + 16, true), alive });
        }
        const killer = champs.find((c) => c.team === job.side && c.alive);
        if (!killer) return;
        champs.filter((c) => c.team !== job.side && c.alive).slice(0, kn).forEach((c) => ex.Game_Sandbox_Damage(H.g, unit(U, killer.h), unit(V, c.h), c.hp + 50));
      };
    }
    if (process.env.H2H_GIFT) {
      const [gr, gg, gm] = process.env.H2H_GIFT.split(":").map(Number), given = new Set();
      hooks.beforeTurn = (round, champ, team) => {
        if (team !== job.side || round < gr || given.has(champ)) return;
        given.add(champ);
        if (gg > 0) H.ex.Game_Sandbox_GiveGold(H.g, champ, gg);
        if (gm > 0) H.ex.Game_Sandbox_GiveGems(H.g, champ, gm);
      };
    }
    let r;
    try { r = await H.play(files[0], files[1], job.map, 2000, null, hooks); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    parentPort.postMessage({ id: job.id, gems: r.gems, error: r.error || r.abort });
  }
  return;
}

const [A, B, mapDirS, nmapsS, workersS, skipS] = process.argv.slice(2);
const NW = Math.min(8, +(workersS || 6));
const mapDir = path.resolve(mapDirS);
const maps = fs.readdirSync(mapDir).filter((f) => f.endsWith(".map26a")).sort().slice(+(skipS || 0), +(skipS || 0) + +(nmapsS || 100000));
const RECYCLE = 40, MAX_RSS = 4.5e9;
const queue = [];
const slots = Array.from({ length: NW }, () => ({ w: null, games: 0, busy: null }));
let errors = 0;
function abort(why) { console.log("ABORT:", why); for (const s of slots) if (s.w) s.w.terminate(); process.exit(2); }
function spawn(slot) {
  slot.w = new Worker(__filename); slot.games = 0;
  slot.w.on("message", (m) => { const job = slot.busy; slot.busy = null; if (m.error) errors++; job.res(m); if (++slot.games >= RECYCLE) { const old = slot.w; slot.w = null; old.terminate().then(() => { spawn(slot); pump(); }); return; } pump(); });
  slot.w.on("error", (e) => abort("worker error " + String(e)));
}
function pump() {
  if (process.memoryUsage().rss > MAX_RSS) abort("memory over 4.5 GB");
  for (const s of slots) { if (!s.w || s.busy || !queue.length) continue; s.busy = queue.shift(); s.w.postMessage(s.busy.job); }
}
let nextId = 0;
const run = (job) => new Promise((res) => { queue.push({ job: { ...job, id: nextId++ }, res }); pump(); });
for (const s of slots) spawn(s);

(async () => {
  const t0 = Date.now();
  const polw = process.env.H2H_POLW ? JSON.parse(fs.readFileSync(process.env.H2H_POLW, "utf8")).w : null;
  const knobs = process.env.H2H_KNOBS ? process.env.H2H_KNOBS.split(",").map(Number) : null; // bot A is a knob lab build
  const mw = process.env.H2H_MACROW ? process.env.H2H_MACROW.split(",").map(Number) : null;
  const per = +(process.env.H2H_PER_MAP || 2);
  const B2 = B.replace(/_c1$/, "_c2");
  const jobs = maps.flatMap((m) => [[0, B], [1, B], [0, B2], [1, B2]].slice(0, per).map(([side, b]) => ({ a: wasm(A), b: wasm(b), map: path.join(mapDir, m), side, w: polw, k: knobs, mw })));
  const rs = await Promise.all(jobs.map(run));
  let w = 0, margin = 0;
  rs.forEach((r, i) => { const s = jobs[i].side; w += r.gems[s] > r.gems[1 - s] ? 1 : r.gems[s] === r.gems[1 - s] ? 0.5 : 0; margin += r.gems[s] - r.gems[1 - s]; });
  const n = rs.length, p = w / n, se = Math.sqrt(p * (1 - p) / n);
  console.log(`${A} vs ${B} on ${path.basename(mapDir)}: ${w}/${n} = ${(100 * p).toFixed(1)}% +- ${(100 * se).toFixed(1)}, gem margin ${(margin / n).toFixed(0)} | ${((Date.now() - t0) / 1000).toFixed(0)} s, errors ${errors}`);
  for (const s of slots) if (s.w) s.w.terminate();
})();
