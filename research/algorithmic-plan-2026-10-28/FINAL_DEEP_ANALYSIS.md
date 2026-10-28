# Final deep analysis: DOOMSDAY v76 architecture, combat, economy and coordination

Date: 2026-10-28. Research and planning only: no bot source was changed, no build or match was launched for this
document, nothing was submitted or activated. Every number below is either a saved measurement (path given) or is
marked as a hypothesis.

Sources:
- the paused strategic audit: `research/strategic-audit-2026-10-28/`
  - `HANDOFF.md`
  - `scripts/`
  - `data/`
  - runs `artifacts/evaluations/v67/SA-*`, all seed 71 and played before this session
- the deep-analysis branch `origin/analysis/deep-2026-10-28` @ 19da05a, read-only worktree `work/deep-analysis-wt`
  - examined set only; the 165 hands-off games were not opened
- the checkpoint branch `checkpoint/research-v85-2026-10-28` @ 8a62987, which is this checkout
  - `research/v81/RESEARCH.md` (v81–v85)
  - `research/v75/*`, `research/v58/*`, `research/v70/*`, `research/v71/*`
- frozen source `bots/v76/src`
- `game rules/GameRules.md`

## 0. Evidence register (cited as E-numbers in every plan document)

| ID | Fact (measured unless marked) | Source |
|---|---|---|
| E1 | v76 fuel per turn (engine trace): mean 40–44k of 100k, p50 ≈41k, p90 ≈67k, p99 ≈82k. Fuel-outs 0.49/game against the proxy. | `SA-P-base`, `scripts/fuel.py` |
| E2 | Instrumented profile (alters behaviour: 26.7 fuel-outs/game, so shares only). farm 45%, of which score_groups 32%; world update 27%, of which hot zones 17%; handle_enemies 7%; tactical_decide 3%; campnet 1.3% (567 fuel/turn). | `SA-C-prof` |
| E3 | Campnet evaluates on 2.6% of turns and overrides the base pick in 24% of evaluations. An override holds for ≤40 rounds. | `SA-C-prof` counters |
| E4 | Matched ablations, 140 paired games, seed 71, one table below (§3.1). | `paired_strict.py` |
| E5 | Draft-net ablation restricted to games whose lineup actually changed. Proxy (n78, 39 maps): −116 [−258, +25], −3.8 pp. v65 (n76): −112 [−298, +79], −10.5 pp. Games with an identical lineup: +11 / −25, which is the pick-order noise floor. | this session, §3.2 |
| E6 | Leave-one-map-out drafting on the saved v70 league (6 lineups × 4 opponents × 70 maps). Per-map oracle +134 [+86, +184], in-sample. Feature kNN +17 [−13, +52]. Best global lineup +9. Per-team-size −9. | `scripts/lomo_draft.py`, `data/lomo_draft.json` |
| E7 | Local contested games are near-chaotic: removing campnet flips the winner in 66/140 games, and the paired margin SD is 620–830 gems. Uncontested (idle opponent) metrics have paired SD 20–180, about 10x sharper. | audit |
| E8 | Exact native ladder income in the 90 ladder losses analysed in research/v81, us vs them: R100 283 vs 381 gold, R300 996 vs 1,407, R500 1,763 vs 2,767. | `research/v81/RESEARCH.md` |
| E9 | 191 ladder losses (platform 69 = v75, examined set). Mean deficit −579 gems: −448.7 income, −103.0 bag loss, −27.5 carried. Banked/collected conversion 63.1% vs 88.4%. Repeated deaths (D3) in 129/191 losses vs 74/169 wins; per-death rate 30.9% vs 18.3%. | deep `FAST_FINDINGS.md` |
| E10 | Same-map contested vs our uncontested level, R500. In losses the opponents reach 96% (capture gold) / 93% (gems) of our idle level; we retain 66% / 62%. In wins we retain 68% / 80% and they get 46% / 47%. | `scripts/headroom.py`, `data/headroom_v76.json` |
| E11 | Ladder losses at R500, us/them. Champion-rounds dead 274/127. Travel 1342/1126. Equipment cost 1463/2334. Kill gold 161/393. Wards 30/77. At R250: dead 120/56, equipment 603/880, capture gold 671/881. | this session from `TIMELINE_DATA.json` |
| E12 | Ladder wins mirror E11 at R500: dead 194/456, kill gold 605/254, equipment 2144/1278. | same |
| E13 | Local contested economy, v76 vs opponent at R500. Against the proxy: collected 369/261, gold 2085/1578, conversion 0.72/0.61, deaths 4.3/5.7. Against v65: 337/298, 1958/1658, 0.69/0.67, 4.6/6.0. In local losses we still collect about as much but lose the gold and die more (proxy losses: gold 1368/1863, deaths 6.6/5.0). | `data/contest_proxy_base.json`, `contest_v65_base.json` |
| E14 | Ladder top-12 fights (v74 duels). In contact we step away without hitting in 28% of rounds (top teams 8%). 2.6 vs 1.7 reversals per episode. Even fights cost 0.76 vs 0.36 deaths. Focus fire and numbers do not differ. From R300 their champions out-stat ours. | `research/v75/TEAMFIGHT.md` |
| E15 | v67 ladder losses: deaths 14.5 vs 5.3 per loss; dive deaths 5.1 vs 1.7. Locally the `winning` formula overrides danger in 26% of deaths, and 77% of local deaths end in a flee. | `research/v75/LOSSES.md` |
| E16 | Ladder duels vs the top 12, 120 games each: v67 17/120 (−444), v74 30/120 (−302; +142±54 vs v67), v75 21/120. Local league-selected per-map work transferred; fight-caution changes did not. | `research/v75/DUELS.md` |
| E17 | Failed redesigns: v58 director (20 screens, none positive), A2_DPLAN −217, gold funnel −141, meta draft −89, opening pack −52, v79 team fight −24..−107, v81 action sequences −532 (12 games), v82 coalition scheduler −89/−95/−115 gold at R100/200/300 uncontested, v83 intent −65 vs proxy, v84 denial −886 (2 games), v85 rendezvous −231 (10 games), mimic 0/120, GPT controllers 0–32/240. | §5 |
| E18 | Deep-analysis puppet harness: 12/12 ladder games (10 losses, 2 wins) reproduced byte-exactly from frozen v75 source against enemy action puppets. It found a recall-restart loop: a winning-bag recall is cancelled and restarted every turn while banking is disabled (C004). | deep `REPRO_RESULTS.json`, `M1_SPEC.json`, `TAKEOVER_PLAN.json` |
| E19 | Several top teams run a "perma-recall" pattern: start a recall at turn end, cancel it next turn. | `research/proxy/README.md` |
| E20 | The proxy is v65 code plus top teams' exact drafts, item milestones and perma-recall. v65 beats it by +250. It predicts the ladder no better than self-play. | memory, `research/proxy/` |
| E21 | Per-map draft and knob tables chosen against a 4-opponent league validate on fresh seeds (+15..+169) and transferred to the ladder (E16). | `research/v70/V70.md`, `research/v71/V71.md` |
| E22 | Claudus-era opening (v57): their first elk-size group starts R21 with 3.7 champions and is captured R50; ours R36 with 2.7, captured R80. Their Vesper earns 466 capture gold by R250, ours 186. | `research/v58/V58_CLAUDUS_FINDINGS.md` |
| E23 | Carry prototypes (audit): Vesper share of gold 0.20 → 0.26–0.32, team gold flat or down (−15..−44), contested −32..+7 (not significant). | audit `HANDOFF.md` |
| E24 | v76 uncontested (vs bots/idle81). R100: 70 gems, 329 gold. R250: 211 gems, 1031 gold. R500: 489 gems, 2312 gold. Median reach-1000 at R892; 4 games never reach it. | `data/idle_v76.json` |
| E25 | Combat authority trace of v76 `handle_enemies` (§2). | this session |
| E26 | The 8-byte shared word is fully used: 6×7-bit claims (42 bits) plus a 22-bit sighting/camp-event beacon (bit 63 multiplexes). | `bot.h:23-32`, `bot.cpp:610-640, 7190-7208` |
| E27 | APEX_TSEARCH=1: 16 fuel-outs/game, +4.5..+5.5 deaths/game, −366 / −325 gems. | E4 |
| E28 | Early divergence in ladder games, us minus them at R100. Losses (n191): capture gold −62, dead champion-rounds +22.5, kill gold −25. Wins (n169): +84, −38, +62. R100 classes in losses: 69 (36%) behind in gold with no extra dead time, 41 behind with extra dead time, 23 not behind but extra dead time, 58 neither. In wins the classes are 34 (20%) / 10 / 22 / 103. Both economy and fights diverge by R100, and neither alone explains the losses. | `strategic-audit-2026-10-28/scripts/early_divergence.py`, `data/early_divergence.txt` |

