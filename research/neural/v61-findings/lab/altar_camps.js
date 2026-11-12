// Maps where a camp group has a spawn tile within Chebyshev 1 of an altar (the growing-bag tribute: start a 1-gem
// tribute there as the capture completes and the whole capture banks in one tick). Prints per map: groups and their gems.
// usage: node altar_camps.js DIR [DIR..]
const fs = require("fs");
const path = require("path");
process.env.ENGWASM = process.env.ENGWASM || path.join(__dirname, "..", "..", "tools", "viz", "v2_0_0.wasm");
const { Host } = require(path.join(__dirname, "host.js"));
const H = new Host();
let hits = 0, total = 0;
for (const d of process.argv.slice(2)) for (const f of fs.readdirSync(d).filter((f) => f.endsWith(".map26a")).sort()) {
  H.newGame(path.join(d, f));
  const ex = H.ex, m = H.m, b = H.arena + 30000;
  const e = H.arena + 19100, o = H.arena + 19000;
  ex.Game_GetAltarBuffer(H.g, e); const ab = m.getUint32(e, true);
  const isAltar = (x, y) => ex.Bitboard_Test(H.meta, ab, x, y, o) === 0 && H.u8[o];
  ex.Game_API_Map_GetNumCampGroups(H.g, b); const n = m.getUint32(b, true);
  ex.Game_API_Map_GetCampGroups(H.g, b + 8, n, b + 4);
  const groups = [];
  for (let k = 0; k < n; k++) {
    const gid = m.getUint32(b + 8 + 4 * k, true);
    ex.Game_API_Map_CampGroup_Get(H.g, gid, b + 4000); const gems = m.getUint32(b + 4000, true), gold = m.getUint32(b + 4004, true);
    ex.Game_API_Map_CampGroup_GetNumCamps(H.g, gid, b + 4100); const nc = m.getUint32(b + 4100, true);
    ex.Game_API_Map_CampGroup_GetCampInfo(H.g, gid, b + 4200, nc, b + 4104);
    let near = false;
    for (let c = 0; c < nc; c++) {
      const ci = m.getUint32(b + 4200 + 4 * c, true);
      ex.Game_API_Map_CampInfo_Get(H.g, ci, b + 5000);
      const x = m.getInt32(b + 5000, true), y = m.getInt32(b + 5004, true), type = m.getInt32(b + 5008, true); // camp_info {x, y, type}
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) if (isAltar(x + dx, y + dy)) near = true;
    }
    if (near) groups.push(`${gems}g/${gold}gold`);
  }
  total++;
  if (groups.length) { hits++; console.log(`${path.basename(d)}/${f}: ${groups.join(" ")}`); }
}
console.log(`maps with a camp tile next to an altar: ${hits}/${total}`);
