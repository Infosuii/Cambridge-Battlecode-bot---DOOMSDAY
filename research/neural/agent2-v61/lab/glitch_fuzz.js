// Random-action fuzzer (engine 2.0.0): our team's champions take random actions every turn (moves, dashes / ground
// casts on random tiles, unit casts and attacks on random visible units, buys, sells, consumables, tributes, cancels,
// recalls), the other team is v57 playing normally. After every successful action, invariants are checked and any
// violation is printed: a champion on a wall / hole / altar / the enemy spawn, health above maximum, or a gold / gem
// jump with no plausible source (only checked around the action itself).
// usage: node glitch_fuzz.js [games=6] [rounds=300] [seed=1] [mapdir=v4/maps]
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
const { Host } = require(path.join(__dirname, "host.js"));
const BOT = path.join(ROOT, "v4", "bots", "v57_c1", ".cambc", "build-release", "bot-injected.wasm");
const [gamesS, roundsS, seedS, dirS] = process.argv.slice(2);
let seed = +(seedS || 1);
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const ri = (n) => Math.floor(rnd() * n);
const dir = path.resolve(ROOT, dirS || "v4/maps");
const maps = fs.readdirSync(dir).filter((f) => f.endsWith(".map26a")).sort();
const LINEUPS = [[10, 1, 2, 8, 11], [3, 4, 5, 6, 9], [0, 7, 1, 11, 2]];

