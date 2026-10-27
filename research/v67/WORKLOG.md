# Current checkpoint

The user requested a handoff because usage is low. Continue from HANDOFF.md and GPT_PROMPT.md.
The 220/240 goal is unfinished; there is no evidence it is impossible. Best tested: b06-life15,137/240,+108.0.
Latest/current source: b18-public-camp-state,126/240,+55.7,0faults,fuel941vs359. No benchmark is still running.
Seeds3/4 and checks vs v61/v58/v66b remain unused. No ladder queue/submission. v65/mimic unchanged.

RESULTS.md/jsonl contain all 19 complete240-game experiments. BENCHMARK_OUTPUTS.txt preserves all available
actual stdout/stderr, including the two failed builds; b00's original output was not captured to a file.
CHECKPOINT.json records the exact source hash set matching b18. Every historical source/build remains under
artifacts/evaluations/v67/<run>/build. The 70-map study covers all1177 replays after underscore/hyphen normalization.

First next investigation: new controller's >60000fuel gate around build_fields may prevent field_calls becoming
nonzero, while legacy farm refuses to select its first job with field_calls==0. This is an untested hypothesis,
not an implemented fix. Read the full handoff for protocol limitations and other concrete next steps.
