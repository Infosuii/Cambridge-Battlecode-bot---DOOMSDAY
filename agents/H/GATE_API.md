# Gate API for Agent G (`promote`) and other callers

```python
from nfs.evaluate import gate, ledger, protocol, schedule

p = protocol.load(verify=True)                 # raises if protocol/schedules differ from the lock
res = gate.evaluate_files(cand_results_json, teacher_results_json,
                          incumbent_results=None, mode='final')   # or mode='selection'
res.passed        # bool
res.reasons       # list[str]: every failed check, "name: value vs threshold (detail)"
res.as_dict()     # {'verdict': 'PASS'|'FAIL', 'checks': [...], 'tables': {...}, 'labels': {...}}
```

- **Results files** come from `tools/eval_run.py`. Candidate: `--wasm` or `--bot-dir`, plus `--family <run id>` for
  `final`. Teacher baseline: `--reference original` on the same schedule. Incumbent: the results file of the
  currently promoted candidate on the same schedule.
- **`selection` mode** applies the same per-opponent rules, without the ledger. G may call it repeatedly while
  training, on `evaluation/schedules/selection.json` only. Log how many selection evaluations each run made; the
  number must be reported next to any final result.
- **`final` mode** requires a ledger reservation for the candidate sha256. `eval_run.py` creates it before running
  and refuses a repeat for the same sha256 or family unless `--final-reason` (>= 20 chars) is given.
  `promote` must not reserve again and must not choose between candidates using final results.
- **Programmatic runs:** `schedule.run(protocol.load_schedule('selection'), wasm, match_root, p, workers<=4)`
  returns rows. `schedule.summarize(rows)` returns the summary. Wrap them in the same document shape as
  `eval_run.py` (schedule, protocol_sha256, provenance.candidate_sha256, provenance.reference_sha256, rows) before
  calling `gate.evaluate`.
- **Promotion is a registry status change** to `validated`, done by B's tools after a PASS. The gate does not edit
  models or sources.
- **Map partitions:** `protocol.load_schedule('map_partitions')['partitions']` gives `training` (G's training and
  self-play maps), `selection`, and `final` (never used for training or selection).
