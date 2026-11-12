// Engine edge-case probes (engine 2.0.0): scripted turns for every champion (hooks.force), sandbox setup (gold, gems,
// teleport, damage) and spectator state reads, to find rule gaps or bugs a bot could exploit. Each probe prints what
// the engine did next to what the rules say.
// usage: node glitch_probe.js [probe names...]   (default: all)
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
const { Host } = require(path.join(__dirname, "host.js"));
const MAP = process.env.PROBE_MAP || path.join(ROOT, "v4", "maps", "00ambush.map26a");
const BOT = path.join(ROOT, "v4", "bots", "v57_c1", ".cambc", "build-release", "bot-injected.wasm");
// Draft ids: ryth 0, vesper 1, vendetta 2, C&I 3, stellar 4, prism 5, marcella 6, willow 7, ren 8, varg 9, tavi 10, heart 11.
const LINEUP = [[10, 6, 3, 1, 11], [0, 9, 8, 2, 4]];
const item = (fam, stat, emblem = false) => fam * 6 + stat * 2 + (emblem ? 1 : 0); // families 0..13, stats str 0 / foc 1 / hp 2
const FAM = { monster: 0, power: 1, durability: 2, treasure: 3, jungle: 4, home: 5, bruiser: 6, tribute: 7, capture: 8, prospector: 9, hunter: 10, skirmish: 11, greed: 12, collectors: 13 };

function api(H) {
  const ex = H.ex, m = () => H.m, A = H.arena + 8192;
  const SP = () => H.E.persp(2, 0xffffffff);
  const u32 = (fn) => (fn(A) === 0 ? m().getUint32(A, true) : null);
  const U = ex.Engine_Malloc(16), V = ex.Engine_Malloc(16), P = ex.Engine_Malloc(8), O = ex.Engine_Malloc(8);
  const unit = (buf, kind, h) => { m().setUint32(buf, kind, true); m().setUint32(buf + 4, h, true); m().setUint32(buf + 8, 0, true); return buf; };
  const pos = (x, y) => { m().setInt32(P, x, true); m().setInt32(P + 4, y, true); return P; };
  const err = (rc) => (rc === 0 ? "ok" : `rc ${rc} ${H.E.cstr(ex.GetLastErrorMsg())}`);
  const self = {
    champ(h) {
      if (ex.Game_API_Champion_Get(H.g, SP(), h, A) !== 0) return null;
      const d = m();
      return { h, team: d.getInt32(A, true), type: d.getInt32(A + 4, true), x: d.getInt32(A + 8, true), y: d.getInt32(A + 12, true),
        hp: +d.getFloat32(A + 16, true).toFixed(1), mhp: +d.getFloat32(A + 20, true).toFixed(1), str: +d.getFloat32(A + 24, true).toFixed(1), foc: +d.getFloat32(A + 28, true).toFixed(1) };
    },
    champs() { const r = []; for (let h = 0; h < 16; h++) { const c = self.champ(h); if (c) r.push(c); } return r; },
    gold: (h) => u32((o) => ex.Game_API_Champion_GetGold(H.g, SP(), h, o)),
    gems: (h) => u32((o) => ex.Game_API_Champion_GetGems(H.g, SP(), h, o)),
    banked: (t) => u32((o) => ex.Game_API_GetSubmittedGemCount(H.g, t, o)),
    items(h) {
      if (ex.Game_API_Champion_GetItems(H.g, SP(), h, A, 84) !== 0) return null;
      const r = {};
      for (let i = 0; i < 84; i++) { const n = m().getUint32(A + 4 * i, true); if (n) r[i] = n; }
      return r;
    },
    campState(ci) { const rc = ex.Game_API_Camp_GetState(H.g, SP(), ci, A); if (rc !== 0) return "rc " + rc + " " + H.E.cstr(ex.GetLastErrorMsg()); const d = m(); return "camp state " + d.getUint32(A, true); },
    groupState(gid, h) { const P = H.E.persp(0, h); const rc = ex.Game_API_CampGroup_GetState(H.g, P, gid, A); const s = m().getUint32(A, true); const rc2 = ex.Game_API_CampGroup_GetCaptureState(H.g, H.E.persp(0, h), gid, A + 64); return `group rc ${rc} state ${s} | capture rc ${rc2} timer ${m().getInt32(A + 64, true)} state ${m().getInt32(A + 68, true)}`; },
    channel: (h) => u32((o) => ex.Game_API_Champion_GetChannelTime(H.g, SP(), h, o)),
    consumables(h) { if (ex.Game_API_Champion_GetConsumables(H.g, SP(), h, A, 4) !== 0) return "err " + H.E.cstr(ex.GetLastErrorMsg()); return JSON.stringify([0, 1, 2, 3].map((i) => m().getUint32(A + 4 * i, true))); },
    // actions for the champion whose turn it is
    buy: (it, n = 1) => err(ex.Game_Action_BuyItem(H.g, it, n)),
    sell: (it) => err(ex.Game_Action_Sell(H.g, it)),
    buyConsumable: (id) => err(ex.Game_Action_BuyConsumable(H.g, id)),
    useConsumable: (id, x, y) => err(ex.Game_Action_UseConsumable(H.g, id, pos(x, y), O)),
    move: (x, y) => err(ex.Game_Action_Move(H.g, x, y, O)),
    submit: (x, y) => err(ex.Game_Action_SubmitGems(H.g, pos(x, y))),
    cancel: () => err(ex.Game_Action_CancelChannel(H.g)),
    recall: () => err(ex.Game_Action_Recall(H.g)),
    cast: (slot, x, y) => err(ex.Game_Action_Cast(H.g, slot, 0, pos(x, y), O)),
    castOn: (slot, kind, h) => err(ex.Game_Action_Cast(H.g, slot, unit(U, kind, h), pos(0, 0), O)),
    attack: (kind, h) => err(ex.Game_Action_Attack(H.g, unit(U, kind, h))),
    // sandbox
    giveGold: (h, n) => err(ex.Game_Sandbox_GiveGold(H.g, h, n)),
    giveGems: (h, n) => err(ex.Game_Sandbox_GiveGems(H.g, h, n)),
    teleport: (h, x, y) => err(ex.Game_Sandbox_Teleport(H.g, unit(U, 1, h), pos(x, y))),
    damage: (src, dst, n, dstKind = 1) => err(ex.Game_Sandbox_Damage(H.g, unit(U, 1, src), unit(V, dstKind, dst), n)),
  };
  return self;
}

