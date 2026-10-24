# D integration instructions (lead-owned source changes)

Modules and schemas are implemented. All-off official Wasm rebuild is pending the compiler access blocker.
No original gameplay files were edited by D. These exact hook semantics should be applied by the lead.

1. Include `nn_strategy.h` in `bot.cpp` and `draft.cpp` (prefer under `#if NN_ANY_HEAD`).
2. In `Bot::score_groups`, immediately after `cap_objective(...)`, before `return best`:

```cpp
if constexpr (nncfg::mode(nncfg::H::objective) != nncfg::Mode::off)
    best = nns::objective(*this, best, best_need, best_score);
```

3. In the existing behaviour chain, insert a new `else if` immediately after the body of
   `go_home_if_needed()`, before `a2_join_fight` / rush / hunt. This preserves all emergency guards:

```cpp
} else if ([&]() {
    if constexpr (nncfg::mode(nncfg::H::strategy) != nncfg::Mode::off ||
                  nncfg::mode(nncfg::H::role) != nncfg::Mode::off ||
                  nncfg::mode(nncfg::H::value) != nncfg::Mode::off)
        return nns::act(*this);
    return false;
}()) {
    // A neural priority acted; exact execution and legality remained in Bot methods.
```

   If the lead prefers a named compile-time predicate/helper, that is equivalent. With all heads off
   the lambda returns the constant false and must optimize away. **Prove byte identity.**
   Candidate 0 means the remaining teacher chain unchanged; the teacher's branch is only known after
   it acts, so do not claim a precomputed branch label. Other choices attempt a priority; failure to
   act falls through to that same chain. `nns::act` returns false in shadow mode.

4. In the dead-turn branch (the existing `cap_chain(*this, nnt::Chain::dead)` site), add:

```cpp
if constexpr (nncfg::mode(nncfg::H::role) != nncfg::Mode::off ||
              nncfg::mode(nncfg::H::value) != nncfg::Mode::off)
    nns::reset_role();
```

   This invalidates the 20-round role option so respawn starts a fresh sampled option. The role head
   emits one decision per option start, never repeated forced records. Roles affect strategy priors,
   objective features, and (in role-only active ablations) deterministic priority attempts. No shared
   memory format or writes are added. Existing teacher camp claims still communicate assignments.

5. Pass the existing main-loop Bot by const reference through draft functions only when `NN_ANY_HEAD`:

```cpp
// draft.h (include nn_config.h, forward declare class Bot)
#if NN_ANY_HEAD
void play_draft(const Bot& bot);
#else
void play_draft();
#endif
```

   Apply the same preprocessor split to the definition in draft.cpp and `ml_draft_pick(size, bot)`;
   at the main.cpp call, `#if NN_ANY_HEAD play_draft(bot); #else play_draft(); #endif`.
   Avoid creating a dummy Bot, global constructor, or invalid reference for the draft.

6. After `cap_draft_pick(best)` inside ml_draft_pick, before `bc::draft::pick`, add:

```cpp
if constexpr (nncfg::mode(nncfg::H::draft_pick) != nncfg::Mode::off) {
    unsigned ours_mask = 0, theirs_mask = 0, taken_mask = 0;
    for (int c = 0; c < 12; ++c) if (taken[c]) taken_mask |= 1u << c;
    for (auto c : ours) if (static_cast<unsigned>(c) < 12) ours_mask |= 1u << static_cast<unsigned>(c);
    for (auto c : theirs) if (static_cast<unsigned>(c) < 12) theirs_mask |= 1u << static_cast<unsigned>(c);
    best = nns::draft_pick(bot, best, feat, taken_mask, ours_mask, theirs_mask,
                           static_cast<float>(j) / static_cast<float>(sz), first);
}
```

   The masks are deterministic bounded legality reductions. Melee composition features are built
   inside the module after admission. The teacher `feat` array is cached public map data; its first
   six entries are copied only after admission. The existing inherited draft network is unchanged.
   If the inherited network fails, the existing lineup-table whole-bot draft fallback remains.

7. All D candidate heads use F=24, a single `default` context (id 0), R=2.0; schema K maxima are
   draft12 / strategy6 / objective8 / role5. Regenerate untrained exports AFTER every schema lands;
   otherwise existing action hashes will correctly reject the new builders.

8. Fuel feature reservations in the module are conservative **unmeasured** provisional numbers:
   strategy2500, role2500, draft3000, objective1800+600K. The lead's engine probe must measure the
   complete builder, capture/encoder, and record path before accepting these as final budgets.
   No neural admission is nested inside an admitted builder (the runtime has one token).

Value outputs are bounded into a single auxiliary ranking signal and cached for the same round.
The combined strategy/objective path consumes it. A value-only profile exercises a critic auxiliary
head and has no independent action rule; do not advertise value-only play as a learned policy.
