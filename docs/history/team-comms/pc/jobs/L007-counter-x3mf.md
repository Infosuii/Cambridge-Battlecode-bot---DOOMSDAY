id: L007
title: URGENT - robust counter table: all 30 variants vs x3inv (Rishik wants a much stronger bot today)
priority: 0 (pause other work; resume it after)
commit: build/z-plan 4b493009 or later
run:
  PFX=ctr3 EXTRA="--set X1_MAPFIT=1" bash tools/x3_counter_run.sh "$(seq -s ' ' 0 29)" x3inv 14
post after EACH run (do not wait for the rest): g3/results/L007/ctr3-x3inv-kK.json = artifacts/tmp/dz/ctr3-x3inv-kK/results.json
  (copy as is) and one line in g3/results/L007.md: run name, wins / 172, candidate sha.
why: the PC builds one per-map / per-side table that wins against x3mf, x3inv, v86h and x1bru together
  (tools/x3_counter.py robust), then gates it on held-out v92 / v81hl / v86h-s2 / x1. The PC plays any variant you
  have not posted yet, from k29 downwards, so start at k0.

CHANGED (09:10 UTC): opponent is now x3inv, not x3mf (the PC plays x3mf). Post to g3/results/L007/.
