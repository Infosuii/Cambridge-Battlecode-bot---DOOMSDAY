# g3 status —3 November2026,06:15 UTC

CURRENT L006 ACTIVE: fixed-seed refits of13 weak tabled maps, per pc/jobs/L006-J023-takeover.md/msg0047. Code x1g3/build/z-plan-g3 on8bbe438 (base94c35fe plus tooling fixes). Bots unchanged. Starting default hash check then artifacts/tmp/g3_l006.py, log artifacts/tmp/g3-L006-fit.log. Sixiterations/threepairs/sigma0.5/lr1/seed1, four fitted opponents v92,v86h,x1bru,x3inv,14workers. State research/x3/es/mapfit-<map>.json. ES run names have -g3 via X3_RUN_SUFFIX. One heavy campaign; do not launch another. Expect several hours; status posted per iteration and at most15min apart, states/code/results pushed per map.
Tooling: new tools/x3_g3_mapfit_table.py uses recorded runtimefp research/x3/counter_fp.json copied from g5060/J024, preserves13original J022 rows, refuses key collisions/asymmetric fingerprints. Dry-run/no-state preserves exactbytes; new-row fixture preservesall13 and correctkey. Do NOT use upstream x3_mapfit_table.py (authored-half bug and would drop rows without original states).
NEXT after13fits: python tools/x3_g3_mapfit_table.py --fp research/x3/counter_fp.json; verify default hash, then fitted gate poolv92/v86h/x1bru/x3inv (base96/115/130/102=443) and held-out poolv81hl/v86h-s2/x1 (base137/107/133=377); table must gain on BOTH; report fuel/faults/pairs. Push states/header only to g3 branch, PC merges.
L005 four runs complete: fullinvader102,invasion-only84,aggression-only88,item-only93 of172; allfaults0,pattern/loss-cell reports posted. Fullinvader PCaggregate102 matches; exactpergame reference still requested,msg0003. Final L005 report notes limitation. L004 completed,allfourfeatures below377baseline,noadoption. L002/L003 withdrawn.
Machine ASUS_LAPTOP/i5-12500H/16threads/16,858,320,896bytesRAM. WORKERS=DZ_MAX_PARALLEL14,NFS_REPLAY_ENGINE2.0.0,Python3.12.14/numpy2.3.5. Plugged-in screen/sleep Never. Only g3/commswrites and build/z-plan-g3codepushes; no ladder/login/uploads/submissions or sources edits. Preserveall local evidence,neverstage runnerledger/artifactreplays.

L006 CURRENT fitting 00elkring; six iterations,three pairs,four opponents,seed1; no simultaneous gate.

L006 00elkring iter 0: mean fit/game 0.632 wins 5/8 best iter 0 grad |0.414|

L006 00elkring iter 1: mean fit/game 0.832 wins 6/8 best iter 1 grad |0.497|

L006 00elkring iter 2: mean fit/game 0.943 wins 7/8 best iter 2 grad |0.284|

L006 00elkring iter 3: mean fit/game 0.679 wins 5/8 best iter 2 grad |0.482|

L006 00elkring iter 4: mean fit/game 0.795 wins 6/8 best iter 2 grad |0.219|

L006 00elkring iter 5: mean fit/game 0.671 wins 5/8 best iter 2 grad |0.187|

L006 00elkring complete; gain+0.311562, state/code pushed; next map follows.

L006 CURRENT fitting 01gold-rush; six iterations,three pairs,four opponents,seed1; no simultaneous gate.

L006 01gold-rush iter 0: mean fit/game 0.698 wins 5/8 best iter 0 grad |0.901|

L006 01gold-rush iter 1: mean fit/game 0.977 wins 6/8 best iter 1 grad |0.339|

L006 01gold-rush iter 2: mean fit/game 0.488 wins 4/8 best iter 1 grad |0.431|

