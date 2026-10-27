// k64 block rotation driver (agent2/KNOBS.md); Node version of rot_all.ps1 + rot_search.ps1 with run_guarded.ps1's RAM
// watchdog built in (a child job is killed when free physical memory falls under ROT_FREE_FLOOR GB, default 3; os.freemem() reads the same
// figure as Win32_OperatingSystem.FreePhysicalMemory).
// For each block in order: a knob_rot.js search of that block only (15 generations; per generation 10 official + 10
// maze + 5 open maps x 2 sides vs v61_c2 + b5_c2 = 100 games per candidate), then a held-out check of the mean of
// generations 8-15 against the block's start on the same games (knob_val.js: 25 maze test + 25 maps_test4 maps x 2
// sides vs v61_c3 + b5_c3 = 200 games, fresh slices per block; maps_test4 150-199 stay for the final check). The block
// is kept when the paired win difference is at least MIN_GAIN points, otherwise it reverts to its start.
// The current vector is <tag>_cur.txt; blocks marked DONE in <tag>_all.log are skipped, so a rerun resumes.
// usage: node agent2/lab/rot_all.js [tag=rot1] [blocks=F,C,K,S,A,B] [gens=15] [workers=3] [minGain=1.0] [start=agent2/lab/knobs_k64_start.txt]
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
const LAB = __dirname;
const [tag = "rot1", blocksS = "F,C,K,S,A,B", gensS = "15", workersS = "3", minS = "1.0", start = "agent2/lab/knobs_k64_start.txt"] = process.argv.slice(2);
const GENS = +gensS, W = +workersS, MIN = +minS;
const FLOOR = +(process.env.ROT_FREE_FLOOR || 3); // GB of free RAM under which the running job is killed (agreed 27 Oct: 3 GB)
const RANGES = { A: "0-23", B: "24-44", F: "64-88", C: "89-112", K: "113-128", S: "129-142" };
const ORDER = ["F", "C", "K", "S", "A", "B"];
const logF = path.join(LAB, `${tag}_all.log`), cur = path.join(LAB, `${tag}_cur.txt`);
const say = (s) => { const line = `${new Date().toISOString().slice(5, 16).replace("T", " ")} ${s}`; fs.appendFileSync(logF, line + "\n"); console.log(line); };
const vec = (f) => fs.readFileSync(f, "utf8").trim().split(/[\s,]+/).filter(Boolean).map(Number);
const save = (f, v) => fs.writeFileSync(f, v.map((x) => (+x).toFixed(4)).join(",") + "\n");
const rowsOf = (tsv) => (fs.existsSync(tsv) ? fs.readFileSync(tsv, "utf8").trim().split("\n").slice(1).map((l) => l.split("\t").map(Number)).filter((r) => r.length > 5) : []);
const BASE_ENV = { ENGWASM: "tools/viz/v2_0_0.wasm", BOTS_DIR: "v4/bots", LAB_DRAFT_FUEL: "10000000" };

// One child job (node script) with the RAM watchdog; resolves to "ok", "failed" or "killed".
function job(script, args, env, logFile) {
  return new Promise((res) => {
    const out = fs.openSync(logFile, "w"), err = fs.openSync(logFile + ".err", "w");
    const p = spawn(process.execPath, [script, ...args], { cwd: ROOT, env: { ...process.env, ...BASE_ENV, ...env }, stdio: ["ignore", out, err], windowsHide: true });
    let minFree = 99, killed = false;
    const t = setInterval(() => {
      const free = os.freemem() / 2 ** 30;
      minFree = Math.min(minFree, free);
      if (free < FLOOR && !killed) {
        killed = true;
        p.kill();
        fs.appendFileSync(logFile, `KILLED by watchdog: free RAM ${free.toFixed(2)} GB\n`);
      }
    }, 3000);
    p.on("exit", (code) => { clearInterval(t); fs.closeSync(out); fs.closeSync(err); say(`  ${path.basename(script)} ${killed ? "killed" : "exit " + code}; lowest free RAM ${minFree.toFixed(1)} GB`); res(killed ? "killed" : code === 0 ? "ok" : "failed"); });
  });
}

