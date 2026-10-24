# D contract resolutions / remaining integration issues

1. **Strategy teacher branch exists only after acting.** Per A's issue 3, candidate zero is the unchanged
   remaining chain after emergency combat/win-bank/home, not a guessed precomputed branch. Alternatives
   are priority attempts with deterministic fallthrough. The actual branch remains captured afterwards.
2. **Draft needs an actual Bot reference.** The runtime requires `const Bot&` even though draft uses no
   shared context. The proposed gated draft signature passes main's existing Bot; no dummy object or
   invalid reference. Lead owns this integration.
3. **Value-only mode is auxiliary.** The critic meaningfully feeds strategy priors/features and objective
   features in combined configurations. A lone value head has no action policy. Explicit coverage docs
   must describe that dependency.
4. **Budget evidence is incomplete.** Builder reservations are provisional. Native tests are not fuel
   measurements. Official Wasm compilation was blocked by permission denial at time of D verification.
5. **Inherited draft fallback.** The active inherited-network path is hooked; its emergency lineup fallback
   remains deterministic if the original draft network/API throws. No speculative new draft action is
   inserted into an error fallback.
