# Top-team reverse engineering: observations, inferred decision systems, confidence

> **Carried forward into the DOOMSDAY Zero (clean-slate) package, 2026-10-28.**
> - "TEP" means DZ's economy planner, and "executors" means DZ's action scorer (ALGORITHM_SPECIFICATIONS §6).
> - v76 appears only as a benchmark and as the source of lessons. DZ reuses no v76 code.
> - Where this text mentions a v76 fallback path, DZ uses its own SafeMode (MASTER_ARCHITECTURE §3).


**Scope and honesty rules.**
- No top-team source code is available. A web search found no public current-rules bots beyond two weak ones already
  tested (`research/v81/RESEARCH.md`: Midnight Wardens and gamebot; both fail on fuel).
- Every mechanism below is a **hypothesis about decision principles**, inferred from replays. It is never a claim
  about anyone's code.

**Data used (examined sets only; nothing new was played):**
- `analysis/deep-2026-10-28` @ 19109c4:
  - `P5_OPPONENTS.md`, `PROFILE_DATA.json`: 8 opponent profiles, 360 own ladder games against platform 69 = v75
  - `TIMELINE_DATA.json`: 385 examined games plus 25 top-v-top games
- `research/proxy/TABLES.md`: item milestones from 1,470 native summaries, mostly before Sprint 3
- `research/v58/V58_CLAUDUS_FINDINGS.md`, `research/v75/TEAMFIGHT.md`, `research/v75/MG_18208504.md`

The deep study's 165 reserved games were spent by that study's own confirmation (REPORT.md). I used only its
published aggregate statements, never the reserved data.

**Confidence scale:**
- **H**: consistent across several teams and measures, with a mechanical rationale
- **M**: consistent but confounded
- **L**: plausible, with weak or indirect evidence

## 1. What strong opponents measurably do differently (paired, same games)

| Opponent (n, our W) | R100 gold, us/them | R250 gold | R500 equipment | Deaths/game | Conversion | Wards/game | Damage per contact champion-round | Middle camp-gem share |
|---|---|---|---|---|---|---|---|---|
| Intercontinental Fish (17, 0W) | 278 / **483** | 739 / **1444** | 1440 / **2929** | 14.9 / **5.5** | 56% / 88% | 48 / 146 | 10.5 / 22.7 | 22% / 43% |
| Mite (14, 2W) | 281 / 349 | 763 / 1090 | 1444 / 2771 | 14.7 / **2.9** | 68% / 89% | 50 / 192 | 10.5 / 28.1 | 35% / 36% |
| SkibidiSloppers (12, 2W) | 374 / 406 | 935 / 1178 | 1785 / 2355 | 8.2 / 10.3 | 86% / 94% | 38 / 244 | 22.2 / 30.7 | 28% / 37% |
| Ad Astra (14, 4W) | 281 / 262 | 786 / 1016 | 1449 / 2177 | 11.3 / 8.9 | 66% / 79% | 41 / 94 | 25.1 / 35.2 | 45% / 52% |
| Univ. of Shingtonwash (15, 2W) | 279 / 295 | 756 / 930 | 1564 / 1900 | 10.0 / 5.2 | 70% / 92% | 60 / 208 | 19.5 / 33.0 | 34% / 48% |
| print dont int (9, 1W) | 261 / 355 | 699 / 1046 | 1260 / 2137 | 9.0 / 3.1 | 71% / 95% | 59 / 115 | 16.1 / 27.2 | 32% / 25% |
| newer team (6, 0W) | 346 / 363 | 1002 / 1038 | 1910 / 2245 | 8.2 / 2.2 | 78% / 94% | 66 / 110 | 12.0 / 28.2 | 21% / 29% |
| error404 (155, 111W) | 348 / 257 | 1001 / 769 | 2022 / 1478 | 7.6 / 16.7 | 84% / 81% | 86 / 114 | 26.4 / 23.5 | 47% / 38% |

**Drafts** (modal ordered draft; P5):
- Fish, error404: Vesper, Vendetta, Heart, C&I, Marcella
- Mite: Vesper, Vendetta, Heart, Tavi, Marcella
- SkibidiSloppers: Vesper, Heart, Marcella, C&I, Willow
- Ad Astra: Heart, Varg, Marcella, Vesper, Ryth
- Shingtonwash: Marcella, Varg, Heart, Vendetta, Vesper
- print dont int: Vesper, Heart, Vendetta, Ryth, Marcella
- newer team: Prism, Vendetta, Marcella, Willow, Heart
- **Ours**: mostly Vendetta-led melee, with Vesper rare.

**Openings:**
- Opponent first purchase: median R48–R62. Ours: R55–R82.
- Opponent first ≥20-gem team receipt: R41 (Fish), R44 (newer team), R55 (Skibidi), R60 (Mite).
- Claudus (v57 era): first elk group started at R21 with 3.7 champions and captured at R50. Ours: R36 with 2.7,
  captured R80.

