# EXP-205 result — A valid existing formula cache was not used

MEASURED: LIVE109_RUNTIME_TARGET_SEARCHCACHE111.json has exact111 off0896a189 and matches original IssacR70 view/action/native crossing. Before formula selection,real fuel81636,nn_sg_need20776,search estimate28243. Cached hint1 matches requested1;cached group13 is alive(state0),avoid_until0 atR70. The existing SGAUTO cache is therefore valid,but current need+search estimate49019fits81636,so the code recomputes the formula reference before the underforecast first NN score.

This supports testing a conservative first-score reservation using an existing constant,not a map-specific rule. It does not prove the cached reference equals the newly recomputed best or that changing reservation preserves all ensemble decisions. Any such scheduling proposal needs explicit same-state observation,teacher-reference reporting,first successful-cost learning,and new full gates. No source policy patch or promotion in this diagnostic.
