#pragma once
// x3inv: ladder-like sparring partner, not a candidate (pc/msgs/0045). Reproduces our ladder losses: invades our half
// (no home-side discount, full aggression) with the top teams' Treasure + Bruiser item plan, on the per-map fit.
#define HOME_TERR 1.0f
#define HOME_AGGR 1.0f
#define V58_ITEM_PLAN 0
// x1 experiment flags (default 0 = v81hl's behaviour; tools/dz.py --candidate-bot x1 --set X1_FLAG=1).
#ifndef X1_MASTERY
#define X1_MASTERY 0 // Draft: penalise champions x1 plays worst (draft-net score bias).
#endif
#ifndef X1_FUEL_PROBE
#define X1_FUEL_PROBE 0 // Diagnostics: 1 = no gated-altar/sole-group behaviours (A2_GATE_FROM/A2_SOLE_FROM off); 2 = no DP plan.
#endif
#if X1_FUEL_PROBE == 1
#define A2_GATE_FROM 100000
#define A2_SOLE_FROM 100000
#elif X1_FUEL_PROBE == 2
#define A2_DP_UNTIL 0
#endif
#ifndef X1_TEL
#define X1_TEL 0 // Diagnostics: v81hl's A2_TEL telemetry (A2SUS fuel-suspension trails) on.
#endif
#if X1_TEL
#define A2_TEL 1
#endif
#ifndef X1_BUSHPRE
#define X1_BUSHPRE 0 // Fuel: label bush clusters ahead of use from each turn's leftover fuel, down to X1_BUSHPRE k fuel (resumable; same labels).
#endif
#ifndef X1_BUSHPRE_LAZY
#define X1_BUSHPRE_LAZY 50 // with X1_BUSHPRE: on-demand labelling stops at this many k fuel (cluster reads unknown until done)
#endif
#ifndef X1_SIEGEFUEL
#define X1_SIEGEFUEL 0 // Fuel: fill the siege line-of-sight cache only above X1_SIEGEFUEL k fuel (was 30k), direct bit writes.
#endif
#ifndef X1_WALKRES
#define X1_WALKRES 0 // Fuel: walk_toward's capped path searches keep X1_WALKRES k fuel for the rest of the turn (was 6k; 19 of 29 plan-4 fuel-outs crossed right after a walk).
#endif
#define X1_WALK_RESERVE (X1_WALKRES ? static_cast<std::uint64_t>(X1_WALKRES) * 1000 : rb::kTailReserve)
#ifndef X1_WALKTAIL
#define X1_WALKTAIL 0 // Fuel: after an approach walk, skip the camp re-pick and attack when under X1_WALKTAIL k fuel (15 of 24 plan-4 fuel-outs crossed there).
#endif
#ifndef X1_EARLYFLEE
#define X1_EARLYFLEE 0 // Fights: with no healthy ally within 5, leave once enemies within X1_EARLYFLEE tiles have more total
#endif                 // health than X1_EARLYFLEE_RATIO x ours (ladder: 03one-gem deaths are lone champions caught while fleeing late).
#ifndef X1_EARLYFLEE_RATIO
#define X1_EARLYFLEE_RATIO 1.0f
#endif
#if X1_EARLYFLEE
#define X1_EARLYFLEE_HOOK                                                                                                  {                                                                                                                          bool x1_alone = true;                                                                                                  for (const auto& a : w.allies) x1_alone &= !(cheb(a.pos, pos) <= 5 && a.hp >= a.max_hp * 0.4f);                        float x1_ehp = 0.0f;                                                                                                   for (const auto& e : w.enemies)                                                                                            if (e.hp > 0 && cheb(e.pos, pos) <= X1_EARLYFLEE) x1_ehp += e.hp;                                                  if (x1_alone && !(target && target_ttk <= 1.0f) && x1_ehp > hp * X1_EARLYFLEE_RATIO) {                                     in_danger = true;                                                                                                      winning = false;                                                                                                       if (threat_on_me <= 0) threat_on_me = 1.0f;                                                                        }                                                                                                                  }
#else
#define X1_EARLYFLEE_HOOK
#endif
#ifndef X1_LEASH
#define X1_LEASH 0 // Feeding: for X1_LEASH rounds after this champion respawns it farms only its own half (territory 0) with
#endif             // aggression x X1_LEASH_AGGR (ladder: lone champions walk back into the half where they were killed).
#ifndef X1_LEASH_AGGR
#define X1_LEASH_AGGR 0.7f
#endif
#if X1_LEASH
#define X1_LEASH_HOOK \
    { \
        static int x1_last_turn = -1, x1_respawn = -100000; \
        if ((x1_last_turn >= 0 && round - x1_last_turn > 3) || bc::self().state().is_dead()) x1_respawn = round; \
        x1_last_turn = round; \
        if (round - x1_respawn < X1_LEASH) tune::kTerritory = 0.0f, tune::kAggression *= X1_LEASH_AGGR; \
    }
