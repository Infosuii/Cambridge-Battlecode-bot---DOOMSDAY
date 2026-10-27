// Helpers for the k64 block rotation (rot_all.ps1).
// node rot_pick.js avg SEARCH.tsv A B OUT.txt   mean knob vector of generation rows A..B (fewer rows: the last half)
// node rot_pick.js decide VAL.json CTL CAND MIN  paired win difference CAND - CTL (points) and keep (diff >= MIN) or revert;
//                                                prints "KEEP|REVERT diff se n" and exits 0 for keep, 1 for revert
// node rot_pick.js merge START.txt CAND.txt BLOCK OUT.txt   START with BLOCK's knobs (a-b[,c-d]) taken from CAND
const fs = require("fs");
const [cmd, ...a] = process.argv.slice(2);
const vec = (f) => fs.readFileSync(f, "utf8").trim().split(/[\s,]+/).filter(Boolean).map(Number);
if (cmd === "avg") {
  const [tsv, A, B, out] = a;
  const rows = fs.readFileSync(tsv, "utf8").trim().split("\n").slice(1).map((l) => l.split("\t").map(Number)).filter((r) => r.length > 5);
  let use = rows.filter((r) => r[0] >= +A && r[0] <= +B);
  if (use.length < 3) use = rows.slice(Math.floor(rows.length / 2));
  const v = use[0].slice(5).map((_, i) => use.reduce((s, r) => s + r[5 + i], 0) / use.length);
  fs.writeFileSync(out, v.map((x) => x.toFixed(4)).join(",") + "\n");
  console.log(`avg of ${use.length} rows (gens ${use.map((r) => r[0]).join(" ")}) -> ${out}`);
} else if (cmd === "decide") {
  const [file, ctl, cand, min] = a;
  const j = JSON.parse(fs.readFileSync(file, "utf8"));
  const win = (u, t) => (u > t ? 1 : u === t ? 0.5 : 0);
  const C = j.entries[ctl], D = j.entries[cand];
  const d = D.us.map((u, i) => win(u, D.them[i]) - win(C.us[i], C.them[i]));
  const n = d.length, md = d.reduce((s, v) => s + v, 0) / n;
  const se = Math.sqrt(d.reduce((s, v) => s + (v - md) * (v - md), 0) / Math.max(1, n - 1) / n);
  const keep = 100 * md >= +min;
  console.log(`${keep ? "KEEP" : "REVERT"} ${(100 * md).toFixed(1)} ${(100 * se).toFixed(1)} ${n}`);
  process.exit(keep ? 0 : 1);
} else if (cmd === "merge") {
  const [start, cand, block, out] = a;
  const s = vec(start), c = vec(cand);
  for (const part of block.split(",")) {
    const [x, y] = part.split("-").map(Number);
    for (let i = x; i <= (Number.isFinite(y) ? y : x); i++) s[i] = c[i];
  }
  fs.writeFileSync(out, s.map((x) => (+x).toFixed(4)).join(",") + "\n");
  console.log(`merged ${block} -> ${out}`);
} else {
  console.log("usage: avg | decide | merge (see the header)");
  process.exit(2);
}