L006 01gold-rush iter 3: mean fit/game 0.727 wins 5/8 best iter 1 grad |0.456|

L006 01gold-rush iter 4: mean fit/game 0.212 wins 3/8 best iter 1 grad |0.195|

L006 01gold-rush iter 5: mean fit/game -0.198 wins 1/8 best iter 1 grad |0.473|

L006 01gold-rush complete; gain+0.278500, state/code pushed; next map follows.

L006 CURRENT fitting 00quadrants; six iterations,three pairs,four opponents,seed1; no simultaneous gate.

L006 00quadrants iter 0: mean fit/game 0.685 wins 5/8 best iter 0 grad |0.365|

L006 00quadrants iter 1: mean fit/game 0.633 wins 5/8 best iter 0 grad |0.364|

L006 00quadrants iter 2: mean fit/game 0.207 wins 2/8 best iter 0 grad |0.507|

L006 00quadrants iter 3: mean fit/game 0.481 wins 4/8 best iter 0 grad |0.439|

L006 00quadrants iter 4: mean fit/game 0.304 wins 3/8 best iter 0 grad |0.351|

L006 00quadrants iter 5: mean fit/game 0.505 wins 4/8 best iter 0 grad |0.625|

L006 00quadrants complete; gain+0.000000, state/code pushed; next map follows.

L006 CURRENT fitting 00great-wall; six iterations,three pairs,four opponents,seed1; no simultaneous gate.

L006 00great-wall iter 0: mean fit/game 0.818 wins 6/8 best iter 0 grad |0.399|

L006 00great-wall iter 1: mean fit/game 0.663 wins 5/8 best iter 0 grad |0.216|

L006 00great-wall iter 2: mean fit/game 0.163 wins 2/8 best iter 0 grad |0.668|

L006 00great-wall iter 3: mean fit/game -0.133 wins 0/8 best iter 0 grad |0.533|

L006 00great-wall iter 4: mean fit/game 0.347 wins 3/8 best iter 0 grad |0.338|

L006 00great-wall iter 5: mean fit/game 0.304 wins 3/8 best iter 0 grad |0.237|

L006 CURRENT fitting 00great-wall; six iterations,three pairs,four opponents,seed1; no simultaneous gate.

L006 00great-wall complete; gain+0.000000, state/code pushed; next map follows.

L006 CURRENT fitting 00road-of-riches; six iterations,three pairs,four opponents,seed1; no simultaneous gate.

L006 00road-of-riches iter 0: mean fit/game 0.454 wins 4/8 best iter 0 grad |1.092|

L006 00road-of-riches iter 1: mean fit/game 0.379 wins 3/8 best iter 0 grad |0.213|

L006 00road-of-riches iter 2: mean fit/game 0.647 wins 5/8 best iter 2 grad |0.702|

L006 00road-of-riches iter 3: mean fit/game 0.553 wins 4/8 best iter 2 grad |0.139|

L006 00road-of-riches iter 4: mean fit/game 0.693 wins 5/8 best iter 4 grad |0.292|

L006 00road-of-riches iter 5: mean fit/game 0.487 wins 4/8 best iter 4 grad |0.179|

L006 00road-of-riches complete; gain+0.238812, state/code pushed; next map follows.

L006 CURRENT fitting 00interlock; six iterations,three pairs,four opponents,seed1; no simultaneous gate.

L006 00interlock iter 0: mean fit/game 0.873 wins 6/8 best iter 0 grad |0.590|

L006 00interlock iter 1: mean fit/game 0.877 wins 6/8 best iter 1 grad |0.806|

L006 00interlock iter 2: mean fit/game 1.320 wins 8/8 best iter 2 grad |0.354|

L006 00interlock iter 3: mean fit/game 0.687 wins 5/8 best iter 2 grad |0.263|

L006 00interlock iter 4: mean fit/game 0.878 wins 6/8 best iter 2 grad |0.238|

