# EXP-118 fully bounded greedy fallback

The SDK returned the same target in all 896 charged comparisons on both sides of 16 development maps. Dense nearby cases saved a median 611 fuel and dense far cases saved 402,666.5. The largest extra cost on sparse or empty masks was 543. There were no faults or codes. [SDK comparisons](CPG_GREEDY_FULL_PROOF.json).

The release and rebuild both produced `ca5b2a73f2dff4d494d7ed58f471f1e4b547eaffe678757fa49f697a0c632f36`, and switches off reproduced v92. The standard-budget 160-pair check again removed all six Vendetta suspensions and the 160 reduced-budget pairs had no increases. The independent Marcella replay retained the original ward and attack and also removed all six suspensions. [Builds](CPG_GREEDY_FULL_BUILDS.json), [Vendetta and paired checks](CPG_GREEDY_FULL_EXACT.json), [Marcella](MARCELLA_GREEDY_FULL.json).

The unsubmitted candidate won 101/172 versus v92's 86/172 in the official pool, with candidate-only and baseline-only wins 48 and 33. Total suspensions fell from 160 to 26, including round one from 28 to 12. No faults, diagnostic codes or round-one increases. One previously clean game suspended, so L0 failed. L1, L2 and ladder testing did not start. [Official-pool safety results](CPG-GREEDY-FULL_POOL_SAFETY.json).
