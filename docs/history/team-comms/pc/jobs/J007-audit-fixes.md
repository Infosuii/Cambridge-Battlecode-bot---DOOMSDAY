id: J007
title: full gates for the six x1-audit fixes (research/x1-audit-2026-11-02, by ishanp765)
commit: b23ef86 on build/z-plan (off build 1746f2bb7fa3)
bot: x1
run: gate (tools/x1_gate.sh), one gate per line
opponents: x2 x2-s2
maps: ladder styled (maze when it exists)
priority: 1 (with J006, after J005; J006 first)
switches:
  fleehold4:   --set X1_FLEEHOLD=4
  fleehold8:   --set X1_FLEEHOLD=8
  fleehold15:  --set X1_FLEEHOLD=15
  teamwin:     --set X1_TEAMWIN=1
  heartfix:    --set X1_HEARTFIX=1
  soak64:      --set X1_SOAK64=1
  prunefix:    --set X1_PRUNEFIX=1         (more candidates scored: watch fuel-outs)
  siegestrict: --set X1_SIEGE_STRICT=1
expected hashes (full wasm, built here): heartfix d33f07d1b245, soak64 2a325ed8fb12, prunefix ca003ee9fb5e,
  teamwin 2a635090d298 (before the bot.h guard; rebuild may differ), siegestrict f529dbda8510, fleehold8 8037be82a2c7.
done when: g5060/results/J007.md as for J006 (wins vs base, deaths, gold@R250/500, finish round, fuel-outs, verdict).
