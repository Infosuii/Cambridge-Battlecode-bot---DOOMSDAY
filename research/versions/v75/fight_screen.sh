#!/bin/bash
# Screen every switched-off fight / team behaviour on bots/v76 against the league (seeds 24/25, where v76's own games are
# cached from its validation), whole-bot first; per-map gains are read from the same runs afterwards
# (tools/v67/c_map_delta.py / c_draft_league.py) to decide which to turn into per-map runtime knobs.
# Output research/v75/fight_screen.txt. Variants build into artifacts/tmp/v67/fs-<name>.
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
P=../neural-gameplay/.venv/Scripts/python.exe
V=(
  "burst:APEX_BURST=1"
  "f2gate:NOVA_FIGHT2=1"
  "f2focus:NOVA_FIGHT2=2"
  "f2regroup:NOVA_FIGHT2=4"
  "escort:APEX_ESCORT=6"
  "squads2:APEX_SQUADS=2"
  "disengage:A2_DISENGAGE=1"
  "commit:NOVA_COMMIT_RETREAT=0.5f"
  "commitlate:NOVA_COMMIT_LATE=0.5f"
  "escsearch:APEX_ESCAPE_SEARCH=1"
  "retarget:V55_CAST_RETARGET=1"
  "tsfightonly:A2_TS_FIGHTONLY=1"
  "burst2:A2_BURST2=1"
  "join:A2_TEAM=2"
  "team3:A2_TEAM=3"
  "rolesquad:APEX_ROLE_SQUAD=1"
  "stunfocus:NOVA_STUN_FOCUS=0.5f"
  "assess:A2_ASSESS=1"
  "a2belief:A2_BELIEF=1"
  "burshold:A2_BURST_HOLD=2"
  "savedash:APEX_SAVE_DASH=1"
  "tsearch:APEX_TSEARCH=1"
  "fightsim:APEX_FIGHT_SIM=1"
  "outnum2:APEX_OUTNUMBERED=2"
  "outnum3:APEX_OUTNUMBERED=3"
  "tf1:A2_TEAMFIGHT=1"
  "tf2:A2_TEAMFIGHT=2"
  "belief:APEX_BELIEF=1"
  "pair2:APEX_PAIR=2"
  "fleeally:APEX_FLEE_ALLY=2"
  "earlysafe:NOVA_EARLY_SAFE_UNTIL=300"
  "stand3:APEX_STAND=3"
  "stand2home:APEX_STAND2=1"
  "distress:APEX_DISTRESS=1"
  "race:V75_RACE=1.0f"
  "lone:V75_LONE=2.0f V75_LONE_ALL=1"
  "bag300:V75_BAG=300"
)
J="base=bots/v76"
for v in "${V[@]}"; do
  name=${v%%:*}; sets=${v#*:}
  out=artifacts/tmp/v67/fs-$name
  if [ ! -d $out ]; then
    a=(); for s in $sets; do a+=(--set "$s"); done
    $P tools/v67/c_variant.py --base bots/v76 --out $out "${a[@]}" > /dev/null
  fi
  J="$J $name=$out"
done
args() { for j in $J; do echo "$1-${j%%=*}=${j#*=}"; done; }
echo "fight screen started $(date -u +%FT%TZ)"
for o in v65 v61 v58; do $P tools/v67/c_batch.py --seeds 24 25 --workers 1 --opponent $o $(args F-$o); done
$P tools/v67/c_batch.py --seeds 24 25 --workers 1 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json $(args F-proxy)
for v in "${V[@]}"; do n=${v%%:*}; for o in v65 v61 v58 proxy; do $P tools/v67/c_paired.py F-$o-$n F-$o-base | grep "margin difference" | sed "s/^/$n $o: /"; done; done
echo "fight screen finished $(date -u +%FT%TZ)"
