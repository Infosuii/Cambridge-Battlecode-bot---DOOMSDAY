// Item build search per champion (lab build table, lab.h builds). For each champion, a lineup led by it (the rest from
// L21) plays nb1 on the same maps and sides for every candidate build of that champion (paired); other champions keep
// the bot's default build. Candidates: the default, and 9 shapes x main stat strength / focus.
// usage: node build_lab.js out.json [games=40] [workers=6] [champs=all]
// env: CONFIRM_FROM=screen.json - per champion only the default and its top CONFIRM_TOP (2) screen candidates;
//      BUILD_SEED - map sample seed (use a new one to confirm on fresh games)
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v1_0_1.wasm");
const LAB = path.join(ROOT, "v3", "bots", "a2c_mlab", ".cambc", "build-release", "bot-injected.wasm");
const NB1 = path.join(ROOT, "v3", "bots", "sb_nb1_c1", ".cambc", "build-release", "bot-injected.wasm");
const SLOT = 17;
// Champions by draft id -> champion types (C&I is two types).
const CHAMPS = { ryth: [0, [0]], vesper: [1, [1]], vendetta: [2, [2]], ci: [3, [3, 4]], stellar: [4, [5]], prism: [5, [6]],
  marcella: [6, [7]], willow: [7, [8]], ren: [8, [9]], varg: [9, [10]], tavi: [10, [11]], heart: [11, [12]] };
const L21 = [11, 2, 9, 0, 6, 7, 4, 10, 8, 5, 3, 1];
const sh = (fam, stat) => fam * 6 + stat * 2; // families: monster 0, power 1, durability 2, treasure 3, jungle 4, home 5, bruiser 6
const SHAPES = {
  pure: (S) => [[sh(1, S), 60]],
  monster: (S) => [[sh(0, S), 5], [sh(1, S), 60]],
  jungle: (S) => [[sh(4, S), 5], [sh(1, S), 60]],
  durab: (S) => [[sh(2, 2), 5], [sh(1, S), 60]],
  tank: (S) => [[sh(1, 2), 30], [sh(1, S), 60]],
  treasure: (S) => [[sh(3, S), 5], [sh(1, S), 60]],
  bruiser: (S) => [[sh(6, S), 5], [sh(1, S), 60]],
  mixed: (S) => [[sh(0, S), 5], [sh(4, 2), 5], [sh(1, S), 30], [sh(1, 2), 60]],
  home: (S) => [[sh(5, 2), 5], [sh(1, S), 60]],
};
const CANDS = [["default", null]];
for (const [name, f] of Object.entries(SHAPES)) for (const [sn, S] of [["str", 0], ["foc", 1]]) CANDS.push([`${name}-${sn}`, f(S)]);

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    const n = [0, 0];
    const hooks = { draft: (team) => (team === job.side ? job.lineup[n[team]++ % job.lineup.length] : -1) };
    // The opponent drafts itself: its draft hook answer is ignored when it is -1 (the host takes the next free type),
    // so let the nb1 draft run instead by only forcing our team.
    const files = job.side === 0 ? [LAB, NB1] : [NB1, LAB];
    H.builds = job.table ? (job.side === 0 ? [job.table, null] : [null, job.table]) : null;
    let r;
    try { r = await H.play(files[0], files[1], job.map, 2000, null, job.forceOnly ? { draft: (team) => (team === job.side ? job.lineup[n[team]++ % job.lineup.length] : null) } : hooks); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    H.builds = null;
    const s = job.side;
    parentPort.postMessage({ id: job.id, win: r.gems[s] > r.gems[1 - s] ? 1 : r.gems[s] === r.gems[1 - s] ? 0.5 : 0, margin: r.gems[s] - r.gems[1 - s], error: r.error || r.abort });
  }
  return;
}

const [outFile, gamesS, workersS, champsS] = process.argv.slice(2);
const GAMES = +(gamesS || 40), NW = Math.min(8, +(workersS || 6));
const champs = champsS ? champsS.split(",") : Object.keys(CHAMPS);
const mapList = [[path.join(ROOT, "v3", "maps_new"), 150], [path.join(ROOT, "v3", "maps"), 35]]
  .flatMap(([d, k]) => fs.readdirSync(d).filter((f) => f.endsWith(".map26a")).sort().slice(0, k).map((f) => path.join(d, f)));
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
  const out = fs.existsSync(outFile) ? JSON.parse(fs.readFileSync(outFile, "utf8")) : {};
  const t0 = Date.now();
  let seed = +(process.env.BUILD_SEED || 11);
  const screen = process.env.CONFIRM_FROM ? JSON.parse(fs.readFileSync(process.env.CONFIRM_FROM, "utf8")) : null;
  const TOP = +(process.env.CONFIRM_TOP || 2);
  const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
  for (const c of champs) {
    if (out[c]) continue;
    const [did, types] = CHAMPS[c];
    const lineup = [did, ...L21.filter((x) => x !== did)];
    const games = Array.from({ length: GAMES }, (_, g) => ({ map: mapList[Math.floor(rnd() * mapList.length)], side: g % 2 }));
    const res = {};
    let cands = CANDS;
    if (screen && screen[c]) {
      const top = Object.entries(screen[c]).filter(([n]) => n !== "default").sort((a, b) => b[1].win - a[1].win).slice(0, TOP).map(([n]) => n);
      cands = CANDS.filter(([n]) => n === "default" || top.includes(n));
    }
    await Promise.all(cands.map(async ([name, steps]) => {
      let table = null;
      if (steps) {
        table = new Array(16 * SLOT).fill(0);
        for (const t of types) { table[t * SLOT] = steps.length; steps.forEach(([id, tot], k) => { table[t * SLOT + 1 + 2 * k] = id; table[t * SLOT + 2 + 2 * k] = tot; }); }
      }
      const rs = await Promise.all(games.map((g) => run({ ...g, lineup, table, forceOnly: true })));
      res[name] = { win: rs.reduce((a, r) => a + r.win, 0) / rs.length, margin: rs.reduce((a, r) => a + r.margin, 0) / rs.length, wins: rs.map((r) => r.win) };
    }));
    out[c] = res;
    fs.writeFileSync(outFile, JSON.stringify(out));
    const base = res.default.win;
    const top = Object.entries(res).sort((a, b) => b[1].win - a[1].win).slice(0, 4);
    console.log(`${c}: default ${(100 * base).toFixed(0)}% | best ${top.map(([n, v]) => `${n} ${(100 * v.win).toFixed(0)}% (${v.margin >= 0 ? "+" : ""}${v.margin.toFixed(0)})`).join(", ")} | ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}`);
  }
  for (const s of slots) if (s.w) s.w.terminate();
})();
