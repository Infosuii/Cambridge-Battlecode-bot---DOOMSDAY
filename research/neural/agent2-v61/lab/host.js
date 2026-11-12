// Engine lab host: runs real bot wasm (cambc builds, bot-injected.wasm) inside the scriptable engine module
// (tools/viz/v0_0_3.wasm). Every SDK import is forwarded to the engine's Game_API_* / Bitboard_* / DistanceField_*
// counterpart under the instance's perspective; buffers are copied between the two memories; `yield` suspends the
// instance (JSPI) until its next turn. Fuel is not metered: fuel_remaining() reports the turn budget.
// This is the base of the training environment: games can be branched, states injected, bots swapped mid-game.
//
// usage (as a script): node host.js botA.wasm botB.wasm map.map26a [maxRounds] [--debug]
process.env.ENGWASM = process.env.ENGWASM || require("path").join(__dirname, "..", "..", "tools", "viz", "v0_0_3.wasm");
const fs = require("fs");
const path = require("path");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));

const SZ = { aabb: 16, ability_props: 36, altar_lock_info: 24, buff_data: 12, camp_buff_data: 12, camp_design: 124,
  camp_group_info: 8, camp_info: 12, camp_state: 32, champion_design: 128, champion_identity: 8, champion_info: 44,
  consumable_info: 8, item_info: 40, metadata: 28, position: 8, teleport_info: 28, ward_info: 20, ward_resources: 8,
  game_settings: 120, items: /v2_\d/.test(process.env.ENGWASM || "") ? 336 : 168, consumables: 16 }; // engine 2.0.0: 84 item types (336 bytes)

class Host {
  constructor(opts = {}) {
    this.E = load();
    this.ex = this.E.ex;
    this.debug = !!opts.debug;
    this.arena = this.ex.Engine_Malloc(1 << 20);
    this.meta = this.ex.Engine_Malloc(64);
    this.persp = this.ex.Engine_Malloc(16);
    this.unitBuf = this.ex.Engine_Malloc(16);
    this.posBuf = this.ex.Engine_Malloc(16);
    this.errors = {};
    this.stdout = [];
  }
  get m() { return new DataView(this.ex.memory.buffer); }
  get u8() { return new Uint8Array(this.ex.memory.buffer); }

  newGame(mapFile) {
    const ex = this.ex, bytes = fs.readFileSync(mapFile);
    const p = ex.Engine_Malloc(bytes.length);
    this.u8.set(bytes, p);
    // 4th argument: the game's random seed (real matches get a random one). H.seed / LAB_SEED; default 0 as before.
    const seed = this.seed !== undefined ? this.seed : +(process.env.LAB_SEED || 0);
    this.E.check(ex.Game_FromMapFileBytes(p, bytes.length, this.E.outBuf, seed), "FromMap");
    ex.Engine_Free(p);
    this.g = this.m.getBigUint64(this.E.outBuf, true);
    ex.Game_Runner_Init(this.g);
    this.initMeta();
    this.instances = new Map(); // key "d<team>" (draft) or "c<handle>"
  }
  initMeta() {
    const ex = this.ex;
    ex.Game_API_Map_GetBitboardMetadata(this.g, this.meta);
    ex.Bitboard_GetRawBufferSize(this.meta, this.arena);
    this.R = this.m.getUint32(this.arena, true);
    ex.DistanceField_GetRawBufferSize(this.meta, this.arena);
    this.D = this.m.getUint32(this.arena, true);
  }
  state() {
    this.ex.Game_Runner_GetState(this.g, this.arena);
    const d = this.m;
    return [0, 1, 2, 3].map((i) => d.getInt32(this.arena + 4 * i, true));
  }