## 1. What v76 actually is

v76 is about 16.5k lines; `bot.cpp` alone is 7.4k. Each champion runs its own instance of a per-turn priority
cascade in `Bot::play_turn` (`bot.cpp` ≈6582+):

1. **Knob mutation, every turn.**
   - `brain::adapt` sets the map class and current-score aggression, ttd, tribute carry, hunt and shop settings
     (`strategy.h:470-498`).
   - V71 per-map knob rows overwrite lab knobs, keyed on the exact (w, h, groups, gems) map identity (`bot.cpp` ≈6790).
   - A2_LAB applies 48 knobs on top (`bot.cpp:6822-6858`).
2. Channel guard, ward reveal, counter-ambush.
3. `handle_enemies()` whenever an enemy is visible (§2).
4. Win-now tribute, `go_home_if_needed`.
5. Join-fight, rush and fog-regroup layers.
6. `hunt`.
7. `tribute_if_needed`.
8. `farm()`:
   - `score_groups`: per-champion value / cost.
   - `campnet_pick`: an 18-feature MLP that re-ranks the top-K candidates.
   - route / capture / `fight_camps`.
9. Opportunistic attack, ward, altar pre-lock.

The value is gems + gold_weight × gold, with gold_weight ≈0.18 scaled by knobs. The cost is participants ×
(approach + wait + kill) + capture + 4 + drain, followed by belief and contest discounts (`bot.cpp` ≈5634–5800).

