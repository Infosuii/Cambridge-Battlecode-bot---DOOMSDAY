// Per-champion emblem openings (E61 step 3). Our bot (an A2_ITEMTAB=1 lab build: a build-table row replaces only the
// opening emblems and the bot's own stat stacks follow) plays a control set first with no table, recording our drafted
// lineup per game (Game_API_Draft_Get). Then, for each champion type c and each candidate opening, only the games where
// we drafted c are replayed with c's row set: the lab is deterministic, so every other game is unchanged and the
// comparison is paired. Families: monster 0, power 1, durability 2, treasure 3, jungle 4, home 5, bruiser 6, tribute 7,
// capture 8, prospector 9, hunter 10, skirmish 11, greed 12, collectors 13; stats strength 0, focus 1, health 2.
// usage: node item_champ.js out.json US OPP1,OPP2 MAPLIST [workers=5] [champs=all] [cands=all]
//   (bots in BOTS_DIR; MAPLIST = file of map paths relative to the project root; ITEM_KNOBS = our lab knobs)
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
const wasmOf = (b) => path.join(process.env.BOTS_DIR || path.join(ROOT, "v4", "bots"), b, ".cambc", "build-release", "bot-injected.wasm");

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    const files = job.side === 0 ? [job.us, job.opp] : [job.opp, job.us];
    H.builds = job.table ? (job.side === 0 ? [job.table, null] : [null, job.table]) : null;
    H.knobs = job.knobs ? (job.side === 0 ? [job.knobs, null] : [null, job.knobs]) : null;
    const hooks = {
      final: (h) => {
        const ex = h.ex, picks = [];
        if (ex.Game_API_Draft_GetNumRounds(h.g, h.arena) !== 0) return picks;
        const nr = h.u8[h.arena];
        for (let r = 0; r < nr; r++) if (ex.Game_API_Draft_Get(h.g, job.side, r, h.arena) === 0) picks.push(h.m.getUint32(h.arena, true));
        return picks;
      },
    };
    let r;
    try { r = await H.play(files[0], files[1], job.map, 2000, null, hooks); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    H.builds = null; H.knobs = null;
    const s = job.side;
    parentPort.postMessage({ id: job.id, win: r.gems[s] > r.gems[1 - s] ? 1 : r.gems[s] === r.gems[1 - s] ? 0.5 : 0, margin: r.gems[s] - r.gems[1 - s], picks: r.final || [], error: r.error || r.abort });
  }
  return;
}

const F = { monster: 0, power: 1, durability: 2, treasure: 3, jungle: 4, home: 5, bruiser: 6, tribute: 7, capture: 8, prospector: 9, hunter: 10, skirmish: 11, greed: 12, collectors: 13 };
const S = 0, FO = 1, HP = 2;
const NAMES = ["ryth", "vesper", "vendetta", "cassi", "issac", "stellar", "prism", "marcella", "willow", "ren", "varg", "tavi", "heart"];
const FOCUS = new Set([3, 5, 6, 7, 8]), TANK = 12, RANGED = new Set([1, 11]);
// The bot's own opening (bot.cpp build_for, V59_ITEMS 2) as [family, stat]; candidates reuse its stat per family.
function baseOpening(t) {
  if (t === 7) return [["jungle", S], ["prospector", FO], ["durability", HP], ["monster", FO], ["capture", HP], ["collectors", FO]];
  if (t === TANK) return [["prospector", HP], ["jungle", FO], ["durability", HP], ["capture", HP], ["monster", FO], ["collectors", FO]];
  if (FOCUS.has(t)) return [["prospector", FO], ["durability", HP], ["monster", FO], ["capture", HP], ["collectors", FO]];
  const v = [["prospector", RANGED.has(t) ? S : HP]];
  if (t !== 11) v.push(["jungle", S]);
  return [...v, ["durability", HP], ["monster", S], ["capture", S], ["collectors", S]];
}
const mainStat = (t) => (FOCUS.has(t) || t === TANK ? FO : S);
const CANDS = {
  base: null, // the base opening written as a row (sanity: should match the control)
  prosCapJungDur: ["prospector", "capture", "jungle", "durability"],
  capProsJungDurMon: ["capture", "prospector", "jungle", "durability", "monster"],
  prosDur: ["prospector", "durability"],
  prosJungDur: ["prospector", "jungle", "durability"],
  prosMonCapColl: ["prospector", "monster", "capture", "collectors"],
  monProsJungDurCap: ["monster", "prospector", "jungle", "durability", "capture"],
  prosCollJungDurMon: ["prospector", "collectors", "jungle", "durability", "monster"],
  prosJungDurGreed: ["prospector", "jungle", "durability", "greed25"],
  jungProsDurMonCap: ["jungle", "prospector", "durability", "monster", "capture"],
  prosJungCapDurMonColl: ["prospector", "jungle", "capture", "durability", "monster", "collectors"],
  prosJungDurMonCapCollSkirm: ["prospector", "jungle", "durability", "monster", "capture", "collectors", "skirmish"],
};
function row(t, cand) {
  const base = baseOpening(t);
  const statOf = (fam) => { const b = base.find(([f]) => f === fam); return b ? b[1] : fam === "durability" ? HP : mainStat(t); };
  const fams = cand ? cand : base.map(([f]) => f);
  const steps = fams.map((f) => (f === "greed25" ? [F.greed * 6 + 2 * statOf("greed"), 25] : [F[f] * 6 + 2 * statOf(f), 5]));
  const r = new Array(17).fill(0);
  r[0] = Math.min(8, steps.length);
  steps.slice(0, 8).forEach(([id, n], k) => { r[1 + 2 * k] = id; r[2 + 2 * k] = n; });
  return r;
}
const tableFor = (t, cand) => { const tb = new Array(16 * 17).fill(0); row(t, cand).forEach((v, i) => { tb[t * 17 + i] = v; }); return tb; };

