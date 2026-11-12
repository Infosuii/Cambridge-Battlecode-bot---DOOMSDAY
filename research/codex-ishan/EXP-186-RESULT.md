# EXP-186 result — Key generation/sort dominate cold field preparation

MEASURED: LIVE109_RUNTIME_TARGET_ORDERDETAIL111.json contains exact current111, off0896a189, enabled matching own view, action prefix and native actor0/R1. Charged spans: group-distance reserve339, slots412,pointers414,temporary key reserve337,key generation10610,sort5962,final order reserve218,copy2150. Small boundary overhead remains included in spans; no timing claim from an unmatched trace.

The crossing is inside key generation, not allocation. Existing EXP098 already implemented equivalent packed field order and pointer reuse on the old v92 source, with235491coordinate/262618key checks across46geometries. Its old release and later CPG port both failed wider safety despite successful local controls. EXP188 may test the exact same implementation on the materially changed111 source, with no claim that older results qualify it. No new numerical threshold, holdout or platform action.
