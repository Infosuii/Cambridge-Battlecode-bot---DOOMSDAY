# Fresh-clone evaluation portability

Fixed two original-laptop path dependencies, within the assigned Python modules:

- `python/nfs/evaluate/protocol.py`: when the original `diagnosis-phase2/protocol.json` is absent, rebuilds use
  the existing locked fuel scenario choices and their exact historical properties from repository schedules.
  The protocol and all schedule hashes are verified before reuse, the training partition must match, and each
  scenario must contain its two declared training maps with consistent property records. Existing original
  diagnosis data remain the recomputation source when actually present.
- `tools/verify_release.py`: frozen reference binaries resolve as `references/builds/<reference-name>.wasm`,
  independent of absolute Windows paths retained in the immutable historical manifest. Both full binary hash
  and code-section hash must match. Missing/corrupt/mismatched files are explicit failed checks with local
  path/hash diagnostics, rather than uncaught missing-original-path exceptions. Reference-name traversal is
  rejected. No reference manifest, reference binary, frozen protocol, lock, or schedule was edited.

Evidence limitation: the frozen fuel schedule contains properties for nine selected maps. The original scenario
ranking used the whole training cohort, including its median. Reranking just those nine properties could change
the historical `typical` choices, so the portable fallback deliberately restores the exact verified selections.
It does not claim to reconstruct the unavailable original summaries or independently recompute missing rankings.

Targeted tests on 2026-10-24, with the configured development environment:

| Suite | Result |
| --- | --- |
| `test_eval_protocol.py` | 6 passed |
| `test_eval_release.py` | 20 passed |
| new `test_eval_portability.py` | 8 passed |

Regression coverage explicitly hides the original diagnosis, forbids evidence reads/reranking in that case,
requires rebuilt legacy protocol and every schedule to be byte-identical to the existing frozen files, rejects
schedule tampering and partition changes, verifies local binaries while historical paths are absent, and rejects
missing/malformed/full-hash/code-hash failures. Existing release tests also verify real frozen local references.
No full suite, engine game, training job, submission, frozen evidence mutation or commit was performed here.