// Map facts: altars and spawn tiles from the map bitboards (spectator view).
function mapFacts(H) {
  const ex = H.ex, E = H.E;
  const b = H.arena + 16384;
  const read = (fn) => { fn(b); const pts = []; const W = H.W || 100, Hh = H.Hh || 100; for (let y = 0; y < Hh; y++) for (let x = 0; x < W; x++) { const ok = ex.Bitboard_Test(H.meta, b, x, y, H.arena + 12000) === 0 && H.u8[H.arena + 12000]; if (ok) pts.push([x, y]); } return pts; };
  return { altars: read((o) => ex.Game_API_Map_GetAltarBitboard(H.g, o)) };
}

async function scenario(name, script, opts = {}) {
  const H = new Host();
  const n = [0, 0];
  let A = null;
  const log = [];
  const hooks = {
    draft: (team) => (opts.lineup || LINEUP)[team][n[team]++ % 5],
    force: (round, champ, team) => (H2) => {
      if (!A) A = api(H2);
      // Turn bookkeeping for probes: which champions already took their turn this round.
      if (H2.__round !== round) { H2.__round = round; H2.__actedThisRound = new Set(); }
      if (team === 0 || opts.both) script({ round, champ, team, A, H: H2, log });
      H2.__actedThisRound.add(champ);
    },
    afterTurn: (round) => round >= (opts.rounds || 30),
  };
  await H.play(BOT, BOT, opts.map || MAP, (opts.rounds || 30) + 1, null, hooks);
  console.log(`\n=== ${name}`);
  for (const l of log) console.log("  " + l);
}

// Altar tiles: test every tile of the altar bitboard (spectator).
function altars(H) {
  // Game_GetAltarBuffer writes a pointer to the engine's own altar board (the same source the bot's map mask uses).
  const ex = H.ex, e = H.arena + 19100, o = H.arena + 19000;
  if (ex.Game_GetAltarBuffer(H.g, e) !== 0) return [];
  const b = H.m.getUint32(e, true);
  const r = [];
  for (let y = 0; y < 100; y++) for (let x = 0; x < 100; x++) if (ex.Bitboard_Test(H.meta, b, x, y, o) === 0 && H.u8[o]) r.push([x, y]);
  return r;
}
// Put champion h on a free tile next to the altar nearest to it; returns [altar, tile] or null.
function toAltar(H, A, h) {
  const c = A.champ(h);
  const al = altars(H).sort((p, q) => Math.max(Math.abs(p[0] - c.x), Math.abs(p[1] - c.y)) - Math.max(Math.abs(q[0] - c.x), Math.abs(q[1] - c.y)));
  for (const a of al) for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [-1, -1], [1, -1], [-1, 1]])
    if (A.teleport(h, a[0] + dx, a[1] + dy) === "ok") return [a, [a[0] + dx, a[1] + dy]];
  return null;
}

// Camp groups with a spawn tile next to an altar: [{gid, gems, tiles: [[x, y]...], camps: [ci...], adj: [[x, y] next to an altar]}].
function altarCamps(H) {
  const ex = H.ex, m = H.m, b = H.arena + 30000, e = H.arena + 19100, o = H.arena + 19000;
  ex.Game_GetAltarBuffer(H.g, e); const ab = m.getUint32(e, true);
  const isAltar = (x, y) => ex.Bitboard_Test(H.meta, ab, x, y, o) === 0 && H.u8[o];
  ex.Game_API_Map_GetNumCampGroups(H.g, b); const n = m.getUint32(b, true);
  ex.Game_API_Map_GetCampGroups(H.g, b + 8, n, b + 4);
  const res = [];
  for (let k = 0; k < n; k++) {
    const gid = m.getUint32(b + 8 + 4 * k, true);
    ex.Game_API_Map_CampGroup_Get(H.g, gid, b + 4000); const gems = m.getUint32(b + 4000, true);
    ex.Game_API_Map_CampGroup_GetNumCamps(H.g, gid, b + 4100); const nc = m.getUint32(b + 4100, true);
    ex.Game_API_Map_CampGroup_GetCampInfo(H.g, gid, b + 4200, nc, b + 4104);
    const g = { gid, gems, tiles: [], camps: [], adj: [] };
    for (let c = 0; c < nc; c++) {
      const ci = m.getUint32(b + 4200 + 4 * c, true);
      ex.Game_API_Map_CampInfo_Get(H.g, ci, b + 5000);
      const x = m.getInt32(b + 5000, true), y = m.getInt32(b + 5004, true); // camp_info {x, y, type}
      g.tiles.push([x, y]); g.camps.push(ci);
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) if (isAltar(x + dx, y + dy)) g.adj.push([x, y, x + dx, y + dy]);
    }
    if (g.adj.length) res.push(g);
  }
  return res.sort((p, q) => q.gems - p.gems);
}

