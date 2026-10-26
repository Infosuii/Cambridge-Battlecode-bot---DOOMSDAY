#!/bin/bash
# Compatibility entry point: fresh holdouts share the verified bench3 cache and fault checks.
export HOLDOUT=1
export MAP_DIR="${MAP_DIR:-$(dirname "$0")/../local-only/pool-maps/new15}"
exec bash "$(dirname "$0")/bench3.sh" "$@"
