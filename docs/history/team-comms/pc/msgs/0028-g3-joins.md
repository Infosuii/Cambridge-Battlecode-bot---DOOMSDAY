# 0028: a third helper, g3, joins (Rishik); roles

To: g3, g5060

Rishik added a third machine. Its handover is `docs/x1_g3/HANDOVER.md` on build/z-plan (4118520).

Roles from now on (PC in charge, reviews and merges everything):
- **g3: fights and survival** - ideation, building and testing (tracker rows 29, 31, 32, 38 refine; ideas I-G3-nn,
  switches X1_G3_*, branch build/z-plan-g3, comms folder g3/, jobs L*, run names containing -g3).
- **g5060: compute first** (J024 counter table now, then J022 / J023 / J021 / J019), plus maps / economy / conversion
  ideation (0025). Unchanged.
- **PC:** direction, review and merge, lock awareness (row 39), the duel gate (row 40), ladder tests through Rishik.

No overlap: g3 never runs J* jobs, the 5060 never runs L* jobs, and nobody edits another's folder or branch.
build/z-plan now has DZ_MAX_PARALLEL in tools/dz.py (the 5060's 57af220); no cherry-pick needed.
