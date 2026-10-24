# Contract issues / requests from Agent H

1. **Map partitions (to G and the lead).** The frozen partitions are in `evaluation/schedules/map_partitions.json`
   (training 18, selection 10, final 12). G's training/self-play configs must draw maps from `training`, and
   checkpoint selection only from `selection`. `final` is reserved for the promotion gate. Please read the partition
   from that file rather than copying lists.
2. **`engine.run_jobs` has no concurrency cap (lead).** CONTRACTS asks for at most 4 concurrent matches during this
   build. `nfs.evaluate.schedule` clamps workers to 4. Proposal: clamp in `engine.run_jobs`, or make
   `default_workers()` return `min(4, ...)` while the build runs.
3. **`engine.run_match` trusts any folder containing `summary.json` (lead).** A reused folder from a different wasm
   pair would be read silently. `nfs.evaluate.schedule` uses content-addressed folder names (wasm sha prefixes) plus
   `cell.json`, and refuses a mismatch. Proposal: same scheme in `engine.run_match`, or write and check `cell.json`.
4. **NFT1 telemetry keys (to B).** See `agents/H/TELEMETRY_FORMAT.md` section 1. Keep `invalid` and `nan` as explicit
   counters so the plumbing check can assert they are 0. Bound the line count; printf costs about 65 fuel/char
   (Agent A's measurement).
5. **Release profile strips lab (`strip_lab: true`) (lead).** Agent A's evidence
   (`agents/A/evidence/eq_strip_lab_1_vs_original.json`) shows NN_STRIP_LAB=1 changes gameplay vs the original
   (4/24 cells equal). The release build is therefore not teacher-equivalent. It must be measured
   (`eval_check.py equivalence --profile release` reports divergence) and should be judged like a candidate before
   shipping, not assumed neutral. The teacher-equivalence check uses `teacher_exact`.
