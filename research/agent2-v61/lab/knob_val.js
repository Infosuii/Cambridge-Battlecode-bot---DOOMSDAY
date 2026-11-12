// Paired validation of knob vectors (k64 rotation, agent2/KNOBS.md): every entry plays the same games (maps x both
// sides x each opponent), so differences against the first entry (the control) are paired game by game.
// usage: node knob_val.js out.json [workers=3]
// env: VAL_ENTRIES="name=spec;name=spec;.."  spec: bot:NAME (that build's own baked knobs) or NAME@k0,k1,.. or
//      NAME@@file (a lab build playing those knobs; file = a comma list, or a knob_rot.js .tsv: its last row, or
//      file#avgA-B: the mean of generation rows A..B). The first entry is the control.
//      VAL_OPPS (default v61_c3,b5_c3)  VAL_SETS="dir:n:skip .." (default "v4/maps_mazetest:30:0 v4/maps_test4:20:0")
//      BOTS_DIR  ENGWASM  LAB_DRAFT_FUEL (default 10M = cambc 4.0.0)
// Prints per entry: score, win %, mean gem margin, and against the control: games that differ, paired win difference
// +- its standard error. out.json keeps every game result (entry, map, side, opponent, our gems, theirs).
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
process.env.LAB_DRAFT_FUEL = process.env.LAB_DRAFT_FUEL || "10000000";
const wasmOf = (b) => path.join(process.env.BOTS_DIR || path.join(ROOT, "v4", "bots"), b, ".cambc", "build-release", "bot-injected.wasm");

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    const files = job.side === 0 ? [job.a, job.b] : [job.b, job.a];
    H.knobs = job.k ? (job.side === 0 ? [job.k, null] : [null, job.k]) : null;
    let r;
    try { r = await H.play(files[0], files[1], job.map, 2000, null, {}); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    H.knobs = null;
    parentPort.postMessage({ id: job.id, us: r.gems[job.side], them: r.gems[1 - job.side], error: r.error || r.abort });
  }
  return;
}

const [outFile, workersS] = process.argv.slice(2);
const NW = Math.min(8, +(workersS || 3));
function knobsFrom(spec) {
  if (!spec.startsWith("@")) return spec.split(",").map(Number);
  let [file, sel] = spec.slice(1).split("#");
  const txt = fs.readFileSync(path.resolve(ROOT, file), "utf8").trim();
  if (!file.endsWith(".tsv")) return txt.split(/[\s,]+/).filter(Boolean).map(Number);
  const rows = txt.split("\n").slice(1).map((l) => l.split("\t").map(Number));
  let use = rows.slice(-1);
  if (sel && sel.startsWith("avg")) { const [a, b] = sel.slice(3).split("-").map(Number); use = rows.filter((r) => r[0] >= a && r[0] <= b); }
  if (!use.length) throw new Error("no rows for " + spec);
  return use[0].slice(5).map((_, i) => use.reduce((s, r) => s + r[5 + i], 0) / use.length);
}
const entries = (process.env.VAL_ENTRIES || "").split(";").filter(Boolean).map((s) => {
  const [name, spec] = [s.slice(0, s.indexOf("=")), s.slice(s.indexOf("=") + 1)];
  if (spec.startsWith("bot:")) return { name, bot: spec.slice(4), k: null };
  const at = spec.indexOf("@");
  const bot = spec.slice(0, at), k = knobsFrom(spec.slice(at + 1));
  // Builds before k64 hold 48 knobs (lab.h); writing more would overwrite other memory.
  const maxk = /^k64/.test(bot) ? 160 : 48;
  if (k.length > maxk) {
    if (k.slice(maxk).some((v) => v !== 0)) console.log(`warning: ${name}: knobs past ${maxk} dropped for ${bot}`);
    k.length = maxk;
  }
  return { name, bot, k };
});
if (!entries.length) { console.log("VAL_ENTRIES is required"); process.exit(2); }
// VAL_SWEEP=a-b:v (wiring check): one more entry per knob i in a..b, the first knob entry with knob i moved by v.
if (process.env.VAL_SWEEP) {
  const [range, v] = process.env.VAL_SWEEP.split(":");
  const [a, b] = range.split("-").map(Number);
  const base = entries.find((e) => e.k);
  if (!base) { console.log("VAL_SWEEP needs a knob entry"); process.exit(2); }
  for (let i = a; i <= (Number.isFinite(b) ? b : a); i++) {
    const k = base.k.slice();
    while (k.length <= i) k.push(0);
    k[i] += +v;
    entries.push({ name: `k${i}${+v >= 0 ? "+" : ""}${v}`, bot: base.bot, k });
  }
}
const opps = (process.env.VAL_OPPS || "v61_c3,b5_c3").split(",");
const maps = (process.env.VAL_SETS || "v4/maps_mazetest:30:0 v4/maps_test4:20:0").split(/\s+/).filter(Boolean).flatMap((s) => {
  const [d, n, k] = s.split(":");
  const dir = path.resolve(ROOT, d);
  return fs.readdirSync(dir).filter((f) => f.endsWith(".map26a")).sort().slice(+(k || 0), +(k || 0) + +n).map((f) => path.join(dir, f));
});

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
  const games = maps.flatMap((map) => [0, 1].flatMap((side) => opps.map((opp) => ({ map, side, opp }))));
  const res = await Promise.all(entries.map((e) => Promise.all(games.map((g) => run({ a: wasmOf(e.bot), b: wasmOf(g.opp), map: g.map, side: g.side, k: e.k })))));
  const win = (r) => (r.us > r.them ? 1 : r.us === r.them ? 0.5 : 0);
  const out = { games: games.map((g) => ({ map: path.relative(ROOT, g.map), side: g.side, opp: g.opp })), entries: {} };
  const ctl = res[0];
  entries.forEach((e, ei) => {
    const rs = res[ei];
    out.entries[e.name] = { bot: e.bot, knobs: e.k, us: rs.map((r) => r.us), them: rs.map((r) => r.them) };
    const n = rs.length, w = rs.reduce((a, r) => a + win(r), 0), m = rs.reduce((a, r) => a + r.us - r.them, 0) / n;
    const byOpp = opps.map((o) => { const ix = games.map((g, i) => (g.opp === o ? i : -1)).filter((i) => i >= 0); return `${o} ${(100 * ix.reduce((a, i) => a + win(rs[i]), 0) / ix.length).toFixed(1)}`; }).join(", ");
    let line = `${e.name.padEnd(14)} ${w}/${n} = ${(100 * w / n).toFixed(1)}% (${byOpp}), margin ${m.toFixed(0)}`;
    if (ei > 0) {
      const d = rs.map((r, i) => win(r) - win(ctl[i]));
      const differ = rs.filter((r, i) => r.us !== ctl[i].us || r.them !== ctl[i].them).length;
      const md = d.reduce((a, v) => a + v, 0) / n, sd = Math.sqrt(d.reduce((a, v) => a + (v - md) * (v - md), 0) / Math.max(1, n - 1));
      line += ` | vs ${entries[0].name}: ${differ} games differ, ${md >= 0 ? "+" : ""}${(100 * md).toFixed(1)} +- ${(100 * sd / Math.sqrt(n)).toFixed(1)}`;
    }
    console.log(line);
  });
  fs.writeFileSync(outFile, JSON.stringify(out));
  console.log(`${games.length} games x ${entries.length} entries, ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}`);
  for (const s of slots) if (s.w) s.w.terminate();
})();
