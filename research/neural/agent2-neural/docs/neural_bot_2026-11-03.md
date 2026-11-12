# Neural bot (nn1): entity encoder, pointer heads, privileged critic, distilled student (3 Nov 2026)

This is the user's architecture, made concrete for CAMBC. Wherever the user gave no detail, the choices below are marked *(choice)*.

## Network

### Entities

Everything is seen from the acting champion's viewpoint: positions are relative to it, and walking distances come from the bot's distance fields.

| Type | Count | Features (about) |
|---|---|---|
| self | 1 | type (12 one-hot), health / max, max health, strength, focus, range, carried gems, gold, two cooldowns and ready flags, emblems, recalling / tributing, in bush, in hot zone, walking distance to home / nearest altar |
| ally | ≤ 5 | type, dx / dy, walking distance, health / max, max health, strength, focus, range, carried gems, claimed target (shared memory), is fighting |
| enemy | ≤ 5 (+ last sightings) | type, dx / dy, distance, health / max, max health, strength, focus, range, carried gems, tributing / recalling, visible or remembered, sighting age, can reach me next turn |
| camp group | nearest 10 | dx / dy, walking distance, gems, gold, state (alive / reward / respawning), rounds to respawn, health left / max, strength, harmless, enemy seen near (age), allies near, ally claims, side margin |
| altar | ≤ 4 | dx / dy, walking distance, enemy near, locked, our ward on it |
| ward / bush cluster | nearest 4 | dx / dy, distance, warded by us, enemy last seen |

**Global features:** round, our and enemy banked score, distance to the winning count, team size, map width and height, team gold, alive counts.

### Encoders and trunk

- **Encoders:** one per entity type, shared across entities of that type.
- **Pooling:** mean and max per type, concatenated with the global features.
- **Trunk:** fully connected layers, then a context vector.

| | Teacher | Student |
|---|---|---|
| Encoder | 2 layers × 64 | 1 layer × 16 |
| Trunk | 2 layers × 128 | 2 layers × 64 |

### Heads

Every head is masked, with invalid choices set to −inf.

- **move:**
  - *(choice)* a pointer to a destination entity (camp group, altar, ally, enemy, home), plus "hold". The bot's pathfinding walks there.
  - A 9-way local step head refines the step when an enemy is within 6.
  - **Why:** a raw 9-way step cannot learn map-wide routing.
- **target:** a pointer over enemies and camps, plus "none". It is masked to targets in range after the step.
- **ability:**
  - slot (none / 0 / 1), masked by ready;
  - then a pointer target (self / ally / enemy / ground at an entity), masked by range and kind;
  - then timing (before / after the step / reset).
- **shop:** item or consumable (shard type, ward, altar lock, ...) or none. It is masked by gold and by being at spawn.
- **utility:** none, recall, tribute (submit gems), place ward (pointer to a bush or altar entity), lock altar. Each is masked by the engine's can_* checks.

**Pointer scores:** dot(W_q · context, W_k · entity embedding) / √d.

### Critic

- Used only in training: 3 layers × 256 over the full state.
- The full state is both teams' true champion states, all camp groups and the scores. It is decoded from the replay after the game (p1_decode-style), so it never needs to exist in the bot.

## Training plan and gates

0. **Tooling.**
   - PyTorch with CUDA (RTX 5060, 8 GB). Not installed yet; it needs the user's OK for a download of about 3 GB.
   - **Data path:** the real engine stores each team's stdout inside the replay bundle (team-a.stdout; `--log-limit` raises the 1 MB cap). The recorder build prints compact rows, which means:
     - recording runs at real-engine speed, about 200 games a minute;
     - the training features are exactly what the bot computes (no repeat of the E107 mismatch).
1. **Recorder (v92 + A2_NNREC).**
   - Every Nth turn per champion, it prints the entity tensors (int16, base64) and v92's decisions as labels:
     - its destination entity (target group, altar, ally, enemy, home);
     - its step, attack target, cast slot / target / timing, purchases and utility action.
   - It runs with fuel ignored (`--fuel-quantum 1000000`). Opponents are v92, x1, x3ctr, b5 and v81, on the ladder and unseen map suites.
2. **Teacher by imitation.** Cross-entropy on every head, with masks. Held out by map.
   - **Gate:** per-head accuracy against v92 (destination ≥ 80%, attack target ≥ 90%).
3. **Student and the shipped bot.**
   - Distil the teacher (KL on every head) into the student, then quantise to int16 / int8 with wasm SIMD (the build already has `-msimd128`).
   - Measure fuel per turn in the real engine.
   - The bot is nn1 = v92's engine plumbing (pathfinding, shop, sensing) with all decisions made by the student.
   - **Gate:** nn1 against v92 at ≥ 45% under real fuel. It starts from imitation, so it should be near parity.
4. **Reinforcement learning.**
   - PPO on the teacher, with the privileged critic, from the imitation start.
   - Rollouts run in the real engine: the bot samples from the teacher with fuel ignored and prints its features, actions and log-probabilities. Weights are baked in by a rebuild (about 70 s) each iteration.
   - Opponents: a league of v92, x1, x3ctr and past nn1 snapshots. Reward: win ±1 plus small shaping (banked-gem margin).
   - **Gate:** at least +5 points against held-out bots on held-out maps, at 200+ games.
   - Then distil again into the student, and test under real fuel against v92, x3ctr and the weighted pool.

## Risks

- **RL so far:** every earlier RL attempt here was flat (E70 macro ES, ppo_lab fight/run, E92–E96 and E113 knob ES). The difference this time is a learned policy over every decision with a critic, rather than a few knobs.
- **Imitation:** imitating v92 at best copies v92.
- **Compute:** the PC has 12 cores and 8 GB of VRAM; the real engine is the rollout bottleneck at about 200 games a minute.
- **Kill rule** (the user's efficiency rule): stop at any gate that fails clearly.
