id: L007
title: URGENT (Rishik: a bot that steamrolls x3mf within 2 hours) - counter search vs x3mf, variants 15-29
priority: 0 - PAUSE L006 now (finish the current ES iteration if it is under 5 minutes from done, else stop it; the
  per-map state is saved), run L007, then resume L006 where it stopped.
commit: build/z-plan 49c42399 or later (tools/x3_counter_run.sh with PFX / EXTRA, exact-fingerprint table writer)
run:
  PFX=ctr3 EXTRA="--set X1_MAPFIT=1" bash tools/x3_counter_run.sh "15 16 17 18 19 20 21 22 23 24 25 26 27 28 29" x3mf 14
  (each run: all 86 pool maps x 2 sides = 172 games vs bots/x3mf, variant k forced; the PC runs 0-14)
post after EACH run, without waiting for the rest:
  g3/results/L007/ctr3-x3mf-kK.json = artifacts/tmp/dz/ctr3-x3mf-kK/results.json (copy as is; small)
  plus one line in g3/results/L007.md: run name, wins / 172, candidate sha.
done when: all 15 posted. Then resume L006.
