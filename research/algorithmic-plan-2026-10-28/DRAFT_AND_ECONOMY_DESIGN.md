# Deterministic drafting and team economy planning: detailed design

Status: a design, not implemented. E-numbers refer to the evidence register in FINAL_DEEP_ANALYSIS.md. Module names
(M1–M10, flags `OCC_*`) match ALGORITHMIC_BOT_BLUEPRINT.md.

Contents:
- Part A: the economy
  - M1 TeamLedger
  - M2 ObjModel (time and reward model)
  - M3 Team Economy Planner (TEP), which replaces `score_groups` + `campnet_pick`
  - M9 the opening schedule
  - banking and shopping
- Part B: the deterministic draft (M7)

---

## Part A: Economy

### A.0 Design premises taken from the evidence

1. **Retention under contest is the target, not the uncontested rate.**
   - Our uncontested farming already matches strong teams' contested farming after R100 (E10, E24).
   - TEP must therefore be *non-inferior* uncontested and *better under contest*: contest-aware objective choice,
     crews that hold objectives, and less abandoned work.
2. **The opening is the one place where uncontested speed is behind** (E8, E22, E24): their R100 381 gold contested
   vs our 329 uncontested. An opening improvement must hand over to a planner that keeps its gains. The opening pack
   failed exactly there (E17).
3. **Every prediction TEP relies on is validated first** against replays (E17, cause 1): travel time, clear time,
   damage taken, capture time.
4. **Plans have a progress contract and are re-validated every turn** (E17, cause 2).
5. **No carry funnel** (E23, E17). Reward routing is free only when Vesper is already in the crew.

### A.1 M1 TeamLedger: what each champion believes about objectives

Per camp group `g` (≤112 groups per map; the claim code space caps it):

```
struct GroupBelief {
  uint8  state;          // ALIVE, PARTIAL(hp known), REWARD (all dead, uncaptured), RESPAWNING, UNKNOWN
  int16  respawn_round;  // when state == RESPAWNING (deterministic: capture round + max member respawn)
  int16  last_seen;      // round of last own observation
  float  hp_left;        // summed member HP if known, else full HP
  uint8  owner_hint;     // ALLY_CLAIM(slot), ENEMY_SEEN, NONE
  float  enemy_pressure; // expected enemies near g in the next 10 rounds (from EnemyBelief)
};
```

Update rules, in order each turn:
1. **Own vision is authoritative** for the camps it covers.
2. **Ally claims** (on-site codes, existing V54 protocol). An ally on-site with a REWARD group plus 5 rounds means
   the group is RESPAWNING with a known timer (v76 already infers this). Keep v76's `pending_events` beacon for camp
   events.
3. **Deterministic timers.** RESPAWNING → ALIVE at `respawn_round`. Any occupied tile delays the respawn, so mark it
   UNKNOWN when enemy presence was last seen there.
4. **Decay.** UNKNOWN after `now − last_seen > 2 × respawn_time` for states not explained by claims.

EnemyBelief, kept per enemy id (≤5):
- last seen position and round, hp
- bag (as seen)
- items (count of shards seen on its body, via SDK info when visible)
- alive / dead
- `dead_until` = death round + 60

Expected position after k unseen rounds:
- a uniform disc of radius k around the last position, clipped by walls
- for planning, use the "pressure" at a point p: `Σ_e P(e within r of p in τ rounds)`

The pressure is approximated cheaply as `min(1, (k_e + τ + r − d(e.last, p)) / (k_e + τ + 1))` for alive enemies, a
ramp in Chebyshev distance with no pathing. This replaces `w.expected_enemies`, or reuses it if that is cheaper.

Cost: O(G) per turn for timers plus O(visible camps) updates, about 1–2k fuel. Persistent: per-champion statics.

### A.2 M2 ObjModel: validated time and reward predictions

For a crew `C` (1–3 champions, rarely 4) and group `g` at round `t`:

