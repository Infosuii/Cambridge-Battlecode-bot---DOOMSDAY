# Executive recommendation: DOOMSDAY Zero (clean slate)

## Decision requested

Approve building **DOOMSDAY Zero (DZ)**, a fresh C++ bot in `bots/dz` using **no code from any previous DOOMSDAY
bot**. It is built on:
- the official SDK and CLI
- the repository's research findings and data, as design inputs
- the repository's evaluation tooling, which tests bots and is not part of them

Previous bots serve only as benchmark opponents. The current live bot stays the finals fallback. **Nothing has been
implemented.**

## What DZ is

A hierarchical algorithmic bot where every decision has one owner and one value scale (gem-equivalents):

1. **Kernel.**
   - Exception boundary and fuel governor.
   - An **Actuator** that is the only SDK action caller and refuses stale actions after a fuel-out resumption.
   - Engine fingerprinting.
   - Always-available **SafeMode**.
2. **Knowledge.**
   - Static world built from engine metadata only, with engine-side distance fields.
   - Per-turn observation.
   - Memory: group ledger with persistent partial HP (camps don't regenerate), enemy beliefs, ally beliefs from the
     shared word.
3. **Coordination.** A fresh 64-bit protocol: 6 × 8-bit slot records (objective, on-site) plus a 16-bit typed team
   message (sighting, camp event, crew stance, team mode), with pre-emption and freshness.
4. **Strategy.**
   - Race controller (time to 1000).
   - Economy auction: crews, solo cluster circuits using Capture and Prospector, respawn timing, single capturer,
     progress contracts.
   - Bank rule: optimal stopping, Marcella preference, altar locks.
   - Gear planner: marginal value from engine item data.
5. **Tactics.**
   - Engagement evaluator: a stance portfolio scored by a 4-round focused-fire attrition model, with hysteresis and
     crew stance.
   - One **action scorer** for every concrete move, attack, cast, ward and consumable.
6. **Draft instance.** Exhaustive utility optimiser with a research prior (top teams' core) and league-selected
   per-map rows, plus an opening planner using the 10M first-draft-turn fuel.

## Why this is safe from surprises

- **The complete game reference** (GAME_MECHANICS_AND_WIN_CONDITIONS.md) lists every rule and quantity with its
  verification status. Planning found and fixed several places where the published rules are wrong:
  - The draft first turn gets **10M fuel (100×)**, not 10×.
  - **Treasure is +10%**, on all gold including kills.
  - **Vesper + Treasure = +43%**, not 53%.
  - Monster is +15%.
  - **Capture emblem: 3-round capture.**
  - **Prospector: +25% cluster gems.**
  - **Camps never regenerate HP.**
  - Many champion stats differ.
- **The variable coverage matrix** maps every quantity to its source and the module that uses it.
- **The SDK interface guide** covers all 154 engine imports, visibility rules, error codes and turn-ordering rules.
- **The engine conformance suite** (27 tests, Day 1–2) settles every remaining unknown before strategy depends on
  it, and re-runs on every engine release. cambc has shipped every 3–5 days.

## Plan and gates (14 days)

| Day | Date | Milestone |
|---|---|---|
| 1 | 10-29 | Conformance suite, kernel |
| 2 | 10-30 | **Walking skeleton (SafeMode) plays full games** |
| 3–5 | | Memory, protocol, validated ObjModel, auction, action scorer, gear |
| 6 | | EE live; **idle parity with v76** (G-P1) |
| 7 | | **Decision D7** |
| 8 | 11-05 | Crew stance, race controller; **last architecture change** |
| 9 | | **Contested parity** (G-P2), else finals with the live bot |
| 10 | | League tuning and per-map draft rows |
| 11 | | Ladder duel request (your approval) |
| 12 | 11-09 | **Freeze** and once-only holdout |
| 14 | 11-11 | Your decision |

## Honest assessment

- A clean slate starts behind v76, the product of 76 iterations, in executor detail.
- My judgement is a **30–45% chance** that DZ beats v76 against top teams by Day 12. That rises if the conformance
  and calibration work lands by Day 4.
- The design is built to close the measured gap (opening and gear, deaths, retention, conversion). The gates make
  sure a worse bot cannot reach the finals.

## Questions for you

- **Q1:** Will the finals use the 70-map pool, or new maps?
- **Q2:** Will ladder duels be approved?
- **Q3:** Which bot is the finals fallback?
- **Q4:** Do you accept the clean-slate risk with these gates?
- **Q5:** May the agent download fresh top-team replays for calibration?

## Files

`research/zero-bot-plan-2026-10-28/`. Start with HANDOFF.md.
