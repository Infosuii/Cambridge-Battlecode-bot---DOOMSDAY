# Generated maps (engine 2.0.0)

50 maps generated from the official pool by `tools/mapgen` (see `tools/mapgen/README.md`); with the 70 official maps
they form the 120-map suite in `evaluation/schedules/map_suite_120.json`.

- `dev/` (22, template-anchored, one per dev template): development use, `MAP_DIR="$PWD/maps/generated/dev" bash tools/bench3.sh ...`
- `holdout/` (28): frozen candidates only, `HOLDOUT=1 MAP_DIR="$PWD/maps/generated/holdout" bash tools/bench3.sh ...`
