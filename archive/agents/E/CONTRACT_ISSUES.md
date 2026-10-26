# E integration issues

1. **Resolved by agreement, awaiting lead integration:** `nnh::leaf` must honor the `nnh::admit` token and meter the
   admitted feature construction, as `decide` does. E calls admit before leaf features and then `nnh::leaf`.
2. **Resolved by agreement, awaiting lead integration:** `nnh::context_position(int&,int&)` returns the cached RawTurn
   self position only when context is ready. Belief sectors must use this anchor after own movement.
3. **Schema consistency:** observation.json specifies9 belief sectors (eight octants plus far). The initial model
   config specified8. The lead agreed to align it to9 and own the belief schema/Python training-target twin.
4. **Training records:** runtime scalar leaf/value heads do not currently emit candidate-style feature/target records.
   ts_leaf fitting needs supported endpoint supervision. Tactical action intent records do not separately log SDK
   executor refusal/fallthrough; later on-policy analysis must treat these as intent/options or add execution records.
5. **Fuel:** builder constants are provisional pending official engine measurements, not claimed engine measurements.
6. **Integration ownership:** original source hooks are staged in apply_hooks.py and have not been applied to bot/src
   by this worker. Lead must rebuild all profiles and re-check exact teacher Wasm after applying them.
