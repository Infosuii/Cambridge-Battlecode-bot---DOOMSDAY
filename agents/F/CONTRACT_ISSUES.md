# Economy contract resolutions / integration requirements

1. F=20 for both bank and shop; regenerate the exported untrained models after schemas land. No registry/model
   changes were made by F.
2. Existing bank route fields support safe-nearest versus static-nearest reachable altar selection without adding
   expensive path builds. Arbitrary per-altar route ranking is intentionally outside this candidate version.
3. Shop candidate0 is the opaque complete unchanged teacher purchase plan, identified by its plan flag. Its item,
   count, cost, owned and projected-gold-after fields are zero sentinels. The patch removes the entire Wave1
   duplicate preview/capture pre-pass; no `build_for` allocation is added to the candidate builder. Alternatives are
   one guarded purchase or save. Failed immediate recheck means save. This changes shop schema semantics to v2.
4. Feature fuel constants in `nn_economy.h` require real engine measurement by the lead. Native parity cannot
   establish a fuel bound.
5. Shared encoder caching after action effects belongs to lead/runtime integration. These hooks read the current
   self state for candidate features but reuse the runtime's declared shared context snapshot.
