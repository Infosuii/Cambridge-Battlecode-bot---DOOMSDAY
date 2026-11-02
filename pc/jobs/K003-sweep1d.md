id: K003
for: g5070
title: = J002, moved from the 5060: sweep 1d remainder, if time is left after K002
steps: as pc/jobs/J002-sweep1d.md, but name runs x1-sd-<flag>-<set>-x2-g5070 (edit a local copy of
  tools/x1_sweep1d.sh; do not push it). Skip flags whose x1-sd-*-x2-01 results.json already exist on build/z-plan.
  research/x1/sweep1c_hashes.json is complete (65 flags). List "same binary" flags as "dead or already on / not
  overridable" (pc/msgs/0003).
stop: at 1 h 20 min after your start; post exactly which flags are done.