```
T_arrive(c,g) = field_g(c.pos)                      // v76 distance field: walking steps; dash ignored (conservative)
T_ready(C,g)  = max( max_c T_arrive(c,g),  respawn_round(g) - t )
DPS_camp(c)   = strength_c * (1 + 0.10*monster_emblem_c) * atk_rate_c            // basic: 1/turn; ranged must stand
              + Σ_slots spell_dmg_c(slot) / 8                                      // focus x multiplier, 8-turn cooldown
              + reset_bonus_c * strength_c / 8                                     // attack-reset kits
              + splash_c(g)                                                        // Varg: +strength per extra adjacent camp
T_clear(C,g)  = Σ_members hp / Σ_c DPS_camp(c) * κ_overkill(g)                      // κ ≈ 1.05–1.15 for multi-camp groups
D_taken(C,g)  = Σ_members str_m * T_alive_m(C,g) * (1 - 0.30*jungle) * (1 - 0.10*durability)   // spread over C
T_capture     = 5                                       // one capturer; others leave at the last kill
R_gold(g,cap) = gold_g * (1 + 0.33*[cap is Vesper] + 0.20*[cap has Treasure])
Reward(C,g)   = gems_g + λ_gold * R_gold(g, cap*) + λ_kill * 0                       // kills handled by EE
Feasible      ⇔ D_taken ≤ Σ_c (hp_c − hp_floor_c)        // otherwise add a heal trip, or the crew is too small
```

**Champion-round cost.** `Cost(C,g) = Σ_c (T_arrive(c,g) + wait_c) + |C| · T_clear + T_capture + heal_cost`, where
`wait_c = T_ready − T_arrive(c)`.

**Rate.** `ρ(C,g) = P_ok(C,g) · Reward(C,g) / Cost(C,g)`, in gem-equivalents (GE) per champion-round.

**Contest factor.** `P_ok(C,g) = σ( α · (S_crew − β · S_enemy_near(g)) )`:
- `S_crew = Σ hp·dps` of the crew members, the same strength scale EE uses
- `S_enemy_near(g)` = enemy pressure × average visible enemy strength
- P_ok also enters EE (Part C of COMBAT_AND_COORDINATION_DESIGN.md) as the objective's survival value

**Parity with v76.** v76's value is `gems + gold_weight·gold` and its cost is
`participants·(approach + wait + kill) + capture + 4 + drain`. ObjModel has the same structure with three
corrections:
1. the crew is explicit, so the cost is per champion-round, not per assumed `need`
2. the respawn-arrival term
3. contest risk as a probability, not v76's ad-hoc divisor

The first build sets `λ_gold` to v76's effective gold weight on that map. That is the brain map class × A2 knob 8 ×
V71 row; logging the effective value is a Day-2 task. Behaviour therefore starts near parity.

**Validation gate (before any decision uses it).** Replay-validate T_arrive, T_clear, D_taken and T_capture against
uncontested v76 games (SA-IDLE-v76, 140 games, already on disk; extract with `tools/replay/camp_clear.mjs`):
- clear time: median absolute error ≤20% and bias ≤10%
- arrival time: error ≤3 rounds for distances ≤30
- damage-taken bias ≤20%

If the gate fails, fix the model before writing the planner (this is exactly what v82 skipped).

### A.3 M3 Team Economy Planner (TEP)

**Ownership.** Each champion runs TEP for itself, but solves the *team* problem from its own belief, then commits
only its own assignment through its 7-bit claim. Champions act in a fixed priority order, so later movers see
earlier movers' claims in the same round and solve the residual problem. This is a deterministic sequential auction
that needs no extra shared bits (E26), and it degrades gracefully: a stale or missing claim only means a duplicated
job, which v76 already tolerates.

**Algorithm (per replan):**

