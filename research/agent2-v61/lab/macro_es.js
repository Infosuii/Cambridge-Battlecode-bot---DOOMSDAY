// Strategy-switcher policy search (E70): evolution strategies over the A2_MACRO weights (lab.h macro_w: 4 styles x 6
// features = 24). Every candidate plays the same games against a league: v61_c2 and b5_c2, each plain and with the
// 0.25-gold-a-turn handicap for them (the out-earned case of the platform losses). Score = win + gem margin / 2000;
// antithetic pairs, rank-normalised update. Fresh training maps every generation (maps_new4, official, maps_maze).
// usage: node macro_es.js out.tsv [gens=20] [pairs=10] [maps=13] [sigma=0.5] [lr=0.2] [workers=5]   (env MACRO_BOT=p63mac)
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
process.env.LAB_DRAFT_FUEL = process.env.LAB_DRAFT_FUEL || "10000000";
const wasm = (b) => path.join(ROOT, "v4", "bots", b, ".cambc", "build-release", "bot-injected.wasm");
const US = wasm(process.env.MACRO_BOT || "p63mac");
const LEAGUE = [["v61_c2", 0], ["b5_c2", 0], ["v61_c2", 0.25], ["b5_c2", 0.25]];
const NW_ = 24;

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    const files = job.side === 0 ? [US, wasm(job.opp)] : [wasm(job.opp), US];
    H.macroW = job.side === 0 ? [job.w, null] : [null, job.w];
    const bTeam = 1 - job.side;
    const hooks = job.boost > 0 ? { beforeTurn: (round, champ, team) => { const g = Math.floor(round * job.boost) - Math.floor((round - 1) * job.boost); if (team === bTeam && g > 0) H.ex.Game_Sandbox_GiveGold(H.g, champ, g); } } : {};
    let r;
    try { r = await H.play(files[0], files[1], job.map, 2000, null, hooks); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    H.macroW = null;
    const us = r.gems[job.side], them = r.gems[1 - job.side];
    const win = us > them ? 1 : us === them ? 0.5 : 0;
    parentPort.postMessage({ id: job.id, s: win + (us - them) / 2000, win, error: r.error || r.abort });
  }
  return;
}

const [outFile, gensS, pairsS, mapsS, sigmaS, lrS, workersS] = process.argv.slice(2);
const GENS = +(gensS || 20), PAIRS = +(pairsS || 10), NMAPS = +(mapsS || 13), SIGMA = +(sigmaS || 0.5), LR = +(lrS || 0.2), NW = Math.min(8, +(workersS || 5));
const all = ["maps_new4", "maps", "maps_maze"].flatMap((d) => fs.readdirSync(path.join(ROOT, "v4", d)).filter((f) => f.endsWith(".map26a")).sort().map((f) => path.join(ROOT, "v4", d, f)));
let seed = +(process.env.ES_SEED || 70);
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const gauss = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());
const queue = [], slots = Array.from({ length: NW }, () => ({ w: null, games: 0, busy: null }));
let errors = 0;
function spawn(slot) {
  slot.w = new Worker(__filename); slot.games = 0;
  slot.w.on("message", (m) => { const job = slot.busy; slot.busy = null; if (m.error) errors++; job.res(m); if (++slot.games >= 40) { const old = slot.w; slot.w = null; old.terminate().then(() => { spawn(slot); pump(); }); return; } pump(); });
  slot.w.on("error", (e) => { console.log("ABORT: worker error", String(e)); process.exit(2); });
}
function pump() {
  if (process.memoryUsage().rss > 4.5e9) { console.log("ABORT: memory"); process.exit(2); }
  for (const s of slots) { if (!s.w || s.busy || !queue.length) continue; s.busy = queue.shift(); s.w.postMessage(s.busy.job); }
}
let nextId = 0;
const run = (job) => new Promise((res) => { queue.push({ job: { ...job, id: nextId++ }, res }); pump(); });
for (const s of slots) spawn(s);
const mean = (a, f) => a.reduce((x, y) => x + f(y), 0) / a.length;
(async () => {
  const t0 = Date.now();
  const theta = process.env.MACRO_INIT ? process.env.MACRO_INIT.split(",").map(Number) : new Array(NW_).fill(0);
  fs.writeFileSync(outFile, ["gen", "win_centre", "s_centre", "best_gain", ...theta.map((_, i) => `w${i}`)].join("\t") + "\n");
  for (let g = 1; g <= GENS; g++) {
    const pool = all.slice(), maps = [];
    while (maps.length < NMAPS && pool.length) maps.push(pool.splice(Math.floor(rnd() * pool.length), 1)[0]);
    const games = maps.flatMap((map) => LEAGUE.flatMap(([opp, boost]) => [0, 1].map((side) => ({ map, opp, boost, side }))));
    const play = (w) => Promise.all(games.map((gm) => run({ ...gm, w })));
    const eps = Array.from({ length: PAIRS }, () => Array.from({ length: NW_ }, gauss));
    const centreP = play(theta.slice());
    const fs_ = [];
    await Promise.all(eps.flatMap((e, p) => [1, -1].map(async (sg) => { fs_[2 * p + (sg > 0 ? 0 : 1)] = mean(await play(theta.map((t, i) => t + sg * SIGMA * e[i])), (r) => r.s); })));
    const centre = await centreP, sc = mean(centre, (r) => r.s);
    const order = fs_.map((f, i) => [f, i]).sort((a, b) => a[0] - b[0]), rank = new Array(fs_.length);
    order.forEach(([, i], r) => { rank[i] = r / (fs_.length - 1) - 0.5; });
    for (let i = 0; i < NW_; i++) {
      let gs = 0;
      for (let p = 0; p < PAIRS; p++) gs += (rank[2 * p] - rank[2 * p + 1]) * eps[p][i];
      theta[i] += LR * gs / (PAIRS * SIGMA);
    }
    fs.appendFileSync(outFile, [g, mean(centre, (r) => r.win).toFixed(4), sc.toFixed(4), (Math.max(...fs_) - sc).toFixed(4), ...theta.map((t) => t.toFixed(4))].join("\t") + "\n");
    console.log(`gen ${g}: centre win ${(100 * mean(centre, (r) => r.win)).toFixed(1)}% on ${games.length} games | best candidate +${(Math.max(...fs_) - sc).toFixed(3)} | ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}`);
  }
  console.log("final weights:", theta.map((t) => t.toFixed(4)).join(","));
  for (const s of slots) if (s.w) s.w.terminate();
})();
