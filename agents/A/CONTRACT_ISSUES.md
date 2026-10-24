# Agent A contract issues / proposals

1. **nn_budget.h now depends on nn_registry.h (agent B, in progress).** Patch 01 includes `nn_budget.h` in bot.cpp,
   tsearch.cpp, world.cpp, draft.cpp and runtime_budget.h. With the live B header (12:24) a scratch build fails until
   `nn_registry.h` exists. My verification uses the lead stub saved in `agents/A/base_stubs/nn_budget.h` (frozen base =
   git HEAD bot/src + stubs + nn_teacher.*). Proposal: the lead re-runs `tools/audit_build_compare.py` on the integrated
   tree after B lands; I1 must still hold with B's real header and all heads off.
2. **Every `bot/src/*.cpp` is compiled (GLOB_RECURSE).** B's `nn_head.cpp` and any other nn TU are linked into every
   build including `teacher_exact`; their code must be GC-able (no exports, no dynamic init) or the I1 hash breaks.
   `nn_teacher.cpp` was verified to add zero bytes.
3. **heads.json `strategy`: "0 = teacher order".** The teacher chain decides by acting, so its choice is not available
   before the chain runs; candidate 0 must be "run the chain unchanged" and the label is the captured branch
   (`nn_teacher_access::turn()`, available after the turn). D should not expect a pre-computed teacher behaviour.
4. **heads.json call sites that are compiled out in the original:** `combat` lists `position_and_attack` (APEX_POSITION 0)
   and `try_burst_kill` (APEX_BURST 0); `engage` lists `team_decide` (never called: APEX_TFC 0, NOVA_PACK_C 0); `ward`
   lists `drop_ward` (APEX_WARDS 0). Hooks there would add new behaviour rather than re-rank a teacher decision.
   Active alternatives are in `decision_inventory.json` (cast_on_enemy, engage_exec, caster_micro, deny_tribute,
   ward_ahead, ward_reveal, reveal_bush_camp).
5. **Release requirement vs teacher equivalence.** USER_REQUEST 5.8 asks the release to drop inherited lab code. In this
   build the lab does no logging (cn_log/pol_log are compiled out); stripping removes exports, inert checks and the
   zero-weight learner, and changes behaviour on 20/24 fixture cells (fuel). Proposal: `release`/`teacher_exact` keep
   `NN_STRIP_LAB=0`; a stripped build is evaluated as a separate candidate (H), never labelled "teacher".
6. **kFuelCredit cannot credit savings.** `teacher_left()` adds neural spend back; a variant that uses *less* fuel than
   the teacher (e.g. stripped lab) cannot be made neutral this way.
7. **Capture switch names.** nn_teacher.h derives `nnt::kObjective/kBank/...` from `nncfg::mode`. If B renames
   `nncfg::H` values, nn_teacher.h needs the same rename (compile error, not silent).
