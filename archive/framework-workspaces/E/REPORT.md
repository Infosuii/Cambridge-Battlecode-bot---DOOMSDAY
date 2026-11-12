# Agent E: tactical decision modules (Wave 2)

Implemented in the configured Codex child-agent runtime. The agent tool did not offer Opus 5.5; the exact inherited
model identifier was not exposed. No training, submission, browser/desktop control, or external writes occurred.
No original gameplay sources were edited by this worker. Integration is staged in `apply_hooks.py` for the lead.

## Delivered

- `bot/src/nn_tactics.{h,cpp}`: bounded pure candidate builders, SDK-aware tactical glue, teacher-first stable IDs,
  legal masks, four movement contexts, target intent and spell/keep options, final fight/run/keep verdict,
  ward placement/keep options, and a planning leaf residual capped at four leaves per real turn.
- `schemas/heads/{move,combat,engage,ward,ts_leaf}.json`: F=24 for candidate heads, F=8 for the leaf. Candidate
  contexts have four slots; leaf context is zero. Candidate residual bound is2, leaf bound25 in teacher-value units.
- `python/nfs/heads/tactics.py`: Python twin of typed raw feature normalization, mask/ID/prior handling and bounded
  belief feature construction. Feature extraction uses only the admitted candidate set and current legal observation.
- `tests/cpp/test_tactics_parity.cpp` and `tests/python/test_tactics_parity.py`: synthetic native/Python parity.
- `archive/agents/E/apply_hooks.py`: reviewable, idempotent, workspace-only integration script for the lead.

## Hook coverage

| Area | Active original hook | Effect |
|---|---|---|
| Route/waypoint and chase | `follow_field`, immediately after `cap_steps` | Reorders already narrowed downhill endpoints; original move-attempt fallthrough remains. |
| Retreat | `retreat_from`, after original safe candidate sorting | Reorders original improving endpoints; exact movement execution remains. |
| Spacing | `kite_step`, after teacher endpoint selected | Admitted generator of legal neighbor endpoints plus hold; teacher remains candidate0. |
| Escape mobility | `dash_away`, after original candidate sorting | Ranks original top four landings, preserving spell execution and fallback loop. |
| Target priority | `handle_enemies`, after `cap_fight_final` | Ranks currently visible, live target intents; attack/spell dispatch checks exact range/readiness. |
| Spell/mobility timing | `cast_on_enemy`, after `cap_cast` | Ranks teacher spell/striking dash, other legal offensive slot and keep-spell; original aim/use paths remain. |
| Fight/run/keep | `handle_enemies`, after final teacher verdict | Learned verdict among deterministically masked options; emergency retreat and unmodelled threat restrictions remain. |
| Ward timing | `ward_ahead`, after `cap_ward` | Teacher placement or keep ward. |
| Ward placement | `ward_reveal`, after cooldown check | Original top three placements or keep ward; original placement attempts remain. |
| Ward camp reveal | `reveal_bush_camp`, before placement | Teacher reveal tile or keep ward; no hidden camp health/position query is added. |
| Short sequence planning | `tactical_decide`, after each completed teacher playout evaluation | Adds learned bounded endpoint-value residual to fight/run plans. The active path is used, not compiled-out tactical_search. |
| Opponent/fog model | Same movement hooks, gated by move OR belief | Nine cached canonical-sector outputs become move feature23. Belief-only has conservative deterministic rerank when an alternative's bounded risk is more than0.5 below teacher. Shadow returns0 and preserves teacher choice. |

The movement belief feature is a **prediction** from legally observed history, never a future observation. Its sector
anchor is `nnh::context_position`, i.e. the cached observation position rather than the champion's later live position.
Belief values are computed before acquiring the movement admission token to avoid nested-token corruption.

## Safety and semantics

- Candidate0 is the already-computed teacher choice; all tie priors favor index0. Alternatives share a-0.05 prior.
- No per-decision heap allocation, exhaustive sorting, world search, bush labeling or replay information in new modules.
- Feature construction follows `nnh::admit`; a small bounded copy of teacher coordinates/scores at a hook is candidate
  plumbing. Local spacing endpoints are generated only after admission.
- Candidate kind/context disambiguates stable IDs: tile code, visible target handle, spell slot+1, or verdict+1.
- New spell alternatives are live-readiness checked **before** the decision, and target alternatives are visibility/
  liveness checked before inclusion. A chosen spell is not silently replaced after NFS1 logs it.
- Learned target and spell choices are action **intents**. The existing deterministic executor can refuse a hidden
  obstruction or attempt another original movement/ward candidate. These execution outcomes are not currently logged
  as separate NFS1 action-completion records.
- New fight alternatives are forbidden with no target, hp<25%, TTD<=1, omitted reachable enemies, split linked units,
  or hot-zone camp threats. A teacher emergency retreat (hp<15% or TTD<=1) cannot be cleared.
- All-off `nn_tactics.cpp` compiles to an object with only empty section symbols. No runtime initializers or exports.

## Commands and results

With `PYTHONPATH=ROOT/python`, `TMP=TEMP=ROOT/artifacts/tmp` and the configured native compiler on PATH:

```
python archive/agents/E/write_schemas.py
python -m unittest tests.python.test_tactics_parity -v
g++ -std=c++20 -fsyntax-only -Wno-attributes -I./sdk/cpp artifacts/tmp/E2/syntax/nn_tactics.cpp artifacts/tmp/E2/syntax/bot.cpp artifacts/tmp/E2/syntax/tsearch.cpp
g++ -std=c++20 -O2 -c bot/src/nn_tactics.cpp -o artifacts/tmp/E2/tactics_off.o
nm artifacts/tmp/E2/tactics_off.o
```

Synthetic tests: **6/6 pass**. This includes96 candidate shape/context combinations per four-head suite (0,1,2,8,16,19
candidates, truncation at16),30 random leaf vectors, all mask/ID/prior/feature fields, alternative permutation,
teacher-illegal preservation, NaN/Inf preservation for runtime rejection, and1369 canonical sector/bounded-logit cases
against `nfs.transforms.sector_of`. Feature arrays are bit-exact against the native C++ driver.

The staged hook patch was applied twice to scratch successfully (idempotence). Native syntax checks passed both
before and after the final belief extension, with one pre-existing warning in disabled `farm` code (modulo zero
squads). For the final check only, the agreed `nnh::context_position` declaration was appended to the scratch header;
the implementation still requires the lead's runtime integration. This was a syntax check, not a linked engine build.

## Limits / lead verification required

- Official Wasm build, exact teacher hash, engine smoke/fuel/invalid-action checks are **not claimed** here. The lead
  reported installed WASI compiler permission failure and owns the engine verification/integration milestone.
- Builder feature allowances remain conservative provisional literals until engine fuel measurements: move1200+950K,
  local spacing12000, target8000, cast5000, engage4000, ward1400+600K, leaf2200. They include bounded entity loops;
  shared encoder/model costs are admitted separately by runtime. Belief-only endpoint feature work is charged to belief.
- Runtime must consume the preadmission token in `nnh::leaf` (lead agreed to implement this).
- The original runtime emits no NFS1 leaf-feature/target records. Fitting ts_leaf later needs a documented supervised
  endpoint-label collection path. This worker has not claimed that archival summaries provide tactical action labels.
- Pure candidate parity tests cover raw feature normalization/masks/prior/IDs; they do not prove engine-derived raw
  feature correctness. The lead's engine replay/smoke review must validate glue on real legal observations.