#else
#define X1_LEASH_HOOK
#endif
#ifndef X1_FIRSTFIELD
#define X1_FIRSTFIELD 0 // Fuel: first turn builds a group field only with 2x its cost + 15k left (03contours: all 6 bodies ran out on turn 1)
#endif
#ifndef X1_MAPFIT
#define X1_MAPFIT 1 // per-map knob fit table (x1_mapfit.h) for maps without a ladder table
#endif
#ifndef X1_KD_ON
#define X1_KD_ON 0 // 1 = apply the X1_KD knob deltas (search builds)
#endif
#ifndef X1_KD
#define X1_KD 0 // "index,delta,index,delta,..." (tools/x3_knob_es.py)
#endif
#ifndef X1_KD_SCOPE
#define X1_KD_SCOPE 0 // X1_KD knob deltas: 0 all maps, 1 maps without a ladder table, 2 ladder-table maps only
#endif
#ifndef X1_CORNERED
#define X1_CORNERED 0 // Fights: after this many turns fleeing while losing health with the chaser within 2, fight back (0 = off)
#endif
#ifndef X1_FAST_SIEGE
#define X1_FAST_SIEGE 1 // Fuel: cache the siege line-of-sight ring per alive-camp set (same decisions, no per-turn scan).
#endif
#ifndef A2_CAMPWATCH
#define A2_CAMPWATCH 1 // x1 base (2026-11-01): v81hl's switched-off camp watch, +7 wins vs v81hl, 338/560 league wins with fast siege.
#endif
#ifndef X1_ALONE
#define X1_ALONE 0 // Isolation: no ally within 5 and an enemy within 10 -> walk to the nearest ally (teammate's untested alone alert).
#endif
#ifndef X1_SECURE
#define X1_SECURE 0 // MAPF kill-securing coordinator: a target killable this round by allies in reach is worth X1_SECURE_MULT x more.
#endif
#ifndef X1_SECURE_MULT
#define X1_SECURE_MULT 3.0f
#endif
#ifndef X1_HUNT_SOLO
#define X1_HUNT_SOLO 0 // Lone hunters: with no ally within 5, hunt only enemies sighted within this many tiles (0 = off).
#endif
#ifndef X1_PLAN
#define X1_PLAN 0 // Team-plan hook (1 = compiled in; X1_PLAN_ROUND / X1_PLAN_ID pick the plan). 0 = x1 exactly.
#endif
#ifndef X1_PLAN_ROUND
#define X1_PLAN_ROUND -1 // round from which plan X1_PLAN_ID is played (-1 = never)
#endif
#ifndef X1_MAPPLAN
#define X1_MAPPLAN 0 // with X1_PLAN: per-map plan table (x1_mapplan.h) on maps without a ladder fit
#endif
#ifndef X1_PLAN_END
#define X1_PLAN_END 0 // with X1_PLAN: plan X1_PLAN_ID stops at this round and normal play resumes (0 = never; ladder: plan 4 stalled the late economy)
#endif
#ifndef X1_PLAN_ID
#define X1_PLAN_ID 0 // 1 full map, 2 hoard, 3 fight harder, 4 turtle, 5 stricter home, 6 early-contact answer, 7 fast bank, 8 push
#endif
#ifndef X1_ANTIFEED
#define X1_ANTIFEED 0 // Anti-feeding: this many team deaths within X1_ANTIFEED_WIN rounds -> the team plays safe (0 = off).
#endif
#ifndef X1_ANTIFEED_WIN
#define X1_ANTIFEED_WIN 150
#endif
#ifndef X1_HEARTFIX
#define X1_HEARTFIX 0 // audit B01: fight forecast with Heart of Ruin dash landing damage/stun and missing-health damage (A2_KITFIX 25 -> 31).
#endif
#ifndef X1_SOAK64
#define X1_SOAK64 0 // audit B02: camp danger counts up to 64 members per group (12 = v81hl).
#endif
#define X1_SOAK_N (X1_SOAK64 ? 64 : 12)
#ifndef X1_PRUNEFIX
#define X1_PRUNEFIX 0 // audit B03: candidate prune bound includes the later campwatch and dominant-group multipliers.
#endif
#ifndef X1_FLEEHOLD
#define X1_FLEEHOLD 0 // audit F01: rounds after a flee during which a champion keeps away from enemies seen within 8 (0 = off).
#endif
#ifndef X1_TEAMWIN
#define X1_TEAMWIN 0 // audit F03: the win-now bank counts the whole team's carried gems.
#endif
#ifndef X1_SIEGE_STRICT
#define X1_SIEGE_STRICT 0 // audit B04: use the siege LOS cache only when every live camp is cached (else the unfiltered ring).
#endif
#ifndef X1_BAGRISK
#define X1_BAGRISK 0 // Bag risk: carrying this many gems with an enemy seen within 10 in 5 rounds -> bank now (0 = off).
#endif
#ifndef X1_FLEEDROP
#define X1_FLEEDROP 0 // audit F01 alt: drop the camp target on a flee and skip it for this many rounds (0 = off).
#endif
#ifndef X1_ECON
#define X1_ECON 0 // Economy multipliers below (1 = compiled in).
#endif
#ifndef X1_WAIT_MULT
#define X1_WAIT_MULT 1.0f // x respawn-wait cost (more = leave for another camp sooner)
#endif
#ifndef X1_STAGE_MULT
#define X1_STAGE_MULT 1.0f // x helper staging timeout
#endif
#ifndef X1_NEED_MULT
#define X1_NEED_MULT 1.0f // x solo camp health budget (more = take more camps alone)
#endif
#ifndef X1_G3_STYLE
#define X1_G3_STYLE 0
#endif
#ifndef X1_G3_STYLE_FOCUS
#define X1_G3_STYLE_FOCUS 0.32f
#endif
#ifndef X1_G3_STYLE_EQ
#define X1_G3_STYLE_EQ 0.26f
#endif
#ifndef X1_G3_STYLE_NUMBERS
#define X1_G3_STYLE_NUMBERS 1
#endif
#ifndef X1_G3_STYLE_PWIN
#define X1_G3_STYLE_PWIN A2_LC_HI
#endif
#ifndef X1_G3_SECURE
#define X1_G3_SECURE 0
#endif
#ifndef X1_G3_SECURE_TURNS
#define X1_G3_SECURE_TURNS 2.0f
#endif
// ---- Banking B1-B3 (research/x3/banking/BANKING_RESEARCH.md) ----
#ifndef X1_SAFEROUTE
#define X1_SAFEROUTE 0 // B1: 1 = path-aware enemy reach in layers replaces the square mask; 2 = mask first, layers only as its fallback
#endif
#ifndef X1_SR_BAG
#define X1_SR_BAG 15 // bag from which the carrier routes around enemies
#endif
#ifndef X1_SR_AGE
#define X1_SR_AGE 12 // enemy sightings younger than this many rounds count
#endif
#ifndef X1_SR_R
#define X1_SR_R 5 // first layer: tiles enemies reach within this many steps are avoided
#endif
#ifndef X1_SR_STEP
#define X1_SR_STEP 3 // each further layer avoids this many steps less (5, 2)
#endif
#ifndef X1_SR_FUEL
#define X1_SR_FUEL 35000 // skip the safe-route searches below this much fuel left (old square mask instead: none)
#endif
#ifndef X1_SR_DETOUR
#define X1_SR_DETOUR 8 // a safe route may be this many steps (or half the plain distance) longer
#endif
#ifndef X1_SR_HOLD
#define X1_SR_HOLD 0 // 1: with 2x X1_SR_BAG and enemies within reach, never walk the plain path through them
#endif
#ifndef X1_BAGRISK2
#define X1_BAGRISK2 0 // B2 (needs X1_SAFEROUTE): bank when enemies can reach us and gems >= X1_BR2_RATE x trip
#endif
#ifndef X1_BR2_MIN
#define X1_BR2_MIN 20
#endif
#ifndef X1_BR2_RATE
#define X1_BR2_RATE 1.0f
#endif
#ifndef X1_BR2_DIST
#define X1_BR2_DIST 30
#endif
#ifndef X1_RACEBANK
#define X1_RACEBANK 0 // B3: once either score reaches X1_RB_SCORE, any bag of X1_RB_BAG+ banks at any distance
#endif
#ifndef X1_RB_BAG
#define X1_RB_BAG 5
#endif
#ifndef X1_RB_SCORE
#define X1_RB_SCORE 800
#endif
#ifndef X1_RB_DIST
#define X1_RB_DIST 60
#endif
#ifndef X1_NOOP
#define X1_NOOP 0 // measurement only: behaviour-free code change (fuel-chaos baseline)
#endif
#ifndef X1_COUNTER
#define X1_COUNTER 0 // per map and side, the variant that beat the opponent there (x1_counter.h, tools/x3_counter.py); implies X1_PLAN
#endif
#ifndef X1_COUNTER_FORCE
#define X1_COUNTER_FORCE -1 // search builds: play variant k on every map (-1 = use the table)
#endif
#if X1_COUNTER
#undef X1_PLAN
#define X1_PLAN 1
#include "x1_counter.h"
#endif
#if X1_MAPPLAN
#include "x1_mapplan.h"
#endif
#if X1_MAPFIT
#include "x1_mapfit.h"
#endif
