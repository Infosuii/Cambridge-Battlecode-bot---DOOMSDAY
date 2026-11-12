# Training-operations delivery update — 2026-10-24

Core gameplay integration and requested operations interfaces are delivered.287 Python tests pass. Tiny synthetic CPU/CUDA optimization and exact checkpoint recovery passed; no match-data training ran. CLI metrics/status/action inspection, versioned checkpoint recovery/export, regular evaluation hooks and previous-version/non-neural-baseline comparison are implemented. Two role-record smoke games yielded193 usable actor starts; four comparison games passed implementation checks. The bot remains untrained and new heads are off in release.

Use OPERATIONS_HANDOFF.md and DEEPSEEK_TRAINING_PROMPT.md. The approved first cycle is role only,12 collection games maximum,5minutes/four epochs of CUDA fitting, with data/parity/evaluation gates. Final package is artifacts/release/2026-10-24-final; independent rebuild passed. See HANDOFF.md for exact hashes and limitations.

---

Historical milestone below:

# Status — 2026-10-24

The eight-head direct gameplay framework is integrated, with candidate builders, SDK executors, guarded fuel admission, NFS2 recording, Python/C++ parity and a later bounded training/export workflow. New heads are **untrained and disabled** in the checked-in bot and packaged release. The inherited trained draft network stays separate.

The user clarified that winning matters, not a neural percentage quota. This is a framework for training and validation, not a trained competition winner.

Verified:280 Python tests,460 legacy C++ checks,97 tactical synthetic checks and strategic/economy SDK fixtures. Final all-off Wasm is byte-identical to the frozen original. All four direct development profiles build through the official release CLI. The final18-game framework matrix has zero bot faults, zero invalid records,328 actual logit comparisons (max error8.94e-8), and two candidate fuel-exhaustion events on islands. All untrained policies scored zero gems. Details: `evaluation/results/integration_smoke.json`.

Fuel calibration includes positive-gem banking and every builder/kernel/log component; `models/policy_v2_budget.json` generates the direct budget header. These are conservative reused-map measurements, not universal fuel guarantees. Some large-map strategic calls remain refused. Periodic ownership telemetry is partial, and no achieved coverage percentage is claimed.

The heads-off release ZIP/Wasm/checksums are under `archive/release-2026-10-24-draft/` (superseded by `artifacts/release/2026-10-24-final/`); official independent rebuild verification passed. It strips inherited lab exports, so it is identified separately from `teacher_exact` rather than claimed byte-equivalent to that profile.

For later training, read `TRAINING_LATER.md`. Data preflight rejects underfilled, incompatible or unacknowledged samples. The current movement-record check is insufficient by itself; a later bounded collection must pass the minimums. Optimizer/CUDA training and checkpoint recovery have not been exercised on match data. Imitation requires a separate teacher-annotation collection follow-up. No training, parameter update on match data, submission or activation occurred.

Raw diagnostic replays, environments and all training history remain local/ignored. GitHub is the smaller development repository selected by the user. Current continuation instructions are in `HANDOFF.md` and `NEXT_AGENT_PROMPT.md`.