  // One bot instance (a draft or a champion) with its imports bound to (team, champion).
  async makeInstance(wasmFile, team, champ) {
    const H = this;
    const ex = this.ex;
    const mod = H.modCache?.[wasmFile] || new WebAssembly.Module(fs.readFileSync(wasmFile));
    (H.modCache ||= {})[wasmFile] = mod;
    const inst = { team, champ, started: false, turn: 0 };
    let bot = null; // bot memory views
    const bm = () => new DataView(bot.memory.buffer);
    const b8 = () => new Uint8Array(bot.memory.buffer);
    let top = 0;
    const scratch = (n) => { const p = H.arena + 64 + top; top += (n + 15) & ~15; return p; };
    const toE = (bp, n) => { const p = scratch(n); H.u8.set(b8().subarray(bp, bp + n), p); return p; };
    const outE = (n) => { const p = scratch(n); H.u8.fill(0, p, p + n); return p; };
    const back = (ep, bp, n) => { if (bp) b8().set(H.u8.subarray(ep, ep + n), bp); };
    const persp = () => { H.m.setUint32(H.persp, team >>> 0, true); H.m.setUint32(H.persp + 4, champ >>> 0, true); return H.persp; };
    const unit = (kind, h) => { const d = H.m; d.setUint32(H.unitBuf, kind, true); d.setUint32(H.unitBuf + 4, h, true); d.setUint32(H.unitBuf + 8, 0, true); return H.unitBuf; };
    const pos = (x, y) => { H.m.setInt32(H.posBuf, x, true); H.m.setInt32(H.posBuf + 4, y, true); return H.posBuf; };
    const g = () => H.g;
    const R = () => H.R, D = () => H.D;
    const note = (name, rc) => {
      if (rc !== 0) {
        const k = name + ":" + rc;
        H.errors[k] = (H.errors[k] || 0) + 1;
        if (H.debug && H.errors[k] <= 2) console.error(`[${team}/${champ}] ${name} -> ${rc} ${H.E.cstr(ex.GetLastErrorMsg())}`);
      }
      return rc;
    };
    // Wrappers. o(n, call): call(outPtr) then copy n bytes back to bot pointer bp.
    const out = (name, n, bp, call) => { top = 0; const e = outE(n); const rc = call(e); back(e, bp, n); return note(name, rc); };
    const env = {
      // --- settings, metadata, designs
      game_settings: (bp) => out("game_settings", SZ.game_settings, bp, (e) => ex.Game_API_GetSettings(e)),
      bc_metadata: (bp) => {
        // {width, height, chunked_width, chunked_height, chunk_stride, board_bytes, field_bytes}: the engine leaves the
        // two sizes zero, so they come from its raw-size queries (a zero size makes the bot allocate empty boards).
        top = 0; const e = outE(SZ.metadata); const rc = ex.Game_API_Map_GetBitboardMetadata(g(), e);
        H.m.setUint32(e + 20, R(), true); H.m.setUint32(e + 24, D(), true);
        back(e, bp, SZ.metadata); return note("bc_metadata", rc);
      },
      consumable_info: (id, bp) => out("consumable_info", SZ.consumable_info, bp, (e) => ex.Game_API_GetConsumableInfo(id, e)),
      item_info: (id, bp) => out("item_info", SZ.item_info, bp, (e) => ex.Game_API_GetItemInfo(id, e)),
      champion_design: (t, bp) => out("champion_design", SZ.champion_design, bp, (e) => ex.Game_API_Champion_Design(g(), t, e)),
      camp_design: (t, bp) => out("camp_design", SZ.camp_design, bp, (e) => ex.Game_API_Camp_Design(g(), t, e)),
      my_champion: () => champ,
      my_team: () => team,
      bc_round_number: (bp) => out("bc_round_number", 4, bp, (e) => ex.Game_API_GetRoundNumber(g(), e)),
      bc_map_symmetry: (bp) => out("bc_map_symmetry", 4, bp, (e) => ex.Game_API_Map_GetSymmetry(g(), e)),
      bc_map_mask: (kind, bp) => {
        const fn = [ex.Game_GetWallBuffer, ex.Game_GetBushBuffer, ex.Game_GetHoleBuffer, ex.Game_GetAltarBuffer][kind];
        if (!fn) return note("bc_map_mask", 4);
        top = 0; const e = outE(8); const rc = fn(g(), e); const src = H.m.getUint32(e, true);
        b8().set(H.u8.subarray(src, src + R()), bp);
        return note("bc_map_mask", rc);
      },
      spawn_region: (t, bp) => out("spawn_region", SZ.aabb, bp, (e) => ex.Game_API_GetSpawnRegion(g(), t, e)),
      bc_submitted_gems: (t, bp) => out("bc_submitted_gems", 4, bp, (e) => ex.Game_API_GetSubmittedGemCount(g(), t, e)),
      // --- memory
      shared_memory_size: (bp) => out("shared_memory_size", 4, bp, (e) => ex.Game_API_GetSharedMemorySize(g(), e)),
      read_shared_memory: (off, bp, n) => out("read_shared_memory", n, bp, (e) => ex.Game_API_ReadSharedMemory(g(), team, off, e, n)),
      write_shared_memory: (off, bp, n) => { top = 0; const e = toE(bp, n); return note("write_shared_memory", ex.Game_API_WriteSharedMemory(g(), team, off, e, n)); },
      draft_memory_size: (bp) => out("draft_memory_size", 4, bp, (e) => ex.Game_API_GetDraftMemorySize(g(), e)),
      read_draft_memory: (off, bp, n) => out("read_draft_memory", n, bp, (e) => ex.Game_API_ReadDraftMemory(g(), team, off, e, n)),
      bc_submit_draft_memory: (bp, n) => { top = 0; const e = toE(bp, n); return note("bc_submit_draft_memory", ex.Game_API_WriteDraftMemory(g(), team, 0, e, n)); },
      // --- draft
      draft_num_rounds: (bp) => { top = 0; const e = outE(4); const rc = ex.Game_API_Draft_GetNumRounds(g(), e); b8()[bp] = H.u8[e]; return note("draft_num_rounds", rc); },
      draft_get: (t, r, bp) => out("draft_get", 4, bp, (e) => ex.Game_API_Draft_Get(g(), t, r, e)),
      draft_champion: (t) => note("draft_champion", ex.Game_Action_Draft(g(), t)),
      // --- champions
      champion: (h, bp) => out("champion", SZ.champion_info, bp, (e) => ex.Game_API_Champion_Get(g(), persp(), h, e)),
      champion_identity: (h, bp) => out("champion_identity", SZ.champion_identity, bp, (e) => ex.Game_API_Champion_GetIdentity(g(), persp(), h, e)),
      champion_is_alive: (h, bp) => out("champion_is_alive", 4, bp, (e) => ex.Game_API_Champion_IsAlive(g(), h, e)),
      champion_restrictions: (h, bp) => { top = 0; const e = outE(4); const rc = ex.Game_API_Champion_GetRestrictions(g(), persp(), h, e); b8()[bp] = H.u8[e]; return note("champion_restrictions", rc); },
      champion_gems: (h, bp) => out("champion_gems", 4, bp, (e) => ex.Game_API_Champion_GetGems(g(), persp(), h, e)),
      champion_gold: (h, bp) => out("champion_gold", 4, bp, (e) => ex.Game_API_Champion_GetGold(g(), persp(), h, e)),
      champion_cooldown: (h, s, bp) => out("champion_cooldown", 4, bp, (e) => ex.Game_API_Champion_GetCooldown(g(), persp(), h, s, e)),
      champion_items: (h, bp) => { top = 0; const e = outE(1024); const rc = ex.Game_API_Champion_GetItems(g(), persp(), h, e, SZ.items / 4); back(e, bp, SZ.items); return note("champion_items", rc); }, // capacity in counts (42 old engines, 84 on engine 2.0.0)
      champion_consumables: (h, bp) => out("champion_consumables", SZ.consumables, bp, (e) => ex.Game_API_Champion_GetConsumables(g(), persp(), h, e, 4)),
      champion_can_shop: (h, f, bp) => out("champion_can_shop", 4, bp, (e) => ex.Game_API_Champion_CanShop(g(), persp(), h, f, e)),
      champion_can_sell: (h, bp) => out("champion_can_sell", 4, bp, (e) => ex.Game_API_Champion_CanSell(g(), persp(), h, e)),
      champion_ability_props: (h, s, bp) => out("champion_ability_props", SZ.ability_props, bp, (e) => ex.Game_API_Champion_GetAbilityProps(g(), persp(), h, s, e)),
      champion_buff_data: (h, bp, cap, cnt) => {
        top = 0; const e = outE(SZ.buff_data * cap), c = outE(4);
        const rc = ex.Game_API_Champion_GetBuffData(g(), persp(), h, e, cap, c);
        back(e, bp, SZ.buff_data * cap); back(c, cnt, 4); return note("champion_buff_data", rc);
      },
      bc_champion_channel_time: (h, bp) => out("bc_champion_channel_time", 4, bp, (e) => ex.Game_API_Champion_GetChannelTime(g(), persp(), h, e)),
      bc_champion_priority: (h, x, bp) => out("bc_champion_priority", 4, bp, (e) => ex.Game_API_Champion_GetPriority(g(), persp(), h, x, e)),
      champion_wards: (h, bp) => out("champion_wards", SZ.ward_resources, bp, (e) => ex.Game_API_Champion_GetWards(g(), persp(), h, e)),
      num_allies: (bp) => out("num_allies", 4, bp, (e) => ex.Game_API_Champion_GetNumAllies(g(), persp(), e)),
      num_enemies: (bp) => out("num_enemies", 4, bp, (e) => ex.Game_API_Champion_GetNumEnemies(g(), persp(), e)),
      allies: (bp, cap, cnt) => { top = 0; const e = outE(4 * cap), c = outE(4); const rc = ex.Game_API_Champion_GetAllies(g(), persp(), e, cap, c); back(e, bp, 4 * cap); back(c, cnt, 4); return note("allies", rc); },
      enemies: (bp, cap, cnt) => { top = 0; const e = outE(4 * cap), c = outE(4); const rc = ex.Game_API_Champion_GetEnemies(g(), persp(), e, cap, c); back(e, bp, 4 * cap); back(c, cnt, 4); return note("enemies", rc); },
      champion_at: (x, y, bp) => out("champion_at", 4, bp, (e) => ex.Game_API_GetChampion(g(), persp(), x, y, e)),
      has_champion: (x, y, bp) => out("has_champion", 4, bp, (e) => ex.Game_API_HasChampion(g(), persp(), x, y, e)),
      // --- camps and map groups
      camp: (h, bp) => out("camp", SZ.camp_state, bp, (e) => ex.Game_API_Camp_Get(g(), persp(), h, e)),
      camp_state: (h, bp) => out("camp_state", 4, bp, (e) => ex.Game_API_Camp_GetState(g(), persp(), h, e)),
      camp_at: (x, y, bp) => out("camp_at", 4, bp, (e) => ex.Game_API_GetCamp(g(), persp(), x, y, e)),
      has_camp: (x, y, bp) => out("has_camp", 4, bp, (e) => ex.Game_API_HasCamp(g(), persp(), x, y, e)),
      map_num_camp_groups: (bp) => out("map_num_camp_groups", 4, bp, (e) => ex.Game_API_Map_GetNumCampGroups(g(), e)),
      map_camp_groups: (bp, cap, cnt) => { top = 0; const e = outE(4 * cap), c = outE(4); const rc = ex.Game_API_Map_GetCampGroups(g(), e, cap, c); back(e, bp, 4 * cap); back(c, cnt, 4); return note("map_camp_groups", rc); },
      map_camp_group: (gi, bp) => out("map_camp_group", SZ.camp_group_info, bp, (e) => ex.Game_API_Map_CampGroup_Get(g(), gi, e)),
      map_camp_group_num_camps: (gi, bp) => out("map_camp_group_num_camps", 4, bp, (e) => ex.Game_API_Map_CampGroup_GetNumCamps(g(), gi, e)),
      map_camp_group_camps: (gi, bp, cap, cnt) => { top = 0; const e = outE(4 * cap), c = outE(4); const rc = ex.Game_API_Map_CampGroup_GetCampInfo(g(), gi, e, cap, c); back(e, bp, 4 * cap); back(c, cnt, 4); return note("map_camp_group_camps", rc); },
      camp_group_capture_state: (gi, bp) => out("camp_group_capture_state", 8, bp, (e) => ex.Game_API_CampGroup_GetCaptureState(g(), persp(), gi, e)), // engine 2.0.0 {timer, state}
      map_camp_info: (ci, bp) => out("map_camp_info", SZ.camp_info, bp, (e) => ex.Game_API_Map_CampInfo_Get(g(), ci, e)),
      map_camp_group_of: (ci, bp) => out("map_camp_group_of", 4, bp, (e) => ex.Game_API_Map_CampInfo_GetGroup(g(), ci, e)),
      map_camp_at: (x, y, bp) => out("map_camp_at", 4, bp, (e) => ex.Game_API_Map_GetCampAt(g(), x, y, e)),
      bc_camp_group_max_respawn: (gi, bp) => out("bc_camp_group_max_respawn", 4, bp, (e) => ex.Game_API_Map_CampGroup_GetRespawnTime(g(), gi, e)),
      camp_group_state: (gi, bp) => out("camp_group_state", 4, bp, (e) => ex.Game_API_CampGroup_GetState(g(), persp(), gi, e)),
      camp_group_cooldown: (gi, bp) => out("camp_group_cooldown", 4, bp, (e) => ex.Game_API_CampGroup_GetCooldown(g(), persp(), gi, e)),
      camp_buffs: (h, bp, cap, cnt) => { top = 0; const e = outE(SZ.camp_buff_data * cap), c = outE(4); const rc = ex.Game_API_Camp_GetBuffs(g(), persp(), h, e, cap, c); back(e, bp, SZ.camp_buff_data * cap); back(c, cnt, 4); return note("camp_buffs", rc); },
      // --- boards
      board_ally_occupancy: (bp) => out("board_ally_occupancy", R(), bp, (e) => ex.Game_API_GetAllyOccupancy(g(), persp(), e)),
      board_enemy_occupancy: (bp) => out("board_enemy_occupancy", R(), bp, (e) => ex.Game_API_GetEnemyOccupancy(g(), persp(), e)),
      board_camp_occupancy: (bp) => out("board_camp_occupancy", R(), bp, (e) => ex.Game_API_GetCampOccupancy(g(), persp(), e)),
      board_ally_ward_occupancy: (bp) => out("board_ally_ward_occupancy", R(), bp, (e) => ex.Game_API_GetAllyWardOccupancy(g(), persp(), e)),
      board_enemy_ward_occupancy: (bp) => out("board_enemy_ward_occupancy", R(), bp, (e) => ex.Game_API_GetEnemyWardOccupancy(g(), persp(), e)),
      board_teleport_occupancy: (bp) => out("board_teleport_occupancy", R(), bp, (e) => ex.Game_API_GetTeleportOccupancy(g(), persp(), e)),
      board_vision: (bp) => out("board_vision", R(), bp, (e) => ex.Game_API_GetVision(g(), persp(), e)),
      board_vision_mask: (t, x, y, bp) => out("board_vision_mask", R(), bp, (e) => ex.Game_API_GetVisionMask(g(), persp(), t, x, y, e)),
      board_ally_altar_lock_occupancy: (bp) => out("board_ally_altar_lock_occupancy", R(), bp, (e) => ex.Game_API_GetAllyAltarLockOccupancy(g(), persp(), e)),
      board_enemy_altar_lock_occupancy: (bp) => out("board_enemy_altar_lock_occupancy", R(), bp, (e) => ex.Game_API_GetEnemyAltarLockOccupancy(g(), persp(), e)),
      altar_lock: (x, y, t, bp) => out("altar_lock", SZ.altar_lock_info, bp, (e) => ex.Game_API_GetAltarLock(g(), persp(), x, y, t, e)),
      // --- actions
      move_to_with_result: (x, y, bp) => out("move_to", 4, bp, (e) => ex.Game_Action_Move(g(), x, y, e)),
      attack: (kind, h) => note("attack", ex.Game_Action_Attack(g(), unit(kind, h))),
      cast_with_result: (slot, kind, h, x, y, bp) => {
        top = 0; const o = outE(4);
        const rc = ex.Game_Action_Cast(g(), slot, kind ? unit(kind, h) : 0, pos(x, y), o); // (slot, unit*, position*, ok*)
        back(o, bp, 4);
        return note("cast", rc);
      },
      use_consumable_with_result: (id, x, y, bp) => { top = 0; const o = outE(4); const rc = ex.Game_Action_UseConsumable(g(), id, pos(x, y), o); back(o, bp, 4); return note("use_consumable", rc); },
      place_ward_with_result: (x, y, bp) => { top = 0; const o = outE(4); const rc = ex.Game_Action_PlaceWard(g(), pos(x, y), o); back(o, bp, 4); return note("place_ward", rc); },
      buy_consumable: (id) => note("buy_consumable", ex.Game_Action_BuyConsumable(g(), id)),
      buy_item: (a, b) => note("buy_item", ex.Game_Action_BuyItem(g(), a, b)),
      sell: (id) => note("sell", ex.Game_Action_Sell(g(), id)),
      recall: () => note("recall", ex.Game_Action_Recall(g())),
      cancel_channel: () => note("cancel_channel", ex.Game_Action_CancelChannel(g())),
      submit_gems: (x, y) => note("submit_gems", ex.Game_Action_SubmitGems(g(), pos(x, y))),
      set_priority: (p) => note("set_priority", ex.Game_Action_SetPriority(g(), p)),
      resign: () => note("resign", ex.Game_Action_Resign(g())),
      // --- errors, fuel, turn end
      bc_get_last_error: (bp, n) => {
        const s = H.E.cstr(ex.GetLastErrorMsg()), enc = Buffer.from(s, "utf8");
        const k = Math.min(enc.length, Math.max(0, n - 1));
        b8().set(enc.subarray(0, k), bp); if (n > 0) b8()[bp + k] = 0;
        return 0;
      },
      // LAB_DRAFT_FUEL: first draft turn budget (default 1M as before; cambc 4.0.0 gives ~10M, E60).
      fuel_remaining: () => BigInt(inst.turn <= 1 ? (champ === -1 >>> 0 ? +(process.env.LAB_DRAFT_FUEL || 1000000) : 200000) : 100000),
      fuel_pause: () => 0, fuel_resume: () => {}, fuel_adjust: () => {},
      debug_dot: () => 0, debug_line: () => 0,
      yield: new WebAssembly.Suspending(async () => {
        inst.onYield();
        await new Promise((r) => { inst.resume = r; });
      }),
      // --- bitboards (engine versions take the metadata first)
      bc_Bitboard_Zero: (b) => { top = 0; const e = outE(R()); const rc = ex.Bitboard_Zero(H.meta, e); back(e, b, R()); return note("bb_zero", rc); },
      bc_Bitboard_One: (b) => { top = 0; const e = outE(R()); const rc = ex.Bitboard_One(H.meta, e); back(e, b, R()); return note("bb_one", rc); },
      bc_Bitboard_Set: (b, x, y, v) => { top = 0; const e = toE(b, R()); const rc = ex.Bitboard_Set(H.meta, e, x, y, v); back(e, b, R()); return note("bb_set", rc); },
      bc_Bitboard_Toggle: (b, x, y) => { top = 0; const e = toE(b, R()); const rc = ex.Bitboard_Toggle(H.meta, e, x, y); back(e, b, R()); return note("bb_toggle", rc); },
      bc_Bitboard_Test: (b, x, y, o) => { top = 0; const e = toE(b, R()), r = outE(4); const rc = ex.Bitboard_Test(H.meta, e, x, y, r); back(r, o, 4); return note("bb_test", rc); },
      bc_Bitboard_IsZero: (b, o) => { top = 0; const e = toE(b, R()), r = outE(4); const rc = ex.Bitboard_IsZero(H.meta, e, r); back(r, o, 4); return note("bb_iszero", rc); },
      bc_Bitboard_NumSetBits: (b, o) => { top = 0; const e = toE(b, R()), r = outE(4); const rc = ex.Bitboard_NumSetBits(H.meta, e, r); back(r, o, 4); return note("bb_numset", rc); },
      bc_Bitboard_GetSetBits: (b, ps, cap, o) => { top = 0; const e = toE(b, R()), q = outE(8 * cap), r = outE(4); const rc = ex.Bitboard_GetSetBits(H.meta, e, q, cap, r); back(q, ps, 8 * cap); back(r, o, 4); return note("bb_getset", rc); },
      bc_Bitboard_Not: (a, res) => { top = 0; const e = toE(a, R()), r = outE(R()); const rc = ex.Bitboard_Not(H.meta, e, r); back(r, res, R()); return note("bb_not", rc); },
      bc_Bitboard_Union: (a, b, res) => { top = 0; const x = toE(a, R()), y = toE(b, R()), r = outE(R()); const rc = ex.Bitboard_Union(H.meta, x, y, r); back(r, res, R()); return note("bb_union", rc); },
      bc_Bitboard_Intersect: (a, b, res) => { top = 0; const x = toE(a, R()), y = toE(b, R()), r = outE(R()); const rc = ex.Bitboard_Intersect(H.meta, x, y, r); back(r, res, R()); return note("bb_intersect", rc); },
      bc_Bitboard_Xor: (a, b, res) => { top = 0; const x = toE(a, R()), y = toE(b, R()), r = outE(R()); const rc = ex.Bitboard_Xor(H.meta, x, y, r); back(r, res, R()); return note("bb_xor", rc); },
      bc_Bitboard_IsEqual: (a, b, o) => { top = 0; const x = toE(a, R()), y = toE(b, R()), r = outE(4); const rc = ex.Bitboard_IsEqual(H.meta, x, y, r); back(r, o, 4); return note("bb_iseq", rc); },
      bc_Bitboard_ShiftRight: (a, res, n) => { top = 0; const x = toE(a, R()), r = outE(R()); const rc = ex.Bitboard_ShiftRight(H.meta, x, r, n); back(r, res, R()); return note("bb_shr", rc); },
      bc_Bitboard_ShiftUp: (a, res, n) => { top = 0; const x = toE(a, R()), r = outE(R()); const rc = ex.Bitboard_ShiftUp(H.meta, x, r, n); back(r, res, R()); return note("bb_shu", rc); },
      bc_Bitboard_Reflect: (a, res, s) => { top = 0; const x = toE(a, R()), r = outE(R()); const rc = ex.Bitboard_Reflect(H.meta, x, r, s); back(r, res, R()); return note("bb_reflect", rc); },
      bc_Bitboard_DrawCircle: (b, x, y, rad) => { top = 0; const e = toE(b, R()); const rc = ex.Bitboard_DrawCircle(H.meta, e, x, y, rad); back(e, b, R()); return note("bb_circle", rc); },
      bc_Bitboard_DrawChebyshev: (b, x, y, rad) => { top = 0; const e = toE(b, R()); const rc = ex.Bitboard_DrawChebyshev(H.meta, e, x, y, rad); back(e, b, R()); return note("bb_cheb", rc); },
      bc_Bitboard_ImportRawBuffer: (b, bytes, n) => { b8().copyWithin(b, bytes, bytes + Math.min(n, R())); return 0; },
      bc_Bitboard_ExportRawBuffer: (b, bytes, n) => { b8().copyWithin(bytes, b, b + Math.min(n, R())); return 0; },
      bc_Bitboard_ShadowCast: (w, x, y, res, d) => { top = 0; const e = toE(w, R()), r = outE(R()); const rc = ex.Bitboard_ShadowCast(H.meta, e, x, y, r, d); back(r, res, R()); return note("bb_shadow", rc); },
      bc_Bitboard_ReachableMask: (w, x, y, res, d) => { top = 0; const e = toE(w, R()), r = outE(R()); const rc = ex.Bitboard_ReachableMask(H.meta, e, x, y, r, d); back(r, res, R()); return note("bb_reach", rc); },
      bc_DistanceField_ComputeWithExpansionCount: (w, roots, vis, dist, maxd, cnt) => {
        top = 0; const a = toE(w, R()), b = toE(roots, R()), v = outE(R()), d = outE(D()), c = outE(4);
        const rc = ex.DistanceField_ComputeWithExpansionCount(H.meta, a, b, v, d, maxd, c);
        back(v, vis, R()); back(d, dist, D()); if (cnt) b8().set(H.u8.subarray(c, c + 2), cnt); return note("df_compute", rc);
      },
      bc_DistanceField_ComputeToWithExpansionCount: (w, roots, dests, vis, dist, maxd, cnt) => {
        top = 0; const a = toE(w, R()), b = toE(roots, R()), t = toE(dests, R()), v = outE(R()), d = outE(D()), c = outE(4);
        const rc = ex.DistanceField_ComputeToWithExpansionCount(H.meta, a, b, t, v, d, maxd, c);
        back(v, vis, R()); back(d, dist, D()); if (cnt) b8().set(H.u8.subarray(c, c + 2), cnt); return note("df_computeto", rc);
      },
    };
    // Call trace for one instance (HOST_TRACE=c0): the last calls before a crash.
    if (process.env.HOST_TRACE && process.env.HOST_TRACE === (champ === -1 >>> 0 ? "d" + team : "c" + champ)) {
      inst.trace = [];
      for (const k of Object.keys(env)) {
        const f = env[k];
        if (typeof f !== "function" || k === "yield") continue;
        env[k] = (...a) => { const r = f(...a); inst.trace.push(k + "(" + a.join(",") + ")=" + r); if (inst.trace.length > 60) inst.trace.shift(); return r; };
      }
    }
    // Action log (H.onAction(champ, name, args, rc)): what the bot did, for comparisons with forced turns.
    for (const k of ["move_to_with_result", "attack", "cast_with_result", "use_consumable_with_result", "recall", "submit_gems"]) {
      const f = env[k];
      env[k] = (...a) => { const r = f(...a); if (H.onAction) H.onAction(champ, k, a, r); return r; };
    }
    // Anything not mapped: report and fail loudly in debug.
    for (const im of WebAssembly.Module.imports(mod))
      if (im.module === "env" && !(im.name in env)) env[im.name] = (...a) => { note("UNMAPPED_" + im.name, 99); return 99; };
    // Minimal WASI: stdout/stderr captured, no files, no environment.
    const wasi = {
      fd_write: (fd, iovs, n, nw) => {
        let tot = 0; const d = bm();
        for (let i = 0; i < n; i++) {
          const p = d.getUint32(iovs + 8 * i, true), l = d.getUint32(iovs + 8 * i + 4, true);
          const s = Buffer.from(b8().subarray(p, p + l)).toString("utf8");
          H.stdout.push(`[${team}/${champ === -1 >>> 0 ? "d" : champ}] ${s}`); tot += l;
        }
        d.setUint32(nw, tot, true); return 0;
      },
      fd_close: () => 0, fd_seek: () => 70, fd_fdstat_get: () => 0, environ_get: () => 0,
      environ_sizes_get: (c, s) => { bm().setUint32(c, 0, true); bm().setUint32(s, 0, true); return 0; },
      proc_exit: (c) => { throw new Error("proc_exit " + c); },
    };
    const instance = await WebAssembly.instantiate(mod, { env, wasi_snapshot_preview1: wasi });
    bot = instance.exports;
    inst.bot = bot;
    // Lab builds (A2_LAB): the macro intervention for this champion (lab.h: 10 int32), read back at game end.
    // H.labCtlAll = { kind, round, len }: the same intervention for every champion (each bot gets its own handle).
    if (H.labCtlAll && bot.lab_ctl && champ !== (-1 >>> 0)) {
      new Int32Array(bot.memory.buffer, bot.lab_ctl(), 10).set([champ, H.labCtlAll.round, H.labCtlAll.kind, H.labCtlAll.len, -2, -2, -2, -2, -2, -2]);
    }
    if (H.labCtl && bot.lab_ctl && champ === H.labCtl.champ && (H.labCtl.team === undefined || team === H.labCtl.team)) {
      const p = bot.lab_ctl(), v = new Int32Array(bot.memory.buffer, p, 10);
      v.set([H.labCtl.champ, H.labCtl.round, H.labCtl.kind, H.labCtl.len, -2, -2, -2, -2, -2, -2]);
      H.labRead = () => Array.from(new Int32Array(bot.memory.buffer, p, 10));
      if (bot.lab_macro_feat) H.macroRead = () => Array.from(new Float32Array(bot.memory.buffer, bot.lab_macro_feat(), 21));
      if (bot.lab_fight_feat) H.fightRead = () => Array.from(new Float32Array(bot.memory.buffer, bot.lab_fight_feat(), 25));
    }
    // Lab builds (A2_LAB): this team's learner weights.
    const wts = H.weights && H.weights[team];
    if (wts && bot.lab_learner_w) {
      const p = bot.lab_learner_w();
      new Float32Array(bot.memory.buffer, p, 16).set(wts.slice(0, 16));
    }
    // Lab builds (A2_LAB): this team's joint-search knobs (lab.h, 16 floats; knob_es.js).
    const kn = H.knobs && H.knobs[team];
    if (kn && bot.lab_knobs) new Float32Array(bot.memory.buffer, bot.lab_knobs(), kn.length).set(kn);
    // Lab builds with A2_MACRO (E70): this team's strategy switcher weights (lab.h macro_w; macro_es.js).
    const mw = H.macroW && H.macroW[team];
    if (mw && bot.lab_macro_w) new Float32Array(bot.memory.buffer, bot.lab_macro_w(), mw.length).set(mw);
    // Lab builds: this team's item build table (lab.h builds, 16 x 17 ints; build_lab.js).
    const bt = H.builds && H.builds[team];
    if (bt && bot.lab_builds) new Int32Array(bot.memory.buffer, bot.lab_builds(), bt.length).set(bt);
    // Lab builds with A2_POLICY: this team's fight/run policy weights and mode (0 argmax, 1 sample), seeded per champion.
    const pw = H.polW && H.polW[team];
    if (pw && bot.lab_pol_w) {
      new Float32Array(bot.memory.buffer, bot.lab_pol_w(), pw.length).set(pw);
      const cfg = new Int32Array(bot.memory.buffer, bot.lab_pol_cfg(), 4);
      cfg.set([H.polMode ? H.polMode[team] : 0, (H.polSeed || 1) * 7919 + champ * 104729 + 1, 0, cfg[3]]);
    }
    inst.run = WebAssembly.promising(instance.exports._start);
    return inst;
  }

