# C follow-up review, 2026-10-24

Assignment: source-only visibility/freshness audit and eight-byte intent proposal. The worker
previously authored D's Wave-2 modules and independently reviewed the prior C implementation;
this was not an independent review of D. Runtime is the inherited configured Codex session;
the exact underlying model identifier is unavailable to the worker. No new model run is invented.

Deliverable: [VISIBILITY.md](VISIBILITY.md) covers every observation feature family, including all
expansions and four objective slots, with SDK/glue/encoder/World source references, excluded inputs,
actual lazy history cadence and a concrete optional intent codebook within the existing eight bytes.

## Findings requiring integration decisions

1. **Belief dimensional mismatch (high).** Observation target has nine sectors, including far/unknown8;
   model default has eight. Recommend a nine-output head schema/default and regenerated untrained
   exports with parity tests. Do not silently discard sector8. No code change made here.
2. **Objective memory age omitted (medium).** `state`, `respawn_in` and `hp_left_frac` originate from
   legal World memory/inference, but carry no state/health observation age. `enemy_age` is a different
   event. Before fitting a model, either add explicit seen-age/source/confidence fields with a schema
   version/hash change, or clearly specify the current features as stale/predicted and evaluate the
   limitation. No hidden-state leak was found from these reads.
3. **History is opportunistic (medium).** No per-turn observe hook exists. Death totals count observed
   transitions and can miss death+respawn between admitted contexts. History features carry actual
   ages; do not call these exhaustive per-turn histories or exact death counts. Adding a tick affects
   teacher fuel and must be separately measured.
4. **Classification corrections (low).** `self.in_hot_zone` derives from remembered camp health;
   `ally.claim_dist` depends on remembered ally position plus static distance; `acts_before_me` is
   slot seniority, not queried execution priority. Capture sometimes refreshes own live fields beyond
   the schema's Bot-only descriptions. These are semantic/documentation issues, not privileged data.
5. **Context freshness (medium).** Shared context is the first admitted snapshot and is not rebuilt
   after actions/reveals; same-round observe is idempotent. Deterministic execution must recheck live
   legality. Training/runtime must use the same snapshot convention.
6. **No spare shared bits.** Bit63 is the APEX_EVENTS discriminator. The unchanged current protocol
   communicates assigned groups; roles stay local. An explicit-role extension can reuse codes119-125
   only in an opt-in protocol with <=112 groups and comprehensive compatibility/fuel checks.

## Commands/evidence actually checked

Read and cross-referenced `schemas/observation.json`, `bot/src/nn_obs{,_glue}.cpp`, `nn_obs.h`,
`nn_head.cpp`, `main.cpp`, Bot shared-memory and World visibility paths, installed
`sdk/cpp/{cambc,imports}.h`, `python/nfs/{obs,transforms}.py`, `models/config.py`, current model
configuration and A's saved runtime facts. Searched live sources for `nnobs::observe`; no per-turn
call site was present. Inspected actual SDK identity/visibility/self-only-gold/group-state comments
and import calls rather than relying on the schema labels alone.

No tests, new games, engine captures, training, external writes, browser control or submission were
run for this source-only audit. Existing native/synthetic encoder tests do not establish real
capture visibility. New real RawTurn fixtures and engine measurements remain **pending** due to
the official compiler permission blocker. Only these two C markdown files were created.
