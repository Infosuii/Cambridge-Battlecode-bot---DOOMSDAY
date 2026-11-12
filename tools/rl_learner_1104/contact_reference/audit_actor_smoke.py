"""Verify the initial ZERO-weight actor producer; not a generic trained-head audit."""
from pathlib import Path
import hashlib
import json
import math
import struct

root = Path(__file__).resolve().parents[1]
directory = root / 'runs/native-contact-actor-smoke01'
stats = json.loads(directory.with_suffix('.json').read_text())
assert stats['diagnostics']['detailedCaptureComplete']
assert not any(stats['diagnostics']['botFaults'].values())
records, completed, states = {}, {}, {}
actions = [0, 0, 0]
maximum_error = 0.0
mask64 = (1 << 64) - 1
for line in (directory / 'team-a.stdout').read_bytes().replace(b'\0', b'').splitlines():
    t = line.decode().split()
    if t[0] == 'JCA1':
        assert len(t) == 14
        logical, engine, body, seq, win, danger, action = map(int, t[1:8])
        probability = list(map(float, t[8:11]))
        valid = [v == '1' for v in t[11]]
        x = struct.unpack('<48h', bytes.fromhex(t[12]))
        z = struct.unpack('<8h', bytes.fromhex(t[13]))
        assert z == (0,) * 8
        assert len(valid) == 3 and valid[0] and set(t[11]) <= {'0', '1'}
        assert logical == engine and x[25] == win * 2048 and x[26] == danger * 2048
        assert valid[1] == bool(x[27] and not (win and not danger))
        # Positive quantized threat is sufficient to verify this mask on these rows.
        if x[28] > 0:
            assert valid[2] == bool(not (not win and danger))
        expected = [math.exp(2 if j == 0 else 0) if valid[j] else 0 for j in range(3)]
        total = sum(expected)
        expected = [v / total for v in expected]
        maximum_error = max(maximum_error, max(abs(a-b) for a,b in zip(probability, expected)))
        assert maximum_error < 1e-14 and valid[action]
        state, previous = states.get(body, (110701, 0))
        assert seq == previous + 1
        state = (state + 0x9e3779b97f4a7c15) & mask64
        z64 = state
        z64 = ((z64 ^ (z64 >> 30)) * 0xbf58476d1ce4e5b9) & mask64
        z64 = ((z64 ^ (z64 >> 27)) * 0x94d049bb133111eb) & mask64
        z64 ^= z64 >> 31
        u = (z64 >> 11) * 2**-53
        cumulative = 0
        expected_action = max(j for j in range(3) if valid[j])
        for j in range(3):
            cumulative += probability[j]
            if valid[j] and u < cumulative:
                expected_action = j
                break
        assert expected_action == action
        states[body] = state, seq
        assert (body, seq) not in records
        records[body, seq] = engine
        actions[action] += 1
    elif t[0] == 'JCE1':
        assert len(t) == 6
        body, seq, engine, fresh, fuel = map(int, t[1:])
        assert (body, seq) not in completed and fresh == 1
        assert records[body, seq] == engine
        completed[body, seq] = fuel
    else:
        raise AssertionError(t[0])
assert records and records.keys() == completed.keys() and sum(actions[1:]) > 0
report = dict(scope='Initial stochastic contact actor producer smoke, no optimization or strength claim',
              records=len(records), bodies=len(states), actions=actions,
              maximum_probability_error=maximum_error, exact_rng_replay=True,
              all_commands_complete_in_same_round=True,
              minimum_completion_fuel=min(completed.values()),
              wasm_sha256=hashlib.sha256((root/'native-contact-actor/actor.wasm').read_bytes()).hexdigest(),
              diagnostics=stats['diagnostics'],
              limitations=['One training-map game only; not a broad fuel or strength evaluation.',
                           'Initial weights zero with fixed keep prior +2; no contact PPO update yet.',
                           'Earlier combat returns bypass this controller; downstream execution remains heuristic.',
                           'Fixed seed is for reproducibility; training needs an explicit seed schedule.',
                           'This audit covers the initial zero-weight ABI only, not arbitrary trained weights.'])
out = root.parent.parent/'outputs/rl-execution/CONTACT_ACTOR_SMOKE.json'
out.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
