// Item builds with the cambc 4.0.0 emblems (engine 2.0.0): our v57 lab bot follows a candidate build (lab.h build
// table, every champion type) against v57 with its own builds; both draft themselves. Paired: every candidate plays the
// same maps and sides. Build steps are (item, total shards wanted); 5 shards make an emblem (Greed 25).
// usage: node item_v4.js out.json [maps=50] [workers=6] [builds=all]   (maps from v4/maps_test4, spread over the set)
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
const wasmOf = (b) => path.join(ROOT, "v4", "bots", b, ".cambc", "build-release", "bot-injected.wasm");
const US = wasmOf(process.env.ITEM_US || "v57_c1"), THEM = wasmOf(process.env.ITEM_THEM || "v57_c2");

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    const files = job.side === 0 ? [US, THEM] : [THEM, US];
    H.builds = job.table ? (job.side === 0 ? [job.table, null] : [null, job.table]) : null;
    H.knobs = job.knobs ? (job.side === 0 ? [job.knobs, null] : [null, job.knobs]) : null; // ITEM_KNOBS: our side's lab knobs
    let r;
    try { r = await H.play(files[0], files[1], job.map, 2000, null, {}); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    H.builds = null; H.knobs = null;
    const s = job.side;
    parentPort.postMessage({ id: job.id, win: r.gems[s] > r.gems[1 - s] ? 1 : r.gems[s] === r.gems[1 - s] ? 0.5 : 0, margin: r.gems[s] - r.gems[1 - s], error: r.error || r.abort });
  }
  return;
}

// Families: monster 0, power 1, durability 2, treasure 3, jungle 4, home 5, bruiser 6, tribute 7, capture 8,
// prospector 9, hunter 10, skirmish 11, greed 12, collectors 13. Stats: strength 0, focus 1, health 2.
const F = { monster: 0, power: 1, durability: 2, treasure: 3, jungle: 4, home: 5, bruiser: 6, tribute: 7, capture: 8, prospector: 9, hunter: 10, skirmish: 11, greed: 12, collectors: 13 };
const sh = (fam, stat) => F[fam] * 6 + stat * 2;
const CASTERS = new Set([3, 5, 6]); // cassi, stellar, prism (champion_type)
// A build is a function of the main stat S (focus for casters, strength otherwise) -> [[item, total], ...].
const tail = (S) => [[sh("bruiser", S), 40], [sh("bruiser", 2), 60]];
const BUILDS = {
  v57like: (S) => [[sh("treasure", S === 1 ? 1 : 2), 5], [sh("jungle", S), 5], [sh("durability", 2), 5], ...tail(S)],
  capFirst: (S) => [[sh("capture", 2), 5], [sh("treasure", S === 1 ? 1 : 2), 5], [sh("jungle", S), 5], [sh("durability", 2), 5], ...tail(S)],
  capNoTreasure: (S) => [[sh("capture", 2), 5], [sh("jungle", S), 5], [sh("durability", 2), 5], ...tail(S)],
  capTribute: (S) => [[sh("capture", 2), 5], [sh("tribute", 2), 5], [sh("jungle", S), 5], [sh("durability", 2), 5], ...tail(S)],
  capMonster: (S) => [[sh("capture", 2), 5], [sh("monster", S), 5], [sh("jungle", S), 5], ...tail(S)],
  capProspector: (S) => [[sh("capture", 2), 5], [sh("prospector", S), 5], [sh("jungle", S), 5], [sh("durability", 2), 5], ...tail(S)],
  capSkirmish: (S) => [[sh("capture", 2), 5], [sh("jungle", S), 5], [sh("skirmish", S), 5], [sh("durability", 2), 5], ...tail(S)],
  capCollectors: (S) => [[sh("capture", 2), 5], [sh("jungle", S), 5], [sh("durability", 2), 5], [sh("collectors", S), 5], [sh("monster", S), 5], ...tail(S)],
  treasureThenCap: (S) => [[sh("treasure", S === 1 ? 1 : 2), 5], [sh("capture", 2), 5], [sh("jungle", S), 5], [sh("durability", 2), 5], ...tail(S)],
  capGreed: (S) => [[sh("capture", 2), 5], [sh("jungle", S), 5], [sh("durability", 2), 5], [sh("greed", S), 25], [sh("bruiser", 2), 60]],
  capProsMonster: (S) => [[sh("capture", 2), 5], [sh("prospector", S), 5], [sh("monster", S), 5], [sh("jungle", S), 5], ...tail(S)],
  prospectorFirst: (S) => [[sh("prospector", S), 5], [sh("capture", 2), 5], [sh("jungle", S), 5], [sh("durability", 2), 5], ...tail(S)],
  prosNoCap: (S) => [[sh("prospector", S), 5], [sh("jungle", S), 5], [sh("durability", 2), 5], ...tail(S)],
  capHome: (S) => [[sh("capture", 2), 5], [sh("home", 2), 5], [sh("jungle", S), 5], [sh("durability", 2), 5], ...tail(S)],
};
function table(build) {
  const t = new Array(16 * 17).fill(0);
  for (let type = 0; type < 13; type++) {
    const steps = build(CASTERS.has(type) ? 1 : 0).slice(0, 8);
    t[type * 17] = steps.length;
    steps.forEach(([id, tot], k) => { t[type * 17 + 1 + 2 * k] = id; t[type * 17 + 2 + 2 * k] = tot; });
  }
  return t;
}

const [outFile, mapsS, workersS, buildsS] = process.argv.slice(2);
const NMAPS = +(mapsS || 50), NW = Math.min(8, +(workersS || 6));
const dir = process.env.ITEM_DIR ? path.resolve(ROOT, process.env.ITEM_DIR) : path.join(ROOT, "v4", "maps_test4"); // ITEM_DIR: another map set
const allMaps = fs.readdirSync(dir).filter((f) => f.endsWith(".map26a")).sort();
const step = Math.max(1, Math.floor(allMaps.length / NMAPS));
const maps = allMaps.filter((_, i) => i % step === 0).slice(0, NMAPS).map((f) => path.join(dir, f));
const names = buildsS ? buildsS.split(",") : Object.keys(BUILDS);
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
  const out = {};
  // The control first: no table = v57's own builds (a mirror of v57_c2 with another seed).
  for (const name of ["v57own", ...names]) {
    const t = name === "v57own" || name === "plain" ? null : table(BUILDS[name]); // plain: the bot's own build (+ ITEM_KNOBS)
    const knobs = name !== "v57own" && process.env.ITEM_KNOBS ? process.env.ITEM_KNOBS.split(",").map(Number) : null;
    const rs = await Promise.all(maps.flatMap((map) => [0, 1].map((side) => run({ map, side, table: t, knobs }))));
    const w = rs.reduce((a, r) => a + r.win, 0), n = rs.length, p = w / n;
    out[name] = { win: p, n, margin: rs.reduce((a, r) => a + r.margin, 0) / n, wins: rs.map((r) => r.win) };
    fs.writeFileSync(outFile, JSON.stringify(out, null, 1));
    console.log(`${name.padEnd(16)} ${(100 * p).toFixed(1)}% +- ${(100 * Math.sqrt(p * (1 - p) / n)).toFixed(1)} of ${n}, margin ${out[name].margin.toFixed(0)} | ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}`);
  }
  for (const s of slots) if (s.w) s.w.terminate();
})();