const PROBES = {
  // Growing-bag tribute with a real capture: kill the richest altar-side camp group (sandbox), stand on its tile next
  // to the altar with 1 gem, start a 1-tick tribute just before the capture completes; compare with normal banking.
  async captureBank() {
    for (const trick of [true, false]) {
      let st = 0, h0 = -1, g = null, before = 0, t0 = 0;
      await scenario(`captureBank trick=${trick} (map ${path.basename(process.env.PROBE_MAP || "split")})`, ({ round, champ, A, H, log }) => {
        const c = A.champ(champ);
        if (!c) return;
        if (st === 0 && c.type === 7) {
          h0 = champ; g = altarCamps(H)[0];
          log.push(`group gems ${g.gems}, camps ${g.camps.length}, tile+altar ${JSON.stringify(g.adj[0])}`);
          let ok = "";
          for (let r = 1; r <= 3 && !ok; r++) for (let dx = -r; dx <= r && !ok; dx++) for (let dy = -r; dy <= r && !ok; dy++) if (A.teleport(champ, g.adj[0][0] + dx, g.adj[0][1] + dy) === "ok") ok = `${g.adj[0][0] + dx},${g.adj[0][1] + dy}`;
          log.push(`teleport next to the group: ${ok}`);
          st = 0.5; return;
        }
        if (st === 0.5 && champ === h0) {
          const o = H.arena + 9100, P = H.E.persp(0, champ);
          for (const [x, y] of g.tiles) {
            const rc = H.ex.Game_API_GetCamp(H.g, P, x, y, o); const hc = H.m.getUint32(o, true);
            log.push(`camp at ${x},${y}: rc ${rc} handle ${hc} kill: ${rc === 0 ? A.damage(champ, hc, 1e6, 2) : "-"}`);
          }
          log.push(`teleport onto camp tile: ${A.teleport(champ, g.adj[0][0], g.adj[0][1])}`);
          if (trick) A.giveGems(champ, 1);
          before = A.banked(0); t0 = round; st = 1; return;
        }
        if (st === 1 && champ === h0) {
          const cs = H.ex.Game_API_CampGroup_GetCaptureState(H.g, H.E.persp(0, champ), g.gid, H.arena + 9000);
          const timer = H.m.getInt32(H.arena + 9000, true), state = H.m.getInt32(H.arena + 9004, true);
          let act = "";
          if (trick && timer <= 1 && state === 1 && A.gems(champ) > 0 && A.channel(champ) === null) act = `submit(1 gem): ${A.submit(g.adj[0][2], g.adj[0][3])}`;
          if (!trick && A.gems(champ) > 0 && A.channel(champ) === null) act = `submit(${A.gems(champ)} gems): ${A.submit(g.adj[0][2], g.adj[0][3])}`;
          log.push(`round ${round}: ${A.groupState(g.gid, champ)} | carried ${A.gems(champ)} channel ${A.channel(champ)} banked +${A.banked(0) - before} ${act}`);
          if (A.banked(0) - before >= g.gems) { log.push(`=> all ${A.banked(0) - before} banked ${round - t0} rounds after the kill`); st = 2; }
        }
      }, { rounds: 40, map: process.env.PROBE_MAP || path.join(ROOT, "v4", "maps", "00split.map26a") });
    }
  },

  // Tribute length by bag size, with and without the Tribute emblem; and a bag that grows during the channel.
  async tribute() {
    for (const emblem of [false, true]) for (const N of [10, 11, 20, 21, 30, 31, 40, 45, 60, 90]) {
      let st = 0, h0 = -1, at = null, startRound = 0, before = 0;
      await scenario(`tribute N=${N} emblem=${emblem}`, ({ round, champ, A, H, log }) => {
        const c = A.champ(champ);
        if (!c) return;
        if (st === 0 && c.type === 7) { // Marcella
          h0 = champ;
          if (emblem) { A.giveGold(champ, 300); log.push(`buy tribute emblem: ${A.buy(item(FAM.tribute, 2), 5)} items ${JSON.stringify(A.items(champ))}`); }
          A.giveGems(champ, N);
          at = toAltar(H, A, champ);
          before = A.banked(0);
          log.push(`round ${round}: gems ${A.gems(champ)} at altar ${JSON.stringify(at)} submit: ${A.submit(at[0][0], at[0][1])} channel ${A.channel(champ)}`);
          startRound = round, st = 1;
        } else if (st === 1 && champ === h0) {
          const b = A.banked(0);
          log.push(`round ${round}: channel ${A.channel(champ)} carried ${A.gems(champ)} banked +${b - before}`);
          if (b > before) { log.push(`=> banked ${b - before} after ${round - startRound} of its turns`); st = 2; }
        }
      }, { rounds: 14 });
    }
  },
  async growBag() {
    let st = 0, h0 = -1, before = 0;
    await scenario("growBag: start a 1-gem tribute, add 80 gems before it completes", ({ round, champ, A, H, log }) => {
      const c = A.champ(champ);
      if (!c) return;
      if (st === 0 && c.type === 7) {
        h0 = champ; A.giveGems(champ, 1); const at = toAltar(H, A, champ); before = A.banked(0);
        log.push(`round ${round}: submit 1 gem: ${A.submit(at[0][0], at[0][1])} channel ${A.channel(champ)}`);
        A.giveGems(champ, 80); log.push(`same turn after submit: +80 gems -> carried ${A.gems(champ)} channel ${A.channel(champ)}`);
        st = 1;
      } else if (st === 1 && champ === h0) {
        log.push(`round ${round}: carried ${A.gems(champ)} banked +${A.banked(0) - before} channel ${A.channel(champ)}`);
        if (A.banked(0) > before) st = 2;
      }
      if (wall) A.__wall = wall;
    }, { rounds: 6 });
  },
  // Altar lock placed by an ally on the altar where a teammate is channelling.
  async ownLock() {
    let st = 0, ha = -1, hb = -1, at = null, before = 0;
    await scenario("ownLock: teammate locks the altar we are tributing at", ({ round, champ, A, H, log }) => {
      const c = A.champ(champ);
      if (!c) return;
      if (st === 0 && c.type === 7) { ha = champ; A.giveGems(champ, 40); at = toAltar(H, A, champ); before = A.banked(0); log.push(`A submit 40: ${A.submit(at[0][0], at[0][1])} channel ${A.channel(champ)}`); st = 1; return; }
      if (st === 1 && champ !== ha && c.team === 0) {
        hb = champ; A.giveGold(champ, 50);
        log.push(`B consumables before: ${A.consumables(champ)}; buy lock: ${A.buyConsumable(2)}; after: ${A.consumables(champ)}`);
        for (const [dx, dy] of [[2, 0], [-2, 0], [0, 2], [0, -2], [2, 2], [-2, -2], [2, -2], [-2, 2], [1, 2], [2, 1]]) if (A.teleport(champ, at[0][0] + dx, at[0][1] + dy) === "ok") break;
        log.push(`B places lock on our altar: ${A.useConsumable(2, at[0][0], at[0][1])}; A channel now ${A.channel(ha)}`);
        st = 2; return;
      }
      if (st === 2 && champ === ha) { log.push(`round ${round}: A channel ${A.channel(ha)} carried ${A.gems(ha)} banked +${A.banked(0) - before}`); }
    }, { rounds: 8 });
  },
  // Teleport crystal (consumable 0) targets: enemy spawn, altar, wall/hole, camp tile, beyond range.
  async crystal() {
    let done = false;
    await scenario("crystal targets", ({ round, champ, A, H, log }) => {
      const c = A.champ(champ);
      if (done || !c || c.type !== 7) return;
      done = true; A.giveGold(champ, 50);
      log.push(`buy crystal: ${A.buyConsumable(0)} at ${c.x},${c.y}`);
      const al = altars(H)[0];
      // nearest wall tile within 3 (Game_GetWallBuffer board)
      const e = H.arena + 19100, o = H.arena + 19000; let wall = null;
      if (H.ex.Game_GetWallBuffer(H.g, e) === 0) { const wb = H.m.getUint32(e, true);
        for (let dy = -3; dy <= 3 && !wall; dy++) for (let dx = -3; dx <= 3 && !wall; dx++) if (H.ex.Bitboard_Test(H.meta, wb, c.x + dx, c.y + dy, o) === 0 && H.u8[o]) wall = [c.x + dx, c.y + dy]; }
      log.push(`wall within 3: ${JSON.stringify(wall)}`);
      if (wall) { log.push(`crystal -> wall ${wall}: ${A.useConsumable(0, wall[0], wall[1])}`); }
      const tries = [["altar", al[0], al[1]], ["4 away", c.x + 4, c.y], ["3 away", c.x + 3, c.y + 3], ["own tile", c.x, c.y], ["off map", -1, c.y]];
      for (const [k, x, y] of tries) log.push(`crystal -> ${k} (${x},${y}): ${A.useConsumable(0, x, y)}`);
    }, { rounds: 6 });
  },

  // Tavi: buy a full emblem, sell it back on spawn; gold, stats and the emblem passive before/after.
  async taviSell() {
    let done = false;
    await scenario("taviSell", ({ champ, A, log }) => {
      const c = A.champ(champ);
      if (done || !c || c.type !== 11) return;
      done = true;
      A.giveGold(champ, 2000);
      log.push(`start gold ${A.gold(champ)} mhp ${c.mhp} items ${JSON.stringify(A.items(champ))}`);
      log.push(`buy 5 treasure hp shards: ${A.buy(item(FAM.treasure, 2), 5)} -> gold ${A.gold(champ)} items ${JSON.stringify(A.items(champ))} mhp ${A.champ(champ).mhp}`);
      const it = A.items(champ);
      for (const k of Object.keys(it)) log.push(`sell item ${k}: ${A.sell(+k)} -> gold ${A.gold(champ)} items ${JSON.stringify(A.items(champ))} mhp ${A.champ(champ).mhp}`);
      log.push(`buy greed hp x25: ${A.buy(item(FAM.greed, 2), 25)} -> gold ${A.gold(champ)} items ${JSON.stringify(A.items(champ))} mhp ${A.champ(champ).mhp}`);
      const it2 = A.items(champ);
      for (const k of Object.keys(it2)) log.push(`sell item ${k}: ${A.sell(+k)} -> gold ${A.gold(champ)} mhp ${A.champ(champ).mhp}`);
    }, { rounds: 3 });
  },
};