L006 00interlock iter 5: mean fit/game 0.655 wins 5/8 best iter 2 grad |0.267|

L006 00interlock complete; gain+0.446875, state/code pushed; next map follows.

L006 CURRENT fitting 00fragment; six iterations,three pairs,four opponents,seed1; no simultaneous gate.

L006 00fragment iter 0: mean fit/game 0.875 wins 6/8 best iter 0 grad |0.759|

L006 00fragment iter 1: mean fit/game 0.312 wins 3/8 best iter 0 grad |0.472|

L006 00fragment iter 2: mean fit/game 0.495 wins 4/8 best iter 0 grad |0.856|

URGENT CURRENT08:55UTC: L007/msg0048 PREEMPTS L006. L006 PAUSED after00fragment iteration2 (3savediterations),sixmapscomplete; no L006heavyprocessrunning. Statecheckpointpublished,source rebasedcleanly onto49c4239+g3supportcommits. Starting artifacts/tmp/g3_l007.sh,log artifacts/tmp/g3-L007.log:ctr3-x3mf-k15..k29 ONLY,EXTRA X1_MAPFIT=1,14workers. PostexactresultsJSON andwins/SHA perrun; PC0-14notduplicated. Afterall15 scriptresumesL006 atpartialfragment,skipcompletedmaps. OlderCURRENTL006entries superseded untilL007done. Serialcommswrapperrequiredforheartbeatpulls.

L007 CURRENT ctr3-x3mf-k15;onlyoneheavycampaign;L006paused.

L007 completedk15: 57/172,SHA5b1a722f7407,faults0,fuel182;exactJSONposted.

L007 CURRENT ctr3-x3mf-k16;onlyoneheavycampaign;L006paused.

L007 completedk16: 69/172,SHAbfe0e55aad38,faults0,fuel215;exactJSONposted.

L007 CURRENT ctr3-x3mf-k17;onlyoneheavycampaign;L006paused.

REVISED CURRENT09:05UTC: L007/msg0049 nowALL30variants0..29 vsx3inv,NOTx3mf. Stoppedoldcampaign(k15/16posted,k17partialpreserved). Starting artifacts/tmp/g3_l007_inv.sh,log artifacts/tmp/g3-L007-x3inv.log. Source rebasedonto f0f09bb+g3support. PFXctr3,EXTRA X1_MAPFIT=1,14workers,oneheavycampaign. ImmediateJSON/wins/SHAperrun. Oldartifacts/tmp/g3_l007.sh mustNOTrestart. Afterall30,resumeL006partialfragment asbefore. L006 remainspaused,sixmapscomplete,fragment3savediterations.

L007 REVISED CURRENT ctr3-x3inv-k0;L006paused;opponentx3mfwithdrawn.

L007 completedk0: 104/172,SHA2a0bf213a4e5,faults0,fuel181;exactJSONposted.

L007 REVISED CURRENT ctr3-x3inv-k1;L006paused;opponentx3mfwithdrawn.

L007 completedk1: 91/172,SHA4f6cc67520f0,faults0,fuel188;exactJSONposted.

L007 REVISED CURRENT ctr3-x3inv-k2;L006paused;opponentx3mfwithdrawn.

L007 completedk2: 100/172,SHA2154ac06a009,faults0,fuel189;exactJSONposted.

L007 REVISED CURRENT ctr3-x3inv-k3;L006paused;opponentx3mfwithdrawn.

L007 completedk3: 95/172,SHAa4f4765f00d6,faults0,fuel182;exactJSONposted.

L007 REVISED CURRENT ctr3-x3inv-k4;L006paused;opponentx3mfwithdrawn.

