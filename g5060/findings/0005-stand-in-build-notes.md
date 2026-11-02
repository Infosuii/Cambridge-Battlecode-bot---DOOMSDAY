# 0005: stand-in build notes (pc/msgs/0006 ask; follows findings/0002), 2 Nov ~11:20 UTC

## What knobs alone can do: three no-new-code prototypes, measured

Built from bots/x1 at f43d11f with existing switches only; x1 (1746f2bb7fa3) plays each on the 70 ladder maps, both
sides (140 games; both teams' numbers from the native summaries). Run records g5060-si2-*-ladder on build/z-plan-5060.

| stand-in | switches | x1 wins | gold@R500 x1 / opp | banked@R500 x1 / opp | deaths x1 / opp | x1 20+-death games |
|---|---|---|---|---|---|---|
| S1a fast farmer | BP + X1_PLAN 4 from R150 + X1_ECON stage 0.5 | 74 | 1801 / 1773 | 240 / 237 | 8.5 / 8.7 | 19 |
| S1b fast farmer, longer gold value | S1a + UB_GOLD_UNTIL 600 (from 250) | 78 | 1810 / 1865 | 252 / 223 | 8.3 / 8.8 | 16 |
| S2a team push | BP + X1_PLAN 8 from R0 + APEX_COHESION 0.5 (from 0.05) | 103 | 1986 / 1612 | 265 / 195 | 9.0 / 13.9 | 18 |
| *earlier: x2 (v88)* | | 68 | 1777 / 1759 | 220 / 235 | 10.9 / 10.5 | 25 |
| *top teams vs v86h (TOP_TEAMS)* | | *3/35* | *~1000-2000 / 2800-4300* | *213 / 395* | *collapses 23-48* | *9 of 35* |

None reaches the target (x1 ≤ 40% = ≤ 56 of 140, opponent gold@R500 ≥ 1.3x x1's). The x1-family knobs move gold@R500 by
at most ~5%; pushing as a team still feeds (13.9 deaths). The top teams' edge is a ~2x farming rate, which no knob
combination of our own code produces.

## Build notes for the PC (proposals; ordered by expected value)

**S3 action-replay opponent (recommended first).** The x1 audit (research/x1-audit-2026-11-02/REPORT.md) reproduced 20
real top-team games byte for byte with "an opponent that repeats the accepted recorded actions". The same harness is
a stand-in that *is* a top team, exactly, until our bot's actions differ from the recorded game; after that the
replayed actions are stale (rejections pile up). Uses: (a) every candidate plays the 35 + 35 recorded top-team games
(TOP_TEAMS_2026-11-02 and the audit's), score = rounds survived before divergence, banked / deaths at the divergence
round and at R250 / R500, and the final result while the opponent's replayed actions remain legal; (b) a direct test
of the collapse mode, since the recorded opponent fights exactly as it did. Needed: the audit's repeat-opponent
harness on a branch (its source is not on research/x1-audit-2026-11-02 as far as I can see; only the validation
JSON), and the replays' action streams. I can run it at volume once it exists.

**S1 fast farmer, real version.** Port bots/proxy's top-team draft + item tables (PROXY_DRAFT / PROXY_ITEMS) into an
x1 copy (Agent 2: draft + items alone did not reproduce top teams, op1 41%), plus the top teams' farming rule set from
the replay study (one owner per reward / no split captures: 19.6 vs 11.6 gems per capture, Agent 2 handover 7.4) and
perma-recall for the teams that use it. Target check as above. I can screen any build in ~2 min.

**S2 early contact, real version.** Needs a contact *window* (plan switch back after R250), which X1_PLAN cannot do
(a plan holds from its round on): a second hook X1_PLAN2_ROUND / X1_PLAN2_ID, or plan 8 with an end round. Draft
QS2isLaw's Heart + Vendetta + Vesper. S2a above shows that cohesion 0.5 + push still feeds (13.9 deaths), so the
window's fight rule needs the arrival-time fight model (idea bank #9) to be a credible opponent.

Until one of these exists, the gate opponents stay x2 / x2-s2, which do not reproduce either top-team failure mode
(x1 wins 68 / 140 vs x2 but 3 / 35 vs the top teams' style).