// Every camp group with its tiles and gems (map data).
function allGroups(H) {
  const ex = H.ex, m = H.m, b = H.arena + 30000;
  ex.Game_API_Map_GetNumCampGroups(H.g, b); const n = m.getUint32(b, true);
  ex.Game_API_Map_GetCampGroups(H.g, b + 8, n, b + 4);
  const res = [];
  for (let k = 0; k < n; k++) {
    const gid = m.getUint32(b + 8 + 4 * k, true);
    ex.Game_API_Map_CampGroup_Get(H.g, gid, b + 4000); const gems = m.getUint32(b + 4000, true), gold = m.getUint32(b + 4004, true);
    ex.Game_API_Map_CampGroup_GetNumCamps(H.g, gid, b + 4100); const nc = m.getUint32(b + 4100, true);
    ex.Game_API_Map_CampGroup_GetCampInfo(H.g, gid, b + 4200, nc, b + 4104);
    const g = { gid, gems, gold, tiles: [], types: [] };
    for (let c = 0; c < nc; c++) {
      ex.Game_API_Map_CampInfo_Get(H.g, m.getUint32(b + 4200 + 4 * c, true), b + 5000);
      g.tiles.push([m.getInt32(b + 5000, true), m.getInt32(b + 5004, true)]); g.types.push(m.getInt32(b + 5008, true));
    }
    res.push(g);
  }
  return res;
}
// Sandbox-kill every camp of a group visible to champion h.
function killGroup(H, A, h, g, log) {
  const o = H.arena + 9100, P = H.E.persp(0, h);
  let n = 0;
  for (const [x, y] of g.tiles) {
    if (H.ex.Game_API_GetCamp(H.g, P, x, y, o) !== 0) continue;
    if (A.damage(h, H.m.getUint32(o, true), 1e7, 2) === "ok") n++;
  }
  log.push(`killed ${n}/${g.tiles.length} camps of group ${g.gid} (${g.gems} gems, ${g.gold} gold)`);
}
const near = (H, A, h, x, y) => { for (let r = 1; r <= 3; r++) for (let dx = -r; dx <= r; dx++) for (let dy = -r; dy <= r; dy++) if (A.teleport(h, x + dx, y + dy) === "ok") return [x + dx, y + dy]; return null; };
const capState = (H, h, gid) => { H.ex.Game_API_CampGroup_GetCaptureState(H.g, H.E.persp(0, h), gid, H.arena + 9000); return [H.m.getInt32(H.arena + 9000, true), H.m.getInt32(H.arena + 9004, true)]; };

