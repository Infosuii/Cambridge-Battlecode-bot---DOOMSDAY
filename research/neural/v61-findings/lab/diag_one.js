// One lab game with error counts and the bots' stdout tail (diagnostics for a new engine).
// usage: node diag_one.js A.wasm B.wasm MAP [rounds=300]   (ENGWASM selects the engine)
const path = require("path");
const { Host } = require(path.join(__dirname, "host.js"));
(async () => {
  const [a, b, map, rounds] = process.argv.slice(2);
  const H = new Host(); H.debug = true; H.errors = {}; H.stdout = [];
  const r = await H.play(a, b, map, +(rounds || 300), null, {});
  console.log("result", JSON.stringify({ gems: r.gems, round: r.round, abort: r.abort }));
  console.log("errors", JSON.stringify(Object.entries(H.errors).sort((x, y) => y[1] - x[1]).slice(0, 15)));
  console.log("stdout tail:\n" + H.stdout.slice(-15).join(""));
})();
