// Solo farm benchmark (E68): BOT plays against an idle opponent (v4/bots/idle4: drafts, then never acts) on every map
// of the slices, both sides; the score is the round at which BOT has banked 1,000 gems (the game ends), capped at 2,000.
// Lower is better and does not depend on the opponent's style, so farming changes can be measured in our own lab.
// usage: node farm_bench.js BOT "dir:n:skip dir:n:skip" [workers=5]   (env FARM_KNOBS=k0,..: BOT's lab knobs)
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
process.env.LAB_DRAFT_FUEL = process.env.LAB_DRAFT_FUEL || "10000000";
const wasm = (b) => path.join(ROOT, "v4", "bots", b, ".cambc", "build-release", "bot-injected.wasm");

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    const files = job.side === 0 ? [job.bot, job.idle] : [job.idle, job.bot];
    H.knobs = job.k ? (job.side === 0 ? [job.k, null] : [null, job.k]) : null;
    let r;
    try { r = await H.play(files[0], files[1], job.map, 2000, null, {}); } catch (e) { r = { gems: [0, 0], round: 2000, error: String(e) }; }
    H.knobs = null;
    parentPort.postMessage({ id: job.id, round: r.gems[job.side] >= 1000 ? r.round : 2000, gems: r.gems[job.side], error: r.error || r.abort });
  }
  return;
}

const [bot, setsS, workersS] = process.argv.slice(2);
const NW = Math.min(8, +(workersS || 5));
const knobs = process.env.FARM_KNOBS ? process.env.FARM_KNOBS.split(",").map(Number) : null;
const maps = setsS.split(" ").filter(Boolean).flatMap((s) => {
  const [d, n, k] = s.split(":");
  return fs.readdirSync(path.resolve(ROOT, d)).filter((f) => f.endsWith(".map26a")).sort().slice(+(k || 0), +(k || 0) + +n).map((f) => path.resolve(ROOT, d, f));
});
const queue = [], slots = Array.from({ length: NW }, () => ({ w: null, games: 0, busy: null }));
let errors = 0;
function spawn(slot) {
  slot.w = new Worker(__filename); slot.games = 0;
  slot.w.on("message", (m) => { const job = slot.busy; slot.busy = null; if (m.error) errors++; job.res(m); if (++slot.games >= 40) { const old = slot.w; slot.w = null; old.terminate().then(() => { spawn(slot); pump(); }); return; } pump(); });
  slot.w.on("error", (e) => { console.log("worker error", String(e)); process.exit(2); });
}
function pump() { for (const s of slots) { if (!s.w || s.busy || !queue.length) continue; s.busy = queue.shift(); s.w.postMessage(s.busy.job); } }
let nextId = 0;
const run = (job) => new Promise((res) => { queue.push({ job: { ...job, id: nextId++ }, res }); pump(); });
for (const s of slots) spawn(s);
(async () => {
  const t0 = Date.now();
  const jobs = maps.flatMap((map) => [0, 1].map((side) => ({ map, side, bot: wasm(bot), idle: wasm("idle4"), k: knobs })));
  const rs = await Promise.all(jobs.map(run));
  const rounds = rs.map((r) => r.round), n = rounds.length;
  const mean = rounds.reduce((a, b) => a + b, 0) / n;
  const sd = Math.sqrt(rounds.reduce((a, b) => a + (b - mean) ** 2, 0) / n);
  const capped = rounds.filter((r) => r >= 2000).length;
  console.log(`${bot}: mean rounds to 1000 banked ${mean.toFixed(1)} (+- ${(sd / Math.sqrt(n)).toFixed(1)}) over ${n} games, unfinished ${capped} | ${((Date.now() - t0) / 1000).toFixed(0)} s, errors ${errors}`);
  fs.writeFileSync(path.join(__dirname, `farm_${bot}.json`), JSON.stringify(jobs.map((j, i) => ({ map: path.basename(j.map), side: j.side, round: rounds[i] }))));
  for (const s of slots) if (s.w) s.w.terminate();
})();