const PROBES2 = {
  // Capture emblem: none / holder alone / holder + ally, holder leaves after its first turn / ally starts, holder joins late.
  async captureEmblem() {
    for (const mode of (process.env.CAP_MODES || "none,holder,holderLeaves,holderJoinsLate,holderJoinsVeryLate").split(",")) {
      let st = 0, ha = -1, hb = -1, g = null, t0 = 0, gold0 = 0;
      await scenario(`captureEmblem ${mode}`, ({ round, champ, A, H, log }) => {
        const c = A.champ(champ);
        if (!c || c.team !== 0) return;
        if (st === 0 && c.type === 7) {
          ha = champ;
          g = allGroups(H).filter((q) => q.gems > 0 && q.tiles.length >= 2).sort((p, q) => Math.hypot(p.tiles[0][0] - c.x, p.tiles[0][1] - c.y) - Math.hypot(q.tiles[0][0] - c.x, q.tiles[0][1] - c.y))[0];
          if (mode !== "none") { A.giveGold(champ, 300); log.push(`holder buys capture emblem: ${A.buy(item(FAM.capture, 2), 5)}`); }
          log.push(`holder next to group: ${JSON.stringify(near(H, A, champ, g.tiles[0][0], g.tiles[0][1]))}`);
          st = 1; return;
        }
        if (st === 1 && champ !== ha && hb < 0) { hb = champ; log.push(`ally next to group: ${JSON.stringify(near(H, A, champ, g.tiles[1][0], g.tiles[1][1]))}`); st = 2; return; }
        if (st === 2 && champ === ha) {
          killGroup(H, A, champ, g, log);
          if (!mode.startsWith("holderJoins")) log.push(`holder onto tile: ${A.teleport(ha, g.tiles[0][0], g.tiles[0][1])}`);
          st = 3; t0 = round; gold0 = A.gold(ha) + A.gold(hb); return;
        }
        if (st === 3 && champ === hb && round === t0 && mode !== "none" && mode !== "holder") { log.push(`ally onto tile: ${A.teleport(hb, g.tiles[1][0], g.tiles[1][1])}`); return; }
        if (st === 3 && champ === ha) {
          if (mode === "holderLeaves" && round === t0 + 1) log.push(`holder leaves the region: ${JSON.stringify(near(H, A, ha, g.tiles[0][0] + 4, g.tiles[0][1]))}`);
          if ((mode === "holderJoinsLate" && round === t0 + 2) || (mode === "holderJoinsVeryLate" && round === t0 + 4)) log.push(`holder joins: ${A.teleport(ha, g.tiles[0][0], g.tiles[0][1])}`);
          const [timer, state] = capState(H, mode === "holderLeaves" && round > t0 ? hb : ha, g.gid);
          const got = A.gold(ha) + A.gold(hb) - gold0;
          log.push(`round ${round} (+${round - t0}): capture timer ${timer} state ${state} | gold gained ${got}`);
          if (got > 0) { log.push(`=> reward landed ${round - t0} rounds after the kill`); st = 4; }
        }
      }, { rounds: 14 });
    }
  },
  // Hunter emblem (+50 gold per champion kill) on a Cassi & Issac kill (two bodies, "one kill reward").
  async hunterCI() {
    for (const emblem of [false, true]) {
      let st = 0, hk = -1, tgt = -1;
      await scenario(`hunterCI emblem=${emblem}`, ({ round, champ, A, H, log }) => {
        const c = A.champ(champ);
        if (!c || c.team !== 0) return;
        if (st === 0 && c.type === 7) {
          hk = champ;
          if (emblem) { A.giveGold(champ, 300); log.push(`buy hunter emblem: ${A.buy(item(FAM.hunter, 0), 5)}`); }
          const cassi = A.champs().find((q) => q.team === 1 && q.type === 3), issac = A.champs().find((q) => q.team === 1 && q.type === 4);
          tgt = cassi.h;
          log.push(`cassi h${cassi.h} hp ${cassi.hp}; issac h${issac.h} hp ${issac.hp}`);
          // Off her spawn (spawn heals at turn end), down to 5 health, us next to her; attack in this same turn.
          const spot = near(H, A, cassi.h, cassi.x - 8, cassi.y - 8);
          A.damage(champ, cassi.h, A.champ(cassi.h).hp - 5, 1);
          const cc = A.champ(cassi.h);
          log.push(`cassi moved to ${JSON.stringify(spot)} hp ${cc.hp}; teleport next to her: ${JSON.stringify(near(H, A, champ, cc.x, cc.y))}`);
          st = 1;
        }
        if (st === 1 && champ === hk) {
          const before = A.gold(champ);
          log.push(`attack cassi: ${A.attack(1, tgt)} -> gold ${before} -> ${A.gold(champ)} (+${A.gold(champ) - before})`);
          const left = A.champs().filter((q) => q.team === 1 && (q.type === 3 || q.type === 4)).map((q) => `${q.type === 3 ? "cassi" : "issac"} hp ${q.hp}`);
          log.push(`after: ${left.join(", ") || "both gone"}`);
          st = 2;
        }
      }, { rounds: 4, lineup: [[10, 6, 9, 1, 11], [3, 0, 8, 2, 4]] });
    }
  },
  // Dead champion: buy anywhere (rules), Tavi selling while dead and away from spawn, consumables while dead.
  async deadShop() {
    let st = 0, ht = -1;
    await scenario("deadShop", ({ round, champ, A, H, log }) => {
      const c = A.champ(champ);
      if (!c || c.team !== 0) return;
      if (st === 0 && c.type === 11) {
        ht = champ; A.giveGold(champ, 600);
        log.push(`tavi buys 5 power str: ${A.buy(item(FAM.power, 0), 5)} gold ${A.gold(champ)}`);
        log.push(`move off spawn: ${JSON.stringify(near(H, A, champ, c.x + 6, c.y + 6))}`);
        const foe = A.champs().find((q) => q.team === 1);
        log.push(`kill tavi (sandbox): ${A.damage(foe.h, champ, 1e6, 1)}`);
        st = 1; return;
      }
      if (st === 1 && champ === ht) {
        log.push(`dead turn ${round}: readable ${!!A.champ(champ)} gold ${A.gold(champ)}`);
        log.push(`  buy 5 treasure while dead: ${A.buy(item(FAM.treasure, 0), 5)} gold ${A.gold(champ)}`);
        log.push(`  sell power emblem while dead: ${A.sell(item(FAM.power, 0, true))} gold ${A.gold(champ)}`);
        log.push(`  buy altar lock while dead: ${A.buyConsumable(2)}`);
        st = 2;
      }
    }, { rounds: 5 });
  },
};
Object.assign(PROBES, PROBES2);

