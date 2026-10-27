#!/bin/bash
# E64 fix screen: builds and knob variants on the same games (h2h_set.sh slices), vs v61_c3 + b5_c3.
# usage: bash fix_screen.sh WORKERS "SETS" name=BOT[:k=v,k=v..] ...   (k = knob index offset added to the base knobs)
cd "$(dirname "$0")/../.."
W=$1; export SETS="$2"; shift 2
B=$(tr -d '\r\n ' < agent2/lab/knobs_m62_init.txt)
for spec in "$@"; do
  name=${spec%%=*}; rest=${spec#*=}; bot=${rest%%:*}; mods=""; [[ $rest == *:* ]] && mods=${rest#*:}
  if [ -n "$mods" ]; then
    export H2H_KNOBS=$(python -c "import sys
b=[float(x) for x in sys.argv[1].split(',')]
for kv in sys.argv[2].split(','):
    if kv: k,v=kv.split('='); b[int(k)]+=float(v)
print(','.join('%.4f'%x for x in b))" "$B" "$mods")
  else unset H2H_KNOBS; fi
  f=$(powershell -Command "[int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1024)")
  [ "$f" -lt 2500 ] && { echo "SKIP $name: free RAM $f MB"; continue; }
  bash agent2/lab/h2h_set.sh "$bot" 0 "$W" | awk -v n="$name" '/^TOTAL/ {print n": "$3" "$4" "$5} !/^TOTAL/ {split($6,a,"/"); s=s" "$6} END {}'
done
