# Neural bot: first-hour training and v47 comparison

Training and verification are complete. The trained bot is an experimental
candidate, with a narrow loss to the supplied v47. It is not a demonstrated
upgrade over v47. Nothing was submitted to the live ladder.

## Results

| Comparison | Trained bot | Comparator |
|---|---:|---:|
| Directly against supplied v47, 40 maps and both sides | 38 wins | v47: 42 wins |
| Directly against v47 on the 8 reserved maps, both sides | 8 wins | v47: 8 wins |
| Directly against the original supplied bot on reserved maps | 10 wins | Original: 6 wins |
| Reserved-map opponent pool, identical schedule for each bot | 36/48 wins | Original: 32/48 wins |

The pool is the original bot and two explicitly labeled local proxies using
recent winning draft preferences. The proxies reuse our baseline gameplay;
they are not downloaded executables of leading teams.

The v47 test used the user's `Downloads/bot.zip`, SHA-256
`fd502869d770d00c35f36e8f5031d15e2a41b08c257f7fc4211937451a1cda15`.
Its source was compiled unchanged. It has no draft-network file, its neural
fight/movement/evaluation switches are off, and its lab farming adjustment
starts with zero weights. Existing learned tuning constants remain distinct
from an active neural policy. The version label v47 is the user's identification;
the ZIP contains no independently verified platform version identifier.

Both bots had zero bot faults in the 80-game v47 comparison. Tests used the
official CLI 3.0.5, engine 1.0.3, release mode and default competition fuel.
The trained bot recorded 57 fuel-exhaustion entries across that comparison,
including zero on the reserved-map subset; these are separate from crashes.

## What was trained

The new gameplay policy ranks camp choices with an 18-input, 16-hidden-unit
neural network, containing 321 parameters. It adds a bounded correction to the
original camp ranking and checks the remaining turn budget before inference.
Training uses PPO and a separate training-only critic. The competition bot
runs fixed learned weights; it does not train during a match.

The one-hour experiment completed approximately 58 minutes of optimization and
final evaluation, after setup: 692 updates, 16,608 local training games and
2,679,642 recorded decisions. It used 20 CPU match workers and the RTX 5070 Ti
laptop GPU. Training used 26 maps, checkpoint selection used six maps, and eight
maps were reserved for final evaluation. Checkpoint 628 was selected solely from
the selection maps. v47 was introduced after training and did not influence
training or checkpoint selection.

The existing neural drafting policy was retained. Fine-tuning it on 185 recent
match records from 23 October did not improve prediction validation. Separate
pretraining on the 21 October archive improved prediction metrics but lost
20/36 selection games versus 30/36 for the same gameplay checkpoint with the
original draft. That historical draft was therefore rejected before its final
test, following the registered extension rule.

## Historical data and remaining supply

Only 21 October onward was admitted; 20 October and older archives were not
used. Four completed 21 October summary parts contain 93,606 entries. A fixed
UUID-hash sample selected 1,000 per part, for 4,000 sampled games. Of these,
3,070 passed the post-patch version/completion filters. Engine 1.0.1 games were
excluded; 1.0.2 outcomes were used only for observational draft pretraining,
with today's examples weighted more heavily. Current-engine gameplay rewards
and evaluation came from engine 1.0.3.

Match supply did not limit this run. There are 89,606 unsampled archive entries
in the four existing parts, before checking compatibility and map exclusions.
They are not all guaranteed usable. No further downloads are needed for this
completed experiment. The other 18 parts can be considered in a later run.

## Interpretation

The initial-bot pool comparison improved by four wins in 48 paired cells, but
those cells cover only eight independent map clusters. The exploratory map
bootstrap interval for the win-rate difference includes zero (0 to 20.8
percentage points); the gem-margin interval also includes zero. This does not
establish a reliable general advantage or ladder rating.

The v47 result is 47.5% across 80 deterministic side/map cells and a tie on the
reserved-map subset. It supports treating the two bots as closely matched in
this local test, with v47 slightly ahead overall. No further tuning against
these final tests was performed.

## Files

- `release/bot_neural.zip`: trained C++ source candidate, 30 source files.
- `release/bot_neural.wasm`: exact locally tested compiled candidate.
- `report.json`: main training and reserved-test results.
- `verification.json`: source/archive parity, independent rebuild and uncertainty.
- `v47-comparison.json`: complete v47 results, source audit and schedule.
- `historical-training/fit.json`: historical drafting fit and filtering counts.
- `historical-training/selection.json`: historical drafting rejection evidence.
- `checkpoints/best-trained.pt`: selected gameplay training checkpoint.

The source ZIP matches the extracted release sources. An independent rebuild
has identical executable Wasm sections. Training sampling/logging is disabled
in the release, and neural gameplay inference is enabled. The original 27
supplied source files remain byte-for-byte intact in `baseline/src`.

Desktop control remains stopped. Training has stopped, and the progress
automation was deleted after completion.
