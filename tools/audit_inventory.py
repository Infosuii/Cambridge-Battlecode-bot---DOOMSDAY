"""Agent A: generate agents/A/decision_inventory.json (+ agents/A/inventory_table.md) from anchored entries.

Every file:line is computed from the original source (git HEAD bot/src == references/original-src for .cpp files) by
searching the anchor text, so the inventory cannot drift from the code silently: a missing anchor fails the run.

    python tools/audit_inventory.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADS = {h['name']: h['id'] for h in json.loads((ROOT / 'schemas/heads.json').read_text())['heads']}
KEEP = 'deterministic - keep'


def src(name: str) -> list[str]:
    data = subprocess.run(['git', 'show', f'HEAD:bot/src/{name}'], cwd=ROOT, capture_output=True).stdout.decode('utf-8')
    return data.splitlines()


FILES = {n: src(n) for n in ('bot.cpp', 'tsearch.cpp', 'draft.cpp', 'world.cpp', 'deny.cpp', 'fight.cpp', 'episode.cpp', 'strategy.h',
                             'bot.h', 'common.h')}


def find(file: str, pat: str, after: int = 0) -> int:
    """First line containing `pat` at or after `after` (0-based); falls back to the whole file (hooks that live in the caller)."""
    lines = FILES[file]
    for rng in (range(after, len(lines)), range(0, len(lines))):
        for i in rng:
            if pat in lines[i]:
                return i + 1
    raise SystemExit(f'anchor not found in {file} after line {after}: {pat!r}')


E = []


def entry(id, area, file, fn, fn_pat, head, inputs, candidates, choice, fuel, state, hook, decision_pat=None, status='active',
          capture=None, notes=''):
    E.append(dict(id=id, area=area, file=file, fn=fn, fn_pat=fn_pat, head=head, inputs=inputs, candidates=candidates,
                  choice=choice, fuel=fuel, state=state, hook=hook, decision_pat=decision_pat, status=status, capture=capture,
                  notes=notes))


# ------------------------------------------------------------------------------------------------ turn / strategy
entry('chain', 'strategy', 'bot.cpp', 'Bot::play_turn (behaviour chain)', 'void Bot::play_turn() {', 'strategy',
      'fought (handle_enemies), win_now(), hp/max_hp, kDangerHp, every behaviour predicate below',
      'fixed priority order: enemy > tribute-win > home > hunt > tribute > farm (rush/a2_join/fog compiled out)',
      'the first branch whose function returns true (it also acts); captured after the fact as nnt::Turn::chain',
      'none directly (each behaviour gates its own work)', 'mode, heading_home, force_tribute, target_group (via behaviours)',
      ('before', '    } else if (win_now() && hp >= max_hp * tune::kDangerHp && tribute_if_needed()) {',
       'insert `if (!fought && strategy head chose k != 0) { run behaviour k first }`; candidate 0 = run the teacher chain unchanged. '
       'The teacher choice is not known before acting (decide+act are fused), so candidate 0 is "teacher order" and the label is '
       'the captured branch (cap_chain).'),
      decision_pat='    if (fought) {', capture='cap_chain (Chain enum per branch, dead turn)')
entry('brain_adapt', 'strategy', 'strategy.h', 'brain::load/adapt (class profile -> tune::*)', 'inline void adapt(int ally_score, int enemy_score) {',
      KEEP, 'draft-memory class byte, map id, both scores', 'per-class profile and per-map multipliers (tables)',
      'tune::kAggression, kTributeCarry, kRetreatHp, kDangerTtd, kShopGold, kHunt, ... (rewritten every turn)', 'none',
      'tune:: globals (process-wide), brain::state', ('after', '    tune::kShopGold = p.shop_gold;',
                                                         'heads read the resulting tune values as teacher parameters (nn_teacher_access::aggression/retreat_hp/tribute_carry)'),
      notes='Teacher parameterisation, not a choice among actions. Keep: the heads (strategy/bank/engage) consume these as features; '
            'replacing them would change every downstream threshold at once.')
entry('lab_knobs', 'strategy', 'bot.cpp', 'Bot::play_turn lab knob block (A2_LAB)', 'void Bot::play_turn() {', KEEP,
      'lab::knobs[0..47] = A2_KNOBS (24 values) + zeros', 'none', 'scaled tune values', 'none', 'tune:: globals; static b_* first-turn copies',
      ('after', '        if (type == bc::champion_type::prism) tune::kTributeCarry', 'none (constants)'),
      decision_pat='        const float* k = lab::knobs;',
      notes='Baked gameplay knobs; must be kept (patch 02 keeps them as constexpr under NN_STRIP_LAB).')
entry('channel_guard', 'bank', 'bot.cpp', 'Bot::play_turn channel guard (cancel recall/tribute)', 'void Bot::play_turn() {', 'bank',
      'recalling/submitting state, remaining channel time, enemies in range+2 (strength + focus/2), hp, kChannelGuard',
      'keep channelling / cancel and play the turn', '`incoming * (left + 1) * kChannelGuard < hp` (return = keep)', 'none',
      'engine channel state', ('after', '            if (cheb(e.pos, pos) <= e.range + 2) incoming += e.strength + e.focus * 0.5f;',
                                'bank head context "channel": candidate 0 = teacher verdict; alternative = the opposite. Cancelling is always legal while channelling.'),
      decision_pat='        if (incoming * static_cast<float>(left + 1) * tune::kChannelGuard < hp) return;',
      notes='Also: a recall is cancelled when win_now() (deterministic - keep: a bag that wins the game must be banked).')
entry('shop', 'economy', 'bot.cpp', 'Bot::shop', 'void Bot::shop() {', 'shop',
      'gold, item_count(), champion type, build_for(type), tune::kAltarLocks, mobility_farming_map',
      'altar lock (10 g) then shards of the first build steps with want = min(total - owned(shards + 5 x emblem), gold/30)',
      'first step with want > 0 (bought immediately; loop continues while gold >= 30)', 'none',
      'engine inventory/gold (persistent across the game)', ('before', '        const auto counts = me.item_count();',
                                                            'shop head: candidate 0 = the teacher purchase computed by the capture pre-pass; '
                                                            'alternatives = affordable purchasable shards (can_buy), save. Execution keeps can_buy/buy.'),
      decision_pat='        for (const auto& step : build_for(type)) {', capture='cap_shop (pre-pass, no purchase)',
      notes='Called when dead (every dead turn) and when on own spawn or Tavi (anywhere; remote_shop). APEX_SHOP_GOLD only gates the trip home (go_home_if_needed `rich`).')
entry('build_for', 'economy', 'bot.cpp', 'build_for (item build order)', 'std::vector<BuildStep> build_for(bc::champion_type t) {', 'shop',
      'champion type, caster set, tune::kBuild (0), UB_BUILD, mobility_farming_map, lab::builds (zero)', 'static lists per type',
      'returned vector of (item, total) steps', 'none', 'none', ('after', '    if (UB_BUILD && !caster && !mobility_farming_map)',
                                                                 'the build list is the teacher prior for the shop head (steps in order)'),
      notes='lab::builds override is stripped by patch 02 (NN_STRIP_LAB=1); inert with zero table.')
entry('go_home', 'strategy', 'bot.cpp', 'Bot::go_home_if_needed', 'bool Bot::go_home_if_needed() {', 'strategy',
      'on_spawn, hp vs kRetreatHp (C&I factor), kThreatRetreat + sightings, gold >= kShopGold (rich), heading_home, capture in progress, hot_zone, enemies within 6',
      'stay on spawn to heal / leave hot zone / recall / walk home (spawn_field)', 'return true + heading_home = true',
      'none (walks use follow_field / walk_toward gates)', 'heading_home (persistent until spawn)',
      ('after', '    heading_home = true;', 'strategy head "home" option forces this function; bank/strategy can veto the go-home verdict before `heading_home = true`'),
      decision_pat='    if (!heading_home && !low && !rich) return false;',
      notes='Recall vs walk: `dist > kShopWalkDist && !enemy_close` - deterministic (legality: recall is cancelled by damage).')
entry('hunt', 'strategy', 'bot.cpp', 'Bot::hunt', 'bool Bot::hunt() {', 'strategy',
      'kHunt (brain), gems < kHuntGems, hp >= kHuntHp, last_flee_round, sightings <= 3 rounds old within kHuntRange (not enemy spawn)',
      'nearest fresh sighting', '`best` (const Sighting*)', 'none', 'none',
      ('before', '    if (!best) return false;\n    mode = "hunt";', 'strategy head "hunt/contest" option; target = teacher sighting'),
      decision_pat='    if (!tune::kHunt || gems >= tune::kHuntGems || hp < max_hp * tune::kHuntHp) return false;',
      notes='Snipe (APEX_SNIPE 0) and distress rescue (APEX_DISTRESS 0) are compiled out (constexpr false).')
entry('tribute', 'bank', 'bot.cpp', 'Bot::tribute_if_needed', 'bool Bot::tribute_if_needed() {', 'bank',
      'gems, kTributeCarry (brain x knobs), dist to altar ring (static or threat-avoiding safe field when gems >= 15), wins, late, end_bank, rhythm, edge (NOVA_BANK_FIX), threatened, force_tribute, A2_ALTARFIX state',
      'go (bank now) / keep farming; altar = nearest via altar_field (or safe ring); at dist 0 the first altar in submit range (attack enemy lock first)',
      '`go` (bool); altar implicit in the distance field', 'none (ensure_altar_field builds once)',
      'tribute_stuck / tribute_last_dist / tribute_off_until (A2_ALTARFIX), force_tribute',
      ('after', '        dist <= tune::kTributeNearDist + static_cast<int>(std::lround(2.0f * LABK(36))) || (threatened && gems >= 20 && dist <= 8);',
       'bank head: candidate 0 = `go`; alternative = !go (and later: other reachable altars). Substituting go=true must keep the walk/submit code below (legal by construction).'),
      decision_pat='    const bool go = force_tribute || wins || late || end_bank || rhythm || edge || gems >= tune::kTributeCarry ||',
      capture='cap_bank (every term)', notes='Called from the chain twice (tribute-win, tribute), from farm (wait-respawn UseWaits, plan-bank).')
entry('farm_waits', 'bank', 'bot.cpp', 'Bot::farm respawn wait (APEX_USE_WAITS)', 'bool Bot::farm() {', 'bank',
      'respawn wait, altar trip (2 x field dist + bag/10), home trip, gems >= 10, gold >= 90', 'bank while waiting / shop while waiting / wait at the group',
      'force_tribute + tribute_if_needed() or heading_home + go_home_if_needed()', 'none', 'force_tribute, heading_home',
      ('after', '            const int home_trip = std::min(2 * static_cast<int>(fdist(w.spawn_field, pos)), 12);', 'bank head context "wait": candidate 0 = teacher verdict'),
      decision_pat='            if (gems >= 10 && wait > altar_trip + 2) {')

# ------------------------------------------------------------------------------------------------ objective
entry('score_groups', 'objective', 'bot.cpp', 'Bot::score_groups', 'int Bot::score_groups(int participants_hint, int& best_need, float& best_score) {', 'objective',
      'groups (state, gems, gold, hp_left, respawn), distances (field_ptr), claims (shared memory), need (soak model), dps, gold_weight, cohesion, mid weight, enemy recency, stickiness, learner (identity)',
      'groups visited nearest-first, branch-and-bound pruned; top-K (K = kRouteK = 6 of 8 slots) RouteCand {gi, need, value, cost, score, finish}',
      '`best` (+ best_need, best_score); after route_search: top[pick]', 'kDet: stop scoring at kDetScoreN evaluated or fuel < kDetSafety; route search only if fuel > kRouteFuel (55000)',
      'group_order / order_seen (visit order), avoid_until (set for covered / shared-gold groups), big_group, mid_group',
      ('before', '    return best;\n}\n\n// Follow-up table', 'capture top-K here (cap_objective: candidate 0 = returned group). The commit hook is in farm().'),
      decision_pat='        if (score > best_score) {', capture='cap_objective (top-K, teacher first)',
      notes='The v50 camp net built 18 features per scored group INSIDE this loop (before route_search): fuel spent there changed the '
            'route-search gate and the kDet scoring cap. Any head here must read the captured top-K after the loop.')
entry('route_search', 'objective', 'bot.cpp', 'Bot::route_search', 'int Bot::route_search(const RouteCand* top, int n_top) {', KEEP,
      'top-K first targets, follow_value/fixed/respawn table, group_to_group rows', 'routes of depth <= kRouteDepth (2) over follow-ups',
      'returned index into top', 'stops when fuel < kRouteFuel / 2', 'pair rows (World cache)',
      ('after', '        const int pick = tune::kPlan ? plan_search(top, n_top, bank) : route_search(top, n_top);', 'none: the objective head re-ranks the post-route top-K'),
      notes='Teacher planner; its output is candidate 0 of the objective head. plan_search (APEX_PLAN 0) is compiled out.')
entry('farm_commit', 'objective', 'bot.cpp', 'Bot::farm (target commit)', 'bool Bot::farm() {', 'objective',
      'low_fuel keep-target, escort/role-squad/squads/pair (all 0), NOVA_DUO follower (unseen maps), score_groups result, chip-at-big fallback',
      'teacher `best` or a captured top-K alternative (same type: group index + need)', '`best`, `best_need`',
      'low_fuel: kDet ? first turn / fight-search turn / fuel < kDetSafety+10000 : fuel < kLowFuel; chip fallback needs fuel > kDetSafety+10000',
      'target_group, staging_since, my_claim_since, shared-memory claim (write_claim)',
      ('before', '    if (best != target_group) {\n        staging_since = -1;', 'objective head: substitute (best, best_need) from nnt::Objective::cand[k] '
       'when Objective::teacher == best (else K = 1); the claim write that follows keeps the protocol unchanged.'),
      decision_pat='    if (best < 0) best = score_groups(duo_leader ? 2 : 1, best_need, best_score);',
      notes='Verified by the capture self-test: on 100% of farm/nofarm turns the committed target_group equals the captured teacher choice (agents/A/evidence/capture_selftest.json).')
entry('duo', 'role', 'bot.cpp', 'Bot::farm NOVA_DUO / buddy()', 'bool Bot::farm() {', 'role',
      'slot types (melee/ranged), buddy pairing (Cassi+Issac first), buddy claim, distance <= NOVA_DUO_DIST, official-map flag',
      'follow the melee buddy\'s alive group / own job', 'best = buddy claim (ranged member) or duo_ignore_slot (melee leader)', 'skipped when low_fuel',
      'buddy_slot (cached), duo_map_ok, duo_ignore_slot', ('after', '    // Pair mode (WHIM\'s opening shape)', 'role head context: teacher-implied role = duo leader/follower/solo'),
      decision_pat='    if (NOVA_DUO > 0 && duo_map_ok == 1 && !low_fuel && best < 0 && round < NOVA_DUO_UNTIL) {',
      notes='NOVA_DUO_MAPS 1: active only on maps not in the official table (is_official_map() == false).')
entry('claims', 'role', 'bot.cpp', 'shared-memory claims (write_claim / claims_split / senior_claims / open_call_by_lower)', 'void Bot::write_claim(int group) {', KEEP,
      'own target group or kClaimDead/idle; other slots\' 7-bit claims', 'n/a (protocol)', 'claim code in our slot', 'none',
      '8-byte team word: 6 x 7-bit claims (0-41), sighting x/y/round (42-61), distress (62), event flag (63)',
      ('after', '    bc::shared_memory.write(0, std::span<std::uint64_t, 1>{&v, 1});', 'none: heads may read claims (nn_teacher_access::claim_of) but never write their own codes'),
      notes='Protocol is an invariant (INVARIANTS.md I5/I6). Codes 112-118 are fight orders (team_decide; inactive), 126 dead, 127 idle.')
entry('sighting', 'belief', 'bot.cpp', 'share_sighting / read_sighting / APEX_EVENTS respawn publication', 'void Bot::share_sighting(bool call_for_help) {', KEEP,
      'nearest visible enemy; teammate word; pending group events', 'n/a', 'shared word bits 42-63', 'none', 'World::sightings, distress',
      ('after', '    if (call_for_help) v |= std::uint64_t{1} << kDistressBit;', 'none: the belief head reads World::sightings'),
      notes='One sighting slot per team; an event (bit 63) overwrites the sighting when no fresh sighting (<= 11 rounds) would be lost.')

# ------------------------------------------------------------------------------------------------ fights
entry('enemy_gate', 'engage', 'bot.cpp', 'Bot::handle_enemies (entry gates)', 'bool Bot::handle_enemies() {', KEEP,
      'w.enemies, nearest distance (spawn-parked enemies ignored), threat_on_me', 'fight logic runs / skip (return false)',
      '`!nearest || nearest_d > 8` -> false', 'none', 'none', ('after', '    if (!nearest || nearest_d > 8) return false;', 'n/a'),
      notes='Visibility gate; the engage head starts after it (cap_fight_begin).')
entry('target', 'combat', 'bot.cpp', 'Bot::handle_enemies target selection', 'bool Bot::handle_enemies() {', 'combat',
      'per enemy within range+4 (not on enemy spawn): ttk = hp / (my dps + allies in reach), worth (gems, C&I, tributing, recalling, lab knobs 16-21)',
      'scored enemies, key = ttk / worth (lowest wins)', '`target` (const EnemyRec*), target_ttk', 'none', 'none',
      ('before', '    float aggression = tune::kAggression * ep_aggr;', 'combat head (target): candidate 0 = `target`; alternatives = captured enemies (same type)'),
      decision_pat='        const float key = ttk / worth;', capture='cap_enemy (per enemy), cap_formula',
      notes='Self-test: the captured formula target equals argmin(key) on every fight turn (0 violations, 4 matches).')
entry('verdict_formula', 'engage', 'bot.cpp', 'Bot::handle_enemies fight-or-flight formula', 'bool Bot::handle_enemies() {', 'engage',
      'target_ttk, ttd, risk (bag), ci_risk, aggression (brain x knobs x low-hp), danger_ttd, danger_hp, NOVA_BURST_K burst (enemy cooldowns), C&I outnumbered (off)',
      'winning / in_danger / neither', '`winning`, `in_danger` (bool pair)', 'none', 'last_flee_round (set when fleeing)',
      ('before', '    bool tfc_applied = false;', 'engage head context "formula" (or take the final verdict hook below)'),
      decision_pat='    bool winning = target && target_ttk * risk * ci_risk < std::min(ttd, 8.0f) * aggression;', capture='cap_formula')
entry('team_decide', 'engage', 'tsearch.cpp', 'Bot::team_decide (APEX_TFC)', 'int Bot::team_decide(std::uint32_t& focus_handle) {', 'engage',
      'ts snapshot, 3 team plans x 2 enemy models', 'status quo / all fight (focus) / all run', 'order 1/2/0 + focus_handle',
      'fuel < kTsReserve + 30000 -> 0; per playout 2 x worst', 'claim slot order codes 112-118', ('after', '    float mean[3] = {};', '(caller: bot.cpp handle_enemies after order = team_decide(order_target)) engage head context "team"'),
      status='inactive in the original: called only when tune::kTfc (APEX_TFC 0) || tune::packOn (NOVA_PACK_C 0)', capture='cap_tfc')
entry('tactical_decide', 'engage', 'tsearch.cpp', 'Bot::tactical_decide (fight-or-run search)', 'int Bot::tactical_decide() {', 'engage',
      'ts snapshot (units, kits, camps omitted), 2 enemy models, rounds kTsDecideRounds (+knob 31), weights (+knobs 24-29)',
      'fight / run / no verdict (margin kTsDecideMargin + knob 30)', 'return +1 / -1 / 0', 'fuel < kDetSafety + 10000 -> 0; playouts while fuel > reserve + 2 x worst',
      'a2ts::snap (omit_reach, link_partial), ts_ran_round', ('after', '        const int verdict = tactical_decide();',
                                                               'engage head: candidate 0 = verdict; alternatives = the other two verdicts; A2_TD_AUTH '
                                                               'legality (unmodelled risks keep the formula danger) must stay after the head'),
      decision_pat='    if (fight > run + margin) A2RET(5, 1);', capture='cap_td_values (fight, run, margin) + cap_td_verdict')
entry('verdict_final', 'engage', 'bot.cpp', 'Bot::handle_enemies final verdict', 'bool Bot::handle_enemies() {', 'engage',
      'formula, search verdict (A2_TD_AUTH), team-fight knob 41 (inert), lab ctl 4/5', 'fight / flee / neither',
      '`winning`, `in_danger`, threat_on_me', 'none', 'last_flee_round',
      ('before', '    if (tune::kTribDeny & 2) {\n        if (in_danger && !winning) try_lock_altar();', 'engage head (preferred hook): substitute the (winning, in_danger) pair; '
       'everything below executes the chosen verdict with the original legality checks'), capture='cap_fight_final')
entry('deny_tribute', 'combat', 'deny.cpp', 'Bot::deny_tribute (APEX_TRIB_DENY & 2)', 'bool Bot::deny_tribute() {', 'combat',
      'tributing enemies with >= 10 gems, channel time left, our reach (dash), locks, stun, ally damage', 'enemy x (kill / lock / stun) options scored',
      '`best` (EnemyRec*), best_altar, best_kill', 'none', 'mode', ('after', '    if (!best) return false;', 'combat head context "deny": candidate 0 = best'),
      decision_pat='        if (!best || score > best_score) {')
entry('try_lock_altar', 'combat', 'bot.cpp', 'Bot::try_lock_altar', 'bool Bot::try_lock_altar() {', KEEP,
      'altar_lock count, tributing enemies with >= 10 gems, altars within 2', 'first lockable altar', 'lock.use(altar)', 'none', 'consumable',
      ('before', '                if (lock.use(a)) {', 'n/a'), notes='Cancelling an enemy tribute with a lock we already carry is dominant when legal; keep.')
entry('bush_ambush', 'combat', 'bot.cpp', 'Bot::bush_ambush', 'bool Bot::bush_ambush() {', 'combat',
      'hidden bush tiles (cluster without visible enemy, not warded), enemies in range (key hp - 20 x gems)', 'victim from here or from a hidden neighbour step; spell from cover',
      '`victim`, `step`', 'none', 'mode', ('before', '    if (!victim) return false;\n    if (step != pos) {', 'combat head (target) + move head (step) context "ambush"'))
entry('bush_recall', 'strategy', 'bot.cpp', 'Bot::handle_enemies bush recall', 'bool Bot::handle_enemies() {', 'strategy',
      'losing, hp < 50%, hidden_here(), not hot zone, spawn distance > kShopWalkDist', 'recall from cover / continue fight logic', 'recall() + heading_home', 'none',
      'heading_home', ('before', '    if (in_danger && !winning && tune::kBushRecall && hp < max_hp * 0.5f && hidden_here() && !bit(w.hot_zone, pos) &&', 'strategy head context "retreat": candidate 0 = teacher'))
entry('caster_micro', 'move', 'tsearch.cpp', 'Bot::caster_micro (APEX_CMICRO)', 'bool Bot::caster_micro(const EnemyRec* target, bool engage) {', 'move',
      'tiles within one step, threats (enemies + awake camps), my spells (cooldown, range), risk (kCMicroRisk x knob 32 x hp)',
      'Option {to tile, attack index, spell, spell target, cast_first} scored offense - risk x danger', '`best` (Option)', 'none', 'cast_done, walked, pos',
      ('before', '    if (best.to == pos && best.attack < 0 && best.spell < 0 && danger_at(pos, -1, -1) <= 0.0f) return false;',
       'move head (to) + combat head (attack/spell) context "cmicro": candidate 0 = best Option'),
      decision_pat='        if (s > best.score) {')
entry('flee_hit', 'combat', 'bot.cpp', 'Bot::handle_enemies NOVA_FLEE_HIT', 'bool Bot::handle_enemies() {', 'combat',
      'leaving, melee, can_attack, adjacent enemies (lowest hp)', 'adjacent enemy to hit before fleeing', '`adj`', 'none', 'none',
      ('before', '        if (adj && (!target || cheb(target->pos, pos) > range) && attack_unit(adj->unit, adj->pos)) {', 'combat head context "flee-hit"'))
entry('escape_or_stand', 'move', 'bot.cpp', 'Bot::escape_or_stand (APEX_STAND)', 'bool Bot::escape_or_stand(const EnemyRec* target, const EnemyRec* nearest, float ttd) {', 'move',
      'enemies that can hit us next turn (catching), dash, cc spell, spawn steps vs ttd', '1 dash away, 2 stun the single chaser, 3 usual flee, 4 stand and fight (victim lowest hp)',
      'branch taken + victim', 'none', 'mode, heading_home', ('before', '    // 4. No way out: make the chaser pay. Hit whatever is in reach, lowest health first.',
                                                                 'move head context "escape" (branch) + combat head (stand victim)'))
entry('dash_away', 'move', 'bot.cpp', 'Bot::dash_away', 'bool Bot::dash_away() {', 'move',
      'dash range, tiles within reach scored by distance beyond enemy range x100 - spawn distance + bush hide', 'up to 24 dash landings sorted by safety',
      'cands[0..3] tried in order', 'none', 'pos, cast_done', ('before', '        for (int i = 0; i < n && i < 4; ++i) {\n            try {\n                if (bc::self().abilities()[s].use(cands[i].p)) {',
                                                              'move head (dash landings) context "escape"'))
entry('ranged_flee', 'combat', 'bot.cpp', 'Bot::handle_enemies ranged flee (APEX_RANGED_FLEE, kKiteCast & 4)', 'bool Bot::handle_enemies() {', 'combat',
      'nearest within 4, cc spell not exclusive with walking / exclusive stun on a lone melee chaser', 'stun nearest / flee-stun / no cast',
      'cast_done', 'none', 'cast_done, mode', ('before', '            const int planned_r = tune::kEscapeSearch ? run_escape(false) : 0;', 'combat head context "flee"'))
entry('retreat_from', 'move', 'bot.cpp', 'Bot::retreat_from', 'bool Bot::retreat_from(vec2 threat) {', 'move',
      'neighbour tiles: distance from threat (or dps-weighted multi-threat), spawn distance x (1 + kFleeHome), bush hide', 'up to 8 neighbours better than here, sorted',
      'cands in order (first legal move)', 'none', 'pos, walked', ('before', '    for (int i = 0; i < n; ++i) {\n        try {\n            if (me.move_absolute(cands[i].p)) {\n                pos = cands[i].p;\n                walked = true;\n                return true;\n            }\n        } catch (...) {',
                                                                  'move head context "retreat": candidate 0 = cands[0]; the move loop keeps falling through on refusal'))
entry('kite_step', 'move', 'bot.cpp', 'Bot::kite_step (APEX_KITE)', 'bool Bot::kite_step(const EnemyRec& target) {', 'move',
      'neighbours: distance to melee enemies (cap kKite), target in range, spawn distance', 'best neighbour', '`best`', 'none', 'pos, walked',
      ('before', '    if (best == pos) return false;\n    try {\n        if (me.move_absolute(best)) {\n            pos = best;\n            walked = true;\n            return true;\n        }\n    } catch (...) {\n    }\n    return false;\n}\n\nbool Bot::position_and_attack',
       'move head context "kite"'))
entry('cast_on_enemy', 'combat', 'bot.cpp', 'Bot::cast_on_enemy', 'bool Bot::cast_on_enemy(const EnemyRec& e) {', 'combat',
      'ready spells (excludes_walk vs walked), reach, value = modifier x focus (+120 cc, +400 vs tributing), striking dash (Heart of Ruin) landing tiles',
      'spell slot or striking-dash landing', '`best` slot, `dash_slot` + `dash_aim`', 'none', 'cast_done, pos',
      ('before', '    if (dash_slot >= 0) {\n        try {\n            if (bc::self().abilities()[dash_slot].use(dash_aim)) {', 'combat head (ability, target) context "cast"'),
      capture='cap_cast')
entry('engage_exec', 'engage', 'bot.cpp', 'Bot::handle_enemies engage execution (kite-cast, kite, fight-champ, gap-dash, fight-cast, chase)', 'bool Bot::handle_enemies() {', 'combat',
      'dist to target, range, enemy_spell_reach, nearest melee, kChaseRange, A2_GAPDASH landing cands', 'cast first / kite / attack / gap-dash / chase walk / give up',
      'branch taken', 'walk_toward fuel floor', 'mode, pos, cast_done, walked',
      ('after', '    const bool engage = winning || (dist <= range && ttd > 6.0f * risk);', 'combat head context "engage": choose among the legal execution branches'),
      decision_pat='    if (!engage) return false;', notes='position_and_attack is compiled out (APEX_POSITION 0); try_burst_kill (APEX_BURST 0) too.')
entry('reset_attack', 'combat', 'bot.cpp', 'Bot::use_reset_and_attack / attack_unit / opportunistic_attack', 'bool Bot::use_reset_and_attack(const bc::unit& target, vec2 where) {', KEEP,
      'ready attack_reset slot, can_attack, range', 'reset + second hit / nothing; opportunistic: first enemy in range (list order)', 'side effect', 'none', 'cast_done',
      ('after', '    for (int s = 0; s < 2; ++s) {\n        if (!spell_ready(s) || spells[s].kind != bc::ability_kind::attack_reset) continue;', 'n/a'),
      notes='A follow-up hit after a successful hit is additive damage; legality is the SDK\'s. opportunistic_attack target order could be a combat-head context later.')
entry('support_casts', 'combat', 'bot.cpp', 'Bot::support_casts (shield / heal)', 'void Bot::support_casts() {', 'combat',
      'hp fraction (< 0.85 with enemies or a target), A2_SHIELDLATE dash reservation, allies in heal range by missing hp', 'shield now / hold; heal target',
      'cast or not; `best` ally', 'none', 'cast_done, shield_late_pass', ('before', '                if (best && bc::self().abilities()[s].use(best->unit)) cast_done = true;', 'combat head context "support"'))
entry('priority', 'engage', 'bot.cpp', 'Bot::update_priority (APEX_PRIORITY 5)', 'void Bot::update_priority() {', KEEP,
      'nearest enemy, hp, kill available, recent sightings', 'priority value', '`want`', 'none', 'priority_set (engine scheduling persists)',
      ('before', '    if (want == priority_set) return;', 'n/a'), notes='Turn-order request; candidate for a later combat context. Keep: affects both teams\' scheduling.')

# ------------------------------------------------------------------------------------------------ movement / wards
entry('follow_field', 'move', 'bot.cpp', 'Bot::follow_field', 'bool Bot::follow_field(const bc::distance_field& field, const bc::bitboard& blocked, bool allow_dash) {', 'move',
      'distance field, blocked mask, travel dash first', 'downhill neighbours (score dq*4 + orthogonal penalty), sorted', 'cands in order (first legal move)',
      'none (callers gate the field search)', 'pos, walked, bridge_hold',
      ('after', '    std::sort(cands.begin(), cands.begin() + n, [](const Cand& a, const Cand& b) { return a.score < b.score; });',
       'move head context = combat_move ? combat : travel; candidate 0 = cands[0]; keep the fall-through move loop'), capture='cap_steps')
entry('walk_toward', 'move', 'bot.cpp', 'Bot::walk_toward', 'bool Bot::walk_toward(const bc::bitboard& goals_in) {', KEEP,
      'goals, blocked = static | units, governor cap rb::search_cap', 'path search (capped) then follow_field; greedy_step when the cap binds', 'via follow_field',
      'fuel < (kDet ? 9000 : kMinMoveFuel) -> no move; rb::search_cap(kTailReserve)', 'walk_boxed',
      ('after', '    return follow_field(field, blocked, true);\n}', 'n/a (the move head hooks in follow_field)'),
      decision_pat='    if (bc::fuel_remaining() < (tune::kDet ? 9000 : tune::kMinMoveFuel)) return false;',
      notes='Shortest-path machinery and budget governor are deterministic responsibilities (USER_REQUEST 4: navigation).')
entry('try_dash', 'move', 'bot.cpp', 'Bot::try_dash (travel dash)', 'bool Bot::try_dash(const bc::distance_field& field, const bc::bitboard& blocked) {', 'move',
      'dash ready, field distance here >= 3 (or a bridge gap), 5x5 tiles', 'tile with the largest field gain (dq + 1 < best)', '`best`', 'none', 'pos, cast_done',
      ('before', '        if (best == pos) return false;\n        try {\n            if (bc::self().abilities()[s].use(best)) {', 'move head (dash landing) context "travel"'))
entry('ward_ahead', 'ward', 'bot.cpp', 'Bot::ward_ahead (NOVA_WARD_AHEAD 6)', 'bool Bot::ward_ahead() {', 'ward',
      'no enemies, own ward distance, ward cooldown, bush clusters within 2 not covered by allied wards, aim = target group', 'bush tiles scored cheb(q, aim) x 4 + cheb(q, pos)',
      '`best` tile', 'rb::fits(70000, kTailReserve) else skip when a cluster would need labelling', 'ward_pos',
      ('before', '    if (best.x < 0) return false;\n    try {\n        if (me.place_ward(best)) {', 'ward head: candidate 0 = best, no-ward option'), capture='cap_ward')
entry('ward_reveal', 'ward', 'bot.cpp', 'Bot::ward_reveal (APEX_WARD_REVEAL 2)', 'bool Bot::ward_reveal() {', 'ward',
      'unexplained hp loss, sighting lost last round within 4, pre-emptive recent sighting, bush tiles within 2 of other clusters', 'up to 25 tiles sorted by distance to the lost sighting',
      'cands[0..2] tried', 'none', 'ward_pos', ('before', '    if (n == 0) return false;\n    auto& me = bc::self();', 'ward head context "reveal"'))
entry('reveal_bush_camp', 'ward', 'bot.cpp', 'Bot::reveal_bush_camp (NOVA_BUSH_WARD)', 'bool Bot::reveal_bush_camp(const GroupRec& g) {', 'ward',
      'camps of the target group hidden in bushes, ward cooldown', 'ward tile on the bush', '`at`', 'none', 'ward_pos',
      ('before', '    if (me.place_ward(at)) ward_pos = at;', 'ward head context "camp"'), decision_pat='if (me.place_ward(at)) ward_pos = at;')
entry('counter_ambush', 'move', 'bot.cpp', 'Bot::counter_ambush', 'bool Bot::counter_ambush() {', 'move',
      'unexplained hp loss, foreign bush tiles within 4, healthy/hurt', 'step into the attacker\'s bush (healthy) / step away from bushes (hurt)', '`best` tile', 'none', 'pos, walked',
      ('before', '    if (best == pos) return false;\n    try {\n        if (me.move_absolute(best)) {\n            pos = best;', 'move head context "ambush"'))
entry('drop_ward', 'ward', 'bot.cpp', 'Bot::drop_ward', 'void Bot::drop_ward() {', 'ward', 'mode capture/tribute/siege', 'tile within 1', 'first legal tile', 'none', 'ward_pos',
      ('after', '    if (!tune::kWards) return;', 'n/a'), status='inactive: APEX_WARDS 0 (constexpr false; returns immediately)')

# ------------------------------------------------------------------------------------------------ camps
entry('fight_camps', 'objective', 'bot.cpp', 'Bot::fight_camps (stage / siege / disengage / approach / attack)', 'bool Bot::fight_camps(GroupRec& g, int need) {', 'move',
      'need vs present allies, incoming camp damage, siege dps, hp vs incoming x 3, camp hp/strength (target key hp - 1000 x strength)',
      'stage (wait for helpers, timeout kStageTimeout) / siege ring / disengage tile / approach ring / attack target', 'branch + `t` camp index',
      'walk_toward floors', 'staging_since, call_ban_until, approach_* (A2_APPROACHFIX), avoid_until, heading_home',
      ('before', '    int t = pick_target();\n    mode = "fight";', 'move head context "camp" for stage/approach/disengage tiles; camp target choice stays deterministic (pick_target)'),
      notes='Camp target (pick_target: dangerous first, then weakest; Varg splash) is low-level PvE micro: keep deterministic.')
entry('cast_on_camp', 'combat', 'bot.cpp', 'Bot::cast_on_camp', 'bool Bot::cast_on_camp(int ci) {', KEEP,
      'ready spells in range, value (damage / aoe hits)', 'best slot', '`best`', 'none', 'cast_done', ('before', '    if (best < 0) return false;\n    try {\n        const auto ab = bc::self().abilities()[best];\n        const bool ok = spells[best].kind == bc::ability_kind::aoe_damage ? ab.use(c.pos) : ab.use(c.camp);',
                                                                                                   'n/a'),
      notes='PvE damage maximisation; a combat-head context could be added later (heads.json combat targets champions).')
entry('break_out', 'move', 'bot.cpp', 'Bot::break_out (NOVA_UNBOX)', 'bool Bot::break_out() {', KEEP, 'boxed by units, camps in reach', 'cheapest camp to clear', 'attack', 'none', 'none',
      ('after', 'bool Bot::break_out() {', 'n/a'), notes='Unstick fallback.')

# ------------------------------------------------------------------------------------------------ draft / world / misc
entry('ml_draft', 'draft', 'draft.cpp', 'ml_draft_pick (A2_MLDRAFT 1: every map)', 'bool ml_draft_pick(std::uint32_t size) {', 'draft_pick',
      '16 map features (cached first turn), our picks, their picks, team size, picking first, progress', '12 champion_draft values not taken by either team',
      '`best` (argmax z of draft_net, first maximum)', 'none (fast_tanh to stay inside 100k later draft turns)', 'static feat/h_map (first turn)',
      ('before', '    bc::draft::pick(static_cast<cd>(best));\n#if A2_MLPLAN', 'draft_pick head: substitute `best` with a legal free champion; candidate 0 = best'),
      decision_pat='        if (z > best_z) best_z = z, best = c;', capture='cap_draft_begin/score/pick')
entry('lineup_draft', 'draft', 'draft.cpp', 'play_draft lineup tables / pick_from (fallback when the net fails)', 'void play_draft() {', 'draft_pick',
      'map id (nova_map_id), lineup tables, mobility (A44_MOBILITY_DRAFT gap crossings), class draft', 'first untaken champion of the chosen list',
      'pick in pick_from', 'none', 'none', ('before', '        bc::draft::pick(pick);\n        return true;', 'draft_pick head secondary hook (rarely reached: the net picks on every map)'),
      decision_pat='bool pick_from(const cd (&list)[N], const std::vector<cd>& chosen, bool skip_casters = false) {')
entry('draft_memory', 'draft', 'strategy.h', 'brain::record_draft (draft memory header)', 'inline void record_draft(unsigned team_size, int max_group = 0, unsigned flags = 0) {', KEEP,
      'team size, enemy casters, map class, biggest group gems, flags', 'n/a', '6-byte header {magic, team, casters, class, max_group, flags}', 'none',
      'draft memory (frozen after the draft)', ('after', '        bc::draft_memory = mem;', 'n/a'), notes='Protocol (INVARIANTS I5).')
entry('world_update', 'belief', 'world.cpp', 'World::update / observe_* / sightings', 'void World::update(int round) {', KEEP,
      'vision, camps, champions', 'n/a', 'EnemyRec/AllyRec lists, group states, sightings, hot_zone', 'update_beliefs fuel floor (APEX_BELIEF 0: off)',
      'World (persistent memory)', ('after', 'void World::update(int round) {', 'belief head reads World (C glue); never writes it'),
      notes='Deterministic memory; the belief head is a value head over it.')
entry('build_fields', 'budget', 'bot.cpp', 'Bot::build_fields', 'void Bot::build_fields() {', KEEP,
      'fuel, field quota (kDetFields x context)', 'which fields to precompute', 'n/a', 'room(): fuel > full search + kDetSafety', 'World fields',
      ('after', 'void Bot::build_fields() {', 'n/a'), notes='Budgeted precompute; routed through teacher_left (patch 01).')
entry('episode', 'value', 'episode.cpp', 'Bot::episode_tick', 'void Bot::episode_tick(bool dead_now) {', KEEP, '-', '-', '-', '-', 'ep', ('after', '    if (!APEX_EPISODES) return;', 'n/a'),
      status='inactive: APEX_EPISODES 0 (returns immediately)')
entry('tactical_search', 'engage', 'tsearch.cpp', 'Bot::tactical_search / ts_prewarm (APEX_TSEARCH)', 'bool Bot::tactical_search() {', 'engage', '-', '-', '-', '-', '-',
      ('after', 'bool Bot::tactical_search() {', 'n/a'), status='inactive: APEX_TSEARCH 0 (constexpr false at both call sites)')
entry('melee_caught', 'move', 'bot.cpp', 'Bot::melee_caught (APEX_STAND2)', 'bool Bot::melee_caught() {', 'move', '-', '-', '-', '-', '-', ('after', 'bool Bot::melee_caught() {', 'n/a'),
      status='inactive: APEX_STAND2 0')
entry('fight_sim', 'engage', 'bot.cpp', 'simulate_fight (APEX_FIGHT_SIM)', 'bool Bot::handle_enemies() {', 'engage', '-', '-', '-', 'fuel > 30000', '-',
      ('after', '    if (tune::kFightSim && target && nearest_d <= 7 && bc::fuel_remaining() > 30000) {', 'n/a'),
      decision_pat='    if (tune::kFightSim && target && nearest_d <= 7 && bc::fuel_remaining() > 30000) {', status='inactive: APEX_FIGHT_SIM 0')
entry('rush', 'strategy', 'bot.cpp', 'Bot::rush (NOVA_RUSH_UNTIL)', 'bool Bot::rush() {', 'strategy', '-', '-', '-', '-', '-', ('after', 'bool Bot::rush() {', 'n/a'),
      status='inactive: NOVA_RUSH_UNTIL 0')


def build() -> list[dict]:
    out = []
    for e in E:
        f = e['file']
        fn_line = find(f, e['fn_pat'])
        dec_line = find(f, e['decision_pat'], fn_line - 1) if e['decision_pat'] else fn_line
        where, pat, how = e['hook']
        first = pat.split('\n')[0]
        hook_file = f if any(first in s for s in FILES[f]) else 'bot.cpp'  # hooks that live in the caller (bot.cpp)
        hook_line = find(hook_file, first, fn_line - 1 if hook_file == f else 0)
        out.append({
            'id': e['id'], 'area': e['area'], 'function': e['fn'], 'file': f'bot/src/{f}', 'line': fn_line,
            'decision_line': dec_line,
            'head': e['head'], 'head_id': HEADS.get(e['head']),
            'status': e['status'],
            'teacher_inputs': e['inputs'], 'candidates_in_code': e['candidates'], 'teacher_choice_variable': e['choice'],
            'fuel_gating': e['fuel'], 'persistent_state_touched': e['state'],
            'hook': {'position': where, 'statement': pat, 'file': f'bot/src/{hook_file}', 'line': hook_line, 'proposal': how},
            'capture': e['capture'] or ('member read (nn_teacher_access)' if e['head'] != KEEP else None),
            'notes': e['notes'],
        })
    return out


def main() -> int:
    inv = build()
    doc = {'_doc': 'Decision inventory of the original bot (Agent A). Lines refer to git HEAD bot/src (== references/original-src for '
                   '.cpp/.h except bot.h friend lines). Generated by tools/audit_inventory.py from anchors; head ids from schemas/heads.json. '
                   '"hook" = where a head call goes so that the teacher choice is fully computed before it and an alternative of the same '
                   'type can be substituted; captures are in agents/A/patches/03_teacher_capture.diff.',
           'macro_config': 'common.h lines 1-96 (A2_LAB 1, A2_KNOBS, A2_MLDRAFT 1, A2_GOV 1, A2_TD_AUTH 1, APEX_DET 1, ...)',
           'entries': inv}
    (ROOT / 'agents/A/decision_inventory.json').write_text(json.dumps(doc, indent=1) + '\n', encoding='utf-8')
    rows = ['| id | function (file:line) | head | status | teacher choice | hook (line) |', '|---|---|---|---|---|---|']
    for e in inv:
        head = e['head'] if e['head_id'] is None else f"{e['head']} ({e['head_id']})"
        st = 'active' if e['status'] == 'active' else 'inactive'
        rows.append(f"| {e['id']} | {e['function']} ({e['file'].split('/')[-1]}:{e['line']}) | {head} | {st} | "
                    f"{e['teacher_choice_variable'][:70].replace('|', '/')} | {e['hook']['position']} {e['hook']['line']} |")
    (ROOT / 'agents/A/inventory_table.md').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    by_head = {}
    for e in inv:
        by_head.setdefault(e['head'], 0)
        by_head[e['head']] += 1
    print(len(inv), 'entries', by_head)
    missing = [h for h in HEADS if h not in by_head and h not in ('belief', 'value', 'ts_leaf')]
    print('heads without an entry:', missing)
    return 0


if __name__ == '__main__':
    sys.exit(main())
