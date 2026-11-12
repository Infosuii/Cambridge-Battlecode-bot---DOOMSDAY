# Architecture comparison: simplify (A) vs redesign (B) vs clean slate (C)

E-numbers refer to FINAL_DEEP_ANALYSIS.md.

## The three candidates

- **A: Simplified v76 ("v76s").**
  - Keep the whole decision hierarchy and remove only what is proven harmful or dead.
  - Add verified bug fixes, starting with the recall-restart guard (E18, S7).
  - Optionally add unseen-map profile generalisation (S9).
  - No new decision modules.
- **B: Redesigned algorithmic controller on v76 infrastructure ("OCC": Objective–Crew–Combat).**
  - Reuse v76's engine-facing layer: SDK wrappers, World update, fields, movement, executors, shopping builds,
    tribute/recall, claims, draft tables, knobs.
  - Replace the strategic and decision hierarchy module by module behind flags:
    - TeamLedger + ObjModel + TEP for objectives
    - EE for the single combat authority
    - the crew protocol for coordination
  - Every flag at 0 gives a byte-identical v76 build.
  - Spec: ALGORITHMIC_BOT_BLUEPRINT.md.
- **C: Clean-slate algorithmic bot.** A new lean controller from first principles that keeps only verified SDK
  wrappers and engine-facing code. Its own world model, pathing, executors and shopping.

## Assessment

| Factor | A: Simplified v76 | B: OCC on v76 infrastructure | C: Clean slate |
|---|---|---|---|
| **Competitive potential** | Low upside. Removing dead code changes nothing (flags compile it out). Measured layers are positive (E4). Gains limited to bug fixes and maybe unseen-map knobs. Does not address the contest gap (E10–E12). | Medium-high. Targets the measured gap directly: objective-aware single combat authority, crews, contest-aware economy, survival rules. Ceiling unknown until EE/TEP are measured. | Highest theoretical ceiling, but must first re-earn everything v76's ~16.5k lines of tuned behaviour do (bush ambush, deny tribute, caster micro, gate maps, siege freeze fixes…). |
| **Development risk** | Very low. | Medium. Each module can regress, but flags isolate it, the disabled build is byte-identical, and v76 executors and fallback stay. | Very high. Base rates: mimic 0/120, GPT controllers 0–32/240, every v81–v85 partial replacement lost (E17). |
| **Effort before finals** | 1–2 days. | 9–11 days for the core (TEP, EE, crew), within the 14-day window with a freeze on Day 12. | More than 14 days to parity. A single missing behaviour (e.g. the 00vault-type freeze) can cost hundreds of gems on a map. |
| **Fuel efficiency** | As v76: mean ~41k, p99 ~82k, 0.5 fuel-outs (E1). | Target: mean ≤48k, p99 ≤88k. TEP replaces score_groups' ~13k; EE adds 8–12k on contact turns; hard deadlines and fallbacks (COMPUTATIONAL_DESIGN.md). | Could be leaner. No evidence fuel limits v76 (E1), so this buys little. |
| **Strategic coherence** | Unchanged: five verdict writers, per-champion objectives, no team plan. | High: one value scale (gem-equivalents) shared by economy, combat and banking; one owner per decision; crews. | Highest if done right. |
| **Generalisation** | Per-map tables don't generalise (E6); unseen maps fall to global knobs + ML draft. | Analytic models built from the rules, plus a few calibrated scalars, should generalise across maps better than per-map tables. Unproven; the held-out-map gate tests it. | Same as B, without per-map tables to fall back on. |
| **Debuggability** | Poor: overrides interact; "why did it flee?" needs layer tracing. | Good: every decision logs per-stance values and per-objective rates. | Good. |
| **Testing complexity** | Low: bug-fix scenarios plus a league confirmation. | Medium: model-first offline gates, idle mechanism gates, puppet scenarios, league, then ladder (VALIDATION_PLAN.md). | High: full-behaviour regression across 70 maps before any strength claim. |
| **Maintainability** | Poor (accreted flags). | Improves module by module; the old code stays as fallback. | Best long-term, worst near-term. |
| **Fallback safety** | Is the fallback. | Strong: v76s remains a ready candidate; each OCC flag is independently revertible. | Weak: no partial credit if parity is not reached. |

## Recommendation

**Build B, staged as a strangler on v76, with A (v76s) prepared on Day 1–2 as the guaranteed fallback candidate.**

Reasons:
1. **The measured problem is decision-level, not infrastructure-level.** Contest retention, deaths and combat
   coherence (E10–E15, E25) live in `handle_enemies`, `score_groups` / `farm` and the claim protocol. B replaces
   exactly those and nothing else.
2. **Previous failures were failures of unvalidated models, stale plans, fuel violations and layering** (FINAL_DEEP_
   ANALYSIS §5.2). B's process (model-first gates, progress contracts, fuel governor, replacement not layering,
   byte-identical controls) is designed against each. C carries the same risks plus the parity problem.
3. **Proven tuned assets remain usable in B:** the V70 table, knob tables, ML draft and executors. That matters
   because they are the only changes demonstrated to transfer to the ladder (E21).
4. **Fourteen days is too short for C.** The deep-analysis branch (E18) and v81–v85 show how long it takes to prove
   even one module.

## The strongest alternative: A+ (v76s plus targeted fixes and per-map re-selection)

A+ is preferable to B if any of these hold:
- **By Day 7 (2026-11-04), neither TEP nor EE has passed its mechanism gate** (VALIDATION_PLAN.md gates G1/G2). The
  remaining week is then better spent on A+ items: bug fixes, the endgame race, S9, and league re-selection of draft
  or knob rows. The roadmap has an explicit switch point.
- **Ladder duels are not approved** (they require activation, E16). B's combat value then cannot be judged before
  finals. Promoting B on local evidence alone would repeat the v79/v75 pattern, where fight changes look neutral
  locally and are unknown on the ladder. In that case ship A+, unless B shows a strong *economic* gain on the idle and
  league gates (TEP alone), which local tests can measure.
- **The finals are on the known 70-map pool and the user prioritises minimum risk.** The per-map assets of v74/v76
  are then fully in force, and A+ keeps them untouched.

## When C would be preferable

Only for a post-finals rebuild, after B's modules prove their models: TEP's ObjModel and EE's exchange model,
validated on replays and games. Then they can be re-hosted in a lean controller without v76's accreted layers. Before
finals, C is not recommended.
