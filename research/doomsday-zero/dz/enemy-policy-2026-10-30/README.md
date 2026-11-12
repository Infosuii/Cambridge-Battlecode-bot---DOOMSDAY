# Enemy cast-policy evidence, with v76 confirmation

No production policy or selected binary changes. No new games or old bot source
were used. This retrospective audit uses each opponent body's own view from
frozen native replays, rounds1-500 on six fixed development maps, both sides.
These full-replay owner views must never become hidden live-bot inputs.

Training is12 cells against v65. HYPOTHESES_FROZEN.json was written before
reading the12 v76 confirmation cells; CONFIRMATION_INPUTS.json records its hash.
Both manifests bind original bundles, inner replay, frozen reader and opponent
Wasm. Existing source-matched candidate release is5cf28cb7 in all24 cells.

| Observation | v65 discovery | v76 confirmation |
| --- | ---: | ---: |
| Varg owner turns | 5880 | 5820 |
| Varg shields before first basic | 386/386 | 329/329 |
| Varg resets after a basic | 230/230 | 189/189 |
| Varg shield-first in competing ready/low-HP combat subset | 15/15 | 18/18 |
| Heart owner turns | 3000 | 2940 |
| Heart shields before first basic | 189/191 | 184/188 |
| Heart dash casts | 305 | 306 |

All frozen descriptive checks pass. Three Varg shields across both opponents
occur at>=85% current HP, with HP/maxHP increasing within that owner turn;
start fractions were below85%. Do not turn this into an exact causal threshold
or claim a purchase intent. No Heart shield is at>=85%. The competing Varg
subset requires owner-start cast readiness, low HP, both CDs0 and a first basic
whose target survives. Those fields do not establish a desired target or force
any action. Owner-start readiness also misses within-turn channel cancellations.

Across17640 owner turns,2124 have one accepted cast and15516 have none; none
has two. INSTRUMENTATION_CHECK.json audits12 known casts from our independent
basic-before-cast duel controller and identifies all as post-basic, so pre-basic
enemy shields are not an instrumentation assumption. That frozen replay comes
from a rejected predictor pilot: only actual controller ordering is checked.

The unused duel primitive currently prescribes basic/reset before shield and
omits Heart dash. Its controlled conformance does not validate these enemy
policies. Recorded action counts establish neither dash damage/value nor that
matching an opponent's priority would improve us. Repeated turns within fixed
games are dependent observations; no independent-game confidence or competitive
parity claim follows. Production EE/new-job admission remains disabled.

Reproduce: extract each cell with tools/dz_extract_replay.py, verify its inner
SHA, then run analysis-source/dz_enemy_casts.mjs with opponent team0/1 and500,
NFS_REPLAY_ENGINE=2.0.0. tools/dz_enemy_policy_report.py recomputes both summaries.
Frozen native source capsules remain immutable; raw analysis outputs and all
exceptions are preserved here.

Next: test the unused Heart ground dash through a controlled native adapter,
then a bounded camp-only experiment. Preserve shield priority and collateral,
movement, release and productivity gates. Dash remains outside live EE.