```
inputs: me, allies A (positions from own vision or last claim/beacon; unseen allies assumed on their claimed objective),
        ledger, model, claims
1. Fixed jobs: allies whose claim is fresh (≤ 3 rounds) and whose progress contract holds keep their job.
2. Candidate objectives O = top-M groups (M = 8) by single-champion rate ρ({c},g) for each free champion,
   plus BANK(me), SHOP(me), and RESPAWN-ARRIVAL variants for groups respawning within 25 rounds.
3. Greedy crew assembly with regret (k-best, k = 2):
     while free champions remain:
        for each candidate g, best crew C_g of size 1..3 drawn from the free champions nearest g
            (C extended only while ρ improves: Δρ_team = ρ(C+c,g)·|C+c| − ρ(C,g)·|C| − ρ_alt(c)·1 > 0)
        pick (g, C_g) with max  Σ ρ gain  −  regret term (second-best option of its members)
        mark members assigned; remove g
4. Follow-up lookahead: score each assignment as ρ(C,g) + γ · max_{g'} ρ({c}, g' | start at g, t + T_g)  (γ = 0.5)
   (keeps champions moving toward rich neighbourhoods; replaces "after the opening the greedy loop takes over")
5. Output my assignment (objective, crew-mates, role = CLEAR | CAPTURE | ESCORT | BANK | SHOP), write my claim.
```

**Capturer rule.** The crew member with the furthest next objective captures. Vesper captures *only if* already in
the crew and her next objective is no more than 3 rounds further than the default capturer's. The others leave at the
last kill. This gives finish-before-reset and single-capturer, both proven in v58 R3. It is not a funnel.

**Progress contract** (the fix for v82 on 02arena). Each assignment records its expected milestone: distance to the
objective decreasing by ≥1 per 2 rounds, or the group's HP decreasing, or the capture timer advancing.
- 6 rounds without progress → release, and set `avoid_until[g] = t + 15`.
- The same group failing twice → avoid for 40 rounds.

**Replan triggers.**
- Event: own objective completed or invalid, death, respawn, a new group state seen, enemy contact starting or
  ending, a crew-mate's claim changing.
- Periodic: every 8 rounds.
- Between replans the assignment stands unless EE overrides it (Part C of COMBAT_AND_COORDINATION_DESIGN.md).
- Hysteresis: switch only if the new ρ exceeds the current one by 15%.

**Complexity.**
- Single rates: O(F · G) with F ≤ 5 free champions and G ≤ 112. Each rate costs about 40–80 wasm ops with cached
  fields, so roughly 25–45k ops in the worst case.
- Crew assembly over M = 8 candidates: O(M · F²), negligible.
- Pruning: precompute single-champion rates only for groups within a distance cutoff (`field_g(c) ≤ 45`) or the top
  25 by static value; v76's score_groups already uses branch-and-bound by distance.
- Target: ≤8k fuel for an event replan, ≤3k for a non-replan turn (contract check plus cached plan).
- v76's score_groups costs about 32% of a 41k mean, roughly 13k (E2), so TEP must not exceed it on average.
- Fallback: if `fuel_remaining < reserve + 10k` when a replan is due, keep the current assignment, or call v76
  `score_groups` (still compiled in) if there is none.

**Contest-aware behaviour, the point of the module.**
- `P_ok` lowers objectives under enemy pressure *unless* the crew is strong enough. That turns some fights into
  "take a different camp" and others into "bring a crew and hold".
- EE receives `V_obj = Reward · progress_fraction` and `rounds_to_complete`, so a capture two rounds from finishing is
  worth defending (§C of COMBAT_AND_COORDINATION_DESIGN.md).
- Cohesion is emergent: crews and follow-up lookahead keep champions near each other. There is no separate cohesion
  knob, though v76's knob can stay as a tie-break.

**How TEP could beat campnet (and how it might not).**
- **Information campnet does not have:**
  - crew composition and team allocation (campnet ranks for one champion)
  - respawn-arrival timing
  - follow-up value
  - contest probability with crew strength
  - single-capturer economics
- **What campnet has that TEP lacks:** a 40-round commitment that the ablation suggests is mildly useful (E4),
  whether from the commitment itself or the learned residual. TEP's hysteresis and progress contract replace it.
- **Falsifiers:**
  - idle-gate non-inferiority fails (R250 collected gems below −2% of v76)
  - contested league retention does not improve (R500 collected vs idle, both opponents)
  If TEP only ties v76 + campnet uncontested and also ties contested, it has no case for replacing v76 farming.

### A.4 Banking (BANK objective)

Every N rounds, and whenever the bag changes, compare carrying with banking now:
- `E_loss_carry = bag · h(t) · T_horizon`, where h is the death hazard per round. Fit h offline from our own death
  rate under current enemy pressure; seed it at v76's measured 4.3 deaths per 500 rounds per team, about 0.002 per
  champion-round, scaled by pressure and HP.