(async () => {
  if (!fs.existsSync(cur)) { fs.copyFileSync(path.resolve(ROOT, start), cur); say(`start vector ${start}`); }
  for (const b of blocksS.split(",")) {
    const name = `${tag}_${b}`, i = ORDER.indexOf(b), range = RANGES[b];
    if (fs.existsSync(logF) && fs.readFileSync(logF, "utf8").includes(`DONE ${b} `)) continue;
    const tsv = path.join(LAB, `${name}.tsv`);
    let rows = rowsOf(tsv);
    if (rows.length < GENS) {
      // Resume from the last generation row when the search was stopped part-way.
      const init = rows.length ? rows[rows.length - 1].slice(5).join(",") : vec(cur).join(",");
      say(`search ${b} (${range}) from generation ${rows.length} of ${GENS}`);
      const r = await job(path.join(LAB, "knob_rot.js"), [path.relative(ROOT, tsv).replace(/\\/g, "/"), String(GENS - rows.length), "12", "25", "0.25", "0.10", String(W)], {
        LAB_BOT: "k64", ES_OPPS: "v61=v61_c2,b5=b5_c2", ES_MAPDIRS: "v4/maps:70:10,v4/maps_maze:150:10,v4/maps_new4:150:5",
        ES_NK: "160", ES_BLOCK: range, ES_SEED: String(801 + 37 * i + 100 * rows.length), KNOB_INIT: init,
      }, path.join(LAB, `${name}.log`) + (rows.length ? `.r${rows.length}` : ""));
      rows = rowsOf(tsv);
      if (r !== "ok" || rows.length < GENS) { say(`STOPPED in ${b} after ${rows.length} generations (${r})`); break; }
    }
    // Candidate: mean of generations 8..GENS, block knobs only (the others never moved).
    const use = rows.filter((r) => r[0] >= 8 && r[0] <= GENS).length >= 3 ? rows.filter((r) => r[0] >= 8 && r[0] <= GENS) : rows.slice(Math.floor(rows.length / 2));
    const avg = use[0].slice(5).map((_, k) => use.reduce((s, r) => s + r[5 + k], 0) / use.length);
    const cand = vec(cur);
    const [x, y] = range.split("-").map(Number);
    for (let k = x; k <= y; k++) cand[k] = avg[k];
    const candF = path.join(LAB, `${name}_cand.txt`);
    save(candF, cand);
    const valJ = path.join(LAB, `${name}_val.json`), valL = path.join(LAB, `${name}_val.log`);
    const r = await job(path.join(LAB, "knob_val.js"), [path.relative(ROOT, valJ).replace(/\\/g, "/"), String(W)], {
      VAL_OPPS: "v61_c3,b5_c3",
      VAL_ENTRIES: `ctl=k64@@${path.relative(ROOT, cur).replace(/\\/g, "/")};cand=k64@@${path.relative(ROOT, candF).replace(/\\/g, "/")}`,
      VAL_SETS: `v4/maps_mazetest:25:${(25 * i) % 100} v4/maps_test4:25:${25 * i}`,
    }, valL);
    if (r !== "ok" || !fs.existsSync(valJ)) { say(`STOPPED in ${b} validation (${r})`); break; }
    const j = JSON.parse(fs.readFileSync(valJ, "utf8"));
    const win = (u, t) => (u > t ? 1 : u === t ? 0.5 : 0);
    const C = j.entries.ctl, D = j.entries.cand;
    const d = D.us.map((u, k) => win(u, D.them[k]) - win(C.us[k], C.them[k]));
    const n = d.length, md = d.reduce((s, v) => s + v, 0) / n;
    const se = Math.sqrt(d.reduce((s, v) => s + (v - md) * (v - md), 0) / Math.max(1, n - 1) / n);
    const keep = 100 * md >= MIN;
    if (keep) fs.copyFileSync(candF, cur);
    const train = rows.reduce((s, r) => s + r[1], 0) / rows.length;
    const lines = fs.readFileSync(valL, "utf8").split("\n").filter((l) => /^(ctl|cand) /.test(l)).map((l) => l.replace(/\s+/g, " ").trim()).join(" / ");
    const moved = Array.from({ length: y - x + 1 }, (_, k) => [x + k, cand[x + k] - vec(path.resolve(ROOT, start))[x + k]]).sort((p, q) => Math.abs(q[1]) - Math.abs(p[1])).slice(0, 5).map(([k, v]) => `k${k} ${v >= 0 ? "+" : ""}${v.toFixed(2)}`).join(", ");
    say(`DONE ${b} ${keep ? "KEEP" : "REVERT"} ${(100 * md).toFixed(1)} +- ${(100 * se).toFixed(1)} (n ${n}) | train centre win avg ${(100 * train).toFixed(1)}% | ${lines} | moved ${moved}`);
  }
  say(`rotation finished or stopped; current vector ${path.relative(ROOT, cur)}`);
})();
