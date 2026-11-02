# g5070 status — K004/K005/K006 experimental worker

Updated 2026-11-02T13:14:53.035616+00:00. No runtime cutoff (current user instruction).

- Bot source: job commit `6efc360`; tree `1936131c445dcf87e1a1be3a8729ec3246bae16d` equals current tree. Checkout `0f962250c2a476881fcc20771c979313fbe5b55c` includes maze set A; local cherry-pick 57af220 retained. Production bots unchanged.
- Concurrency: WORKERS=18 and DZ_MAX_PARALLEL=18, preserved from prior worker. Standard gates include 70 ladder, 50 styled and 29 maze maps, both sides. Maze fuel amendment applies.
- Running: between lines.
- Complete lines: K004A: 7, K004B: 4, K005: 36, K006: 7, K006H: 6.
- Pending: remaining prescribed lines and focused diagnostics. K005 has 35 planned lines plus its no-switch reference; exact completed configurations are in the reports. Duplicate configurations are reused only after identity checks.
- Blocked: none.
- Supplied K007: 7/7 full lines, 0/3 conditional robustness references/candidates, 0/3 conditional fresh-map references/candidates. Separate source 6ed38b9, isolated checkout; original six K006 finalists unchanged. [K007 report](results/K007.md). Additional validation runs only if a novel setting passes R1 with positive gain.
- K001 completed previously. K002/K003 closed: 5060 completed them (PC message 0007).

Results: [K004](results/K004.md), [K005](results/K005.md), [K006](results/K006.md). Detailed resume state remains local at artifacts/local-only/g5070/state.json.