REVISED CURRENT09:15UTC perPC0050: L007 BOTHopponents,finishx3mf15-29FIRST,THENall30x3inv,thenresumeL006. mf15/16andinv0-3alreadycompleted/resultsretained. Oldshellcampaignsstopped. Starting artifacts/tmp/g3_l007_queue.py,log artifacts/tmp/g3-L007-queue.log,plan artifacts/tmp/g3-L007-plan.json re-readbetweenruns. DoNOTrestartolderg3_l007*.sh. Partialmf17preservedandfreshretry,finishedresultsnotrerun. Oneheavycampaign,L006paused. Updatequeueplanonfurtherorderswithoutinterruptingcurrentgameifpossible.

L007 CURRENT ctr3-x3mf-k17, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk17: 65/172,SHA6fa77c57a52a,faults0,fuel174;exactJSONposted.

L007 CURRENT ctr3-x3mf-k18, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk18: 76/172,SHA9eced7310c47,faults0,fuel165;exactJSONposted.

L007 CURRENT ctr3-x3mf-k19, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk19: 75/172,SHAcbee25737ee4,faults0,fuel170;exactJSONposted.

L007 CURRENT ctr3-x3mf-k20, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk20: 59/172,SHAdbdbed26e496,faults0,fuel183;exactJSONposted.

L007 CURRENT ctr3-x3mf-k21, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk21: 77/172,SHA42015d046e07,faults0,fuel195;exactJSONposted.

L007 CURRENT ctr3-x3mf-k22, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

PC0051 ANTI_OVERFIT read09:25UTC: L007counterrunsunchanged. Before L006restart,alignESobjective/currentopponentsplitwithnewwins-onlyrule;oldESuseswin+margin/2000. Existingmarginfitsremainpreserved,notadopted. Queueplanresume_l006=false nowpreventsautomaticoldobjective restart afterL007; nextheartbeatwillalignnewobjective-specificstates/names,notmixcachedhistories. L007 CURRENTstillactiveandpriority0.

L007 completedk22: 81/172,SHAaa74c9d3a677,faults0,fuel199;exactJSONposted.

L007 CURRENT ctr3-x3mf-k23, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk23: 74/172,SHAeed305f6fba6,faults0,fuel159;exactJSONposted.

L007 CURRENT ctr3-x3mf-k24, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk24: 64/172,SHA995c60c183cd,faults0,fuel172;exactJSONposted.

L007 CURRENT ctr3-x3mf-k25, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

PC0052 UPDATE09:35UTC: L007queueextendedafterx3inv withv86h0-29,thenx1bru0-29 (ascending). Currentmf25uninterrupted. Planatomicallyupdated;order nowmf15-29,inv0-29,v86h0-29,x1bru0-29. PCdescendsfrom29;skipvisiblefinishedPCdata,butper0052keepgoingifPCdataunpublished. L006remainspausedthroughallL007batches.

L007 completedk25: 79/172,SHA2d2e7cd95863,faults0,fuel186;exactJSONposted.

L007 CURRENT ctr3-x3mf-k26, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk26: 81/172,SHAc9e549781aba,faults0,fuel203;exactJSONposted.

L007 CURRENT ctr3-x3mf-k27, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk27: 86/172,SHAada76874a8cd,faults0,fuel179;exactJSONposted.

L007 CURRENT ctr3-x3mf-k28, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk28: 72/172,SHA9e14d0d5632d,faults0,fuel174;exactJSONposted.

L007 CURRENT ctr3-x3mf-k29, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk29: 87/172,SHAa2035839b5e2,faults0,fuel193;exactJSONposted.

L007 CURRENT ctr3-x3inv-k4, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk4: 98/172,SHAed20a1b79c58,faults0,fuel182;exactJSONposted.

L007 CURRENT ctr3-x3inv-k5, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk5: 91/172,SHAd2657fa2320e,faults0,fuel174;exactJSONposted.

L007 CURRENT ctr3-x3inv-k6, queue PC0050: mf15-29 then inv0-29; plan re-read between runs; L006paused.

L007 completedk6: 95/172,SHA54b2dda44c4c,faults0,fuel214;exactJSONposted.