Coordination is a 7-bit claim per champion in shared memory, plus a multiplexed sighting beacon (E26). There is no
team-level plan object; every champion re-decides each turn from its own vision.

Learned and tuned layers active in v76:
- A2_CAMPNET (321-weight residual re-ranker)
- A2_MLDRAFT (53×64 MLP, only on maps outside the V70 table)
- V70 draft table (30 maps)
- V71 per-map knob table
- A2_LAB global knob vector (48 values from black-box search; not a network)
- NOVA_SEED jitter

Everything else neural is compiled out: A2_POLICY, A2_ASSESS, A2_ENEMY_NET, APEX_TS_LOCALNET, NOVA_LEARNER, A2_MOVENET,
A2_TILENET, A2_MLPLAN. Tactical search (APEX_TSEARCH) is off, but its **verdict** entry point `tactical_decide`
(APEX_TS_DECIDE=1) is on.

## 2. Combat decision architecture (E25)

### 2.1 What is compiled and active

`handle_enemies` (`bot.cpp:3162-4219`) contains about 20 branches. Resolving every flag and tune constant in
`common.h` (values listed in the audit notes) gives this order of authority in v76:

| # | Layer | Active? | Effect |
|---|---|---|---|
| 1 | `camp_contact`, `capture_stand` (V58 = 2), `deny_capture` | yes | Early return. Owns the turn before any verdict exists. |
| 2 | `try_burst_kill` | no (APEX_BURST 0) | |
| 3 | `bush_ambush` | yes | Early return. |
| 4 | Base formula: target = argmin ttk/worth (lab knobs 16–21 reshape worth); `winning = ttk·risk·ci < min(ttd,8)·aggression`; `in_danger = ttd < kDangerTtd·risk… ∨ hp < kDangerHp` | yes | First verdict. |
| 5 | Outnumbered (APEX_OUTNUMBERED 0, early-safe 0) | no | |
| 6 | Burst danger (NOVA_BURST_K 1.0) | yes | Sets danger, clears winning. |
| 7 | A2_BURST2, C&I outnumbered, side-HP, commit-retreat | no | |
| 8 | Team fight commander (APEX_TFC 0, NOVA_PACK_C 0) | no | |
| 9 | Neural policy (A2_POLICY 0) | no | |
| 10 | `tactical_decide` verdict (APEX_TS_DECIDE 1, A2_TD_AUTH 1) | **yes** | Overrides both flags; a fight verdict is ignored when the risk is unmodelled. |
| 11 | Fight sim, commit-late, disengage, FIGHT2 strength gate, burst-hold, A2_ASSESS | no | |
| 12 | Lab knob 41 team-fight engage (ratio ≥ 3/(1+0.2595) ≈ 2.38 → fight) | **yes** | Can only set "fight". |
| 13 | Engine-lab force | inert in competition | |
| 14 | `deny_tribute` (APEX_TRIB_DENY 3) | yes | Early return. |
| 15 | Bush recall | yes | Early return. |
| 16 | Tactical search (APEX_TSEARCH 0) | no | |
| 17 | `caster_micro` (APEX_CMICRO 1) | yes | Own stay/step scoring for casters; takes `winning ∨ ¬in_danger` as its engage flag. |
| 18 | NOVA_FLEE_HIT | yes | A melee champion hits once before leaving. |
| 19 | `escape_or_stand` (APEX_STAND 1) | yes | May stand. |
| 20 | Flee / kite / kite-cast / fight / gap-dash executors | yes | |