**Time use.** Mite, newer team and print dont int log about 4,200–4,450 channel rounds per game, with 90–150
travel/stationary rounds. That is perma-recall: a recall started at about 90% of turn ends and cancelled next turn
(`research/proxy/README.md`). Mite also logs 68.9 fuel-outs per game.

## 2. Inferred mechanisms

### M-A. A team-level economic opening with early carry gear ("fast first elk, early Treasure")

1. **Observed.**
   - First large receipts at R41–60, against our R55–82.
   - Fish reaches 483 R100 gold, 1.47× our *uncontested* R100 of 329.
   - First purchase R48–62.
   - Claudus: 3.7 champions on the first elk group by R21.
   - Item milestones: nearly every top hero opens Treasure 5, then Jungle 5 (proxy tables). That is consistent with
     maximising gold early and then reducing camp damage.
2. **Hidden decision system that could produce it.** A precomputed or rule-based opening:
   - the team starts on the nearest elk-size group at once, with all but one champion
   - then crew-sized follow-ups
   - Treasure bought on the first spawn visit

   This is consistent with **explicit opening scripts per map, or a simple "nearest high-value group with the whole
   team" rule**.
3. **Alternatives.**
   - Their drafts clear faster (Vesper, Heart, Vendetta damage).
   - Our opening is slowed by our own heuristics (staging, need counts) rather than theirs being clever.
4. **Confidence.** H that a large opening gap exists against Fish, Mite and print. M on the mechanism.
5. **Reproduce.**
   - A draft-time opening schedule, validated live, plus a team economy planner that keeps crews on high-rate
     groups.
   - Early emblem completion chosen by marginal value, not by copying Treasure: Treasure is now +10% per the engine,
     and Prospector/Capture may be worth more.
6. **Transfer.** Partial. The v58 opening pack reproduced the first-capture timing (R40) but R250 gold did not move,
   because the greedy loop took over afterwards. The planner after the opening is what matters.
7. **Validation.** Idle bench: R100 gold +15% with R250 non-inferior. On examined ladder timelines, compare our and
   their first-three targets per map (`opening_rows`).

### M-B. Low-death engagement policy: fight only with local superiority, trade efficiently, never trickle in

1. **Observed.**
   - Deaths per game: 2.2–5.5 for Mite, Fish, newer team and print, against our 9–15.
   - Their damage per contact champion-round is 2–3× ours.
   - Their basic-focus rate is higher.
   - Their low-HP separation rate is *lower* than ours (they separate less when hurt but die less).
   - From v74 duels: we step away without hitting in 28% of contact rounds (them 8%) and reverse 2.6× per episode
     (1.7×).
   - Even fights cost us 0.76 deaths and them 0.36.
2. **Hidden system.** A *commit-or-avoid* engagement rule evaluated at the team or crew level:
   - Engage only when local strength (HP × DPS, Lanchester-style) clearly favours them, then commit and hit every
     turn.
   - Avoid contact otherwise, *before* range is entered, not after taking damage.

   This is consistent with **predictive combat evaluation plus commitment**, or with simple "group up, fight
   together" heuristics plus better micro.
3. **Alternatives.**
   - They out-gear us from R300, so their fights simply are favourable.
   - Their micro (stepping into range and casting) is better, not their decisions.
   - Perma-recall teams avoid fights by exploiting our targeting (M-E).
4. **Confidence.** H on the outcome. M on "decision before contact plus commitment". L on team-level evaluation.
5. **Reproduce.** The Engagement Evaluator: one owner, objective-aware value, hysteresis, the free-action rule, and a
   crew stance.
6. **Transfer.** Unknown. Every local fight-rule change was neutral or negative, though those were layered on the old
   stack. Judge on puppets and the ladder.
7. **Validation.** Puppet takeovers of reproduced losses. Metrics: deaths per game, the step-away share, reversals.
   Then a ladder duel.

### M-C. Objective control of the middle and of shared regions

1. **Observed.**
   - Their middle camp-gem share is higher than ours against Fish (43% vs 22%), Shingtonwash (48% vs 34%) and
     Skibidi (37% vs 28%).
   - On yellow-brick-road their home group generated 9,667 gold against our 600 (MG_18208504).
   - Shared strips were already cleared by R40.
2. **Hidden system.** Territory or "contested-value" planning: they claim and hold high-value shared regions early,
   aided by superior fight odds.
3. **Alternative.** It may be a by-product of winning fights (M-B) rather than a separate plan.
4. **Confidence.** M.
5. **Reproduce.** Contest-aware objective rates (`P_ok` in TEP) and DEFEND/CONTEST team modes, with no fixed guards.
   v84 fixed-guard denial lost −886 on 2 games.
