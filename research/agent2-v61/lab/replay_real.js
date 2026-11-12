// Replays real-engine games (cambc run-batch outputs: <dir>/<u|o>_<map>_<A|B>.json, CAND as team A in _A files) in the
// lab with the same bots, map and sides, and compares the results game by game: does the lab reproduce the engine?
// usage: node replay_real.js RESULT_DIR CAND OTHER MAPDIR_U MAPDIR_O [workers=6]
//   e.g. node replay_real.js v4/bench_out/t61real t61_c1 t58 v4/maps_real250 v4/maps
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
const wasmOf = (b) => path.join(ROOT, "v4", "bots", b, ".cambc", "build-release", "bot-injected.wasm");

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(async () => {
    let r;
    try { r = await H.play(job.a, job.b, job.map, 2000, null, {}); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    parentPort.postMessage({ id: job.id, gems: r.gems, round: r.round });
  }); });
  return;
}
const [dirS, cand, other, mapU, mapO, workersS] = process.argv.slice(2);
const dir = path.resolve(ROOT, dirS);
const files = fs.readdirSync(dir).filter((f) => f.endsWith(".json")).sort();
const jobs = files.map((f, i) => {
  const base = f.slice(0, -5), kind = base[0], side = base.slice(-1), map = base.slice(2, -2);
  const j = JSON.parse(fs.readFileSync(path.join(dir, f), "utf8")).match;
  const me = side === "A" ? "teamA" : "teamB";
  return { id: i, f, side, map: path.resolve(ROOT, kind === "u" ? mapU : mapO, map + ".map26a"), a: wasmOf(side === "A" ? cand : other), b: wasmOf(side === "A" ? other : cand),
    real: j.outcome === me ? 1 : j.outcome === "teamA" || j.outcome === "teamB" ? 0 : 0.5, realRounds: j.roundsCompleted };
});
const NW = +(workersS || 6), queue = [...jobs], res = [];
let live = 0;
const next = (w) => { const j = queue.shift(); if (!j) { w.terminate(); if (--live === 0) done(); return; } w.postMessage(j); };
for (let k = 0; k < NW; k++) { const w = new Worker(__filename); live++; w.on("message", (m) => { res[m.id] = m; next(w); }); next(w); }
function done() {
  let agree = 0, labW = 0, realW = 0, sameRounds = 0;
  const diff = [];
  jobs.forEach((j, i) => {
    const r = res[i], s = j.side === "A" ? 0 : 1;
    const lab = r.gems[s] > r.gems[1 - s] ? 1 : r.gems[s] === r.gems[1 - s] ? 0.5 : 0;
    labW += lab, realW += j.real, agree += lab === j.real;
    if (Math.abs(r.round - j.realRounds) <= 1) sameRounds++;
    if (lab !== j.real) diff.push(`${j.f}: real ${j.real} (round ${j.realRounds}) lab ${lab} (round ${r.round}, gems ${r.gems})`);
  });
  console.log(`${jobs.length} games: real ${realW}/${jobs.length}, lab ${labW}/${jobs.length}; same winner ${agree}/${jobs.length}; same length (+-1 round) ${sameRounds}/${jobs.length}`);
  console.log(diff.slice(0, 12).join("\n"));
}