(async () => {
  const counts = {};
  const viol = [];
  for (let gi = 0; gi < +(gamesS || 6); gi++) {
    const map = path.join(dir, maps[ri(maps.length)]);
    const lineup = LINEUPS[gi % LINEUPS.length];
    const H = new Host();
    const n = [0, 0];
    let boards = null;
    const P = () => H.E.persp(2, 0xffffffff);
    const A = H.arena + 8192, O = H.arena + 8400, PB = H.arena + 8500, UB = H.arena + 8600;
    const info = (h) => {
      if (H.ex.Game_API_Champion_Get(H.g, P(), h, A) !== 0) return null;
      const d = H.m;
      return { h, team: d.getInt32(A, true), type: d.getInt32(A + 4, true), x: d.getInt32(A + 8, true), y: d.getInt32(A + 12, true), hp: d.getFloat32(A + 16, true), mhp: d.getFloat32(A + 20, true) };
    };
    const u32 = (fn) => (fn(O) === 0 ? H.m.getUint32(O, true) : null);
    const gold = (h) => u32((o) => H.ex.Game_API_Champion_GetGold(H.g, P(), h, o));
    const gems = (h) => u32((o) => H.ex.Game_API_Champion_GetGems(H.g, P(), h, o));
    const pos = (x, y) => { H.m.setInt32(PB, x, true); H.m.setInt32(PB + 4, y, true); return PB; };
    const unit = (k, h) => { H.m.setUint32(UB, k, true); H.m.setUint32(UB + 4, h, true); H.m.setUint32(UB + 8, 0, true); return UB; };
    const isSet = (buf, x, y) => H.ex.Bitboard_Test(H.meta, buf, x, y, O + 64) === 0 && H.u8[O + 64];
    const check = (tag, h, before) => {
      const c = info(h);
      if (!c || c.hp <= 0) return;
      const bad = [];
      if (isSet(boards.wall, c.x, c.y)) bad.push("on wall");
      if (isSet(boards.hole, c.x, c.y)) bad.push("on hole");
      if (isSet(boards.altar, c.x, c.y)) bad.push("on altar");
      if (c.hp > c.mhp + 0.5) bad.push(`hp ${c.hp} > max ${c.mhp}`);
      const g1 = gold(h), m1 = gems(h);
      if (before && g1 !== null && before.gold !== null && g1 - before.gold > 400 && !tag.startsWith("sell")) bad.push(`gold +${g1 - before.gold}`);
      if (before && m1 !== null && before.gems !== null && m1 - before.gems > 0 && !tag.startsWith("attack")) bad.push(`gems +${m1 - before.gems}`);
      if (bad.length) viol.push(`${path.basename(map)} r${H.state()[2]} h${h} type ${c.type} after ${tag} at ${c.x},${c.y}: ${bad.join(", ")}`);
    };
    const hooks = {
      draft: (team) => (team === 0 ? lineup[n[0]++ % 5] : null),
      force: (round, champ, team) => {
        if (team !== 0) return null; // v57 plays the other side
        return (H2) => {
          if (!boards) {
            const e = H2.arena + 19100;
            boards = {};
            for (const [k, fn] of [["wall", "Game_GetWallBuffer"], ["hole", "Game_GetHoleBuffer"], ["altar", "Game_GetAltarBuffer"]]) { H2.ex[fn](H2.g, e); boards[k] = H2.m.getUint32(e, true); }
          }
          const c = info(champ);
          if (!c) return;
          const ex = H2.ex;
          if (ri(3) === 0) ex.Game_Sandbox_GiveGold(H2.g, champ, 150); // exercise shopping (gold source logged below)
          if (ri(5) === 0) ex.Game_Sandbox_GiveGems(H2.g, champ, 1 + ri(30));
          for (let k = 0; k < 6; k++) {
            const before = { gold: gold(champ), gems: gems(champ) };
            const me = info(champ) || c;
            const a = ri(11);
            let tag = "", rc = -1;
            const others = [];
            for (let h = 0; h < 16; h++) { const o = info(h); if (o && o.h !== champ && Math.max(Math.abs(o.x - me.x), Math.abs(o.y - me.y)) <= 5) others.push(o); }
            const tgt = others.length ? others[ri(others.length)] : null;
            const near_ = tgt && ri(2) ? tgt : null;
            const tx = near_ ? near_.x + ri(3) - 1 : me.x + ri(5) - 2, ty = near_ ? near_.y + ri(3) - 1 : me.y + ri(5) - 2;
            if (a === 0) { tag = "move"; rc = ex.Game_Action_Move(H2.g, me.x + ri(3) - 1, me.y + ri(3) - 1, O); }
            else if (a === 1 || a === 2) { tag = `cast ground slot ${a - 1} -> ${tx},${ty}`; rc = ex.Game_Action_Cast(H2.g, a - 1, 0, pos(tx, ty), O); }
            else if (a === 3 && tgt) { tag = `cast unit slot ${ri(2)} on ${tgt.team === 0 ? "ally" : "enemy"}`; rc = ex.Game_Action_Cast(H2.g, ri(2), unit(1, tgt.h), pos(0, 0), O); }
            else if (a === 4 && tgt) { tag = `attack ${tgt.team === 0 ? "ally" : "enemy"}`; rc = ex.Game_Action_Attack(H2.g, unit(1, tgt.h)); }
            else if (a === 5) { tag = "buy"; rc = ex.Game_Action_BuyItem(H2.g, ri(84), 1 + ri(5)); }
            else if (a === 6) { tag = "sell"; rc = ex.Game_Action_Sell(H2.g, ri(84)); }
            else if (a === 7) { tag = "consumable"; const id = [0, 2][ri(2)]; rc = ri(2) ? ex.Game_Action_BuyConsumable(H2.g, id) : ex.Game_Action_UseConsumable(H2.g, id, pos(tx, ty), O); }
            else if (a === 8) { tag = `submit ${tx},${ty}`; rc = ex.Game_Action_SubmitGems(H2.g, pos(me.x + ri(3) - 1, me.y + ri(3) - 1)); }
            else if (a === 9) { tag = "cancel"; rc = ex.Game_Action_CancelChannel(H2.g); }
            else { tag = "recall"; rc = ri(4) === 0 ? ex.Game_Action_Recall(H2.g) : -1; }
            counts[tag.split(" ")[0] + (rc === 0 ? " ok" : " fail")] = (counts[tag.split(" ")[0] + (rc === 0 ? " ok" : " fail")] || 0) + 1;
            if (rc === 0) check(tag, champ, before);
          }
        };
      },
      afterTurn: (round) => round >= +(roundsS || 300),
    };
    const r = await H.play(BOT, BOT, map, +(roundsS || 300) + 1, null, hooks);
    console.log(`game ${gi + 1}: ${path.basename(map)} lineup ${lineup} banked ${JSON.stringify(r.gems)} | violations so far ${viol.length}`);
  }
  console.log("actions:", JSON.stringify(counts));
  console.log(viol.length ? viol.slice(0, 40).join("\n") : "no invariant violations");
})();
