#!/bin/bash
# Bench v3: cached builds and verified, retried shards. Stable output layout:
# (<out>-seed<s>-s<k>/summary.json, <out>-seed<s>.txt), so every analysis tool works unchanged.
#   bash tools/bench3.sh <abs candidate dir> <abs opponent dir> <abs out prefix> [seed ...]
# Env: MAPS_OVERRIDE, HOLDOUT, PY; RETRIES (failed shard retries, default 2).
# MAP_DIR selects an explicit fresh-map directory and requires HOLDOUT=1; uses the same build/fault checks.
# Guarantees:
#   * each (environment, source tree, seed) is built once and cached by content hash, so frozen
#     opponents and unchanged candidates are not rebuilt for every run;
#   * every shard's summary must hold 2 games per map; a crashed shard (WinError 1455, killed process) is rerun up to
#     RETRIES times, and the run fails loudly (exit 1) rather than silently reporting fewer games.
set -e
CAND="$1"; OPP="$2"; OUT="$3"; shift 3
SEEDS="${*:-1 2 3}"
RETRIES="${RETRIES:-2}"
cd "$(dirname "$0")/.." # repo root
export PYTHONPATH="$PWD/python" PYTHONDONTWRITEBYTECODE=1 TMP="$PWD/artifacts/tmp" TEMP="$PWD/artifacts/tmp" PATH="/c/msys64/ucrt64/bin:$PATH"
PY="${PY:-$(sed -n 's/.*"python": *"\([^"]*\)".*/\1/p' config/paths.json)}"
ENV_KEY=$("$PY" tools/bench_environment.py --json "$OUT-environment.json")
CACHE="$PWD/artifacts/tmp/wasm-cache/$ENV_KEY"; B="$OUT-build"; mkdir -p "$CACHE" "$B"
if [ -n "$MAP_DIR" ]; then
  [ "$HOLDOUT" = "1" ] || { echo "MAP_DIR requires HOLDOUT=1 (frozen candidate only)"; exit 1; }
  MAPS=${MAPS_OVERRIDE:-$("$PY" -c "import pathlib,sys;print(' '.join(p.stem for p in sorted(pathlib.Path(sys.argv[1]).glob('*.map26a'))))" "$MAP_DIR")}
else
  MAPS=${MAPS_OVERRIDE:-$("$PY" -c "import json;p=json.load(open('evaluation/schedules/map_partitions.json'))['partitions'];print(' '.join(p['training']+p['selection']))")}
fi

build() { # <bot dir> <seed> <out wasm>: seed-substituted copy, content-hashed, built only on a cache miss
  local d="$B/src-$(basename "$3" .wasm)"; rm -rf "$d"; mkdir -p "$d"; cp -r "$1/src" "$d/"
  grep -q '^#define NOVA_SEED 1$' "$d/src/common.h" || { echo "no NOVA_SEED 1 line in $1"; exit 1; }
  sed -i "s/^#define NOVA_SEED 1\$/#define NOVA_SEED $2/" "$d/src/common.h"
  local h; h=$("$PY" -c "import hashlib,sys,pathlib;s=pathlib.Path(sys.argv[1]);print(hashlib.sha256(b''.join(p.name.encode()+b'\0'+p.read_bytes() for p in sorted(s.iterdir()) if p.is_file())).hexdigest())" "$d/src")
  if [ -s "$CACHE/$h.wasm" ]; then cp "$CACHE/$h.wasm" "$3"; echo "cache hit $(basename "$3") $h"; return; fi
  "$PY" -c "import sys; from pathlib import Path; from nfs import engine; engine.official_build(Path(sys.argv[1]), Path(sys.argv[2]))" "$d" "$3"
  cp "$3" "$CACHE/$h.wasm.tmp" && mv "$CACHE/$h.wasm.tmp" "$CACHE/$h.wasm"
}
for s in $SEEDS; do build "$CAND" $s "$B/cand-s$s.wasm" & build "$OPP" $s "$B/opp-s$s.wasm" & done; wait
for s in $SEEDS; do [ -s "$B/cand-s$s.wasm" ] && [ -s "$B/opp-s$s.wasm" ] || { echo "BUILD FAILED for seed $s"; exit 1; }; done

shard_maps() { local k=$1 j=0 m out=""; for m in $MAPS; do [ $((j % 4)) -eq $k ] && out="$out $m"; j=$((j+1)); done; echo $out; }
run_shard() { # <seed> <shard>: fresh output dir each attempt
  local s=$1 k=$2 dir="$OUT-seed$s-s$k" maps; maps=$(shard_maps $k); [ -z "$maps" ] && return 0
  rm -rf "$dir"
  if [ -n "$MAP_DIR" ]; then
    "$PY" tools/fresh_match.py --a "$B/cand-s$s.wasm" --b "$B/opp-s$s.wasm" --map-dir "$MAP_DIR" --out "$dir" --maps $maps > "$dir.log" 2>&1 || true
  else
    "$PY" tools/bot_match.py --a "$B/cand-s$s.wasm" --b "$B/opp-s$s.wasm" ${HOLDOUT:+--holdout} --out "$dir" --maps $maps > "$dir.log" 2>&1 || true
  fi
}
shard_ok() { # <seed> <shard>: summary exists with 2 games per map
  local s=$1 k=$2 maps n; maps=$(shard_maps $k); [ -z "$maps" ] && return 0
  n=$(echo $maps | wc -w)
  "$PY" -c "import json,sys;d=json.load(open(sys.argv[1]));sys.exit(0 if d['games']==2*int(sys.argv[2]) else 1)" "$OUT-seed$s-s$k/summary.json" "$n" 2>/dev/null
}
for s in $SEEDS; do for k in 0 1 2 3; do run_shard $s $k & done; done; wait
for attempt in $(seq 1 "$RETRIES"); do
  bad=""; for s in $SEEDS; do for k in 0 1 2 3; do shard_ok $s $k || bad="$bad $s:$k"; done; done
  [ -z "$bad" ] && break
  echo "retry $attempt for shards:$bad"
  for sk in $bad; do run_shard ${sk%:*} ${sk#*:} & done; wait
done
bad=""; for s in $SEEDS; do for k in 0 1 2 3; do shard_ok $s $k || bad="$bad $s:$k"; done; done
dirs=()
for s in $SEEDS; do
  sd=(); for k in 0 1 2 3; do [ -f "$OUT-seed$s-s$k/summary.json" ] && sd+=("$OUT-seed$s-s$k") && dirs+=("$OUT-seed$s-s$k"); done
  [ ${#sd[@]} -gt 0 ] && "$PY" tools/bench_summary.py "${sd[@]}" > "$OUT-seed$s.txt"
done
"$PY" tools/bench_summary.py "${dirs[@]}"
if [ -n "$bad" ]; then echo "INCOMPLETE: shards failed after $RETRIES retries:$bad (see $OUT-seed<s>-s<k>.log)"; exit 1; fi
"$PY" tools/bench_environment.py --json "$OUT-environment.json" --verify
"$PY" tools/check_bench_run.py "$OUT" --seeds "${SEEDS// /,}" --maps "${MAPS// /,}"
