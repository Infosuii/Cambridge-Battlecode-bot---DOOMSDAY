# Session 1 setup and provenance

**Status: blocked before live provenance.** This preflight supports no conclusion
about current bot strength, failure frequency or causality.

## Environment (measured)

| Check | Evidence | Sample |
|---|---|---:|
| Official CLI | Linux x86_64, PyPI cambc 4.0.0, as advertised by official download page | 1 install |
| CLI binary SHA-256 | `552056aab1b99a6626597b6aaf0ae38f967709626f90f2d6926c4510ca929eb4` | 1 binary |
| Engine assets | 2.0.0, shared-loader checksum pins match; loader instantiates | 3 assets |
| Native-summary reconciliation | Pending authenticated downloads | 0 games |
| CLI authenticated | No; ladder command requests login | 1 read |
| CLI login initiation | `io: Connection refused` before credential entry | 2 attempts |
| Website signed in | No at this preflight | 1 browser observation |
| Replay download | HTTP 401 | 1 official bundle request |

No auth value was copied, printed or committed. Official assets were extracted
with `cambc mapeditor --no-browser`; its local server was stopped afterward.
Windows CLI checksums describe a different binary. The runtime briefly became
unavailable while checkpointing and then recovered; the local files were retained.

## Repository

The handoff's named working branch is `claude/compare-fix-replay-decoder`.
The analysis branch was created at its head
`294500b8c4da4af19a81f2cdb262305ea54d27f9`. Direct Git lacks authentication;
publication uses the GitHub connector with the complete parent tree. Main's older
README is not authoritative for the live site. The named branch contains newer
v59-v67 research, including the v67 disclosure of failed generalization.

## Actual input mismatch (measured, n=5 archives)

Attached archive sizes are 16, 16, 17, 17 and 17 files. The apex_c9.zip SHA-256 is
`dc27db72ce51ee9bb498668fe92927c163cf561ffed3efbdc5831fd41e0b1295`.
Against pinned bots/v58/src, 5 of its 17 shared paths match byte-for-byte; v58 has
33 source files. None of the five attachments is an exact full bot-tree match.
The master prompt's separate 29-of-33 comparison does not describe these actual
attachments. Git blob comparison is line-ending-sensitive; all individual
SHA-256 hashes are preserved in INPUT_PROVENANCE.json.

The expected `artifacts/local-only/live-src/bot.zip` is absent. An earlier
signed-in UI observation showed platform v69, note `v75 ladder duel candidate`.
That is historical evidence, not a current activation time or source hash.

## Decoder issue from source inspection

Shared engine.mjs supports explicit NFS_REPLAY_ENGINE=2.0.0; all three asset pins
match. The independent decode_replays.mjs still hardcodes engine 1.0.3 and an
engine_1_0_3 reconciliation condition. Setting the environment alone does not
migrate that decoder. It must be corrected or replaced, then checked on five
native-summary/replay pairs before current-engine bulk processing.

## Historical evidence guiding the next step

- V53_LIFE_ANALYSIS is historical engine-1 evidence; some old shopping timing was
  invalidated by the later fix counting purchases while champions are dead.
- V55_LADDER_ANALYSIS and V58_CLAUDUS_FINDINGS distinguish ordinary opponents from
  Claudus and document that copying draft or opening choices did not transfer.
- HANDOFF_V61 and V59_LOSS_ANALYSIS warn that lineage self-play did not predict
  ladder improvement; fewer deaths can also reflect surrendered farming.
- v66/RESULTS records later top-team tests. v67/README and CONTINUATION disclose
  substantial seed overfitting and failed independent-controller prototypes.

These reports do not establish today's live submission or its failure rates.
Resume at authenticated provenance, as STATE.md specifies.
