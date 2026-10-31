# DOOMSDAY Zero — pure algorithmic bot

Current development: `DZ_ECONOMY_V2` includes finite-horizon farm, delivery and
equipment-visit scoring (`macro_value.h`), with the same project quoted and
purchased. See [the macro checkpoint](../../research/dz/macro-2026-10-31/README.md)
and [live backlog](../../research/dz/BACKLOG.md). Native correctness fixtures pass;
the preliminary strategy screen fails banking. Defaults remain unchanged. Full
Z8, gate investment and real tank formation are unfinished.

Clean-slate C++20 implementation begun 2026-10-28. No previous bot code, weights,
learned policies, or old per-map decision tables are included. The official SDK
and standard library are the only bot dependencies. Old bots are opponents only.

Start with [the current handoff](../../CLAUDE_HANDOFF.md).
The resumed selected source and results are in
[the foundation manifest](../../research/dz/FOUNDATION_RESUMED_2026-10-29.json). The supplied research
is preserved under `research/zero-bot-plan-2026-10-28/` along with its supporting
audit packages. Its planning sketches are inputs, not assertions of implemented behavior.

## Implemented starter

- Persistent draft/play loops, catch boundaries, fuel tiers, hard reserve, stale-round
  checks before SDK mutations, and immediate restart after suspended execution.
- All actions and shared-memory writes pass through `Actuator`.
- Runtime map/group/item/champion metadata, budgeted startup, cached home/altar fields,
  lazy group fields, and dynamic collision-aware walking.
- Self/visible-unit observations, persistent partial camp HP, respawn-generation reset,
  bounded camp scans, six-round progress contracts, and avoid timers.
- Tested six-slot claim codec; sorted body handles; unsupported group indices publish
  IDLE. Claims are soft hints. Team messages remain disabled because freshness is unresolved.
- Research-prior legal draft for 3/4/5 picks; fixed role shopping; reward-rate farming over
  solo-survivable groups (`clear_risk.h`), leader-led crews and a starvation fallback to nearest-group farming;
  basic attack and metadata-driven reset/damage/CC/shield spells; basic banking, recall,
  camp-blocked altar prerequisites, and ward placement.
- No output in the default release build. A separate `--trace` copy prints diagnostics.

## Integrated development candidate (unpromoted)

`DZ_ECONOMY_V2=1` enables bounded objective quotes, dynamic crew allocation,
timestamped crew leases, single capturers, cluster follow-up valuation, marginal
gear projects, a bounded four-turn combat forecast, common action values and a
near-finish race clock. `DZ_SIEGE=1` separately enables persistent gate waves,
checked escapes, heal-return, first-phase shields, committed ally protection and
cached actual altar reachability. See the
[siege checkpoint](../../research/dz/siege-2026-10-31/README.md).
The default is **0**: development screens have not established a banking gain.
See [the implementation checkpoint](../../research/dz/engineering-2026-10-31/README.md)
for exact model assumptions, failed runs, validation and the ordered backlog.
Full ObjModel/EE calibration, tank positioning, competitive siege conversion, joint action
enumeration, opening rollout and release promotion remain unfinished.

On macOS/Linux install official `cambc==4.0.0` and put it on PATH, or set
`DZ_CAMBC` to its executable. Use Python 3.12+ explicitly if the system Python
is older. `tools/dz.py verify --names <run> ...` verifies selected immutable
capsules without repeating the historical archive audit.

## Still required for a validated release

Remaining portions of Z0's 27 conformance tests; calibrated ObjModel and EE;
economy auction and crews; single capturer and timed cluster circuits; hazard banking;
gear utility; exhaustive map-aware draft; race controller; tested team-message freshness;
opening schedule; dash/heal/consumable policies; meaningful parity/league/holdout gates.
The low-fuel emergency path banks beside an altar or heads home; it is not the complete planned 5k-fuel SafeMode.
Below the normal reserve, a separate bounded path clears its claim and attempts
one cached-home step. It preserves this turn's action history, uses no route
allocation or full observations, and passes forced sub-5k native checks for all
16 bodies on the two stress maps. See `research/dz/LOW_FUEL_RECOVERY.md` for scope.
Observation, boot, shopping, camp scan, memory, planner, execution, communication
and field modules are quarantined after three contained exceptions per instance.
Budget suspension propagates separately and does not count as a module failure.
Memory/planner/execution failure uses bounded bank/home recovery; failed
observation or boot yields because the necessary state is unavailable. Allocation
failures during object construction still use the outer catch/retry boundary.

The fundamentals audit adds live allowance/history guards, transactional camp
memory, known-dead frontier avoidance, respawn yielding, bounded loops, immediate
role actions, and conservative spell collateral checks. Experimental camp safety
remains off: it improves survival but has not improved final contested banking.
The full 1,311-field engine fingerprint is pinned and automatically checked by a
separate diagnostic; production does not dump metadata. See
`research/dz/FUNDAMENTALS_AUDIT.md` for current results and unresolved work.

This is a walking skeleton, not a finals candidate. Read `research/dz/RESULTS.md` for
known weak maps and failed experiments. A win against idle can come from the gold
tiebreak with few or zero banked gems; never use idle win rate as an economy claim.

## Reproduce (from the repository root)

```powershell
python tools/dz.py host
python tools/dz.py build
python tools/dz.py verify
python tools/dz.py smoke --name my-fresh-idle-run --pool
python tools/dz.py smoke --name my-fresh-v65-run --pool --opponent v65
python tools/dz.py conformance --name my-fresh-ct-run --maps 00collision 01big-world
```

The runner uses Python's standard library and repo-relative paths, without
`config/paths.json`, NumPy, Node, training data, credentials, or a Python venv.
The official CLI builds through the repository's official `cmake/CMakeLists.txt` and
vendored `sdk/`; a bot-local build template is not used by this CLI.
For host tests install a C++20 g++ compiler and put it on PATH, or set `DZ_CXX`.
See repository `CONTINUE_HERE.md` for restoring the pinned Windows build toolchain.

Every run requires a fresh name. Raw working files go to `artifacts/tmp/dz/<name>`;
portable frozen source, both Wasm binaries, build logs, full native summaries and
replays go into `research/dz/runs/<name>/evidence.zip`, with external JSON reports.
`verify` checks capsule CRCs and content hashes. Diagnostic truncated games intentionally
have no match outcome; their fault counts are not measured. The fuel resumption test
deliberately exhausts fuel and must never be evaluated as a release candidate.

No automatic submission, activation, or ladder duel occurs in these commands.

After an uncaught fault the engine starts a new guest next round. DZ clears its
own surviving shared claim before map initialization, then gives a replacement
guest a fresh turn for map work if startup received only the ordinary budget.
A forced-restart fixture checks both small and largest-map recovery. This does
not make shared claims fresh; they remain soft hints without a freshness protocol.
