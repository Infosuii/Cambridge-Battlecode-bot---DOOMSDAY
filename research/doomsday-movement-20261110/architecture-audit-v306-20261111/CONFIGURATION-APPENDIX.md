# v306 complete source macro inventory

[Project home](../../../README.md) · [Architecture overview](../../../docs/architecture.md) · [Results](../../../docs/RESULTS.md)

Generated from the release-target compiler preprocessing of all 13 C++ translation units, and the 44 source files. No bot source was edited.

Source SHA-256: `7f3dadb1d3876137ddd4606f340eb64f1fed67c9e4d6a70defa93c2c59a75d3e`. Release Wasm SHA-256: `9e335df552156d37ff5b3e0befafcbfe98c56d0a63004cab4335b20efefaab32`.

These are named source macros, not a count of independent features. They include feature switches, numeric tuning values, bit masks, weight lists and helper macros. A value of 1 does not prove that a feature executes; earlier returns, runtime settings and other gates still apply. Undefined means absent from that translation unit's final macro environment, not necessarily absent from every compiled code path: local macros can be defined and later undefined.

The bot column is the main decision file. Exceptions list every distinct value in the other translation units. Values are literal preprocessor replacements; aliases and C++ expressions are not numerically evaluated here. Refer to BOT-ARCHITECTURE.md for execution status and interactions.