- The bank trip costs `T_trip = field_altar(pos) + ceil(bag/10)` champion-rounds × ρ̄ (the champion's current
  farming rate).
- Bank when `E_loss_carry(T_trip) > T_trip · ρ̄ · η`, with η tuned (start at v76's `kTributeCarry` equivalence on a
  calibration set).
- Win-now override: v76's win-now tribute stays, with the deep-analysis guard. A recall that would carry a winning bag
  must not be cancelled while banking is disabled (`tribute_off_until`) (E18). This is the first bug fix, in both the
  A and B tracks.
- Altar selection: nearest by field among altars not under enemy pressure. The altar watch is v76's, where a stale-bag
  stall means another altar.
- Marcella's +2 gold per tributed gem enters as `λ_gold · 2 · bag` in the BANK value when Marcella banks.

### A.5 Shopping (SHOP objective and gear tempo)

- The SHOP objective appears when `gold ≥ next_item_cost` and one of the following holds:
  - the champion is dead (free shopping)
  - it is on spawn after a recall or bank trip
  - spawn is within `k_shop` rounds
  - the build plan's next item completes an emblem, whose passive is only granted on completion
- Build plan: keep v76's `build_for` per champion, then later evaluate role builds:
  - Monster or Jungle for clearers
  - Durability for frontliners
  - Treasure on Vesper only if Vesper captures more than 30% of team gold
- Metric: equipment cost at R100/250/500 (E11). Target +10% at R250 uncontested without income loss.

### A.6 M9 Opening schedule (optional; after TEP passes its gates)

At the last draft turn the full lineup, map and spawn regions are known. With up to 1M fuel on the first draft turn
and 100k on later ones, compute the R0–R120 schedule:
1. Simulate TEP's assignment rollout forward from the spawn with ObjModel, deterministically, for 120 rounds and no
   enemies.
2. Optimise by local search over the first two objectives per crew (swap and resize moves, ~200 rollouts).
3. Encode the first 3 assignments per champion: 7-bit group, 2-bit role, 8-bit start round, about 17 bits each,
   ≤ 32 bytes total in draft memory after the existing brain header.

At runtime the schedule is a **prior bonus** inside TEP (×1.3 on ρ), not a command. It is dropped on the first ledger
mismatch (group not ALIVE when expected, enemy pressure > 0.5, or a crew-mate missing). This is the DPLAN fix: the
plan is advisory, re-validated every turn, and hands over to the same planner that produced it.

Gate: uncontested R100 gold +10% and first elk-group capture ≤ R55, with R250 non-inferior. The opening pack passed
the first two and failed the third.

---

## Part B: Deterministic draft (M7, OCC_DRAFT)

### B.0 Facts that shape it

- **No exclusivity.** Both teams may pick the same champion and picks are revealed as they go. There are no denial
  picks, and counters only matter as best responses to revealed enemy picks.
- **The draft must fit our controller.** Top-team drafts lose on our controller (−89 meta draft; the proxy with top
  drafts earns less than v76, E13).
- **Per-map value is large but idiosyncratic.**
  - In-sample per-map oracle: +134 gems/game.
  - Feature-predicted out-of-sample: +17 [−13, +52] (E6).
  - Coarse map features (area, aspect, team size, density) do not predict *which* lineup wins on a map.
- **Per-map tables chosen against a league transfer to fresh seeds and to the ladder** (E21).

### B.1 Recommendation in one line

For the 70 pool maps, keep the V70 table plus the knob tables: proven and transferring. For unseen maps, keep the ML
draft until an algorithmic draft beats it in the leave-one-map-out (LOMO) test below.

The algorithmic draft is worth building **only if the finals may use unseen maps** (OPEN_QUESTIONS.md Q1), and it
must be judged by LOMO, not by local margin on the pool.

### B.2 Algorithmic draft: specification (option C)

**Champion model (static, from GameRules.md):** base stats and growth; kit flags (dash, stun, AoE, reset, heal,
shield, ranged); passives:
- Vesper gold ×1.33
- Marcella +2 gold per gem, stun-immune
- Prism focus per gem
- Ren retaliation
- Varg splash
- Heart missing-HP damage
- Vendetta reset on kill
- Tavi field shopping
- C&I: one pick, two bodies, one fate