// Turn-state flags of a champion (spectator): which allowances remain.
const allow = (H, h) => {
  const ex = H.ex, o = H.arena + 9300;
  if (ex.Game_API_Champion_Get(H.g, H.E.persp(2, 0xffffffff), h, o) !== 0) return "?";
  return "info@32-44 " + [32, 36, 40].map((k) => H.m.getInt32(o + k, true)).join(",");
};
const firstOf = (A, team, type) => A.champs().find((q) => q.team === team && q.type === type);

const PROBES3 = {
  // Friendly fire: basic attack and a damage spell on our own champion; a "kill" of a carrier by a teammate.
  async friendlyFire() {
    let st = 0;
    await scenario("friendlyFire", ({ round, champ, A, H, log }) => {
      const c = A.champ(champ);
      if (!c || c.team !== 0 || st) return;
      if (c.type !== 7) return; // Marcella attacks, Vesper (type 1) is the victim
      st = 1;
      const v = firstOf(A, 0, 1);
      A.giveGems(v.h, 50);
      near(H, A, v.h, c.x + 3, c.y + 3); const vv = A.champ(v.h);
      log.push(`teleport next to ally: ${JSON.stringify(near(H, A, champ, vv.x, vv.y))}`);
      A.damage(champ, v.h, vv.hp - 5, 1);
      log.push(`ally hp ${A.champ(v.h).hp} gems ${A.gems(v.h)}; our gold ${A.gold(champ)} gems ${A.gems(champ)}`);
      log.push(`basic attack on ally: ${A.attack(1, v.h)} -> ally hp ${A.champ(v.h) ? A.champ(v.h).hp : "dead"}, our gems ${A.gems(champ)} gold ${A.gold(champ)}`);
      log.push(`marcella slot1 (2x focus damage) on ally: ${A.castOn(1, 1, v.h)} -> ally hp ${A.champ(v.h) ? A.champ(v.h).hp : "dead"}, our gems ${A.gems(champ)}`);
    }, { rounds: 3 });
  },
  // Ranged: attack, attack reset, then move (and move, reset, attack) in one turn.
  async rangedReset() {
    for (const order of ["attack-reset-move", "move-reset-attack", "attack-move"]) {
      let st = 0;
      await scenario(`rangedReset ${order}`, ({ round, champ, A, H, log }) => {
        const c = A.champ(champ);
        if (!c || c.team !== 0 || st || c.type !== 1) return; // Vesper: ranged, slot 0 attack reset
        st = 1;
        const foe = A.champs().find((q) => q.team === 1);
        near(H, A, foe.h, c.x + 6, c.y + 6);
        const f = A.champ(foe.h);
        // stand 2 tiles from the foe (in basic range 3)
        let spot = null;
        for (const [dx, dy] of [[2, 0], [-2, 0], [0, 2], [0, -2], [2, 2], [-2, -2]]) if (A.teleport(champ, f.x + dx, f.y + dy) === "ok") { spot = [f.x + dx, f.y + dy]; break; }
        const me = A.champ(champ);
        const step = [me.x + Math.sign(me.x - f.x || 1), me.y];
        const out = [];
        for (const a of order.split("-")) {
          if (a === "attack") out.push(`attack ${A.attack(1, foe.h)}`);
          if (a === "reset") out.push(`reset ${A.cast(0, me.x, me.y)} / self ${A.castOn(0, 1, champ)}`);
          if (a === "move") out.push(`move ${A.move(step[0], step[1])}`);
        }
        log.push(`at ${JSON.stringify(spot)} foe at ${f.x},${f.y}: ${out.join(" | ")} | foe hp ${A.champ(foe.h).hp}`);
      }, { rounds: 3 });
    }
  },
  // Teleport crystal onto a wall tile (the rules table says crystals "can reach walls").
  async wallCrystal() {
    for (const map of ["00ambush", "00corners", "01corridors", "02cuts"]) {
      let st = 0;
      await scenario(`wallCrystal ${map}`, ({ round, champ, A, H, log }) => {
        const c = A.champ(champ);
        if (!c || c.team !== 0 || c.type !== 7) return;
        if (st === 0) {
          A.giveGold(champ, 50);
          log.push(`buy crystal on spawn: ${A.buyConsumable(0)}`);
          const e = H.arena + 19100, o = H.arena + 19000;
          H.ex.Game_GetWallBuffer(H.g, e); const wb = H.m.getUint32(e, true);
          const isWall = (x, y) => H.ex.Bitboard_Test(H.meta, wb, x, y, o) === 0 && H.u8[o];
          // a wall tile 2-3 away from a tile we can stand on
          let found = null;
          for (let y = 2; y < 98 && !found; y++) for (let x = 2; x < 98 && !found; x++) {
            if (!isWall(x, y)) continue;
            for (const [dx, dy] of [[3, 0], [-3, 0], [0, 3], [0, -3], [2, 2]]) if (!found && A.teleport(champ, x + dx, y + dy) === "ok") found = [x, y, x + dx, y + dy];
          }
          if (!found) { log.push("no wall next to a standable tile"); st = 9; return; }
          A.giveGold(champ, 50);
          log.push(`standing at ${found[2]},${found[3]}, wall ${found[0]},${found[1]}: buy crystal ${A.buyConsumable(0)} (needs spawn: trying anyway)`);
          log.push(`crystal -> wall: ${A.useConsumable(0, found[0], found[1])}`);
          A.__wall = found; st = 1; return;
        }
        if (st >= 1 && st < 5) { const me = A.champ(champ); log.push(`round ${round}: at ${me.x},${me.y} channel ${A.channel(champ)}`); st++; }
      }, { rounds: 7, map: path.join(ROOT, "v4", "maps", map + ".map26a") });
    }
  },
  // Channels: tribute start, cancel, restart in one turn; tribute then recall; recall while capturing.
  async channels() {
    let st = 0;
    await scenario("channels", ({ round, champ, A, H, log }) => {
      const c = A.champ(champ);
      if (!c || c.team !== 0 || c.type !== 7 || st) return;
      st = 1; A.giveGems(champ, 40);
      let at = null;
      try { at = toAltar(H, A, champ); } catch (e) { log.push("toAltar error " + e); return; }
      if (!at) { log.push("no altar tile reachable"); return; }
      log.push(`submit ${A.submit(at[0][0], at[0][1])} ch ${A.channel(champ)} | cancel ${A.cancel()} ch ${A.channel(champ)} | submit again ${A.submit(at[0][0], at[0][1])} ch ${A.channel(champ)}`);
      log.push(`recall while tributing: ${A.recall()} | move: ${A.move(c.x, c.y)}`);
    }, { rounds: 5 });
  },
};
Object.assign(PROBES, PROBES3);