  // Give one turn to an instance: start or resume it; resolves when it yields.
  turn(inst) {
    inst.turn++;
    return new Promise((res, rej) => {
      inst.onYield = res;
      if (!inst.started) {
        inst.started = true;
        inst.run().then(() => rej(new Error("bot returned")), (e) => {
          inst.dead = String(e);
          if (e instanceof WebAssembly.Exception) inst.deadInfo = "wasm exception (C++ throw escaped)";
          else inst.deadInfo = e && e.stack ? e.stack.split("\n").slice(0, 3).join(" | ") : "";
          inst.onYield(); // the turn in progress (not necessarily the first)
        });
      } else inst.resume();
    });
  }

  // Play a game between two bot wasm files; returns submitted gems per team and rounds.
  // hooks (all optional):
  //   draft(team) -> champion type to draft (the host drafts; no draft instance runs)
  //   beforeTurn(round, champ, team) -> called at each champion input boundary before the bot (state setup)
  //   force(round, champ, team) -> a function(host) that plays this turn instead of the bot, or null
  //   afterTurn(round, champ, team) -> called after the turn ends; return true to stop the game
  async play(wasmA, wasmB, mapFile, maxRounds = 2000, weights = null, hooks = {}) {
    this.weights = weights;
    this.abort = undefined;
    this.endFails = 0;
    this.newGame(mapFile);
    const ex = this.ex, files = [wasmA, wasmB];
    let steps = 0;
    for (;;) {
      ex.Game_Runner_Advance(this.g);
      const [phase, team, round, champ] = this.state();
      if (phase > 1 || round > maxRounds) break;
      if (team === 2) { if (++steps > 5e6) break; continue; }
      const want = phase === 0 && hooks.draft ? hooks.draft(team) : null;
      if (want !== null && want !== undefined) {
        // The wanted type, else the next free one. A hook answering null lets that team's own draft bot pick.
        for (let k = 0; k < 12 && ex.Game_Action_Draft(this.g, (want + k) % 12) !== 0; k++);
        if (ex.Game_Runner_EndTurn(this.g, 0) !== 0 && ++this.endFails > 50) { this.abort = "draft end turn keeps failing"; break; }
        if (++steps > 5e6) break;
        continue;
      }
      if (phase === 1 && hooks.beforeTurn) hooks.beforeTurn(round, champ, team);
      const forced = phase === 1 && hooks.force ? hooks.force(round, champ, team) : null;
      if (forced) {
        forced(this);
        if (ex.Game_Runner_EndTurn(this.g, 0) !== 0 && ++this.endFails > 50) { this.abort = "forced end turn keeps failing"; break; }
        if (++steps > 5e6) break;
        if (hooks.afterTurn && hooks.afterTurn(round, champ, team)) break;
        continue;
      }
      const key = phase === 0 ? "d" + team : "c" + champ;
      let inst = this.instances.get(key);
      if (!inst) {
        inst = await this.makeInstance(files[team], team, phase === 0 ? -1 >>> 0 : champ);
        this.instances.set(key, inst);
      }
      this.cur = { key, round, phase };
      if (!inst.dead) await this.turn(inst);
      const rc = ex.Game_Runner_EndTurn(this.g, 0);
      if (rc !== 0) {
        this.endFails = (this.endFails || 0) + 1;
        if (this.debug && this.endFails <= 3) console.error("EndTurn", rc, this.E.cstr(ex.GetLastErrorMsg()), this.state(), key, "dead:", inst.dead || "-");
        if (this.endFails > 50) { this.abort = "end turn keeps failing: " + this.E.cstr(ex.GetLastErrorMsg()); break; }
      }
      if (phase === 1 && hooks.afterTurn && hooks.afterTurn(round, champ, team)) break;
      if (++steps > 5e6) break;
    }
    const gems = [0, 1].map((t) => (ex.Game_API_GetSubmittedGemCount(this.g, t, this.arena) === 0 ? this.m.getUint32(this.arena, true) : -1));
    const out = { gems, round: this.state()[2], phase: this.state()[0], abort: this.abort };
    if (hooks.final) out.final = hooks.final(this);
    // Policy decision logs (A2_POLICY lab builds): features, action, log-probability, round per decision.
    if (this.polW) {
      out.polLogs = [];
      for (const inst of this.instances.values()) {
        const b = inst.bot;
        if (!b || !b.lab_pol_cfg || inst.dead) continue;
        const cfg = new Int32Array(b.memory.buffer, b.lab_pol_cfg(), 4), n = cfg[2], entry = cfg[3] || 27;
        if (n > 0) out.polLogs.push({ team: inst.team, champ: inst.champ, entry, data: Array.from(new Float32Array(b.memory.buffer, b.lab_pol_log(), n * entry)) });
      }
    }
    // Map context (A2_LAB builds with lab_ctx): raw features each champion read at turn one.
    out.ctx = [];
    for (const inst of this.instances.values()) {
      const b = inst.bot;
      if (b && b.lab_ctx && !inst.dead) out.ctx.push({ team: inst.team, raw: Array.from(new Float32Array(b.memory.buffer, b.lab_ctx(), 5)) });
    }
    this.ex.Game_Destroy(this.g);
    // Release every bot instance: a suspended instance (pending JSPI promise) keeps its whole memory alive as long
    // as anything references its resume function or promise (measured ~6 MB per game leaked before this).
    for (const inst of this.instances.values()) {
      inst.resume = null; inst.onYield = null; inst.run = null; inst.trace = null; inst.bot = null;
    }
    this.instances.clear();
    this.modCache = {};
    return out;
  }
}

module.exports = { Host };

if (require.main === module) {
  const args = process.argv.slice(2);
  const debug = args.includes("--debug");
  const [a, b, map, maxR] = args.filter((x) => !x.startsWith("--"));
  const H = new Host({ debug });
  const t0 = Date.now();
  process.on("beforeExit", () => { if (!H.done) { console.log("STALLED at", JSON.stringify(H.cur), "errors", JSON.stringify(H.errors)); console.log(H.stdout.slice(-15).join("")); for (const [k, v] of H.instances) if (v.trace) console.log(k, v.trace.slice(-25).join("\n")); } });
  H.play(a, b, map, parseInt(maxR || "2000", 10)).then((r) => {
    H.done = true;
    console.log(JSON.stringify({ ...r, ms: Date.now() - t0, errors: H.errors }));
    for (const [k, v] of H.instances) { console.log(k, "turns", v.turn, "dead", v.dead || "-", v.deadInfo || ""); if (v.trace) console.log(v.trace.join("\n")); }
    if (debug) console.log(H.stdout.slice(0, 40).join(""));
  }, (e) => { console.error("host error", e); console.log(H.stdout.slice(-20).join("")); });
}
