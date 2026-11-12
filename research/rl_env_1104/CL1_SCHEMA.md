# Observation layout `cl1` (proposal, for JOHNDOE review)

Our own layout, written against the SDK (`API_AUDIT.md` §3). No code or layout from Agent 2. One int16 vector per
decision of one body, built only from what that body can legally read this turn, plus its own memory of earlier
sightings (with explicit ages). Fixed-point: positions/distances in tiles; fractions ×1000; counts as-is; ages in rounds,
capped at 2000; `-1` = unknown. Every row of every block is cleared each decision before filling (lesson: stale absent
rows).

| block | rows × width | contents |
|---|---|---|
| `g` globals | 1 × 16 | round; our and enemy submitted gems (`global_submitted_gems`); win target; team size; map width, height, symmetry; my slot; allies alive (known); enemies visible now; enemies seen within 50 rounds; my distance to own spawn and to nearest altar; draft-memory valid flag; fuel left at capture ÷100 |
| `s` self | 1 × 32 | champion type; x, y; health, max health, strength, focus; gems; gold; state bits (alive, recalling, submitting, can_move, can_attack, can_cast, teleporting); ability 0/1 cooldowns; ward charges and recharge; remaining channel; items held (count by family for 14 families) |
| `a` allies | 5 × 16 | present; type; dx, dy (relative to self); health fraction; gems; alive; visible now; age of info; recalling; submitting; distance; their claimed target row (from shared memory, if v92 wrote it this round; else -1); 3 spare |
| `e` enemies | 6 × 16 | present (known to exist); type (from draft); visible now; age since this body last saw it; last-known dx, dy; last-known health fraction, gems; alive-known; distance; attack range; in my attack range now; 4 spare |
| `c` camp groups | 12 × 16 | the 12 nearest groups by path-free distance; present; dx, dy of centroid; camps in group; counts by type (wolf, elk, gem cluster, gold cluster, monolith, golem); awake / asleep / dead counts; summed health fraction; distance; age of info |
| `l` altars | 4 × 8 | present; dx, dy; distance; ally lock / enemy lock; lock hits remaining; in submit range |

Total: 16 + 32 + 80 + 96 + 192 + 32 = **448** features (int16).

## Labels recorded with each row (teacher traces from v92)

- **Macro target** (hybrid head `target13-cl1`): v92's chosen camp group mapped to its `c` row (0..11), or 12 =
  none/outside the 12 nearest. Mask: rows with `present == 1`, plus 12.
- **Primitive outcome of the turn** (for full-control curricula; measured by diffing self state at turn start and end,
  not by reading v92's code): moved (dx, dy), attacked, cast ability 0/1, recall started, submit started, items bought,
  ward placed. Exclusivity between primitives is measured from these, not assumed.

## Recording rules

- Capture at the **start** of the turn (before v92 acts); labels at the **end**. Both inside `debug_block`, so release
  builds and fuel accounting are untouched. Gated by `CLRL_REC` (default 0): the default build must stay byte-identical
  to v92 (`5704d7ba41ac…`), checked by test.
- **Every** turn of every alive body is logged (`sampling="teacher"`, no log-probabilities).
- Dead turns get one row at death and one at respawn (`reset=1`), not a row per dead round.
- Row format on stdout: `CLR1 <round> <slot> <body_id> <macro> <prim bits> <dx> <dy> <b64 int16[448]>`; the collector
  checks counts against the summary's rounds and flags log cuts.

## Questions for review

1. 12 camp groups, or fewer or more? (Large maps have more groups; overflow goes to label 12.)
2. Should the ally rows carry v92's shared-memory claims? That couples features to v92's protocol. Useful for a hybrid,
   wrong for full RL. My default is to include them, flagged, so the learner can mask them.
3. Is int16 fixed-point fine for your encoders, or do you want float32 rows?