Every turn the knob layer also rescales aggression, danger_ttd, danger_hp and retreat_hp:
- `brain::adapt`
- A2_LAB knobs 0–3, 22–23, 43–44
- V71 per-map rows

**Finding.** The "ten fight/flee layers" are really **five verdict writers** (base formula, burst, tactical_decide,
knob-41 engage, team-numbers). They sit inside a ladder of **six early-return owners** and **five execution
sub-policies**. The verdict is two booleans that later layers overwrite in turn: the last writer wins, and no layer
sees why an earlier one wrote. The objective at stake is absent from the verdict (camp progress, capture timer, ally
bags, distance to altar) except through early returns that run *before* any fight assessment. Each champion decides
alone: the team commander is off, and nothing in shared memory carries a team stance.

### 2.2 Does the fragmentation cause bad behaviour? Evidence for

- **Fight ownership is inconsistent.** 28% of contact rounds step away without hitting (top teams 8%). There are 2.6
  reversals per episode (1.7). In 21.8% of grouped rounds one champion hits while a neighbour leaves (13.7%) (E14).
  This is the expected signature of per-champion binary verdicts with no shared commitment.
- **Deaths dominate both outcomes.** Dead champion-rounds at R500 are 274 vs 127 in losses and 194 vs 456 in wins
  (E11–E12). D3 repeated deaths is the strongest detector association in the deep analysis (E9).
- **Inconsistent overrides kill.** `winning` overriding `in_danger` accounts for 26% of local deaths, and 77% of
  local deaths end in a flee (E15): the verdict flips at the wrong time.
- **The objective is not in the decision.** The economic loss under contest is large: we retain 62–66% of
  uncontested income in losses, the opponents 93–96% (E10).

### 2.3 Evidence against redesigning it

- Every local fight-rule change has been neutral or negative:
  - v79 −24..−107
  - v75 caution neutral locally and −91 on the ladder vs v74
  - v80 sharing not shown
  - v81 −532
  - v83 −65 vs proxy
  - tactical search −366
- **Removing tuned layers hurts.** Removing the lab and map knobs, which rescale this stack, costs −148 / −197 gems
  (E4). The current stack is tuned and load-bearing, not obviously redundant.
- **Local measurement is weak here.** Local opponents share our lineage, and only ladder duels judged fight changes
  (E16). A redesigned combat core therefore cannot be validated cheaply. That is the strongest argument for a staged,
  fallback-protected redesign, not a rewrite.