6. **Transfer.** Conditional on M-B.
7. **Validation.** League retention metric on maps with a high centre-contest index.

### M-D. Vision as infrastructure

1. **Observed.** 94–244 wards per game against our 38–86.
2. **Hidden system.** Continuous ward cycling: re-placing the ward whenever it recharges, probably on paths and
   objectives.
3. **Alternative.** Cheap habit with little effect. The deep analysis found the unseen-killer gap weakens after
   exposure normalisation.
4. **Confidence.** H that it happens. L that it matters.
5. **Reproduce.** Ward on every recharge at objective approaches (cheap), and feed sightings to the shared beacon.
6. **Transfer.** Cheap to try; low expected gain.
7. **Validation.** Offline: the fraction of our deaths where the killer was first seen 2 rounds or less before. Then
   the league.

### M-E. Perma-recall (recall started at turn end, cancelled at the next turn start)

1. **Observed.** Several Learn-cohort teams (Mite, newer team, print dont int; and NEETCoders, Trzy, willow best girl
   in older data) do this on 89–97% of turns.
2. **Candidate decision systems or purposes (competing):**
   - **(a) Insurance against fuel-out suspension.** If a turn suspends mid-way, the channel keeps ticking and the
     champion goes home. Supporting: Mite's 68.9 fuel-outs per game. Against: newer team and print rarely run out of
     fuel.
   - **(b) Exploiting opponents' heuristics.** Many bots, ours included, treat recalling enemies specially: v76 gives
     `worth += 0.5` to a recalling target, making it a *more attractive* chase target, which could feed dives.
   - **(c) A visual or stat artefact of a "recall when idle" rule** with no real purpose.
3. **Confidence.** L for each.
4. **Reproduce.** Do **not** copy it. The proxy experiment changed v65's margin by −33 ± 40 against these teams.
   Instead:
   - Make our targeting robust: remove the "recalling" bonus unless the channel is several rounds old. Enemy channel
     age is observable over consecutive turns.
5. **Transfer.** The defensive half (robust targeting) transfers. Copying the behaviour does not.
6. **Validation.** On examined replays: our engagement rate and death rate after targeting a "recalling" enemy,
   against non-recalling enemies.

### M-F. Banking discipline and converting under contest

1. **Observed.**
   - Conversion 88–95% for them and 56–86% for us.
   - Our high-bag losses are 0.3–1.5 per game, 28–140 gems.
   - Their bank R250 is typically 1.5–3× ours.
2. **Hidden system.** Bank-on-route: bank whenever an altar is near the current path, with small bags. Or Marcella as
   the carrier banking under fire, since damage does not interrupt a tribute and she is stun-immune.
3. **Alternative.** It is downstream of fewer deaths (M-B).
4. **Confidence.** M.
5. **Reproduce.** A hazard-based BANK objective (the burglar problem), bank-on-route insertion, Marcella preference,
   and altar locks against enemy carriers and in the endgame.
6. **Transfer.** Likely, as an economy change with a sharp local metric.
7. **Validation.** Idle bench conversion (no deaths), then league conversion and bag-loss metrics.

### M-G. Draft as a fixed meta core

1. **Observed.** 6 of 8 profiled teams first-pick Vesper. Heart, Vendetta and Marcella appear in nearly every top
   draft.
2. **Hidden system.** A fixed meta lineup chosen offline, largely map-independent.
3. **Alternative.** Their controller is built around those kits (dash, gold, stun-immune banker), so the draft and
   the controller co-evolved.
4. **Confidence.** H for the observation. M for "their controller fits their draft".
5. **Reproduce.** Do not copy alone: the meta draft on our controller was −89 and the proxy with top drafts is weak.
   Re-test meta lineups *after* TEP, EE and banking exist, as one league option per map (V70 protocol).
6. **Transfer.** Conditional on controller compatibility.
7. **Validation.** League per-map lineup screen on the final controller.

## 3. What this implies for the architecture

1. The gap is a **coupled loop**: a faster opening and earlier gear give favourable fights, which give fewer deaths,
   which keep income and control the middle, which buys more gear.
   - In 36% of our losses we trail in gold at R100 with no extra deaths; in 34% we have extra dead time by R100 (E28).
   - **Both an economy core and a combat core are required**, and they must share one value scale.
2. **Don't copy surface behaviour** (draft, perma-recall, item lists). Reproduce the principles:
   - commit-or-avoid fights with local superiority
   - crew economy with fast high-value openings
   - banking discipline
   - cheap continuous vision
3. **Error404 is a bad mirror.** It is 155 of our 360 examined games and we beat it 111 times. Aggregate statistics
   from the mixed corpus understate the gap against the real top. Validation must weight Fish, Mite and the other
   top teams' behaviour profiles, not mixed averages.
