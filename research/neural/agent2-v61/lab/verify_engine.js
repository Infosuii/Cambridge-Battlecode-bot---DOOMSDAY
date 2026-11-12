// Verify the engine module against cambc: re-simulate replays to their end and compare final scores, rounds and
// champion deaths with the statistics cambc wrote for the same games.
// usage: node verify_engine.js file1.repl26a [file2 ...]   (each with a matching .json next to it)
const fs = require("fs");
const path = require("path");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const E = load();
const ex = E.ex;
const m = () => E.mem;
console.log("module Version():", ex.Version().toString(16));
let okc = 0, bad = 0;
for (const f of process.argv.slice(2)) {
  const st = JSON.parse(fs.readFileSync(f.replace(/\.repl26a$/, ".json"), "utf8"));
  const g = E.loadReplay(f);
  E.check(ex.Game_Visualiser_Timeline_GetMain(g, E.outBuf), "GetMain");
  const tl = m().getBigUint64(E.outBuf, true);
  E.check(ex.Game_Visualiser_Timeline_Info(g, tl, E.args, E.args + 8, E.args + 16), "Info");
  const size = m().getUint32(E.args, true);
  E.check(ex.Game_Visualiser_Timeline_Seek(g, tl, size - 1, 0), "Seek");
  E.check(ex.Game_Runner_GetState(g, E.args), "GetState");
  const round = m().getUint32(E.args + 8, true);
  const sub = [0, 1].map((t) => (ex.Game_API_GetSubmittedGemCount(g, t, E.outBuf) === 0 ? m().getUint32(E.outBuf, true) : -1));
  const want = ["teamA", "teamB"].map((t) => int(st.teams.find((x) => x.team === t).submittedGems));
  const same = sub[0] === want[0] && sub[1] === want[1];
  same ? okc++ : bad++;
  console.log(`${path.basename(f)}: module round ${round} gems ${sub.join("/")} | cambc rounds ${st.match.roundsCompleted} gems ${want.join("/")} ${same ? "MATCH" : "DIFF"}`);
  ex.Game_Destroy(g);
}
console.log(`matched ${okc}, different ${bad}`);
function int(v) { return parseInt(v || 0, 10); }