**Conclusion.** Redesign the combat *decision* as one owner per turn with an objective-aware value, but keep v76's
*executors* (flee pathing, kite, cast, gap-dash, caster micro) until each is individually beaten. The redesign has to
be validated by scenario replays plus ladder duels, not by local margin alone.

## 3. Learned components: matched ablations (E4–E6)

### 3.1 Full table (140 paired games each, seed 71, 70 pool maps × both sides)

| Removed | vs proxy: Δ margin [95% CI], Δ win pp [CI] | vs v65 | Deaths Δ | Fuel-outs |
|---|---|---|---|---|
| A2_CAMPNET | −58 [−174, +48], −5.0 [−14.3, +4.3] | −91 [−225, +41], −2.9 [−15.0, +9.3] | +0.7 / +1.6 | = |
| A2_MLDRAFT | −60 [−142, +19], −1.4 [−6.4, +3.6] | −72 [−178, +35], −7.1 [−16.4, +2.1] | +0.4 / −0.8 | = |
| both nets | — | −128 [−259, +6], −9.3 [−20.0, +1.4] | +0.5 | = |
| V71 map knobs | **−100 [−200, −9]**, −5.7 | **−171 [−283, −54]**, −11.4 [−20.7, −2.1] | +0.7 / +1.7 | = |
| A2_LAB + map knobs | **−148 [−256, −44]**, −11.4 [−21.4, −2.1] | **−197 [−305, −93]**, −17.9 [−27.1, −8.6] | +2.4 / +2.8 | = |
| + APEX_TSEARCH on | **−366 [−470, −263]**, −25.0 | **−325 [−453, −204]**, −21.4 | **+5.5 / +4.5** | **16.1 / 16.0** |

Notes:
- The SA-C-nolab opponent fuel-out mean of 8.34 is a single game: 00vault side b, v65 at 1001 fuel-outs. That is the
  known v65 00vault siege freeze (fixed in v68), not a measurement fault.
- Map knobs and A2_LAB knobs were tuned on these same 70 maps, on other seeds. Their measured value is therefore
  **in-sample by map**. On a map outside the V71 table only the global A2 vector applies.

### 3.2 The draft net, measured where it acts (E5)

The ML draft decides only when the map is outside the V70 table. Restricting to the 76–78 games whose lineup changed,
removing it costs −116 / −112 gems and −3.8 / −10.5 pp. The intervals cross zero but the direction is consistent.
Pooling both opponents gives about −114 ± 115 (95%).

On games with the same lineup the result was +11 / −25. That is the noise floor from a changed pick order (champion
IDs and turn priority change even when the set is the same).

### 3.3 Interpretation the user asked to challenge

- "Draft net valuable, campnet dispensable" is **not established**. Both point estimates are negative when removed:
  campnet −58 / −91, draft net −114 on the maps it controls. Both intervals cross zero, and the two estimates are
  statistically indistinguishable. The honest summary is that each is worth roughly 0–150 gems/game *against its own
  fallback*, with campnet the less certain.
- These ablations compare a net with v76's fallback, not with a purpose-built algorithm. NEURAL_VS_ALGORITHMIC.md
  designs the algorithmic alternatives and the experiments that would decide.
- Fuel is irrelevant to the verdict: campnet costs 567 fuel/turn (1.3%), the draft net ≈1% of one draft turn.

## 4. Economy and resource conversion

### 4.1 The lifecycle and where value leaks

Farm → clear → capture → gold → equipment → combat advantage → gem collection → banking → victory.