const PROBES4 = {
  // Camp aggro: an enemy stands next to a camp group, we stand farther away (in our range of a camp), hit the camp once,
  // then stand still. Who do the woken camps hit? Does a camp kill destroy the enemy's carried gems?
  async campAggro() {
    for (const kind of ["wolf", "elk", "golem"]) {
      let st = 0, hf = -1, g = null, me = -1;
      await scenario(`campAggro ${kind}`, ({ round, champ, A, H, log }) => {
        const c = A.champ(champ);
        if (!c) return;
        if (st === 0 && c.team === 0 && c.type === 1) { // Vesper: ranged (3)
          me = champ;
          const want = { wolf: 0, elk: 1, golem: 5 }[kind];
          g = allGroups(H).filter((q) => q.types.includes(want)).sort((p, q) => Math.hypot(p.tiles[0][0] - c.x, p.tiles[0][1] - c.y) - Math.hypot(q.tiles[0][0] - c.x, q.tiles[0][1] - c.y))[0];
          if (!g) { log.push(`no ${kind} group`); st = 9; return; }
          const t = g.tiles[g.types.indexOf(want)];
          const foe = A.champs().find((q) => q.team === 1);
          hf = foe.h;
          A.giveGems(hf, 60);
          log.push(`${kind} group ${g.gems} gems at ${t}; enemy h${hf} next to it: ${JSON.stringify(near(H, A, hf, t[0], t[1]))}`);
          // us: 3 tiles from the camp tile
          let spot = null;
          for (const [dx, dy] of [[3, 0], [-3, 0], [0, 3], [0, -3], [3, 3], [-3, -3], [3, -3], [-3, 3]]) if (!spot && A.teleport(champ, t[0] + dx, t[1] + dy) === "ok") spot = [t[0] + dx, t[1] + dy];
          log.push(`us at ${JSON.stringify(spot)}`);
          const o = H.arena + 9100;
          const rc = H.ex.Game_API_GetCamp(H.g, H.E.persp(0, champ), t[0], t[1], o);
          log.push(`hit the camp: ${rc === 0 ? A.attack(2, H.m.getUint32(o, true)) : "camp not visible rc " + rc}`);
          st = 1; return;
        }
        if (st >= 1 && st < 8 && champ === me) {
          const f = A.champ(hf), u = A.champ(me);
          log.push(`round ${round}: enemy hp ${f ? f.hp : "dead"} gems ${A.gems(hf)} | us hp ${u.hp}`);
          st++;
        }
      }, { rounds: 9 });
    }
  },
};
Object.assign(PROBES, PROBES4);

