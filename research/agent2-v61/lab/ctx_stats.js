// Map-context feature stats (A2_CTX): plays 12 rounds on every map of the given folders with a lab bot that exports
// lab_ctx and prints the raw features per map plus mean / sd of the transformed features (team size, ln area,
// ln gems per tile, ln groups, monolith) for A2_CTX_MU / A2_CTX_SD.
// usage: node ctx_stats.js BOT DIR [DIR..] > out.tsv
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v1_0_1.wasm");
const { Host } = require(path.join(__dirname, "host.js"));
const [bot, ...dirs] = process.argv.slice(2);
const W = path.join(ROOT, "v3", "bots", bot, ".cambc", "build-release", "bot-injected.wasm");
(async () => {
  const H = new Host();
  const xs = [];
  for (const d of dirs) for (const f of fs.readdirSync(d).filter((f) => f.endsWith(".map26a")).sort()) {
    const r = await H.play(W, W, path.join(d, f), 12, null, {});
    const c = (r.ctx || []).find((e) => e.raw[1] > 0);
    if (!c) { console.error("no ctx", f); continue; }
    const [n, area, gems, groups, mono] = c.raw;
    const x = [n, Math.log(area), Math.log(Math.max(1e-3, gems / area)), Math.log(Math.max(1, groups)), mono];
    xs.push(x);
    console.log([path.basename(d), f, ...c.raw, ...x.map((v) => v.toFixed(3))].join("\t"));
  }
  const mu = xs[0].map((_, j) => xs.reduce((a, x) => a + x[j], 0) / xs.length);
  const sd = xs[0].map((_, j) => Math.sqrt(xs.reduce((a, x) => a + (x[j] - mu[j]) ** 2, 0) / xs.length));
  console.error(`maps ${xs.length}\nA2_CTX_MU ${mu.map((v) => v.toFixed(3) + "f").join(", ")}\nA2_CTX_SD ${sd.map((v) => Math.max(0.05, v).toFixed(3) + "f").join(", ")}`);
})();