| Stage | Our loss vs strong opponents | Evidence | Structural or correlational |
|---|---|---|---|
| Uncontested throughput | **Not a deficit.** Our idle R500 is 489 gems / 2312 gold; the opponents' *contested* level in our losses is 414 / 2145 capture. | E10, E24 | Measured on the same maps. Drafts differ, so this is indicative. |
| Opening speed (R0–100) | Their contested R100 gold (381) exceeds our *uncontested* R100 (329). Claudus first elk R21 vs ours R36. | E8, E22, E24 | Structural (team opening). It does not persist: the opening pack fixed timing but R250 was unchanged (E17). |
| Retention under contest | We keep 62–66% at R500 in losses (75% vs the proxy locally); they keep 93–96%. | E10, E13 | **The biggest gap.** Mechanism: deaths, flee-abandonment of objectives, capture resets. |
| Deaths → income | 2× dead champion-rounds by R250 (120 vs 56) and R500. Every death is 60 champion-rounds of zero income, the bag lost, and +100 gold to the enemy. | E11, E15 | Structural. It compounds through gear. |
| Gold → equipment | Equipment R250 603 vs 880 and R500 1463 vs 2334 in losses. First purchase R71 vs R54. | E11, audit | Mostly a consequence of income and kill gold, partly shopping tempo. |
| Kill gold | 161 vs 393 by R500 in losses, 605 vs 254 in wins. | E11–E12 | Symmetric snowball: whoever wins fights farms kill gold. |
| Banking conversion | 63% vs 88% banked/collected. | E9 | **Mostly downstream of deaths**: the bag-loss term is −103 of −579. Our local conversion vs v65 is equal (0.69/0.67). |
| Channel time | 93 vs 658 channel rounds by R500. | audit | **Artefact**: the perma-recall pattern (E19) counts as channel rounds. Not banking skill. *Correction to the paused audit.* |
| Carry concentration | Top Vesper 0.54–0.79 of team gold. | audit | Copying it (funnel, carry yield) raised share but not team gold (E23, E17). The loop is not reproducible by scoring tweaks. |

### 4.2 Accounting for confounders

- **Map and side.** All headroom comparisons are same-map. Side imbalance exists locally (v65 mirror 136/240 by
  schedule).
- **Draft.** Opponents in our losses draft Vesper 71% / Marcella 84% vs our 34% / 69%. The proxy, which uses top
  drafts with v65's controller, earns *less* than v76 locally (E13). Top drafts do not create top economy on our
  controller, consistent with the −89 meta-draft result.
- **Duration.** All comparisons use fixed rounds (R100/250/500), not lifetime totals.
- **Opponent.** In the ladder data, loss-conditioning inflates every gap: in wins the gaps reverse (E12).
- **What remains structural** after these: early deaths and fight outcomes drive the gold, gear and kill-gold
  snowball. Local mirror data agree: the side ahead in gold at R250 wins 75% (memory, v67 baseline).

## 5. Coordination, survival and the history of failures (V58–V85)

### 5.1 Coordination today

- **Shared memory carries claims, not plans.** Six 7-bit claims (group id, on-site code, fight orders 112–118 now
  unused, idle/dead), plus one beacon carrying an enemy sighting *or* a camp event (E26).
- **Vision is not shared.** Each champion's world is its own vision plus a camp-state memory.
- **Job sizing is decided per champion.** The `need` participants count and job calls exist, but
  `UB_JOB_MAX`/director variants failed.
- **Reinforcement is opportunistic.** Join-fight and fog-regroup are local, reacting to a distress bit (age ≤ 2
  rounds).

### 5.2 Why earlier coordinated controllers failed (common causes)

1. **Unvalidated forward models.**
   - v82's travel/clear model was wrong: it held a job the local chooser would abandon, and Cassi oscillated on
     02arena for 180 rounds.
   - v81's basic-damage and response approximations were wrong.
   - The tsearch evaluation used learned exchange rates.
   - No module proved its predictions before the bot acted on them.
2. **Stale plans.** A2_DPLAN (−217) and the v58 director made plans at draft time or on a slow cadence, with no
   per-turn validity check or progress contract.
3. **Fuel violations.**
   - tsearch: 16 fuel-outs/game
   - v81 first build: 35.9
   - HOME84D trace: 90.5
   - On this engine a fuel-out suspends the bot mid-turn, so a search that overruns is lethal.
4. **Layering instead of replacing.** v79, v80, v83 and tsearch added another verdict writer on top of the stack. Each
   new writer interacted with the existing ones, and the net was neutral or negative.
5. **Copying surface choices without the loop.** Meta draft, funnel, opening pack and carry: each piece alone costs
   more than it returns (E17, E22, E23).
