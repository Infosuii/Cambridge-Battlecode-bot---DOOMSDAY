# EXP-183 result — Unguarded field-order preparation crosses the turn

MEASURED: LIVE109_RUNTIME_TARGET_FIELDDETAIL111.json is explicitly exact current111 despite the generic helper's historical filename prefix. Disabled diagnostic matches0896a189. The enabled diagnostic matches the selected development own view, action prefix and native actor0/R1 event. Field preparation begins R1 at11452 real fuel and ends R2 at91158:20294 charged fuel. The computed full search budget is42884 and the initial quota1000. nn_spent is0 at field entry and during the following searches.

Source111 bot.cpp:7010 calls prepare_field_order without room(), whereas the following search loop requires room(). Thus this observed crossing is preparation, not the suspected virtual NN budget. The next two searches each stay within R2. No source change or promotion follows from the diagnostic alone. EXP184 tests the existing room predicate on that preparation call.