const PROBES5 = {
  // Stun timing: Ren (slot 0: damage + one-round stun, range 4) stuns an enemy that has / has not yet acted this round.
  // On each of the victim's turns we read its restriction bits (move 1, attack 2, cast 4, ...) to count lost turns.
  async stunTiming() {
    for (const when of ["victimActedFirst", "victimActsLater"]) {
      let st = 0, ren = -1, vic = -1, castRound = -1;
      // Team order alternates each round; within a round the victim acts before or after Ren depending on the round.
      await scenario(`stunTiming ${when}`, ({ round, champ, team, A, H, log }) => {
        const c = A.champ(champ);
        if (!c) return;
        if (team === 1 && champ === vic) {
          const o = H.arena + 9400; H.ex.Game_API_Champion_GetRestrictions(H.g, H.E.persp(1, champ), champ, o);
          log.push(`round ${round}: victim's turn, restrictions ${H.u8[o]} (stun blocks move/attack/cast)`);
          return;
        }
        if (team !== 0) return;
        if (st === 0 && c.type === 9) { // Ren
          ren = champ;
          const foe = A.champs().find((q) => q.team === 1 && q.type !== 3 && q.type !== 4);
          vic = foe.h;
          near(H, A, vic, c.x + 6, c.y + 6);
          const f = A.champ(vic);
          for (const [dx, dy] of [[3, 0], [-3, 0], [0, 3], [0, -3]]) if (A.teleport(champ, f.x + dx, f.y + dy) === "ok") break;
          st = 1; return;
        }
        if (st === 1 && champ === ren) {
          // Cast when the victim has / has not acted this round. The force hook fires in turn order, so record rounds.
          const actedAlready = H.__actedThisRound && H.__actedThisRound.has(vic);
          if ((when === "victimActedFirst") === !!actedAlready) {
            log.push(`round ${round}: Ren stuns the victim (victim already acted this round: ${!!actedAlready}): ${A.castOn(0, 1, vic)}`);
            castRound = round; st = 2;
          }
        }
      }, { rounds: 7, both: true, lineup: [[8, 6, 3, 1, 11], [0, 9, 2, 4, 10]] });
    }
  },
};
Object.assign(PROBES, PROBES5);

(async () => {
  const want = process.argv.slice(2);
  for (const [k, f] of Object.entries(PROBES)) if (!want.length || want.includes(k)) await f();
})();
