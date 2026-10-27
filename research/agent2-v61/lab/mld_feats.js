// Draft-net map features per map and side (v57 built with A2_MLD_DEBUG prints MLDFEAT on its first draft turn).
// usage: node mld_feats.js BOT_WASM out.json DIR [DIR..]   -> { "<dir>/<map>": [[16 feats team 0], [16 feats team 1]] }
const fs = require("fs");
const path = require("path");
process.env.ENGWASM = process.env.ENGWASM || path.join(__dirname, "..", "..", "tools", "viz", "v2_0_0.wasm");
const { Host } = require(path.join(__dirname, "host.js"));
const [bot, out, ...dirs] = process.argv.slice(2);
(async () => {
  const H = new Host();
  const res = {};
  for (const d of dirs) for (const f of fs.readdirSync(d).filter((f) => f.endsWith(".map26a")).sort()) {
    H.stdout = [];
    await H.play(bot, bot, path.join(d, f), 1, null, {});
    // Output chunks carry a "[team/champ] " prefix each; join them per team before parsing.
    const text = ["", ""];
    for (const s of H.stdout) { const m = s.match(/^\[(\d)\/[^\]]*\] ([\s\S]*)$/); if (m) text[+m[1]] += m[2]; }
    const feats = [0, 1].map((t) => { const m = text[t].match(/MLDFEAT ([^\n]*)/); return m ? m[1].trim().split(/\s+/).map(Number) : null; });
    if (!feats[0] || !feats[1] || feats.some((v) => v.length !== 16 || v.some((x) => !Number.isFinite(x)))) console.error("bad", d, f, JSON.stringify(feats));
    res[path.basename(d) + "/" + f] = feats;
  }
  fs.writeFileSync(out, JSON.stringify(res));
  console.error("maps", Object.keys(res).length);
})();