**Map analysis.** On the first draft turn (1M fuel), using the SDK map calls already used by `read_facts` and
`ml_draft_pick`:
- totals and the camp-type mix (wolf/elk/golem/monolith/clusters)
- group sizes
- own-side vs contested value: Voronoi by spawn-region distance field
- gap crossings that unlock value, i.e. value reachable only by dash or teleport (A44 logic)
- altar count and spawn→altar distance
- map area and team size
- "centre-contest index": the share of gem value within 0.4 × map diameter of the midpoint between spawns

**Lineup utility for a set L, |L| = k:**

```
U(L | map, E) =  w1·ClearPower(L,map)      // Σ DPS_camp vs the map's camp HP mix, x mobility access factor
               + w2·Sustain(L,map)         // HP, shields, heals vs camp damage per clear; Jungle-able
               + w3·FightPower(L,E)        // Σ hp·dps + burst + stun count, vs revealed enemy picks E (stun-immune etc.)
               + w4·Mobility(L,map)        // dashes x gap-crossing value share
               + w5·EconBonus(L)           // Vesper gold, Marcella bank gold, scaled by OUR controller's measured use
               + Σ_pairs synergy(i,j)      // C&I fate penalty with weak frontline, Willow heal x frontliners, stun chains
               − RoleViolations(L)          // must have ≥1 frontline (hp ≥ 1000), ≥1 burst/stun, a dash if gaps exist
```

**Optimisation.**
- Exhaustive over all completions of our partial pick: C(12, k) ≤ 792 lineups for k = 5, and the C&I pick counts as
  one choice. About 300 ops each, so ≤250k ops, under the first-turn 1M budget. Later turns rescore only completions
  of the current partial pick (≤126).
- At each pick, choose the champion maximising `max_{completion} U`.
- Before the enemy's picks are visible, use an expected-enemy prior: the empirical top-team pick frequencies
  (current top-12 drafts in `research/v70/pool_plan_teams.json`).
- Tie-break with the current preset order for stability.

**Fitting the weights `w` and the synergy table:**
1. Data: the v70 league (6 lineups × 4 opponents × 70 maps, E6, already on disk) plus the ML draft's training corpus.
2. Fit by pairwise ranking on per-map lineup gains: for each map, U should order the lineups by realised gain.
3. Accept only on the LOMO criterion. Out-of-sample mean gain on held-out maps must exceed the ML-draft fallback's,
   measured on those maps with a fresh league run (VALIDATION_PLAN.md V-D1).

**Expected strength.** Low to moderate (E6). Coarse features failed to predict lineup gains. B.2 adds controller-
specific utilities (clear power vs the actual camp mix, gap access, fight power vs revealed picks), but there is no
evidence yet that they capture the per-map effects. Priority: optional, and only for unseen finals maps.

**Fallback.** On any exception or fuel shortage the existing chain runs: V70 table, then ML draft, then the
map-class lineup, then the preset.

### B.3 Draft memory budget (1024 bytes)

| Bytes | Content |
|---|---|
| 0–7 | Existing brain header: size, max gems, flags (keep) |
| 8–39 | Opening schedule (M9), ≤ 32 bytes |
| 40–71 | Map analysis summary for runtime: contested index, gap flags, altar ranks |
| 72+ | Free |

---

## Computational summary (detail in COMPUTATIONAL_DESIGN.md)

| Module | Typical turn | Worst turn | Notes |
|---|---|---|---|
| Ledger + EnemyBelief | 1–2k | 4k | O(G) timers, O(visible) updates |
| ObjModel (inside TEP) | — | — | 40–80 ops per (c, g) with cached fields |
| TEP replan | 3–8k | 15k (skipped below reserve) | every 8 rounds plus events |
| TEP contract check | <1k | 1k | every turn |
| Opening schedule | 0 at runtime | ≤600k on draft turn 1 | draft has 1M on the first turn |
| Draft C | ≤250k on draft turn 1 | ≤50k on later picks | |