6. **Evaluation against our own lineage.** Local opponents share our weaknesses, so changes aimed at top teams cannot
   show local gains (E16, E20). Several "wins" were seed-overfit (v67 portfolio 220 → 137).
7. **Premature broad benchmarks.** Some families went to 140 games before their mechanism had been shown on the sharp
   uncontested metric (E7).

What succeeded and transferred: league-selected per-map tables with fresh-seed validation (E21), and specific bug
fixes (00vault freeze). A redesign must keep those mechanisms.

### 5.3 What a successful coordination architecture must do differently

- Own a **team objective**, meaning a crew assigned to a camp group, bank trip or contest, with an explicit lifetime,
  progress contract and release rule. It must not be a per-turn rescoring.
- Make the **combat decision about the objective**: fight to keep a capture that is two rounds from completion; leave
  a fight that only protects a wolf.
- Use a **crew stance** that every member reads (one fight leader per crew), with hysteresis. This attacks the
  28% / 2.6-reversal pattern.
- Be **fuel-safe by construction**: anytime algorithms with explicit budgets and a cheap fallback.
- **Validate the forward model first** on uncontested replays (travel, clear time, damage taken) before any decision
  depends on it.

## 6. Engine, platform and evaluation facts that constrain the design

- **Fuel.** 100k per turn; 10× on the first draft turn; 2× on the first play turn. A fuel-out suspends and resumes
  next turn. v76 has about 59k of median headroom but only about 18k at p99 (E1).
- **Memory.** 8 bytes of shared memory, all bits already used (E26). 1024 bytes of draft memory, written at draft and
  read-only afterwards.
- **Draft.** Picks are simultaneous and revealed as they go. Champions are **not exclusive**: both teams may own the
  same one. A draft is therefore a best response to revealed enemy picks plus the map; there are no denial picks.
  Team size is 3–5.
- **Turn order.** Teams alternate within a round and the starting team swaps each round. Within a team, higher
  priority acts first (`set_priority`, effective next round). A fixed "first mover" champion can therefore act as
  leader every round.
- **Capture.** Extra allies do not speed capture, and rewards split among the allies present. One capturer per
  region is optimal for champion-time; who captures matters only for Vesper's gold bonus.
- **Deterministic engine and reproducible ladder games.** The puppet harness reproduces real ladder losses exactly
  (E18). It allows *counterfactual takeover* tests with a horizon of ≤10 rounds before enemy scripts become invalid.
  This is the best available scenario test for combat changes.
- **Noise.** A contested 140-game paired comparison has SE ≈60 gems and a 4-opponent league (560 games) about 30.
  Idle mechanism tests are about 10× sharper. Ladder duel: 120 games, ±54 (E16).

## 7. Bottom line of the investigation

1. v76's losses to strong teams are mainly **contest losses, not farming losses**:
   - deaths (2× dead time)
   - abandoned objectives (retention 62–66% vs 93–96%)
   - the gold → gear → fight snowball that follows
   Our uncontested farming already matches top teams' contested farming, apart from the opening.

   By R100 both channels have already diverged in losses (E28): 36% of losses trail in gold with no extra dead time
   (wins 20%), and 34% have extra dead time (wins 19%). The design therefore needs both an economy core (TEP) and a
   combat core (EE). Neither alone covers the observed losses.
2. The combat decision is fragmented: five verdict writers over two booleans, objective-blind and per-champion. The
   strongest local and ladder evidence ties this to deaths. The strongest counter-evidence is that every incremental
   fight-rule change failed, and that the tuned knob layers are load-bearing.
3. Learned components are cheap and modestly positive against their fallbacks, with the draft net no better
   established than campnet. Per-map tables are the most valuable and most transferable tuning, but do not generalise
   by map features (E6).
4. Fuel is not binding for v76 at the median but is unforgiving at the tail. Unbounded search is fatal.
5. Previous redesigns failed for identifiable, avoidable reasons (§5.2). The recommended architecture
   (ARCHITECTURE_COMPARISON.md, ALGORITHMIC_BOT_BLUEPRINT.md) is built around those reasons.
