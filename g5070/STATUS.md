# g5070 — x3 campaign active

Updated 2026-11-03 00:34 UTC. Earlier K001–K009 results below do not complete K011–K014.

- Machine: CachyOS x86_64; Intel Core Ultra 7 255HX, 20 logical CPUs; 30 GiB RAM; ~425 GiB free disk.
- Environment: isolated CPython 3.12.16, NumPy 2.5.4, verified native cambc 4.0.0. GitHub authentication repaired. No competition login.
- Code: build/z-plan-5070 at 9c1bbde2d5cee6ab53235019027cb452a733b340; own remote branch created; no bot source edits.
- Active: J026 work stealing, claiming escort (row 12) from the bottom; K014 supplied lines complete. 18 workers. K012 next; K013 cancelled per PC0036.
- Measured: 108/172 wins; all 172 map/side/outcome/banked records match J018; 0 own/opponent faults; 186 fuel-outs, each game's count identical. 25.960s whole gate (~397.53 games/min), 18 workers. K011.md published; not a full pass due to build hash.
- Queue per latest PC 0036: finish K014 -> work-steal unfinished J026 rows -> K012 if time. **K013 cancelled for g5070**, transferred to5060 later. Start no new run after2026-11-03 02:15UTC; stop by02:30UTC. Existing analysis/prototype is preserved as handoff only.
- K011 PASSES by explicit PC 0035. Linux default reference is now bf3f65d009c0; all comparisons use own Linux bases. Blockers: none.
- Independent prework: isolated I-70-02 arrival/action prototype passed15 host correctness cases; not integrated in a bot or strength-tested. Idea cards I-70-01/02 and source/replay analyses published; these do not change job priority.
- Local code: /home/om/Projects/Battlecode/x1work; comms ../x1-comms; Python and CLI ../.venv/bin/{python,cambc}.

## Archived earlier campaign

Completed 2026-11-02T14:42:10.598731+00:00. All authorized matrices, worthwhile focused diagnostics and bounded supplied walking-fuel follow-ups are complete, verified and published. WORKERS=DZ_MAX_PARALLEL=18 was preserved.

- K004:7 part-A and4 part-B lines complete.
- K005:all35 planned grids plus no-switch reference complete.
- K006:BP+six frozen finalists complete on149 standard maps against3 opponents and on40 independently frozen fresh layouts. Both sides throughout.
- Focused controls:2 stack ablations,3 null-hook/history controls,2 strict-cache controls, original-x1 standard/fresh references. One preregistered fuel combination failed and correctly stopped before extra validation.
- K007:7 original reserve lines, then BP/selected/x1 standard/fresh validation. Selected P100/WR12 failed standard robustness.
- K009:3 supplied main settings plus BP/x1 references on both specified pools; K007 tail addendum complete (wt3 linked to exact cand; wt5 andwt3wr8 measured). No main setting passes both gates; no supplemental fresh-map setting selected.
- Verification:96 line records,58,414 scheduled rows including references/reuse,50,646 distinct deterministic inputs,7,768 repeated rows,219 distinct map hashes. Zero own/opponent faults. These are not independent map samples.
- Sources isolated:original6efc360 tree1936131c445dcf87e1a1be3a8729ec3246bae16d; K0076ed38b9; K0092732245. Original bot source unchanged. No production bot edits or code-branch pushes.
- Running:none. Blocked:none. Pending:none within this requested campaign and its bounded supplied follow-ups.
- Known limits:related-template holdout/large-forest coverage gap; cached legacy fuel timestamps explicitly unavailable where native data were not shared. No fabricated set, repair or result. No ladder activity, login or external bot upload.

[Final synthesis](results/FINAL_SYNTHESIS.md) · [Diagnostics](results/DIAGNOSTICS.md)

[K004](results/K004.md) · [K005](results/K005.md) · [K006](results/K006.md) · [K007](results/K007.md) · [K009/addendum](results/K009.md)

[Combined verification](results/combined-verification.json). Numerical JSON/provenance accompany every line. Native evidence and detailed resume states remain local under artifacts/local-only/g5070 and research/dz/runs.
