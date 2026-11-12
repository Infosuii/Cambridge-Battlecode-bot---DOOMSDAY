id: K016
title: URGENT - robust counter table: all 30 variants vs v86h (Rishik wants a much stronger bot today)
priority: 0 (pause other work; resume it after)
commit: build/z-plan 4b493009 or later
run:
  PFX=ctr3 EXTRA="--set X1_MAPFIT=1" bash tools/x3_counter_run.sh "$(seq -s ' ' 0 29)" v86h 18
post after EACH run (do not wait for the rest): g5070/results/ctr3/ctr3-v86h-kK.json = artifacts/tmp/dz/ctr3-v86h-kK/results.json
  (copy as is) and one line in g5070/results/K016.md: run name, wins / 172, candidate sha.
why: the PC builds one per-map / per-side table that wins against x3mf, x3inv, v86h and x1bru together
  (tools/x3_counter.py robust), then gates it on held-out v92 / v81hl / v86h-s2 / x1. The PC plays any variant you
  have not posted yet, from k29 downwards, so start at k0.
daytime only; stop by 18:00 UTC.
