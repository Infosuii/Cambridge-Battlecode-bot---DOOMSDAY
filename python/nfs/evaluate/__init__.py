"""Independent evaluation (Agent H): frozen protocol, schedules, statistics, promotion gate, fuel and equivalence.

Nothing in this package trains, selects or submits. Every local map is a reused benchmark (label
`reused_benchmark`); the engine is deterministic for (wasm A, wasm B, map), so re-running a cell never creates an
independent sample. Uncertainty is computed with maps as clusters.
"""