const [outFile, us, oppS, listFile, workersS, champsS, candsS] = process.argv.slice(2);
const NW = Math.min(8, +(workersS || 5));
const maps = fs.readFileSync(path.resolve(ROOT, listFile), "utf8").split("\n").map((s) => s.trim()).filter(Boolean).map((f) => path.resolve(ROOT, f));
const champs = champsS && champsS !== "all" ? champsS.split(",").map(Number) : [...NAMES.keys()];
const cands = candsS && candsS !== "all" ? candsS.split(",") : Object.keys(CANDS);
const knobs = process.env.ITEM_KNOBS ? process.env.ITEM_KNOBS.split(",").map(Number) : null;
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
  const games = maps.flatMap((map) => oppS.split(",").flatMap((opp) => [0, 1].map((side) => ({ map, side, us: wasmOf(us), opp: wasmOf(opp), knobs }))));
  const ctrl = await Promise.all(games.map((g) => run(g)));
  const out = { control: { win: ctrl.reduce((a, r) => a + r.win, 0) / ctrl.length, n: ctrl.length, games: games.map((g, i) => ({ map: path.relative(ROOT, g.map), side: g.side, opp: path.basename(path.dirname(path.dirname(path.dirname(g.opp)))), picks: ctrl[i].picks, win: ctrl[i].win, margin: ctrl[i].margin })) }, champs: {} };
  console.log(`control ${(100 * out.control.win).toFixed(1)}% of ${ctrl.length} | ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}`);
  for (const t of champs) {
    const idx = games.map((_, i) => i).filter((i) => ctrl[i].picks.includes(t));
    if (!idx.length) continue;
    const c0 = idx.reduce((a, i) => a + ctrl[i].win, 0) / idx.length, m0 = idx.reduce((a, i) => a + ctrl[i].margin, 0) / idx.length;
    out.champs[NAMES[t]] = { n: idx.length, control: c0, controlMargin: m0, cands: {} };
    for (const name of cands) {
      const tb = tableFor(t, CANDS[name]);
      const rs = await Promise.all(idx.map((i) => run({ ...games[i], table: tb })));
      const w = rs.reduce((a, r) => a + r.win, 0) / rs.length, m = rs.reduce((a, r) => a + r.margin, 0) / rs.length;
      const changed = rs.filter((r, k) => r.win !== ctrl[idx[k]].win || r.margin !== ctrl[idx[k]].margin).length;
      out.champs[NAMES[t]].cands[name] = { win: w, margin: m, changed, wins: rs.map((r) => r.win) };
      fs.writeFileSync(outFile, JSON.stringify(out));
      console.log(`${NAMES[t].padEnd(9)} ${name.padEnd(27)} ${(100 * w).toFixed(1)}% vs control ${(100 * c0).toFixed(1)}% on ${idx.length} (${changed} changed), margin ${m.toFixed(0)} vs ${m0.toFixed(0)} | ${((Date.now() - t0) / 60000).toFixed(1)} min`);
    }
  }
  fs.writeFileSync(outFile, JSON.stringify(out));
  for (const s of slots) if (s.w) s.w.terminate();
})();