| Macro | Main bot.cpp value | Other translation-unit differences | Source declaration(s) |
|---|---|---|---|
| `A2RET` | `undefined` | same | [tsearch.cpp:793](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L793), [tsearch.cpp:803](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L803), [tsearch.cpp:809](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L809) |
| `A2_ALONE` | `1` | neural_policy.cpp: undefined | [common.h:131](../../../bots/mainline/v306AltarPressureReach/src/common.h#L131), [common.h:142](../../../bots/mainline/v306AltarPressureReach/src/common.h#L142) |
| `A2_ALTARFIX` | `3` | neural_policy.cpp: undefined | [common.h:427](../../../bots/mainline/v306AltarPressureReach/src/common.h#L427), [common.h:1328](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1328) |
| `A2_AMBUSH` | `0` | neural_policy.cpp: undefined | [common.h:1347](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1347) |
| `A2_AMBUSH_FROM` | `60` | neural_policy.cpp: undefined | [common.h:1353](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1353) |
| `A2_AMBUSH_SLOT` | `1` | neural_policy.cpp: undefined | [common.h:1350](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1350) |
| `A2_APPROACHFIX` | `1` | neural_policy.cpp: undefined | [common.h:429](../../../bots/mainline/v306AltarPressureReach/src/common.h#L429), [common.h:1310](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1310) |
| `A2_ASSESS` | `0` | neural_policy.cpp: undefined | [common.h:1245](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1245) |
| `A2_ASSESS_MARGIN` | `5.0f` | neural_policy.cpp: undefined | [common.h:1248](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1248) |
| `A2_BELIEF` | `0` | neural_policy.cpp: undefined | [common.h:1383](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1383) |
| `A2_BELIEF_AGE` | `3` | neural_policy.cpp: undefined | [common.h:1386](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1386) |
| `A2_BRIDGES` | `1` | neural_policy.cpp: undefined | [common.h:428](../../../bots/mainline/v306AltarPressureReach/src/common.h#L428), [common.h:1313](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1313) |
| `A2_BURST2` | `0` | neural_policy.cpp: undefined | [common.h:1341](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1341) |
| `A2_BURST2_K` | `1.0f` | neural_policy.cpp: undefined | [common.h:1344](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1344) |
| `A2_BURST_HOLD` | `0` | neural_policy.cpp: undefined | [common.h:1239](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1239) |
| `A2_BUSH_FAST` | `1` | neural_policy.cpp: undefined | [common.h:432](../../../bots/mainline/v306AltarPressureReach/src/common.h#L432), [common.h:1200](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1200) |
| `A2_CAMPNET` | `0` | neural_policy.cpp: undefined | [common.h:419](../../../bots/mainline/v306AltarPressureReach/src/common.h#L419), [common.h:621](../../../bots/mainline/v306AltarPressureReach/src/common.h#L621) |
| `A2_CAMPWATCH` | `1` | neural_policy.cpp: undefined | [common.h:24](../../../bots/mainline/v306AltarPressureReach/src/common.h#L24), [common.h:573](../../../bots/mainline/v306AltarPressureReach/src/common.h#L573) |
| `A2_CFG_DEFAULT` | `1` | deny.cpp, economy.cpp, episode.cpp, fight.cpp, main.cpp, neural_policy.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [a2stack.h:9](../../../bots/mainline/v306AltarPressureReach/src/a2stack.h#L9) |
| `A2_CFG_S3` | `14377` | neural_policy.cpp: undefined | [common.h:694](../../../bots/mainline/v306AltarPressureReach/src/common.h#L694) |
| `A2_CFG_S4` | `12297` | neural_policy.cpp: undefined | [common.h:697](../../../bots/mainline/v306AltarPressureReach/src/common.h#L697) |
| `A2_CFG_S5` | `14377` | neural_policy.cpp: undefined | [common.h:700](../../../bots/mainline/v306AltarPressureReach/src/common.h#L700) |
| `A2_CHECK` | `0` | neural_policy.cpp: undefined | [common.h:1416](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1416) |
| `A2_CMDR` | `3` | neural_policy.cpp: undefined | [common.h:127](../../../bots/mainline/v306AltarPressureReach/src/common.h#L127), [common.h:145](../../../bots/mainline/v306AltarPressureReach/src/common.h#L145) |
| `A2_CMICRO_FAST` | `1` | neural_policy.cpp: undefined | [common.h:434](../../../bots/mainline/v306AltarPressureReach/src/common.h#L434), [common.h:1206](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1206) |
| `A2_CM_CONV` | `0.70f` | neural_policy.cpp: undefined | [common.h:160](../../../bots/mainline/v306AltarPressureReach/src/common.h#L160) |
| `A2_CM_FIGHT` | `std::clamp(0.55f + 0.05f * lab::knobs[59], 0.5f, 0.9f)` | neural_policy.cpp: undefined | [common.h:128](../../../bots/mainline/v306AltarPressureReach/src/common.h#L128), [common.h:148](../../../bots/mainline/v306AltarPressureReach/src/common.h#L148) |
| `A2_CM_FLEE` | `0.40f` | neural_policy.cpp: undefined | [common.h:151](../../../bots/mainline/v306AltarPressureReach/src/common.h#L151) |
| `A2_CM_HYST` | `0.10f` | neural_policy.cpp: undefined | [common.h:154](../../../bots/mainline/v306AltarPressureReach/src/common.h#L154) |
| `A2_CM_LOWHP` | `0.15f` | neural_policy.cpp: undefined | [common.h:157](../../../bots/mainline/v306AltarPressureReach/src/common.h#L157) |
| `A2_CM_UNTIL` | `2000` | neural_policy.cpp: undefined | [common.h:163](../../../bots/mainline/v306AltarPressureReach/src/common.h#L163) |
| `A2_CN_BASE` | `1.0f` | neural_policy.cpp: undefined | [common.h:627](../../../bots/mainline/v306AltarPressureReach/src/common.h#L627) |
| `A2_CN_SHARP` | `4.0f` | neural_policy.cpp: undefined | [common.h:624](../../../bots/mainline/v306AltarPressureReach/src/common.h#L624) |
| `A2_CN_W` | `0.0f` | neural_policy.cpp: undefined | [common.h:630](../../../bots/mainline/v306AltarPressureReach/src/common.h#L630) |
| `A2_CW_LEAD` | `12` | neural_policy.cpp: undefined | [common.h:576](../../../bots/mainline/v306AltarPressureReach/src/common.h#L576) |
| `A2_CW_MEM` | `150` | neural_policy.cpp: undefined | [common.h:579](../../../bots/mainline/v306AltarPressureReach/src/common.h#L579) |
| `A2_CW_MULT` | `1.6f` | neural_policy.cpp: undefined | [common.h:582](../../../bots/mainline/v306AltarPressureReach/src/common.h#L582) |
| `A2_DANGERMAP` | `0` | neural_policy.cpp: undefined | [common.h:1338](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1338) |
| `A2_DASHX` | `0` | neural_policy.cpp: undefined | [common.h:1332](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1332) |
| `A2_DISENGAGE` | `0` | neural_policy.cpp: undefined | [common.h:1251](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1251) |
| `A2_DIS_MARGIN` | `0.15f` | neural_policy.cpp: undefined | [common.h:1254](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1254) |
| `A2_DPLAN` | `0` | neural_policy.cpp: undefined | [common.h:605](../../../bots/mainline/v306AltarPressureReach/src/common.h#L605) |
| `A2_DP_LATE` | `40` | neural_policy.cpp: undefined | [common.h:614](../../../bots/mainline/v306AltarPressureReach/src/common.h#L614) |
| `A2_DP_MULT` | `3.0f` | neural_policy.cpp: undefined | [common.h:611](../../../bots/mainline/v306AltarPressureReach/src/common.h#L611) |
| `A2_DP_ROLLOUTS` | `40` | neural_policy.cpp: undefined | [common.h:617](../../../bots/mainline/v306AltarPressureReach/src/common.h#L617) |
| `A2_DP_UNTIL` | `200` | neural_policy.cpp: undefined | [common.h:608](../../../bots/mainline/v306AltarPressureReach/src/common.h#L608) |
| `A2_ENEMY_NET` | `0` | neural_policy.cpp: undefined | [common.h:1263](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1263) |
| `A2_FASTGRP` | `1` | neural_policy.cpp: undefined | [common.h:1319](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1319) |
| `A2_FAST_AMBUSH` | `1` | neural_policy.cpp: undefined | [common.h:433](../../../bots/mainline/v306AltarPressureReach/src/common.h#L433), [common.h:1203](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1203) |
| `A2_FEATVEC` | `1` | neural_policy.cpp: undefined | [common.h:14](../../../bots/mainline/v306AltarPressureReach/src/common.h#L14) |
| `A2_FIELDFIRST` | `0` | neural_policy.cpp: undefined | [common.h:1316](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1316) |
| `A2_FIELD_MARGIN` | `3000` | neural_policy.cpp: undefined | [common.h:685](../../../bots/mainline/v306AltarPressureReach/src/common.h#L685) |
| `A2_FOG` | `1` | neural_policy.cpp: undefined | [common.h:133](../../../bots/mainline/v306AltarPressureReach/src/common.h#L133), [common.h:553](../../../bots/mainline/v306AltarPressureReach/src/common.h#L553) |
| `A2_FOG_AGE` | `10` | neural_policy.cpp: undefined | [common.h:556](../../../bots/mainline/v306AltarPressureReach/src/common.h#L556) |
| `A2_FOG_GEMS` | `15` | neural_policy.cpp: undefined | [common.h:565](../../../bots/mainline/v306AltarPressureReach/src/common.h#L565) |
| `A2_FOG_HP` | `0.8f` | neural_policy.cpp: undefined | [common.h:562](../../../bots/mainline/v306AltarPressureReach/src/common.h#L562) |
| `A2_FOG_MARGIN` | `2` | neural_policy.cpp: undefined | [common.h:568](../../../bots/mainline/v306AltarPressureReach/src/common.h#L568) |
| `A2_FOG_R` | `4` | neural_policy.cpp: undefined | [common.h:559](../../../bots/mainline/v306AltarPressureReach/src/common.h#L559) |
| `A2_FUELLOG` | `0` | neural_policy.cpp: undefined | [common.h:1209](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1209) |
| `A2_GAPDASH` | `3` | neural_policy.cpp: undefined | [common.h:430](../../../bots/mainline/v306AltarPressureReach/src/common.h#L430), [common.h:1298](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1298) |
| `A2_GATE_FROM` | `500` | neural_policy.cpp: undefined | [common.h:414](../../../bots/mainline/v306AltarPressureReach/src/common.h#L414) |
| `A2_GATE_JOB` | `0` | neural_policy.cpp: undefined | [common.h:412](../../../bots/mainline/v306AltarPressureReach/src/common.h#L412) |
| `A2_GOV` | `1` | neural_policy.cpp: undefined | [common.h:435](../../../bots/mainline/v306AltarPressureReach/src/common.h#L435), [common.h:1212](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1212) |
| `A2_GOV_WALK` | `A2_GOV` | neural_policy.cpp: undefined | [common.h:1215](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1215) |
| `A2_GOV_WARD` | `A2_GOV` | neural_policy.cpp: undefined | [common.h:1218](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1218) |
| `A2_GROUP_UNTIL` | `0` | neural_policy.cpp: undefined | [common.h:1279](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1279) |
| `A2_HIDEREC` | `0` | neural_policy.cpp: undefined | [common.h:1307](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1307) |
| `A2_HOR` | `2` | neural_policy.cpp: undefined | [common.h:97](../../../bots/mainline/v306AltarPressureReach/src/common.h#L97), [common.h:135](../../../bots/mainline/v306AltarPressureReach/src/common.h#L135) |
| `A2_HORK` | `1` | neural_policy.cpp: undefined | [common.h:130](../../../bots/mainline/v306AltarPressureReach/src/common.h#L130), [common.h:205](../../../bots/mainline/v306AltarPressureReach/src/common.h#L205) |
| `A2_HPVAL2` | `0` | neural_policy.cpp: undefined | [common.h:1266](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1266) |
| `A2_HYB` | `3` | neural_policy.cpp: undefined | [common.h:111](../../../bots/mainline/v306AltarPressureReach/src/common.h#L111) |
| `A2_KITFIX` | `31` | neural_policy.cpp: undefined | [common.h:426](../../../bots/mainline/v306AltarPressureReach/src/common.h#L426), [common.h:1335](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1335) |
| `A2_KNOBS` | `-0.2324,0.0063,0.0843,-0.2104,-0.1657,-1.1852,1.2152,0.2588,0.8167,1.0175,1.4503,-0.7013,1.6018,-0.2131,0.3883,1.2392,0.0052,-0.5969,0.7784,-1.1362,1.1544,-0.1137,0.4351,-0.0003,-0.4823,0.7086,0.8082,0.4128,-0.5672,0.1350,-0.7099,0.2795,0.9522,-0.2219,-0.0928,0.2524,-1.6983,0.6817,-0.1998,0.5488,0.3169,2.0716,1.0775,-0.2822,1.2772,-0.5667,-0.9572,1.5081,-0.3549,0.3643,-0.5579,-0.2293,1.2729,-0.2749,1.5455,0.8006,-1.6255,0.5251,-0.9368,-0.0538,-0.0849,0.4845,-0.0464,-0.7602,-0.0164,-0.2232,-0.1354,0.6741,0.5647,-0.3054,-0.3439,0.1171,0.4163,-0.3921,0.4346,0.6407,-0.1769,0.2024,0.8318,1.0071,-0.0116,0.0373,0.6371,-0.4819,0.0910,-0.3740,0.3058,0.6491,0.4807,-0.5459,-1.0419,-0.8667,-0.5335,-0.4068,-0.1135,-0.2327` | neural_policy.cpp: undefined | [common.h:425](../../../bots/mainline/v306AltarPressureReach/src/common.h#L425) |
| `A2_LAB` | `1` | neural_policy.cpp: undefined | [common.h:424](../../../bots/mainline/v306AltarPressureReach/src/common.h#L424), [learner.h:16](../../../bots/mainline/v306AltarPressureReach/src/learner.h#L16) |
| `A2_LADFIT` | `1` | neural_policy.cpp: undefined | [common.h:108](../../../bots/mainline/v306AltarPressureReach/src/common.h#L108) |
| `A2_LANCH2` | `1` | neural_policy.cpp: undefined | [common.h:129](../../../bots/mainline/v306AltarPressureReach/src/common.h#L129), [common.h:208](../../../bots/mainline/v306AltarPressureReach/src/common.h#L208) |
| `A2_LC_HI` | `0.75f` | neural_policy.cpp: undefined | [common.h:211](../../../bots/mainline/v306AltarPressureReach/src/common.h#L211) |
| `A2_LC_LO` | `0.25f` | neural_policy.cpp: undefined | [common.h:214](../../../bots/mainline/v306AltarPressureReach/src/common.h#L214) |
| `A2_MAP_PROFILE` | `0` | neural_policy.cpp: undefined | [common.h:1371](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1371) |
| `A2_MICLOG` | `0` | neural_policy.cpp: undefined | [common.h:1295](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1295) |
| `A2_MID_W` | `1.0f` | neural_policy.cpp: undefined | [common.h:1291](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1291) |
| `A2_MLDRAFT` | `0` | draft.cpp: 1; neural_policy.cpp: undefined | [common.h:422](../../../bots/mainline/v306AltarPressureReach/src/common.h#L422), [common.h:635](../../../bots/mainline/v306AltarPressureReach/src/common.h#L635), [draft.cpp:341](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L341) |
| `A2_MLPLAN` | `0` | neural_policy.cpp: undefined | [common.h:639](../../../bots/mainline/v306AltarPressureReach/src/common.h#L639) |
| `A2_MOVENET` | `0` | neural_policy.cpp: undefined | [common.h:1377](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1377) |
| `A2_NN` | `11` | neural_policy.cpp: undefined | [common.h:706](../../../bots/mainline/v306AltarPressureReach/src/common.h#L706) |
| `A2_NNREC` | `0` | neural_policy.cpp: undefined | [common.h:718](../../../bots/mainline/v306AltarPressureReach/src/common.h#L718) |
| `A2_NNREC_LAYOUT` | `2` | neural_policy.cpp: undefined | [common.h:715](../../../bots/mainline/v306AltarPressureReach/src/common.h#L715) |
| `A2_NN_BEH` | `0` | neural_policy.cpp: undefined | [common.h:664](../../../bots/mainline/v306AltarPressureReach/src/common.h#L664), [nnrec.cpp:638](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L638) |
| `A2_NN_ENS` | `2` | neural_policy.cpp: undefined | [common.h:667](../../../bots/mainline/v306AltarPressureReach/src/common.h#L667) |
| `A2_NN_EPS` | `undefined` | same | [nn_infer.h:574](../../../bots/mainline/v306AltarPressureReach/src/nn_infer.h#L574) |
| `A2_NN_EPSQ` | `undefined` | nnrec.cpp: 0 | [nn_infer.h:343](../../../bots/mainline/v306AltarPressureReach/src/nn_infer.h#L343) |
| `A2_NN_FAST` | `1` | neural_policy.cpp: undefined | [common.h:658](../../../bots/mainline/v306AltarPressureReach/src/common.h#L658) |
| `A2_NN_FIELDS_FIRST` | `1` | neural_policy.cpp: undefined | [common.h:688](../../../bots/mainline/v306AltarPressureReach/src/common.h#L688) |
| `A2_NN_LAYOUT` | `2` | neural_policy.cpp: undefined | [common.h:712](../../../bots/mainline/v306AltarPressureReach/src/common.h#L712) |
| `A2_NN_LAZY` | `1` | neural_policy.cpp: undefined | [common.h:673](../../../bots/mainline/v306AltarPressureReach/src/common.h#L673) |
| `A2_NN_LAZY_FLOOR` | `undefined` | nnrec.cpp: 8000 | [nnrec.cpp:810](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L810) |
| `A2_NN_LAZY_TTL` | `undefined` | nnrec.cpp: 2 | [nnrec.cpp:813](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L813) |
| `A2_NN_LIVE` | `1` | neural_policy.cpp: undefined | [common.h:670](../../../bots/mainline/v306AltarPressureReach/src/common.h#L670) |
| `A2_NN_MACRO` | `1` | neural_policy.cpp: undefined | [common.h:655](../../../bots/mainline/v306AltarPressureReach/src/common.h#L655), [common.h:709](../../../bots/mainline/v306AltarPressureReach/src/common.h#L709) |
| `A2_NN_NNUE` | `1` | neural_policy.cpp: undefined | [common.h:676](../../../bots/mainline/v306AltarPressureReach/src/common.h#L676) |
| `A2_NN_NNUE_CEIL` | `undefined` | nnrec.cpp: 70000 | [nnrec.cpp:816](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L816), [nnrec.cpp:818](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L818) |
| `A2_NN_Q16` | `1` | neural_policy.cpp: undefined | [common.h:679](../../../bots/mainline/v306AltarPressureReach/src/common.h#L679) |
| `A2_NN_RESERVE` | `undefined` | nnrec.cpp: 1000 | [nnrec.cpp:631](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L631), [nnrec.cpp:1725](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L1725) |
| `A2_NN_RL_KEEP` | `undefined` | same | [nnrec.cpp:700](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L700) |
| `A2_NN_RL_T` | `undefined` | same | [nnrec.cpp:697](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L697) |
| `A2_NN_SGAUTO` | `1` | neural_policy.cpp: undefined | [common.h:682](../../../bots/mainline/v306AltarPressureReach/src/common.h#L682) |
| `A2_NN_TTL` | `undefined` | nnrec.cpp: 1000000 | [nnrec.cpp:635](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L635) |
| `A2_NN_VALID` | `1` | neural_policy.cpp: undefined | [common.h:661](../../../bots/mainline/v306AltarPressureReach/src/common.h#L661), [nnrec.cpp:641](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L641) |
| `A2_NN_XF` | `undefined` | nnrec.cpp: 0 | [nnrec.cpp:14](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L14) |
| `A2_NN_ZFRESH` | `undefined` | nnrec.cpp: 0 | [nnrec.cpp:659](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L659) |
| `A2_NN_ZSTART` | `undefined` | nnrec.cpp: 0 | [nnrec.cpp:656](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L656) |
| `A2_PAIRHUNT` | `1` | neural_policy.cpp: undefined | [common.h:121](../../../bots/mainline/v306AltarPressureReach/src/common.h#L121), [common.h:166](../../../bots/mainline/v306AltarPressureReach/src/common.h#L166) |
| `A2_PH_FROM` | `60` | neural_policy.cpp: undefined | [common.h:169](../../../bots/mainline/v306AltarPressureReach/src/common.h#L169) |
| `A2_PH_GEMS` | `30` | neural_policy.cpp: undefined | [common.h:181](../../../bots/mainline/v306AltarPressureReach/src/common.h#L181) |
| `A2_PH_HP` | `std::clamp(0.55f + 0.1f * lab::knobs[52], 0.3f, 0.9f)` | neural_policy.cpp: undefined | [common.h:123](../../../bots/mainline/v306AltarPressureReach/src/common.h#L123), [common.h:178](../../../bots/mainline/v306AltarPressureReach/src/common.h#L178) |
| `A2_PH_RANGE` | `(12 + static_cast<int>(std::lround(4.0f * lab::knobs[51])))` | neural_policy.cpp: undefined | [common.h:122](../../../bots/mainline/v306AltarPressureReach/src/common.h#L122), [common.h:175](../../../bots/mainline/v306AltarPressureReach/src/common.h#L175) |
| `A2_PH_UNTIL` | `450` | neural_policy.cpp: undefined | [common.h:172](../../../bots/mainline/v306AltarPressureReach/src/common.h#L172) |
| `A2_PLAN` | `0` | neural_policy.cpp: undefined | [common.h:1260](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1260) |
| `A2_POLICY` | `0` | neural_policy.cpp: undefined | [common.h:1269](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1269) |
| `A2_POOL` | `1` | neural_policy.cpp: undefined | [common.h:13](../../../bots/mainline/v306AltarPressureReach/src/common.h#L13) |
| `A2_RACE` | `0` | neural_policy.cpp: undefined | [common.h:1356](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1356) |
| `A2_RACE_LEAD` | `30.0f` | neural_policy.cpp: undefined | [common.h:1359](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1359) |
| `A2_RAID` | `1` | neural_policy.cpp: undefined | [common.h:124](../../../bots/mainline/v306AltarPressureReach/src/common.h#L124), [common.h:184](../../../bots/mainline/v306AltarPressureReach/src/common.h#L184) |
| `A2_RD_EXP` | `0.5f` | neural_policy.cpp: undefined | [common.h:193](../../../bots/mainline/v306AltarPressureReach/src/common.h#L193) |
| `A2_RD_FROM` | `100` | neural_policy.cpp: undefined | [common.h:187](../../../bots/mainline/v306AltarPressureReach/src/common.h#L187) |
| `A2_RD_MULT` | `std::exp(0.3f * lab::knobs[54])` | neural_policy.cpp: undefined | [common.h:125](../../../bots/mainline/v306AltarPressureReach/src/common.h#L125), [common.h:196](../../../bots/mainline/v306AltarPressureReach/src/common.h#L196) |
| `A2_RD_QUIET` | `30` | neural_policy.cpp: undefined | [common.h:190](../../../bots/mainline/v306AltarPressureReach/src/common.h#L190) |
| `A2_RESETFIX` | `1` | neural_policy.cpp: undefined | [common.h:1304](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1304) |
| `A2_ROUTE_FUEL` | `55000` | neural_policy.cpp: undefined | [common.h:420](../../../bots/mainline/v306AltarPressureReach/src/common.h#L420), [common.h:1890](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1890) |
| `A2_RTSW` | `1` | neural_policy.cpp: undefined | [common.h:114](../../../bots/mainline/v306AltarPressureReach/src/common.h#L114) |
| `A2_SHIELDLATE` | `1` | neural_policy.cpp: undefined | [common.h:431](../../../bots/mainline/v306AltarPressureReach/src/common.h#L431), [common.h:1301](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1301) |
| `A2_SNAP` | `4` | neural_policy.cpp: undefined | [common.h:436](../../../bots/mainline/v306AltarPressureReach/src/common.h#L436), [common.h:1221](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1221) |
| `A2_SOLE_FROM` | `500` | neural_policy.cpp: undefined | [common.h:417](../../../bots/mainline/v306AltarPressureReach/src/common.h#L417) |
| `A2_SOLE_GEM` | `1` | neural_policy.cpp: undefined | [common.h:411](../../../bots/mainline/v306AltarPressureReach/src/common.h#L411) |
| `A2_SORTFIX` | `1` | neural_policy.cpp: undefined | [common.h:12](../../../bots/mainline/v306AltarPressureReach/src/common.h#L12) |
| `A2_SPARSE_AREA` | `1000.0f` | neural_policy.cpp: undefined | [common.h:1365](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1365) |
| `A2_SPARSE_BUILD` | `0` | neural_policy.cpp: undefined | [common.h:1362](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1362) |
| `A2_SPARSE_DENS` | `0.25f` | neural_policy.cpp: undefined | [common.h:1368](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1368) |
| `A2_STACK` | `1` | neural_policy.cpp: undefined | [common.h:691](../../../bots/mainline/v306AltarPressureReach/src/common.h#L691) |
| `A2_STANCE` | `3` | neural_policy.cpp: undefined | [common.h:120](../../../bots/mainline/v306AltarPressureReach/src/common.h#L120), [common.h:220](../../../bots/mainline/v306AltarPressureReach/src/common.h#L220) |
| `A2_ST_DEEP` | `0.4f` | neural_policy.cpp: undefined | [common.h:226](../../../bots/mainline/v306AltarPressureReach/src/common.h#L226) |
| `A2_ST_DEF_AGGR` | `1.15f` | neural_policy.cpp: undefined | [common.h:241](../../../bots/mainline/v306AltarPressureReach/src/common.h#L241) |
| `A2_ST_DEF_TERR` | `0.5f` | neural_policy.cpp: undefined | [common.h:238](../../../bots/mainline/v306AltarPressureReach/src/common.h#L238) |
| `A2_ST_EXP_TERR` | `0.7f` | neural_policy.cpp: undefined | [common.h:232](../../../bots/mainline/v306AltarPressureReach/src/common.h#L232) |
| `A2_ST_FROM` | `80` | neural_policy.cpp: undefined | [common.h:223](../../../bots/mainline/v306AltarPressureReach/src/common.h#L223) |
| `A2_ST_HI` | `8.0f` | neural_policy.cpp: undefined | [common.h:235](../../../bots/mainline/v306AltarPressureReach/src/common.h#L235) |
| `A2_ST_QUIET` | `100` | neural_policy.cpp: undefined | [common.h:229](../../../bots/mainline/v306AltarPressureReach/src/common.h#L229) |
| `A2_TD_AUTH` | `1` | neural_policy.cpp: undefined | [common.h:437](../../../bots/mainline/v306AltarPressureReach/src/common.h#L437), [common.h:1224](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1224) |
| `A2_TEAM` | `2` | neural_policy.cpp: undefined | [common.h:1392](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1392) |
| `A2_TEAMFIGHT` | `0` | neural_policy.cpp: undefined | [common.h:1282](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1282) |
| `A2_TEL` | `0` | neural_policy.cpp: undefined | [common.h:1196](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1196) |
| `A2_TF_AVOID` | `0.55f` | neural_policy.cpp: undefined | [common.h:1288](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1288) |
| `A2_TF_ENGAGE` | `1.8f` | neural_policy.cpp: undefined | [common.h:1285](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1285) |
| `A2_THREAT` | `0` | neural_policy.cpp: undefined | [common.h:1395](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1395) |
| `A2_THREAT_AGE` | `4` | neural_policy.cpp: undefined | [common.h:1410](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1410) |
| `A2_THREAT_DETOUR` | `6` | neural_policy.cpp: undefined | [common.h:1413](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1413) |
| `A2_THREAT_GEMS` | `20` | neural_policy.cpp: undefined | [common.h:1401](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1401) |
| `A2_THREAT_GROUP` | `0.5f` | neural_policy.cpp: undefined | [common.h:1404](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1404) |
| `A2_THREAT_HP` | `0.7f` | neural_policy.cpp: undefined | [common.h:1398](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1398) |
| `A2_THREAT_R` | `3` | neural_policy.cpp: undefined | [common.h:1407](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1407) |
| `A2_TILENET` | `0` | neural_policy.cpp: undefined | [common.h:1380](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1380) |
| `A2_TPS` | `1` | neural_policy.cpp: undefined | [common.h:126](../../../bots/mainline/v306AltarPressureReach/src/common.h#L126), [common.h:199](../../../bots/mainline/v306AltarPressureReach/src/common.h#L199) |
| `A2_TPS_ALLY` | `0.3f` | neural_policy.cpp: undefined | [common.h:202](../../../bots/mainline/v306AltarPressureReach/src/common.h#L202) |
| `A2_TSFIX` | `0` | neural_policy.cpp: undefined | [common.h:1236](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1236) |
| `A2_TSFULL` | `0` | neural_policy.cpp: undefined | [common.h:1233](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1233) |
| `A2_TSX` | `0` | neural_policy.cpp: undefined | [common.h:1389](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1389) |
| `A2_TS_FIGHTONLY` | `0` | neural_policy.cpp: undefined | [common.h:1242](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1242) |
| `A2_TS_FIGHT_BIAS` | `0.0f` | neural_policy.cpp: undefined | [common.h:1257](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1257) |
| `A2_TS_ORDER` | `0` | neural_policy.cpp: undefined | [common.h:1374](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1374) |
| `A2_TS_PARANOID` | `1.0f` | neural_policy.cpp: undefined | [common.h:217](../../../bots/mainline/v306AltarPressureReach/src/common.h#L217) |
| `A2_TS_VIS` | `0` | neural_policy.cpp: undefined | [common.h:1230](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1230) |
| `A2_ZONES` | `0` | neural_policy.cpp: undefined | [common.h:1322](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1322) |
| `A2_ZONE_W` | `0.5f` | neural_policy.cpp: undefined | [common.h:1325](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1325) |
| `A3_BACKOFF` | `1` | neural_policy.cpp: undefined | [common.h:258](../../../bots/mainline/v306AltarPressureReach/src/common.h#L258), [common.h:278](../../../bots/mainline/v306AltarPressureReach/src/common.h#L278) |
| `A3_BACK_EQ` | `0.4f` | neural_policy.cpp: undefined | [common.h:259](../../../bots/mainline/v306AltarPressureReach/src/common.h#L259), [common.h:287](../../../bots/mainline/v306AltarPressureReach/src/common.h#L287) |
| `A3_BACK_HP` | `0.4f` | neural_policy.cpp: undefined | [common.h:281](../../../bots/mainline/v306AltarPressureReach/src/common.h#L281) |
| `A3_BACK_K` | `1.25f` | neural_policy.cpp: undefined | [common.h:284](../../../bots/mainline/v306AltarPressureReach/src/common.h#L284) |
| `A3_BACK_MIN_SIZE` | `0` | neural_policy.cpp: undefined | [common.h:296](../../../bots/mainline/v306AltarPressureReach/src/common.h#L296) |
| `A3_BIG_LINEUP` | `-1` | draft.cpp: 6; neural_policy.cpp: undefined | [common.h:260](../../../bots/mainline/v306AltarPressureReach/src/common.h#L260), [common.h:290](../../../bots/mainline/v306AltarPressureReach/src/common.h#L290), [draft.cpp:343](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L343) |
| `A3_BIG_PICKS` | `undefined` | draft.cpp: cd::vendetta, cd::varg, cd::cassi_and_issac, cd::marcella, cd::heart_of_ruin | [draft.cpp:345](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L345) |
| `A3_BIG_PICKS_UNUSED` | `cd::vendetta, cd::varg, cd::cassi_and_issac, cd::marcella, cd::heart_of_ruin` | neural_policy.cpp: undefined | [common.h:253](../../../bots/mainline/v306AltarPressureReach/src/common.h#L253) |
| `A3_BIG_SIZE` | `5` | neural_policy.cpp: undefined | [common.h:293](../../../bots/mainline/v306AltarPressureReach/src/common.h#L293) |
| `A3_ESCAPE` | `0` | neural_policy.cpp: undefined | [common.h:299](../../../bots/mainline/v306AltarPressureReach/src/common.h#L299) |
| `A3_FOCUS` | `0.0f` | neural_policy.cpp: undefined | [common.h:256](../../../bots/mainline/v306AltarPressureReach/src/common.h#L256), [common.h:272](../../../bots/mainline/v306AltarPressureReach/src/common.h#L272) |
| `A3_ITEMS` | `0` | neural_policy.cpp: undefined | [common.h:255](../../../bots/mainline/v306AltarPressureReach/src/common.h#L255), [common.h:266](../../../bots/mainline/v306AltarPressureReach/src/common.h#L266) |
| `A3_NUMBERS` | `0` | neural_policy.cpp: undefined | [common.h:257](../../../bots/mainline/v306AltarPressureReach/src/common.h#L257), [common.h:275](../../../bots/mainline/v306AltarPressureReach/src/common.h#L275) |
| `A3_ONE_OWNER` | `1` | neural_policy.cpp: undefined | [common.h:254](../../../bots/mainline/v306AltarPressureReach/src/common.h#L254), [common.h:263](../../../bots/mainline/v306AltarPressureReach/src/common.h#L263) |
| `A3_PICKS3` | `cd::vendetta, cd::varg, cd::ren` | neural_policy.cpp: undefined | [common.h:22](../../../bots/mainline/v306AltarPressureReach/src/common.h#L22) |
| `A3_PICKS4` | `cd::vendetta, cd::varg, cd::cassi_and_issac, cd::ren` | neural_policy.cpp: undefined | [common.h:23](../../../bots/mainline/v306AltarPressureReach/src/common.h#L23) |
| `A3_SHOP_GOLD` | `0` | neural_policy.cpp: undefined | [common.h:269](../../../bots/mainline/v306AltarPressureReach/src/common.h#L269) |
| `A44_MOBILITY_DRAFT` | `1` | neural_policy.cpp: undefined | [common.h:423](../../../bots/mainline/v306AltarPressureReach/src/common.h#L423) |
| `APEX_AGGRESSION` | `1.2f` | neural_policy.cpp: undefined | [common.h:1717](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1717) |
| `APEX_AHEAD_AGGR` | `1.0063f` | neural_policy.cpp: undefined | [common.h:480](../../../bots/mainline/v306AltarPressureReach/src/common.h#L480), [strategy.h:143](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L143) |
| `APEX_AHEAD_GAP` | `4` | neural_policy.cpp: undefined | [common.h:481](../../../bots/mainline/v306AltarPressureReach/src/common.h#L481), [strategy.h:140](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L140) |
| `APEX_ALTAR_BONUS` | `0.0f` | neural_policy.cpp: undefined | [common.h:2351](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2351) |
| `APEX_AWAKE_ZONE` | `1` | neural_policy.cpp: undefined | [common.h:2033](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2033) |
| `APEX_BANK_RATIO` | `0.0f` | neural_policy.cpp: undefined | [common.h:2348](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2348) |
| `APEX_BEHIND_AGGR` | `1.1235f` | neural_policy.cpp: undefined | [common.h:483](../../../bots/mainline/v306AltarPressureReach/src/common.h#L483), [strategy.h:134](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L134) |
| `APEX_BEHIND_CARRY` | `0.9080f` | neural_policy.cpp: undefined | [common.h:482](../../../bots/mainline/v306AltarPressureReach/src/common.h#L482), [strategy.h:137](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L137) |
| `APEX_BEHIND_GAP` | `0` | neural_policy.cpp: undefined | [common.h:484](../../../bots/mainline/v306AltarPressureReach/src/common.h#L484), [strategy.h:131](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L131) |
| `APEX_BELIEF` | `0` | neural_policy.cpp: undefined | [common.h:2283](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2283) |
| `APEX_BELIEF_ALLY` | `0.5f` | neural_policy.cpp: undefined | [common.h:2289](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2289) |
| `APEX_BELIEF_W` | `0.5f` | neural_policy.cpp: undefined | [common.h:2286](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2286) |
| `APEX_BOOT_BONUS` | `0.3329f` | neural_policy.cpp: undefined | [common.h:476](../../../bots/mainline/v306AltarPressureReach/src/common.h#L476), [common.h:1760](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1760) |
| `APEX_BOOT_ITEMS` | `15` | neural_policy.cpp: undefined | [common.h:477](../../../bots/mainline/v306AltarPressureReach/src/common.h#L477), [common.h:1757](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1757) |
| `APEX_BRAIN` | `1` | neural_policy.cpp: undefined | [common.h:465](../../../bots/mainline/v306AltarPressureReach/src/common.h#L465), [strategy.h:11](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L11) |
| `APEX_BUILD` | `0` | neural_policy.cpp: undefined | [common.h:445](../../../bots/mainline/v306AltarPressureReach/src/common.h#L445), [common.h:1656](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1656) |
| `APEX_BURST` | `0` | neural_policy.cpp: undefined | [common.h:1898](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1898) |
| `APEX_BUSH_AMBUSH` | `2` | neural_policy.cpp: undefined | [common.h:1820](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1820) |
| `APEX_BUSH_DEF` | `1` | neural_policy.cpp: undefined | [common.h:1827](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1827) |
| `APEX_BUSH_HIDE` | `300` | neural_policy.cpp: undefined | [common.h:1808](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1808) |
| `APEX_BUSH_RECALL` | `1` | neural_policy.cpp: undefined | [common.h:1845](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1845) |
| `APEX_C0_AGGRESSION` | `1.5356f` | neural_policy.cpp: undefined | [common.h:502](../../../bots/mainline/v306AltarPressureReach/src/common.h#L502), [strategy.h:21](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L21) |
| `APEX_C0_DANGER_TTD` | `7.6922f` | neural_policy.cpp: undefined | [common.h:501](../../../bots/mainline/v306AltarPressureReach/src/common.h#L501), [strategy.h:75](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L75) |
| `APEX_C0_HUNT` | `0` | neural_policy.cpp: undefined | [common.h:500](../../../bots/mainline/v306AltarPressureReach/src/common.h#L500), [strategy.h:111](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L111) |
| `APEX_C0_RETREAT_HP` | `APEX_RETREAT_HP` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:57](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L57) |
| `APEX_C0_SHOP_GOLD` | `APEX_SHOP_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:93](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L93) |
| `APEX_C0_TRIBUTE_CARRY` | `APEX_TRIBUTE_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:39](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L39) |
| `APEX_C1_AGGRESSION` | `1.2856f` | neural_policy.cpp: undefined | [common.h:499](../../../bots/mainline/v306AltarPressureReach/src/common.h#L499), [strategy.h:24](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L24) |
| `APEX_C1_DANGER_TTD` | `5.8849f` | neural_policy.cpp: undefined | [common.h:498](../../../bots/mainline/v306AltarPressureReach/src/common.h#L498), [strategy.h:78](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L78) |
| `APEX_C1_HUNT` | `0` | neural_policy.cpp: undefined | [common.h:497](../../../bots/mainline/v306AltarPressureReach/src/common.h#L497), [strategy.h:114](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L114) |
| `APEX_C1_RETREAT_HP` | `APEX_RETREAT_HP` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:60](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L60) |
| `APEX_C1_SHOP_GOLD` | `APEX_SHOP_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:96](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L96) |
| `APEX_C1_TRIBUTE_CARRY` | `APEX_TRIBUTE_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:42](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L42) |
| `APEX_C2_AGGRESSION` | `1.6969f` | neural_policy.cpp: undefined | [common.h:496](../../../bots/mainline/v306AltarPressureReach/src/common.h#L496), [strategy.h:27](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L27) |
| `APEX_C2_DANGER_TTD` | `6.1961f` | neural_policy.cpp: undefined | [common.h:495](../../../bots/mainline/v306AltarPressureReach/src/common.h#L495), [strategy.h:81](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L81) |
| `APEX_C2_HUNT` | `0` | neural_policy.cpp: undefined | [common.h:494](../../../bots/mainline/v306AltarPressureReach/src/common.h#L494), [strategy.h:117](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L117) |
| `APEX_C2_RETREAT_HP` | `APEX_RETREAT_HP` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:63](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L63) |
| `APEX_C2_SHOP_GOLD` | `APEX_SHOP_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:99](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L99) |
| `APEX_C2_TRIBUTE_CARRY` | `APEX_TRIBUTE_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:45](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L45) |
| `APEX_C3_AGGRESSION` | `1.8115f` | neural_policy.cpp: undefined | [common.h:493](../../../bots/mainline/v306AltarPressureReach/src/common.h#L493), [strategy.h:30](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L30) |
| `APEX_C3_DANGER_TTD` | `6.3794f` | neural_policy.cpp: undefined | [common.h:492](../../../bots/mainline/v306AltarPressureReach/src/common.h#L492), [strategy.h:84](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L84) |
| `APEX_C3_HUNT` | `0` | neural_policy.cpp: undefined | [common.h:491](../../../bots/mainline/v306AltarPressureReach/src/common.h#L491), [strategy.h:120](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L120) |
| `APEX_C3_RETREAT_HP` | `APEX_RETREAT_HP` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:66](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L66) |
| `APEX_C3_SHOP_GOLD` | `APEX_SHOP_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:102](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L102) |
| `APEX_C3_TRIBUTE_CARRY` | `APEX_TRIBUTE_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:48](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L48) |
| `APEX_C4_AGGRESSION` | `1.3366f` | neural_policy.cpp: undefined | [common.h:490](../../../bots/mainline/v306AltarPressureReach/src/common.h#L490), [strategy.h:33](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L33) |
| `APEX_C4_DANGER_TTD` | `5.5131f` | neural_policy.cpp: undefined | [common.h:489](../../../bots/mainline/v306AltarPressureReach/src/common.h#L489), [strategy.h:87](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L87) |
| `APEX_C4_HUNT` | `0` | neural_policy.cpp: undefined | [common.h:488](../../../bots/mainline/v306AltarPressureReach/src/common.h#L488), [strategy.h:123](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L123) |
| `APEX_C4_RETREAT_HP` | `APEX_RETREAT_HP` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:69](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L69) |
| `APEX_C4_SHOP_GOLD` | `APEX_SHOP_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:105](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L105) |
| `APEX_C4_TRIBUTE_CARRY` | `APEX_TRIBUTE_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:51](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L51) |
| `APEX_C5_AGGRESSION` | `1.6816f` | neural_policy.cpp: undefined | [common.h:487](../../../bots/mainline/v306AltarPressureReach/src/common.h#L487), [strategy.h:36](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L36) |
| `APEX_C5_DANGER_TTD` | `5.7688f` | neural_policy.cpp: undefined | [common.h:486](../../../bots/mainline/v306AltarPressureReach/src/common.h#L486), [strategy.h:90](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L90) |
| `APEX_C5_HUNT` | `0` | neural_policy.cpp: undefined | [common.h:485](../../../bots/mainline/v306AltarPressureReach/src/common.h#L485), [strategy.h:126](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L126) |
| `APEX_C5_RETREAT_HP` | `APEX_RETREAT_HP` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:72](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L72) |
| `APEX_C5_SHOP_GOLD` | `APEX_SHOP_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:108](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L108) |
| `APEX_C5_TRIBUTE_CARRY` | `APEX_TRIBUTE_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:54](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L54) |
| `APEX_CALL_COOLDOWN` | `0` | neural_policy.cpp: undefined | [common.h:1957](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1957) |
| `APEX_CAP_STAFF` | `0` | neural_policy.cpp: undefined | [common.h:1937](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1937) |
| `APEX_CASTER_FOCUS` | `1` | neural_policy.cpp: undefined | [common.h:1913](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1913) |
| `APEX_CASTER_SELF_TTD` | `1.2325f` | neural_policy.cpp: undefined | [common.h:472](../../../bots/mainline/v306AltarPressureReach/src/common.h#L472), [common.h:1772](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1772) |
| `APEX_CASTER_TTD` | `1.0379f` | neural_policy.cpp: undefined | [common.h:479](../../../bots/mainline/v306AltarPressureReach/src/common.h#L479), [strategy.h:146](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L146) |
| `APEX_CHANNEL_GUARD` | `1.0f` | neural_policy.cpp: undefined | [common.h:2184](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2184) |
| `APEX_CHASE` | `6` | neural_policy.cpp: undefined | [common.h:506](../../../bots/mainline/v306AltarPressureReach/src/common.h#L506), [common.h:1721](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1721) |
| `APEX_CI_FOCUS` | `1` | neural_policy.cpp: undefined | [common.h:1949](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1949) |
| `APEX_CI_OUTNUMBERED` | `-1` | neural_policy.cpp: undefined | [common.h:2191](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2191) |
| `APEX_CI_RISK` | `1.2779f` | neural_policy.cpp: undefined | [common.h:473](../../../bots/mainline/v306AltarPressureReach/src/common.h#L473), [common.h:1768](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1768) |
| `APEX_CLASSDRAFT` | `1` | neural_policy.cpp: undefined | [common.h:464](../../../bots/mainline/v306AltarPressureReach/src/common.h#L464) |
| `APEX_CMICRO` | `1` | neural_policy.cpp: undefined | [common.h:2324](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2324) |
| `APEX_CMICRO_CASSI` | `2` | neural_policy.cpp: undefined | [common.h:2336](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2336) |
| `APEX_CMICRO_FLEE_HP` | `0.35f` | neural_policy.cpp: undefined | [common.h:2333](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2333) |
| `APEX_CMICRO_RANGE` | `6` | neural_policy.cpp: undefined | [common.h:2330](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2330) |
| `APEX_CMICRO_RISK` | `1.5f` | neural_policy.cpp: undefined | [common.h:2327](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2327) |
| `APEX_COHESION` | `0.05f` | neural_policy.cpp: undefined | [common.h:2160](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2160) |
| `APEX_COHESION_DIST` | `8` | neural_policy.cpp: undefined | [common.h:2163](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2163) |
| `APEX_DANGER_HP` | `0.1916f` | neural_policy.cpp: undefined | [common.h:505](../../../bots/mainline/v306AltarPressureReach/src/common.h#L505), [common.h:1795](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1795) |
| `APEX_DANGER_TTD` | `6.6632f` | neural_policy.cpp: undefined | [common.h:1792](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1792) |
| `APEX_DEATHLOG` | `0` | neural_policy.cpp: undefined | [common.h:1085](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1085) |
| `APEX_DET` | `1` | neural_policy.cpp: undefined | [common.h:2302](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2302) |
| `APEX_DET_FIELDS` | `2` | neural_policy.cpp: undefined | [common.h:2317](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2317) |
| `APEX_DET_SAFETY` | `35000` | neural_policy.cpp: undefined | [common.h:421](../../../bots/mainline/v306AltarPressureReach/src/common.h#L421), [common.h:2305](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2305) |
| `APEX_DET_SCORE_N` | `16` | neural_policy.cpp: undefined | [common.h:2308](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2308) |
| `APEX_DET_TS_BUDGET` | `70000` | neural_policy.cpp: undefined | [common.h:451](../../../bots/mainline/v306AltarPressureReach/src/common.h#L451), [common.h:2311](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2311) |
| `APEX_DET_UNIT_COST` | `2200` | neural_policy.cpp: undefined | [common.h:2314](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2314) |
| `APEX_DISTRESS` | `0` | neural_policy.cpp: undefined | [common.h:1800](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1800) |
| `APEX_DISTRESS_RANGE` | `14` | neural_policy.cpp: undefined | [common.h:1803](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1803) |
| `APEX_DRAFT` | `undefined` | draft.cpp: 6 | [draft.cpp:11](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L11) |
| `APEX_EARLY_CARRY` | `0` | neural_policy.cpp: undefined | [common.h:2224](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2224) |
| `APEX_EARLY_UNTIL` | `150` | neural_policy.cpp: undefined | [common.h:2227](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2227) |
| `APEX_EMBLEM_MODEL` | `1` | neural_policy.cpp: undefined | [common.h:1953](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1953) |
| `APEX_ENDGAME_MARGIN` | `0` | neural_policy.cpp: undefined | [common.h:1695](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1695) |
| `APEX_END_BANK` | `600` | neural_policy.cpp: undefined | [common.h:462](../../../bots/mainline/v306AltarPressureReach/src/common.h#L462), [common.h:1638](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1638) |
| `APEX_EPISODES` | `undefined` | episode.cpp: 0 | [episode.cpp:12](../../../bots/mainline/v306AltarPressureReach/src/episode.cpp#L12) |
| `APEX_EP_EXPLORE` | `undefined` | episode.cpp: 0 | [episode.cpp:15](../../../bots/mainline/v306AltarPressureReach/src/episode.cpp#L15) |
| `APEX_EP_LOG` | `undefined` | episode.cpp: 0 | [episode.cpp:18](../../../bots/mainline/v306AltarPressureReach/src/episode.cpp#L18) |
| `APEX_ESCAPE_SEARCH` | `0` | neural_policy.cpp: undefined | [common.h:2073](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2073) |
| `APEX_ESCORT` | `0` | neural_policy.cpp: undefined | [common.h:1921](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1921) |
| `APEX_ESC_DASH_COST` | `0.08f` | neural_policy.cpp: undefined | [common.h:2087](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2087) |
| `APEX_ESC_DEPTH` | `3` | neural_policy.cpp: undefined | [common.h:2079](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2079) |
| `APEX_ESC_FUEL` | `60000` | neural_policy.cpp: undefined | [common.h:2242](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2242) |
| `APEX_ESC_HOME` | `2` | neural_policy.cpp: undefined | [common.h:2083](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2083) |
| `APEX_EVENTS` | `2` | neural_policy.cpp: undefined | [common.h:478](../../../bots/mainline/v306AltarPressureReach/src/common.h#L478), [common.h:1754](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1754) |
| `APEX_FIGHT_SIM` | `0` | neural_policy.cpp: undefined | [common.h:1784](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1784) |
| `APEX_FLEE_ALLY` | `0` | neural_policy.cpp: undefined | [common.h:1816](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1816) |
| `APEX_FLEE_HOME` | `150` | neural_policy.cpp: undefined | [common.h:1869](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1869) |
| `APEX_FLEE_MULTI` | `1` | neural_policy.cpp: undefined | [common.h:2041](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2041) |
| `APEX_FUEL_PROBE` | `0` | neural_policy.cpp: undefined | [common.h:1119](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1119) |
| `APEX_GOLD_TAPER` | `0` | neural_policy.cpp: undefined | [common.h:1969](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1969) |
| `APEX_GOLD_WEIGHT` | `0.18f` | neural_policy.cpp: undefined | [common.h:511](../../../bots/mainline/v306AltarPressureReach/src/common.h#L511), [common.h:1664](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1664) |
| `APEX_HIDE_LOS` | `0` | neural_policy.cpp: undefined | [common.h:1812](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1812) |
| `APEX_HP_COST` | `0.0f` | neural_policy.cpp: undefined | [common.h:1965](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1965) |
| `APEX_HUNT` | `1` | neural_policy.cpp: undefined | [common.h:1725](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1725) |
| `APEX_HUNT_FIX` | `1` | neural_policy.cpp: undefined | [common.h:1741](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1741) |
| `APEX_HUNT_GEMS` | `15` | neural_policy.cpp: undefined | [common.h:504](../../../bots/mainline/v306AltarPressureReach/src/common.h#L504), [common.h:1737](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1737) |
| `APEX_HUNT_HP` | `0.7832f` | neural_policy.cpp: undefined | [common.h:1733](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1733) |
| `APEX_HUNT_RANGE` | `8` | neural_policy.cpp: undefined | [common.h:503](../../../bots/mainline/v306AltarPressureReach/src/common.h#L503), [common.h:1729](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1729) |
| `APEX_INCUMBENT` | `0` | neural_policy.cpp: undefined | [common.h:1973](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1973) |
| `APEX_INITIATE` | `1` | neural_policy.cpp: undefined | [common.h:1705](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1705) |
| `APEX_KITE` | `3` | neural_policy.cpp: undefined | [common.h:474](../../../bots/mainline/v306AltarPressureReach/src/common.h#L474), [common.h:1764](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1764) |
| `APEX_KITE_CAST` | `3` | neural_policy.cpp: undefined | [common.h:456](../../../bots/mainline/v306AltarPressureReach/src/common.h#L456), [common.h:1992](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1992) |
| `APEX_L0` | `8` | neural_policy.cpp: undefined | [common.h:471](../../../bots/mainline/v306AltarPressureReach/src/common.h#L471) |
| `APEX_L1` | `8` | neural_policy.cpp: undefined | [common.h:470](../../../bots/mainline/v306AltarPressureReach/src/common.h#L470) |
| `APEX_L2` | `8` | neural_policy.cpp: undefined | [common.h:469](../../../bots/mainline/v306AltarPressureReach/src/common.h#L469) |
| `APEX_L3` | `8` | neural_policy.cpp: undefined | [common.h:468](../../../bots/mainline/v306AltarPressureReach/src/common.h#L468) |
| `APEX_L4` | `8` | neural_policy.cpp: undefined | [common.h:467](../../../bots/mainline/v306AltarPressureReach/src/common.h#L467) |
| `APEX_L5` | `8` | neural_policy.cpp: undefined | [common.h:466](../../../bots/mainline/v306AltarPressureReach/src/common.h#L466) |
| `APEX_LOCKS` | `1` | neural_policy.cpp: undefined | [common.h:1713](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1713) |
| `APEX_LOG` | `0` | neural_policy.cpp: undefined | [common.h:1088](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1088) |
| `APEX_LOWHP_AGGR` | `0.6f` | neural_policy.cpp: undefined | [common.h:443](../../../bots/mainline/v306AltarPressureReach/src/common.h#L443), [common.h:1979](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1979) |
| `APEX_M0_AGGR` | `APEX_MALL_AGGR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:287](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L287) |
| `APEX_M0_BOOT` | `APEX_MALL_BOOT` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:220](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L220) |
| `APEX_M0_CARRY` | `APEX_MALL_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:341](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L341) |
| `APEX_M0_COH` | `APEX_MALL_COH` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:190](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L190) |
| `APEX_M0_GOLD` | `APEX_MALL_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:160](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L160) |
| `APEX_M0_TERR` | `APEX_MALL_TERR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:250](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L250) |
| `APEX_M0_TTD` | `APEX_MALL_TTD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:314](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L314) |
| `APEX_M1_AGGR` | `APEX_MALL_AGGR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:290](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L290) |
| `APEX_M1_BOOT` | `APEX_MALL_BOOT` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:223](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L223) |
| `APEX_M1_CARRY` | `APEX_MALL_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:344](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L344) |
| `APEX_M1_COH` | `APEX_MALL_COH` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:193](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L193) |
| `APEX_M1_GOLD` | `APEX_MALL_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:163](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L163) |
| `APEX_M1_TERR` | `APEX_MALL_TERR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:253](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L253) |
| `APEX_M1_TTD` | `APEX_MALL_TTD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:317](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L317) |
| `APEX_M2_AGGR` | `APEX_MALL_AGGR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:293](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L293) |
| `APEX_M2_BOOT` | `APEX_MALL_BOOT` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:226](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L226) |
| `APEX_M2_CARRY` | `APEX_MALL_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:347](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L347) |
| `APEX_M2_COH` | `APEX_MALL_COH` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:196](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L196) |
| `APEX_M2_GOLD` | `APEX_MALL_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:166](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L166) |
| `APEX_M2_TERR` | `APEX_MALL_TERR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:256](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L256) |
| `APEX_M2_TTD` | `APEX_MALL_TTD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:320](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L320) |
| `APEX_M3_AGGR` | `APEX_MALL_AGGR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:296](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L296) |
| `APEX_M3_BOOT` | `APEX_MALL_BOOT` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:229](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L229) |
| `APEX_M3_CARRY` | `APEX_MALL_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:350](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L350) |
| `APEX_M3_COH` | `APEX_MALL_COH` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:199](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L199) |
| `APEX_M3_GOLD` | `APEX_MALL_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:169](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L169) |
| `APEX_M3_TERR` | `APEX_MALL_TERR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:259](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L259) |
| `APEX_M3_TTD` | `APEX_MALL_TTD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:323](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L323) |
| `APEX_M4_AGGR` | `APEX_MALL_AGGR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:299](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L299) |
| `APEX_M4_BOOT` | `APEX_MALL_BOOT` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:232](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L232) |
| `APEX_M4_CARRY` | `APEX_MALL_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:353](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L353) |
| `APEX_M4_COH` | `APEX_MALL_COH` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:202](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L202) |
| `APEX_M4_GOLD` | `APEX_MALL_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:172](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L172) |
| `APEX_M4_TERR` | `APEX_MALL_TERR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:262](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L262) |
| `APEX_M4_TTD` | `APEX_MALL_TTD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:326](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L326) |
| `APEX_M5_AGGR` | `APEX_MALL_AGGR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:302](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L302) |
| `APEX_M5_BOOT` | `APEX_MALL_BOOT` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:235](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L235) |
| `APEX_M5_CARRY` | `APEX_MALL_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:356](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L356) |
| `APEX_M5_COH` | `APEX_MALL_COH` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:205](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L205) |
| `APEX_M5_GOLD` | `APEX_MALL_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:175](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L175) |
| `APEX_M5_TERR` | `APEX_MALL_TERR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:265](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L265) |
| `APEX_M5_TTD` | `APEX_MALL_TTD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:329](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L329) |
| `APEX_M6_AGGR` | `APEX_MALL_AGGR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:305](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L305) |
| `APEX_M6_BOOT` | `APEX_MALL_BOOT` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:238](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L238) |
| `APEX_M6_CARRY` | `APEX_MALL_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:359](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L359) |
| `APEX_M6_COH` | `APEX_MALL_COH` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:208](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L208) |
| `APEX_M6_GOLD` | `APEX_MALL_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:178](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L178) |
| `APEX_M6_TERR` | `APEX_MALL_TERR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:268](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L268) |
| `APEX_M6_TTD` | `APEX_MALL_TTD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:332](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L332) |
| `APEX_M7_AGGR` | `APEX_MALL_AGGR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:308](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L308) |
| `APEX_M7_BOOT` | `APEX_MALL_BOOT` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:241](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L241) |
| `APEX_M7_CARRY` | `APEX_MALL_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:362](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L362) |
| `APEX_M7_COH` | `APEX_MALL_COH` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:211](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L211) |
| `APEX_M7_GOLD` | `APEX_MALL_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:181](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L181) |
| `APEX_M7_TERR` | `APEX_MALL_TERR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:271](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L271) |
| `APEX_M7_TTD` | `APEX_MALL_TTD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:335](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L335) |
| `APEX_M8_AGGR` | `APEX_MALL_AGGR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:311](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L311) |
| `APEX_M8_BOOT` | `APEX_MALL_BOOT` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:244](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L244) |
| `APEX_M8_CARRY` | `APEX_MALL_CARRY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:365](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L365) |
| `APEX_M8_COH` | `APEX_MALL_COH` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:214](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L214) |
| `APEX_M8_GOLD` | `APEX_MALL_GOLD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:184](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L184) |
| `APEX_M8_TERR` | `APEX_MALL_TERR` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:274](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L274) |
| `APEX_M8_TTD` | `APEX_MALL_TTD` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:338](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L338) |
| `APEX_MALL_AGGR` | `1.0f` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:278](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L278) |
| `APEX_MALL_BOOT` | `APEX_BOOT_BONUS` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:217](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L217) |
| `APEX_MALL_CARRY` | `1.0f` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:284](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L284) |
| `APEX_MALL_COH` | `APEX_COHESION` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:187](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L187) |
| `APEX_MALL_GOLD` | `APEX_GOLD_WEIGHT` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:157](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L157) |
| `APEX_MALL_TERR` | `APEX_TERRITORY` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:247](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L247) |
| `APEX_MALL_TTD` | `1.0f` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:281](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L281) |
| `APEX_MAPDRAFT` | `1` | neural_policy.cpp: undefined | [common.h:459](../../../bots/mainline/v306AltarPressureReach/src/common.h#L459) |
| `APEX_MAP_MULS` | `(k){ APEX_M##k##_AGGR, APEX_M##k##_TTD, APEX_M##k##_CARRY, APEX_M##k##_GOLD, APEX_M##k##_COH, APEX_M##k##_BOOT, APEX_M##k##_TERR }` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:153](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L153) |
| `APEX_MD_COLLISION` | `undefined` | draft.cpp: -1 | [draft.cpp:196](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L196) |
| `APEX_MD_CORNERS` | `undefined` | draft.cpp: -1 | [draft.cpp:197](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L197) |
| `APEX_MD_ELKRING` | `4` | neural_policy.cpp: undefined | [common.h:461](../../../bots/mainline/v306AltarPressureReach/src/common.h#L461) |
| `APEX_MD_EXPANSE` | `undefined` | draft.cpp: -1 | [draft.cpp:198](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L198) |
| `APEX_MD_INTERLOCK` | `undefined` | draft.cpp: -1 | [draft.cpp:199](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L199) |
| `APEX_MD_LANES` | `2` | neural_policy.cpp: undefined | [common.h:460](../../../bots/mainline/v306AltarPressureReach/src/common.h#L460) |
| `APEX_MD_MONOLITH` | `undefined` | draft.cpp: -1 | [draft.cpp:200](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L200) |
| `APEX_MD_OTHER` | `undefined` | draft.cpp: -1 | [draft.cpp:203](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L203) |
| `APEX_MD_PACKS` | `undefined` | draft.cpp: -1 | [draft.cpp:201](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L201) |
| `APEX_MD_ROWS` | `undefined` | draft.cpp: -1 | [draft.cpp:202](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L202) |
| `APEX_NEAR_DIST` | `6` | neural_policy.cpp: undefined | [common.h:475](../../../bots/mainline/v306AltarPressureReach/src/common.h#L475), [common.h:1626](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1626) |
| `APEX_NEED_POOL` | `1.0176f` | neural_policy.cpp: undefined | [common.h:508](../../../bots/mainline/v306AltarPressureReach/src/common.h#L508), [common.h:1677](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1677) |
| `APEX_NODASH_AGGR` | `0.0f` | neural_policy.cpp: undefined | [common.h:2061](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2061) |
| `APEX_NUMBERS` | `0.0f` | neural_policy.cpp: undefined | [common.h:2362](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2362) |
| `APEX_NUMBERS_BONUS` | `0.5f` | neural_policy.cpp: undefined | [common.h:2368](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2368) |
| `APEX_NUMBERS_INVADE` | `99` | neural_policy.cpp: undefined | [common.h:2365](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2365) |
| `APEX_OPP_MODEL` | `0` | neural_policy.cpp: undefined | [common.h:2374](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2374) |
| `APEX_OUTNUMBERED` | `0` | neural_policy.cpp: undefined | [common.h:1690](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1690) |
| `APEX_PAIR` | `0` | neural_policy.cpp: undefined | [common.h:1941](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1941) |
| `APEX_PHASE_AGGR` | `0` | neural_policy.cpp: undefined | [common.h:2166](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2166) |
| `APEX_PHASE_EARLY` | `0.8f` | neural_policy.cpp: undefined | [common.h:2169](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2169) |
| `APEX_PHASE_LATE` | `1.25f` | neural_policy.cpp: undefined | [common.h:2172](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2172) |
| `APEX_PHASE_ROUND` | `450` | neural_policy.cpp: undefined | [common.h:2175](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2175) |
| `APEX_PLAN` | `0` | neural_policy.cpp: undefined | [common.h:2230](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2230) |
| `APEX_PLAN_BANK_BIAS` | `1.0f` | neural_policy.cpp: undefined | [common.h:2239](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2239) |
| `APEX_PLAN_CARRY` | `0.75f` | neural_policy.cpp: undefined | [common.h:2233](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2233) |
| `APEX_PLAN_DEPTH` | `3` | neural_policy.cpp: undefined | [common.h:2236](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2236) |
| `APEX_POSITION` | `0` | neural_policy.cpp: undefined | [common.h:1902](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1902) |
| `APEX_PRELOCK` | `0` | neural_policy.cpp: undefined | [common.h:1857](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1857) |
| `APEX_PRELOCK_SCORE` | `0` | neural_policy.cpp: undefined | [common.h:1860](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1860) |
| `APEX_PRIORITY` | `5` | neural_policy.cpp: undefined | [common.h:1851](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1851) |
| `APEX_PROFILE` | `0` | neural_policy.cpp: undefined | [common.h:1114](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1114) |
| `APEX_PROFILE_DEFAULTS` | `(k){ APEX_C##k##_AGGRESSION, APEX_C##k##_TRIBUTE_CARRY, APEX_C##k##_RETREAT_HP, APEX_C##k##_DANGER_TTD, APEX_C##k##_SHOP_GOLD, APEX_C##k##_HUNT }` | deny.cpp, economy.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [strategy.h:15](../../../bots/mainline/v306AltarPressureReach/src/strategy.h#L15) |
| `APEX_RANGED_FLEE` | `1` | neural_policy.cpp: undefined | [common.h:2187](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2187) |
| `APEX_RECALL_TRAVEL` | `0` | neural_policy.cpp: undefined | [common.h:2067](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2067) |
| `APEX_RETREAT_HP` | `0.1288f` | neural_policy.cpp: undefined | [common.h:514](../../../bots/mainline/v306AltarPressureReach/src/common.h#L514), [common.h:1646](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1646) |
| `APEX_ROLE_SQUAD` | `0` | neural_policy.cpp: undefined | [common.h:1929](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1929) |
| `APEX_ROUTE_DEPTH` | `2` | neural_policy.cpp: undefined | [common.h:452](../../../bots/mainline/v306AltarPressureReach/src/common.h#L452), [common.h:1876](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1876) |
| `APEX_ROUTE_K` | `6` | neural_policy.cpp: undefined | [common.h:1879](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1879) |
| `APEX_ROUTE_M` | `3` | neural_policy.cpp: undefined | [common.h:1882](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1882) |
| `APEX_ROUTE_SLACK` | `0.6f` | neural_policy.cpp: undefined | [common.h:1894](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1894) |
| `APEX_SAFE_ALTARS` | `1` | neural_policy.cpp: undefined | [common.h:1746](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1746) |
| `APEX_SAVE_DASH` | `0` | neural_policy.cpp: undefined | [common.h:2017](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2017) |
| `APEX_SHARE_GOLD` | `1` | neural_policy.cpp: undefined | [common.h:1985](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1985) |
| `APEX_SHIELD_PVP` | `0` | neural_policy.cpp: undefined | [common.h:1865](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1865) |
| `APEX_SHOP_GOLD` | `126` | neural_policy.cpp: undefined | [common.h:513](../../../bots/mainline/v306AltarPressureReach/src/common.h#L513), [common.h:1651](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1651) |
| `APEX_SIDE_HP` | `0.0f` | neural_policy.cpp: undefined | [common.h:2054](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2054) |
| `APEX_SIEGE` | `1` | neural_policy.cpp: undefined | [common.h:1776](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1776) |
| `APEX_SIM_TURNS` | `6` | neural_policy.cpp: undefined | [common.h:1788](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1788) |
| `APEX_SNIPE` | `0` | neural_policy.cpp: undefined | [common.h:2354](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2354) |
| `APEX_SOLO_INITIATE` | `1` | neural_policy.cpp: undefined | [common.h:1945](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1945) |
| `APEX_SPELL_HOLD` | `0` | neural_policy.cpp: undefined | [common.h:2001](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2001) |
| `APEX_SPELL_HOLD_AGE` | `10` | neural_policy.cpp: undefined | [common.h:2007](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2007) |
| `APEX_SPELL_HOLD_RANGE` | `12` | neural_policy.cpp: undefined | [common.h:2004](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2004) |
| `APEX_SQUADS` | `0` | neural_policy.cpp: undefined | [common.h:1933](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1933) |
| `APEX_SQUAD_SHARE` | `0` | neural_policy.cpp: undefined | [common.h:1925](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1925) |
| `APEX_STAGE_TIMEOUT` | `7` | neural_policy.cpp: undefined | [common.h:510](../../../bots/mainline/v306AltarPressureReach/src/common.h#L510), [common.h:1669](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1669) |
| `APEX_STALE_BAG` | `0` | neural_policy.cpp: undefined | [common.h:1630](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1630) |
| `APEX_STALE_WATCH` | `40` | neural_policy.cpp: undefined | [common.h:1634](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1634) |
| `APEX_STAND` | `1` | neural_policy.cpp: undefined | [common.h:1906](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1906) |
| `APEX_STAND2` | `0` | neural_policy.cpp: undefined | [common.h:2024](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2024) |
| `APEX_STICKY` | `1.5230f` | neural_policy.cpp: undefined | [common.h:507](../../../bots/mainline/v306AltarPressureReach/src/common.h#L507), [common.h:1701](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1701) |
| `APEX_TERRITORY` | `1.0f` | neural_policy.cpp: undefined | [common.h:1681](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1681) |
| `APEX_TERRITORY_MARGIN` | `4` | neural_policy.cpp: undefined | [common.h:1684](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1684) |
| `APEX_TERRITORY_UNTIL` | `100000` | neural_policy.cpp: undefined | [common.h:2181](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2181) |
| `APEX_TFC` | `0` | neural_policy.cpp: undefined | [common.h:2252](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2252) |
| `APEX_TFC_FOLLOW_HP` | `0.35f` | neural_policy.cpp: undefined | [common.h:2266](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2266) |
| `APEX_TFC_MARGIN` | `3.0f` | neural_policy.cpp: undefined | [common.h:2260](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2260) |
| `APEX_TFC_ROUNDS` | `3` | neural_policy.cpp: undefined | [common.h:2257](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2257) |
| `APEX_TFC_SOLO` | `0` | neural_policy.cpp: undefined | [common.h:2263](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2263) |
| `APEX_THREAT_AGE` | `8` | neural_policy.cpp: undefined | [common.h:2095](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2095) |
| `APEX_THREAT_DETOUR` | `6` | neural_policy.cpp: undefined | [common.h:2098](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2098) |
| `APEX_THREAT_HP` | `1.0f` | neural_policy.cpp: undefined | [common.h:2101](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2101) |
| `APEX_THREAT_PATH` | `0` | neural_policy.cpp: undefined | [common.h:2092](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2092) |
| `APEX_THREAT_RETREAT` | `0.4f` | neural_policy.cpp: undefined | [common.h:2047](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2047) |
| `APEX_TRACE` | `0` | neural_policy.cpp: undefined | [common.h:1111](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1111) |
| `APEX_TRIBUTE_CARRY` | `72` | neural_policy.cpp: undefined | [common.h:515](../../../bots/mainline/v306AltarPressureReach/src/common.h#L515), [common.h:1609](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1609) |
| `APEX_TRIB_DENY` | `3` | neural_policy.cpp: undefined | [common.h:463](../../../bots/mainline/v306AltarPressureReach/src/common.h#L463), [common.h:1642](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1642) |
| `APEX_TSEARCH` | `0` | neural_policy.cpp: undefined | [common.h:2119](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2119) |
| `APEX_TS_ALIVE` | `25.0f` | neural_policy.cpp: undefined | [common.h:2142](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2142) |
| `APEX_TS_ALLY_FLEE` | `0.2f` | neural_policy.cpp: undefined | [common.h:2157](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2157) |
| `APEX_TS_BUDGET` | `0` | neural_policy.cpp: undefined | [common.h:2133](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2133) |
| `APEX_TS_BUDGET_RESERVE` | `30000` | neural_policy.cpp: undefined | [common.h:2136](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2136) |
| `APEX_TS_CALIB` | `0` | neural_policy.cpp: undefined | [common.h:2220](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2220) |
| `APEX_TS_CAMPS` | `0` | neural_policy.cpp: undefined | [common.h:2212](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2212) |
| `APEX_TS_DECIDE` | `1` | neural_policy.cpp: undefined | [common.h:2203](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2203) |
| `APEX_TS_DECIDE_MARGIN` | `2.0f` | neural_policy.cpp: undefined | [common.h:2209](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2209) |
| `APEX_TS_DECIDE_ROUNDS` | `3` | neural_policy.cpp: undefined | [common.h:2206](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2206) |
| `APEX_TS_FLEE_A` | `0.12f` | neural_policy.cpp: undefined | [common.h:2151](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2151) |
| `APEX_TS_FLEE_C` | `0.35f` | neural_policy.cpp: undefined | [common.h:2154](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2154) |
| `APEX_TS_HP` | `12.0f` | neural_policy.cpp: undefined | [common.h:2145](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2145) |
| `APEX_TS_LEARNED` | `0` | neural_policy.cpp: undefined | [common.h:2199](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2199) |
| `APEX_TS_LOCALNET` | `0` | neural_policy.cpp: undefined | [common.h:2216](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2216) |
| `APEX_TS_PHANTOM` | `0` | neural_policy.cpp: undefined | [common.h:2295](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2295) |
| `APEX_TS_RANGE` | `6` | neural_policy.cpp: undefined | [common.h:2122](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2122) |
| `APEX_TS_RESERVE` | `22000` | neural_policy.cpp: undefined | [common.h:2128](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2128) |
| `APEX_TS_ROUNDS` | `2` | neural_policy.cpp: undefined | [common.h:2125](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2125) |
| `APEX_TS_THREAT` | `0.5f` | neural_policy.cpp: undefined | [common.h:2148](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2148) |
| `APEX_TS_UNIT_COST` | `1000` | neural_policy.cpp: undefined | [common.h:2139](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2139) |
| `APEX_UNSTICK` | `1` | neural_policy.cpp: undefined | [common.h:1750](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1750) |
| `APEX_USE_WAITS` | `1` | neural_policy.cpp: undefined | [common.h:1709](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1709) |
| `APEX_WAIT_WEIGHT` | `3.2398f` | neural_policy.cpp: undefined | [common.h:509](../../../bots/mainline/v306AltarPressureReach/src/common.h#L509), [common.h:1673](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1673) |
| `APEX_WALK_DIST` | `7` | neural_policy.cpp: undefined | [common.h:512](../../../bots/mainline/v306AltarPressureReach/src/common.h#L512), [common.h:1660](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1660) |
| `APEX_WARDS` | `0` | neural_policy.cpp: undefined | [common.h:1780](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1780) |
| `APEX_WARD_AWARE` | `1` | neural_policy.cpp: undefined | [common.h:1834](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1834) |
| `APEX_WARD_REVEAL` | `2` | neural_policy.cpp: undefined | [common.h:1839](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1839) |
| `APEX_WIN_FIRST` | `1` | neural_policy.cpp: undefined | [common.h:1961](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1961) |
| `CLFS` | `15` | neural_policy.cpp: undefined | [common.h:703](../../../bots/mainline/v306AltarPressureReach/src/common.h#L703), [nnrec.cpp:777](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L777) |
| `CLFS_MARGIN` | `undefined` | nnrec.cpp: 3000 | [nnrec.cpp:780](../../../bots/mainline/v306AltarPressureReach/src/nnrec.cpp#L780) |
| `CL_PLAN` | `1` | deny.cpp, economy.cpp, episode.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [mapplan.h:19](../../../bots/mainline/v306AltarPressureReach/src/mapplan.h#L19) |
| `CL_PLAN_ENEMY_LAG` | `10` | deny.cpp, economy.cpp, episode.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [mapplan.h:31](../../../bots/mainline/v306AltarPressureReach/src/mapplan.h#L31) |
| `CL_PLAN_FLOOR` | `4000000` | deny.cpp, economy.cpp, episode.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [mapplan.h:22](../../../bots/mainline/v306AltarPressureReach/src/mapplan.h#L22) |
| `CL_PLAN_GOLDW` | `0.15f` | deny.cpp, economy.cpp, episode.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [mapplan.h:34](../../../bots/mainline/v306AltarPressureReach/src/mapplan.h#L34) |
| `CL_PLAN_GOLDW_OPEN` | `0.6f` | deny.cpp, economy.cpp, episode.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [mapplan.h:32](../../../bots/mainline/v306AltarPressureReach/src/mapplan.h#L32) |
| `CL_PLAN_MIN` | `0.16f` | deny.cpp, economy.cpp, episode.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [mapplan.h:28](../../../bots/mainline/v306AltarPressureReach/src/mapplan.h#L28) |
| `CL_PLAN_RADIUS` | `16` | deny.cpp, economy.cpp, episode.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [mapplan.h:25](../../../bots/mainline/v306AltarPressureReach/src/mapplan.h#L25) |
| `CL_PLAN_TEAM1` | `3` | deny.cpp, economy.cpp, episode.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [mapplan.h:37](../../../bots/mainline/v306AltarPressureReach/src/mapplan.h#L37) |
| `CL_PLAN_TEAM2` | `7` | deny.cpp, economy.cpp, episode.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [mapplan.h:40](../../../bots/mainline/v306AltarPressureReach/src/mapplan.h#L40) |
| `CL_SW_NEXT` | `1.4f` | deny.cpp, economy.cpp, episode.cpp, fight.cpp, main.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [mapplan.h:30](../../../bots/mainline/v306AltarPressureReach/src/mapplan.h#L30) |
| `DEATH_NEED` | `1.0f` | neural_policy.cpp: undefined | [common.h:68](../../../bots/mainline/v306AltarPressureReach/src/common.h#L68) |
| `DEATH_RETREAT` | `0.0f` | neural_policy.cpp: undefined | [common.h:71](../../../bots/mainline/v306AltarPressureReach/src/common.h#L71) |
| `DEATH_TTD` | `1.0f` | neural_policy.cpp: undefined | [common.h:74](../../../bots/mainline/v306AltarPressureReach/src/common.h#L74) |
| `FB_FLAGS` | `10` | deny.cpp, economy.cpp, fight.cpp, neural_policy.cpp, pressure.cpp, tactics.cpp: undefined | [lab.h:19](../../../bots/mainline/v306AltarPressureReach/src/lab.h#L19) |
| `FIRST_SAFE` | `0` | neural_policy.cpp: undefined | [common.h:37](../../../bots/mainline/v306AltarPressureReach/src/common.h#L37) |
| `FS_RET` | `0.1f` | neural_policy.cpp: undefined | [common.h:43](../../../bots/mainline/v306AltarPressureReach/src/common.h#L43) |
| `FS_TTD` | `1.4f` | neural_policy.cpp: undefined | [common.h:40](../../../bots/mainline/v306AltarPressureReach/src/common.h#L40) |
| `GT_SHOP` | `1.0f` | neural_policy.cpp: undefined | [common.h:46](../../../bots/mainline/v306AltarPressureReach/src/common.h#L46) |
| `HOME_AGGR` | `0.8f` | neural_policy.cpp: undefined | [common.h:251](../../../bots/mainline/v306AltarPressureReach/src/common.h#L251) |
| `HOME_FRONT` | `0` | neural_policy.cpp: undefined | [common.h:59](../../../bots/mainline/v306AltarPressureReach/src/common.h#L59) |
| `HOME_FRONT_MULT` | `0.7f` | neural_policy.cpp: undefined | [common.h:62](../../../bots/mainline/v306AltarPressureReach/src/common.h#L62) |
| `HOME_SIDE` | `1` | neural_policy.cpp: undefined | [common.h:245](../../../bots/mainline/v306AltarPressureReach/src/common.h#L245) |
| `HOME_TERR` | `0.3f` | neural_policy.cpp: undefined | [common.h:248](../../../bots/mainline/v306AltarPressureReach/src/common.h#L248) |
| `HS_CREW` | `3` | neural_policy.cpp: undefined | [common.h:18](../../../bots/mainline/v306AltarPressureReach/src/common.h#L18) |
| `HS_ENEMY` | `8` | neural_policy.cpp: undefined | [common.h:17](../../../bots/mainline/v306AltarPressureReach/src/common.h#L17) |
| `HS_FROM` | `0` | neural_policy.cpp: undefined | [common.h:16](../../../bots/mainline/v306AltarPressureReach/src/common.h#L16) |
| `HS_ON` | `1` | neural_policy.cpp: undefined | [common.h:15](../../../bots/mainline/v306AltarPressureReach/src/common.h#L15) |
| `HS_SHARE` | `0.25f` | neural_policy.cpp: undefined | [common.h:19](../../../bots/mainline/v306AltarPressureReach/src/common.h#L19) |
| `HS_TRACE` | `0` | neural_policy.cpp: undefined | [common.h:20](../../../bots/mainline/v306AltarPressureReach/src/common.h#L20) |
| `LADDER_HOME` | `1` | neural_policy.cpp: undefined | [common.h:32](../../../bots/mainline/v306AltarPressureReach/src/common.h#L32) |
| `LADDER_TABLES` | `1` | neural_policy.cpp: undefined | [common.h:29](../../../bots/mainline/v306AltarPressureReach/src/common.h#L29) |
| `MONO_MULT` | `1.0f` | neural_policy.cpp: undefined | [common.h:77](../../../bots/mainline/v306AltarPressureReach/src/common.h#L77) |
| `NNW_HAS_NTYPE` | `undefined` | nnrec.cpp: 1 | [nn_weights.h:4](../../../bots/mainline/v306AltarPressureReach/src/nn_weights.h#L4) |
| `NNW_HAS_OPTION` | `undefined` | nnrec.cpp: 1 | [nn_weights.h:3](../../../bots/mainline/v306AltarPressureReach/src/nn_weights.h#L3) |
| `NNW_HAS_SLOG` | `undefined` | nnrec.cpp: 1 | [nn_weights.h:168](../../../bots/mainline/v306AltarPressureReach/src/nn_weights.h#L168) |
| `NNW_HAS_T` | `undefined` | nnrec.cpp: 1 | [nn_weights.h:169](../../../bots/mainline/v306AltarPressureReach/src/nn_weights.h#L169) |
| `NOVA_AI_BIG_AREA` | `4000` | neural_policy.cpp: undefined | [common.h:987](../../../bots/mainline/v306AltarPressureReach/src/common.h#L987) |
| `NOVA_AI_BIG_LINEUP` | `2` | neural_policy.cpp: undefined | [common.h:981](../../../bots/mainline/v306AltarPressureReach/src/common.h#L981) |
| `NOVA_AI_MONO_LINEUP` | `6` | neural_policy.cpp: undefined | [common.h:984](../../../bots/mainline/v306AltarPressureReach/src/common.h#L984) |
| `NOVA_AI_SPARSE` | `250` | neural_policy.cpp: undefined | [common.h:990](../../../bots/mainline/v306AltarPressureReach/src/common.h#L990) |
| `NOVA_ALL_LINEUP` | `6` | draft.cpp: -1; neural_policy.cpp: undefined | [common.h:21](../../../bots/mainline/v306AltarPressureReach/src/common.h#L21), [draft.cpp:325](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L325), [draft.cpp:347](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L347) |
| `NOVA_ALTAR_INFER` | `0` | neural_policy.cpp: undefined | [common.h:813](../../../bots/mainline/v306AltarPressureReach/src/common.h#L813) |
| `NOVA_AMBUSH_SAFE` | `0.6f` | neural_policy.cpp: undefined | [common.h:762](../../../bots/mainline/v306AltarPressureReach/src/common.h#L762) |
| `NOVA_AOE_AIM` | `0` | neural_policy.cpp: undefined | [common.h:869](../../../bots/mainline/v306AltarPressureReach/src/common.h#L869) |
| `NOVA_BANK_FIX` | `1` | neural_policy.cpp: undefined | [common.h:1006](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1006) |
| `NOVA_BIGCAMP` | `0` | neural_policy.cpp: undefined | [common.h:971](../../../bots/mainline/v306AltarPressureReach/src/common.h#L971) |
| `NOVA_BIGJOB` | `0.6f` | neural_policy.cpp: undefined | [common.h:453](../../../bots/mainline/v306AltarPressureReach/src/common.h#L453), [common.h:777](../../../bots/mainline/v306AltarPressureReach/src/common.h#L777) |
| `NOVA_BIGJOB_FROM` | `60` | neural_policy.cpp: undefined | [common.h:454](../../../bots/mainline/v306AltarPressureReach/src/common.h#L454), [common.h:782](../../../bots/mainline/v306AltarPressureReach/src/common.h#L782) |
| `NOVA_BIGJOB_MULT` | `6.0f` | neural_policy.cpp: undefined | [common.h:455](../../../bots/mainline/v306AltarPressureReach/src/common.h#L455), [common.h:785](../../../bots/mainline/v306AltarPressureReach/src/common.h#L785) |
| `NOVA_BIG_MAP_GEMS` | `100` | neural_policy.cpp: undefined | [common.h:1015](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1015), [common.h:1619](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1619) |
| `NOVA_BLEND_RACE` | `0` | neural_policy.cpp: undefined | [common.h:1038](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1038) |
| `NOVA_BLEND_RETREAT` | `0.2000f` | neural_policy.cpp: undefined | [common.h:1041](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1041) |
| `NOVA_BUDDY` | `0.3f` | neural_policy.cpp: undefined | [common.h:915](../../../bots/mainline/v306AltarPressureReach/src/common.h#L915) |
| `NOVA_BUDDY_DIST` | `4` | neural_policy.cpp: undefined | [common.h:918](../../../bots/mainline/v306AltarPressureReach/src/common.h#L918) |
| `NOVA_BURST_K` | `1.0f` | neural_policy.cpp: undefined | [common.h:444](../../../bots/mainline/v306AltarPressureReach/src/common.h#L444), [common.h:945](../../../bots/mainline/v306AltarPressureReach/src/common.h#L945) |
| `NOVA_BUSH_WARD` | `1` | neural_policy.cpp: undefined | [common.h:744](../../../bots/mainline/v306AltarPressureReach/src/common.h#L744) |
| `NOVA_CAMP_SAFE` | `0.0f` | neural_policy.cpp: undefined | [common.h:753](../../../bots/mainline/v306AltarPressureReach/src/common.h#L753) |
| `NOVA_CASSI_BUILD` | `0` | neural_policy.cpp: undefined | [common.h:757](../../../bots/mainline/v306AltarPressureReach/src/common.h#L757) |
| `NOVA_CASTER_SET` | `0` | neural_policy.cpp: undefined | [common.h:950](../../../bots/mainline/v306AltarPressureReach/src/common.h#L950) |
| `NOVA_CI_LINK` | `0` | neural_policy.cpp: undefined | [common.h:954](../../../bots/mainline/v306AltarPressureReach/src/common.h#L954) |
| `NOVA_CI_RETREAT` | `1.0f` | neural_policy.cpp: undefined | [common.h:771](../../../bots/mainline/v306AltarPressureReach/src/common.h#L771) |
| `NOVA_CLASSIFY` | `1` | neural_policy.cpp: undefined | [common.h:1035](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1035) |
| `NOVA_CLUSTER_DRAFT` | `0` | neural_policy.cpp: undefined | [common.h:441](../../../bots/mainline/v306AltarPressureReach/src/common.h#L441) |
| `NOVA_CLUSTER_FRAC` | `undefined` | draft.cpp: 0.5f | [draft.cpp:332](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L332) |
| `NOVA_CLUSTER_LINEUP` | `undefined` | draft.cpp: 6 | [draft.cpp:333](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L333) |
| `NOVA_CMICRO_MELEE` | `0` | neural_policy.cpp: undefined | [common.h:801](../../../bots/mainline/v306AltarPressureReach/src/common.h#L801) |
| `NOVA_COMMIT_LATE` | `0.0f` | neural_policy.cpp: undefined | [common.h:876](../../../bots/mainline/v306AltarPressureReach/src/common.h#L876) |
| `NOVA_COMMIT_RETREAT` | `0.0f` | neural_policy.cpp: undefined | [common.h:880](../../../bots/mainline/v306AltarPressureReach/src/common.h#L880) |
| `NOVA_COUNTER` | `0` | neural_policy.cpp: undefined | [common.h:995](../../../bots/mainline/v306AltarPressureReach/src/common.h#L995) |
| `NOVA_DEATH_BAG` | `2.0f` | neural_policy.cpp: undefined | [common.h:1024](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1024) |
| `NOVA_DEATH_BASE` | `150.0f` | neural_policy.cpp: undefined | [common.h:1021](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1021) |
| `NOVA_DENY_RYTH` | `1` | neural_policy.cpp: undefined | [common.h:450](../../../bots/mainline/v306AltarPressureReach/src/common.h#L450), [common.h:795](../../../bots/mainline/v306AltarPressureReach/src/common.h#L795) |
| `NOVA_DRAFT_AI` | `0` | neural_policy.cpp: undefined | [common.h:976](../../../bots/mainline/v306AltarPressureReach/src/common.h#L976) |
| `NOVA_DUO` | `5` | neural_policy.cpp: undefined | [common.h:446](../../../bots/mainline/v306AltarPressureReach/src/common.h#L446), [common.h:821](../../../bots/mainline/v306AltarPressureReach/src/common.h#L821) |
| `NOVA_DUO_DIST` | `14` | neural_policy.cpp: undefined | [common.h:824](../../../bots/mainline/v306AltarPressureReach/src/common.h#L824) |
| `NOVA_DUO_MAPS` | `1` | neural_policy.cpp: undefined | [common.h:447](../../../bots/mainline/v306AltarPressureReach/src/common.h#L447), [common.h:829](../../../bots/mainline/v306AltarPressureReach/src/common.h#L829) |
| `NOVA_DUO_UNTIL` | `3000` | neural_policy.cpp: undefined | [common.h:837](../../../bots/mainline/v306AltarPressureReach/src/common.h#L837) |
| `NOVA_EARLY_SAFE_K` | `1` | neural_policy.cpp: undefined | [common.h:927](../../../bots/mainline/v306AltarPressureReach/src/common.h#L927) |
| `NOVA_EARLY_SAFE_UNTIL` | `0` | neural_policy.cpp: undefined | [common.h:924](../../../bots/mainline/v306AltarPressureReach/src/common.h#L924) |
| `NOVA_EDGE_BAG` | `22` | neural_policy.cpp: undefined | [common.h:1009](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1009), [common.h:1613](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1613) |
| `NOVA_EDGE_DIST` | `14` | neural_policy.cpp: undefined | [common.h:1018](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1018) |
| `NOVA_EDGE_UNTIL` | `250` | neural_policy.cpp: undefined | [common.h:1012](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1012), [common.h:1616](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1616) |
| `NOVA_F2_AVOID` | `0.6f` | neural_policy.cpp: undefined | [common.h:905](../../../bots/mainline/v306AltarPressureReach/src/common.h#L905) |
| `NOVA_F2_ENGAGE` | `2.0f` | neural_policy.cpp: undefined | [common.h:902](../../../bots/mainline/v306AltarPressureReach/src/common.h#L902) |
| `NOVA_F2_FOCUS` | `1.5f` | neural_policy.cpp: undefined | [common.h:911](../../../bots/mainline/v306AltarPressureReach/src/common.h#L911) |
| `NOVA_F2_RADIUS` | `6` | neural_policy.cpp: undefined | [common.h:899](../../../bots/mainline/v306AltarPressureReach/src/common.h#L899) |
| `NOVA_F2_REACH` | `6` | neural_policy.cpp: undefined | [common.h:908](../../../bots/mainline/v306AltarPressureReach/src/common.h#L908) |
| `NOVA_FALLBACK_LINEUP` | `21` | neural_policy.cpp: undefined | [common.h:440](../../../bots/mainline/v306AltarPressureReach/src/common.h#L440) |
| `NOVA_FIGHT2` | `0` | neural_policy.cpp: undefined | [common.h:896](../../../bots/mainline/v306AltarPressureReach/src/common.h#L896) |
| `NOVA_FLEE_HIT` | `1` | neural_policy.cpp: undefined | [common.h:438](../../../bots/mainline/v306AltarPressureReach/src/common.h#L438), [common.h:1227](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1227) |
| `NOVA_FUEL_FIRST` | `0` | neural_policy.cpp: undefined | [common.h:1106](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1106) |
| `NOVA_FUEL_OPEN` | `0` | neural_policy.cpp: undefined | [common.h:1099](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1099) |
| `NOVA_GOLD_UNSEEN` | `0.10f` | neural_policy.cpp: undefined | [common.h:448](../../../bots/mainline/v306AltarPressureReach/src/common.h#L448), [common.h:834](../../../bots/mainline/v306AltarPressureReach/src/common.h#L834) |
| `NOVA_LATE_CARRY` | `1.0f` | neural_policy.cpp: undefined | [common.h:842](../../../bots/mainline/v306AltarPressureReach/src/common.h#L842) |
| `NOVA_LATE_CARRY_R` | `400` | neural_policy.cpp: undefined | [common.h:845](../../../bots/mainline/v306AltarPressureReach/src/common.h#L845) |
| `NOVA_LEARNER` | `0` | deny.cpp, draft.cpp, economy.cpp, episode.cpp, fight.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [learner.h:10](../../../bots/mainline/v306AltarPressureReach/src/learner.h#L10) |
| `NOVA_LEARNER_W` | `0.0f` | deny.cpp, draft.cpp, economy.cpp, episode.cpp, fight.cpp, neural_policy.cpp, nnrec.cpp, pressure.cpp, tactics.cpp, tsearch.cpp, world.cpp: undefined | [learner.h:13](../../../bots/mainline/v306AltarPressureReach/src/learner.h#L13) |
| `NOVA_MAP_LINEUPS` | `24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24` | neural_policy.cpp: undefined | [common.h:439](../../../bots/mainline/v306AltarPressureReach/src/common.h#L439) |
| `NOVA_MONO_BANK` | `0` | neural_policy.cpp: undefined | [common.h:1077](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1077) |
| `NOVA_NO_SIGHT` | `0` | neural_policy.cpp: undefined | [common.h:957](../../../bots/mainline/v306AltarPressureReach/src/common.h#L957) |
| `NOVA_PACK_C` | `0` | neural_policy.cpp: undefined | [common.h:963](../../../bots/mainline/v306AltarPressureReach/src/common.h#L963) |
| `NOVA_PACK_MARGIN` | `2.0f` | neural_policy.cpp: undefined | [common.h:966](../../../bots/mainline/v306AltarPressureReach/src/common.h#L966) |
| `NOVA_QUARTIC` | `0` | neural_policy.cpp: undefined | [common.h:873](../../../bots/mainline/v306AltarPressureReach/src/common.h#L873) |
| `NOVA_RACE_BANK` | `0` | neural_policy.cpp: undefined | [common.h:1071](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1071) |
| `NOVA_RACE_DENS` | `0.25f` | neural_policy.cpp: undefined | [common.h:1074](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1074) |
| `NOVA_RUSH_AGGR` | `1.5f` | neural_policy.cpp: undefined | [common.h:933](../../../bots/mainline/v306AltarPressureReach/src/common.h#L933) |
| `NOVA_RUSH_GEMS` | `30` | neural_policy.cpp: undefined | [common.h:939](../../../bots/mainline/v306AltarPressureReach/src/common.h#L939) |
| `NOVA_RUSH_MARGIN` | `0` | neural_policy.cpp: undefined | [common.h:942](../../../bots/mainline/v306AltarPressureReach/src/common.h#L942) |
| `NOVA_RUSH_RADIUS` | `20` | neural_policy.cpp: undefined | [common.h:936](../../../bots/mainline/v306AltarPressureReach/src/common.h#L936) |
| `NOVA_RUSH_UNTIL` | `0` | neural_policy.cpp: undefined | [common.h:930](../../../bots/mainline/v306AltarPressureReach/src/common.h#L930) |
| `NOVA_SEED` | `1` | neural_policy.cpp: undefined | [common.h:442](../../../bots/mainline/v306AltarPressureReach/src/common.h#L442), [common.h:884](../../../bots/mainline/v306AltarPressureReach/src/common.h#L884) |
| `NOVA_SEED_EPS` | `0.04f` | neural_policy.cpp: undefined | [common.h:887](../../../bots/mainline/v306AltarPressureReach/src/common.h#L887) |
| `NOVA_SIEGE_LOS` | `1` | neural_policy.cpp: undefined | [common.h:767](../../../bots/mainline/v306AltarPressureReach/src/common.h#L767) |
| `NOVA_SPAWN_HOT` | `0` | neural_policy.cpp: undefined | [common.h:891](../../../bots/mainline/v306AltarPressureReach/src/common.h#L891) |
| `NOVA_SPAWN_IGNORE` | `2` | neural_policy.cpp: undefined | [common.h:921](../../../bots/mainline/v306AltarPressureReach/src/common.h#L921) |
| `NOVA_STUN_FOCUS` | `0.0f` | neural_policy.cpp: undefined | [common.h:791](../../../bots/mainline/v306AltarPressureReach/src/common.h#L791) |
| `NOVA_TD_GEM` | `0.75f` | neural_policy.cpp: undefined | [common.h:865](../../../bots/mainline/v306AltarPressureReach/src/common.h#L865) |
| `NOVA_TD_HP` | `3.0f` | neural_policy.cpp: undefined | [common.h:859](../../../bots/mainline/v306AltarPressureReach/src/common.h#L859) |
| `NOVA_TD_HP_SHARE` | `0.0f` | neural_policy.cpp: undefined | [common.h:862](../../../bots/mainline/v306AltarPressureReach/src/common.h#L862) |
| `NOVA_TD_LIFE0` | `8.0f` | neural_policy.cpp: undefined | [common.h:850](../../../bots/mainline/v306AltarPressureReach/src/common.h#L850) |
| `NOVA_TD_LIFE1` | `25.0f` | neural_policy.cpp: undefined | [common.h:853](../../../bots/mainline/v306AltarPressureReach/src/common.h#L853) |
| `NOVA_TD_ROUND` | `450` | neural_policy.cpp: undefined | [common.h:856](../../../bots/mainline/v306AltarPressureReach/src/common.h#L856) |
| `NOVA_TGT` | `0` | neural_policy.cpp: undefined | [common.h:1047](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1047) |
| `NOVA_TGT_THREAT` | `2.0f` | neural_policy.cpp: undefined | [common.h:1050](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1050) |
| `NOVA_TGT_WOUNDED` | `0.75f` | neural_policy.cpp: undefined | [common.h:1053](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1053) |
| `NOVA_TGT_WOUNDED_HP` | `0.45f` | neural_policy.cpp: undefined | [common.h:1056](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1056) |
| `NOVA_UNBOX` | `1` | neural_policy.cpp: undefined | [common.h:748](../../../bots/mainline/v306AltarPressureReach/src/common.h#L748) |
| `NOVA_WARD_AHEAD` | `6` | neural_policy.cpp: undefined | [common.h:449](../../../bots/mainline/v306AltarPressureReach/src/common.h#L449), [common.h:807](../../../bots/mainline/v306AltarPressureReach/src/common.h#L807) |
| `NO_MAPID` | `0` | neural_policy.cpp: undefined | [common.h:90](../../../bots/mainline/v306AltarPressureReach/src/common.h#L90) |
| `P19_BANKCLOSE` | `1` | neural_policy.cpp: undefined | [common.h:8](../../../bots/mainline/v306AltarPressureReach/src/common.h#L8) |
| `P19_CREW` | `1` | neural_policy.cpp: undefined | [common.h:5](../../../bots/mainline/v306AltarPressureReach/src/common.h#L5) |
| `P19_CREW_JOIN` | `0.9f` | neural_policy.cpp: undefined | [common.h:11](../../../bots/mainline/v306AltarPressureReach/src/common.h#L11) |
| `P19_CREW_MAX` | `4` | neural_policy.cpp: undefined | [common.h:10](../../../bots/mainline/v306AltarPressureReach/src/common.h#L10) |
| `P19_CREW_RADIUS` | `12` | neural_policy.cpp: undefined | [common.h:9](../../../bots/mainline/v306AltarPressureReach/src/common.h#L9) |
| `P19_FADE` | `1` | neural_policy.cpp: undefined | [common.h:4](../../../bots/mainline/v306AltarPressureReach/src/common.h#L4) |
| `P19_GATE` | `1` | neural_policy.cpp: undefined | [common.h:7](../../../bots/mainline/v306AltarPressureReach/src/common.h#L7) |
| `P19_OWNER` | `1` | neural_policy.cpp: undefined | [common.h:3](../../../bots/mainline/v306AltarPressureReach/src/common.h#L3) |
| `P19_PAIRVETO` | `1` | neural_policy.cpp: undefined | [common.h:6](../../../bots/mainline/v306AltarPressureReach/src/common.h#L6) |
| `P19_PRESS` | `1` | neural_policy.cpp: undefined | [common.h:2](../../../bots/mainline/v306AltarPressureReach/src/common.h#L2) |
| `P19_STALL` | `1` | neural_policy.cpp: undefined | [common.h:1](../../../bots/mainline/v306AltarPressureReach/src/common.h#L1) |
| `RTG` | `(i)(lab::knobs[i] > 0.0f)` | neural_policy.cpp: undefined | [common.h:117](../../../bots/mainline/v306AltarPressureReach/src/common.h#L117), [common.h:137](../../../bots/mainline/v306AltarPressureReach/src/common.h#L137) |
| `RTV` | `(i,s)std::exp((s) * lab::knobs[i])` | neural_policy.cpp: undefined | [common.h:119](../../../bots/mainline/v306AltarPressureReach/src/common.h#L119), [common.h:139](../../../bots/mainline/v306AltarPressureReach/src/common.h#L139) |
| `RTX` | `(i)(lab::knobs[i] > 0.0f)` | neural_policy.cpp: undefined | [common.h:118](../../../bots/mainline/v306AltarPressureReach/src/common.h#L118), [common.h:138](../../../bots/mainline/v306AltarPressureReach/src/common.h#L138) |
| `SCARCE_AGGR` | `1.0f` | neural_policy.cpp: undefined | [common.h:86](../../../bots/mainline/v306AltarPressureReach/src/common.h#L86) |
| `SCARCE_CAMPS` | `0` | neural_policy.cpp: undefined | [common.h:80](../../../bots/mainline/v306AltarPressureReach/src/common.h#L80) |
| `SCARCE_TERR` | `1.0f` | neural_policy.cpp: undefined | [common.h:83](../../../bots/mainline/v306AltarPressureReach/src/common.h#L83) |
| `SPACING` | `0` | neural_policy.cpp: undefined | [common.h:51](../../../bots/mainline/v306AltarPressureReach/src/common.h#L51) |
| `SPACING_W` | `40.0f` | neural_policy.cpp: undefined | [common.h:54](../../../bots/mainline/v306AltarPressureReach/src/common.h#L54) |
| `UB_BUILD` | `1` | neural_policy.cpp: undefined | [common.h:642](../../../bots/mainline/v306AltarPressureReach/src/common.h#L642) |
| `UB_CAMPFIX` | `0` | neural_policy.cpp: undefined | [common.h:535](../../../bots/mainline/v306AltarPressureReach/src/common.h#L535) |
| `UB_CAMPFIX_SCALE` | `1.0f` | neural_policy.cpp: undefined | [common.h:538](../../../bots/mainline/v306AltarPressureReach/src/common.h#L538) |
| `UB_CAMPFIX_UNTIL` | `600` | neural_policy.cpp: undefined | [common.h:541](../../../bots/mainline/v306AltarPressureReach/src/common.h#L541) |
| `UB_CAMPFIX_W` | `0.025f, 0.163f, -1.508f, 0.545f, -0.658f, 1.424f, 0.695f, 0.705f, 0.692f, 0.100f` | neural_policy.cpp: undefined | [common.h:544](../../../bots/mainline/v306AltarPressureReach/src/common.h#L544) |
| `UB_ENEMY_CAMP` | `1.0f` | neural_policy.cpp: undefined | [common.h:530](../../../bots/mainline/v306AltarPressureReach/src/common.h#L530) |
| `UB_GOLD_FADE` | `700` | neural_policy.cpp: undefined | [common.h:652](../../../bots/mainline/v306AltarPressureReach/src/common.h#L652) |
| `UB_GOLD_FUNNEL` | `0` | neural_policy.cpp: undefined | [common.h:548](../../../bots/mainline/v306AltarPressureReach/src/common.h#L548) |
| `UB_GOLD_MULT` | `4.0f` | neural_policy.cpp: undefined | [common.h:645](../../../bots/mainline/v306AltarPressureReach/src/common.h#L645) |
| `UB_GOLD_UNTIL` | `250` | neural_policy.cpp: undefined | [common.h:648](../../../bots/mainline/v306AltarPressureReach/src/common.h#L648) |
| `UB_JOB_INIT` | `0.7f` | neural_policy.cpp: undefined | [common.h:600](../../../bots/mainline/v306AltarPressureReach/src/common.h#L600) |
| `UB_JOB_MAX` | `2` | neural_policy.cpp: undefined | [common.h:597](../../../bots/mainline/v306AltarPressureReach/src/common.h#L597) |
| `UB_PROXY` | `0` | neural_policy.cpp: undefined | [common.h:523](../../../bots/mainline/v306AltarPressureReach/src/common.h#L523) |
| `UB_QCAMP` | `0` | neural_policy.cpp: undefined | [common.h:586](../../../bots/mainline/v306AltarPressureReach/src/common.h#L586) |
| `UB_Q_BETA` | `0.3f` | neural_policy.cpp: undefined | [common.h:589](../../../bots/mainline/v306AltarPressureReach/src/common.h#L589) |
| `UB_Q_W` | `-25.18f, 76.18f, 13.88f, 9.27f, 37.18f, 133.15f, -33.89f, -8.98f, -112.95f, -67.69f, -32.95f, 110.33f, 45.38f, 90.69f, 25.13f, -25.07f, 129.08f, -25.72f, 105.51f, -64.36f, 85.86f, 133.22f, 27.24f, -66.46f, -18.91f, 102.09f, 131.29f, 82.63f, -13.32f, -133.00f, 40.46f, 35.47f, 46.00f, -135.80f, 40.74f, 37.77f, 121.34f, -67.82f, 118.76f, 130.16f` | neural_policy.cpp: undefined | [common.h:592](../../../bots/mainline/v306AltarPressureReach/src/common.h#L592) |
| `V54_HOLD` | `1` | neural_policy.cpp: undefined | [common.h:397](../../../bots/mainline/v306AltarPressureReach/src/common.h#L397) |
| `V54_HOLD_LEAD` | `160` | neural_policy.cpp: undefined | [common.h:400](../../../bots/mainline/v306AltarPressureReach/src/common.h#L400) |
| `V54_ITEMS` | `3` | neural_policy.cpp: undefined | [common.h:394](../../../bots/mainline/v306AltarPressureReach/src/common.h#L394) |
| `V54_ONSITE` | `1` | neural_policy.cpp: undefined | [common.h:388](../../../bots/mainline/v306AltarPressureReach/src/common.h#L388) |
| `V54_STAGE_ARRIVE` | `1` | neural_policy.cpp: undefined | [common.h:385](../../../bots/mainline/v306AltarPressureReach/src/common.h#L385) |
| `V54_STAGE_HELPED` | `20` | neural_policy.cpp: undefined | [common.h:391](../../../bots/mainline/v306AltarPressureReach/src/common.h#L391) |
| `V54_STAGE_WALK` | `60` | neural_policy.cpp: undefined | [common.h:409](../../../bots/mainline/v306AltarPressureReach/src/common.h#L409) |
| `V54_TP` | `1` | neural_policy.cpp: undefined | [common.h:403](../../../bots/mainline/v306AltarPressureReach/src/common.h#L403) |
| `V54_TP_GAIN` | `8` | neural_policy.cpp: undefined | [common.h:406](../../../bots/mainline/v306AltarPressureReach/src/common.h#L406) |
| `V55_CAST_RETARGET` | `0` | neural_policy.cpp: undefined | [common.h:381](../../../bots/mainline/v306AltarPressureReach/src/common.h#L381) |
| `V55_COMMIT_EVENT` | `1` | neural_policy.cpp: undefined | [common.h:372](../../../bots/mainline/v306AltarPressureReach/src/common.h#L372) |
| `V55_DRAFT_LEGAL` | `1` | neural_policy.cpp: undefined | [common.h:369](../../../bots/mainline/v306AltarPressureReach/src/common.h#L369) |
| `V55_HEART_CAMP` | `1` | neural_policy.cpp: undefined | [common.h:375](../../../bots/mainline/v306AltarPressureReach/src/common.h#L375) |
| `V55_HEART_MODEL` | `0` | neural_policy.cpp: undefined | [common.h:378](../../../bots/mainline/v306AltarPressureReach/src/common.h#L378) |
| `V56_SHOP_DONE` | `1` | neural_policy.cpp: undefined | [common.h:366](../../../bots/mainline/v306AltarPressureReach/src/common.h#L366) |
| `V58_ACT` | `12` | neural_policy.cpp: undefined | [common.h:349](../../../bots/mainline/v306AltarPressureReach/src/common.h#L349) |
| `V58_CAMP_CONTACT` | `1` | neural_policy.cpp: undefined | [common.h:312](../../../bots/mainline/v306AltarPressureReach/src/common.h#L312) |
| `V58_CAPTURE_FOOTWORK` | `1` | neural_policy.cpp: undefined | [common.h:309](../../../bots/mainline/v306AltarPressureReach/src/common.h#L309) |
| `V58_CAPTURE_STAND` | `2` | neural_policy.cpp: undefined | [common.h:318](../../../bots/mainline/v306AltarPressureReach/src/common.h#L318) |
| `V58_CARRY_SHOP` | `0` | neural_policy.cpp: undefined | [common.h:340](../../../bots/mainline/v306AltarPressureReach/src/common.h#L340) |
| `V58_DENY_CAP` | `1` | neural_policy.cpp: undefined | [common.h:358](../../../bots/mainline/v306AltarPressureReach/src/common.h#L358) |
| `V58_DIRECTOR` | `0` | neural_policy.cpp: undefined | [common.h:334](../../../bots/mainline/v306AltarPressureReach/src/common.h#L334) |
| `V58_DRAFT` | `0` | neural_policy.cpp: undefined | [common.h:343](../../../bots/mainline/v306AltarPressureReach/src/common.h#L343) |
| `V58_FINISH_RESET` | `1` | neural_policy.cpp: undefined | [common.h:315](../../../bots/mainline/v306AltarPressureReach/src/common.h#L315) |
| `V58_HUNT_CARRY` | `0` | neural_policy.cpp: undefined | [common.h:361](../../../bots/mainline/v306AltarPressureReach/src/common.h#L361) |
| `V58_ITEM_PLAN` | `1` | neural_policy.cpp: undefined | [common.h:306](../../../bots/mainline/v306AltarPressureReach/src/common.h#L306) |
| `V58_KIT_HEART` | `1` | neural_policy.cpp: undefined | [common.h:327](../../../bots/mainline/v306AltarPressureReach/src/common.h#L327) |
| `V58_KIT_MARCELLA` | `2` | neural_policy.cpp: undefined | [common.h:321](../../../bots/mainline/v306AltarPressureReach/src/common.h#L321) |
| `V58_KIT_TAVI` | `1` | neural_policy.cpp: undefined | [common.h:324](../../../bots/mainline/v306AltarPressureReach/src/common.h#L324) |
| `V58_LOCKS` | `0` | neural_policy.cpp: undefined | [common.h:355](../../../bots/mainline/v306AltarPressureReach/src/common.h#L355) |
| `V58_PATCH` | `1` | neural_policy.cpp: undefined | [common.h:303](../../../bots/mainline/v306AltarPressureReach/src/common.h#L303) |
| `V58_PRECAP` | `0` | neural_policy.cpp: undefined | [common.h:331](../../../bots/mainline/v306AltarPressureReach/src/common.h#L331) |
| `V58_ROUTE` | `0` | neural_policy.cpp: undefined | [common.h:337](../../../bots/mainline/v306AltarPressureReach/src/common.h#L337) |
| `V58_SURVIVE` | `0` | neural_policy.cpp: undefined | [common.h:346](../../../bots/mainline/v306AltarPressureReach/src/common.h#L346) |
| `V58_VISION` | `0` | neural_policy.cpp: undefined | [common.h:352](../../../bots/mainline/v306AltarPressureReach/src/common.h#L352) |

Total: 700 distinct source-defined macro names.
