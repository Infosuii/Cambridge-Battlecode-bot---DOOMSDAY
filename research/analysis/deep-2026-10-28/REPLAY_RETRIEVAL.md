# Website replay retrieval and validation

Completed 2026-10-28T16:04:21.416097+00:00. **Measured: all 555 selected replay/native pairs pass.**

The signed-in official website's “Download 5 games” and per-game “Summary → Download JSON”
controls produced real files on Windows. No CLI login, browser-cookie extraction,
credential entry, new match request, upload, activation or account setting change was used.
One transient group-bundle failure succeeded on a subsequent sequential retry.

| Evidence | Count |
| --- | ---: |
| Frozen groups downloaded and CRC-checked | 111/111 |
| Distinct replay/native pairs decoded and reconciled | 555/555 |
| Calibration-only games, validated before bulk decoding | 5 |
| Accepted study games | 550 |
| Examined / hands-off accepted games | 385 / 165 |
| Physical champion gem/gold conservation checks | 5,356 / 5,356 |
| Current integrity exclusions | 0 |

Engine 2.0.0, build 85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21.
All three shipped visualiser asset pins pass. Each independent replay agrees with its
native summary on engine, outcome, rounds, final input, team submitted gems, physical
champion gold/gems/kills, per-team draft order and full dynamic roster. Internal native
collected = submitted + lost + carried and earned + refunds = spent + gold equations
pass for all 5,356 champion bodies. Draft/physical type names follow official SDK enums.

DOWNLOADS.json records all source ZIP/replay/summary SHA256 values and sizes.
RECONCILIATION.json records every boolean check, replay/summary hashes and decoder
identities. The original split and IDs are preserved in CANDIDATE_MANIFEST.json.
375 decoded rows were retained; only the remaining 180 were decoded in the final pass.

Local raw files: artifacts/local-only/deep-2026-10-28/bundles and
replays/{calibration-excluded,examined,hands-off}. Decoded action rows are in
artifacts/local-only/deep-2026-10-28/decoded.jsonl. They remain Git-ignored.
No decision trajectories were manually reviewed. Hands-off integrity checks were
automatic; no hands-off decision or detector outputs were exposed to the analysis.

Limitations: server-source hash and absolute activation time remain unverified;
the prior machine's raw catalog.json was not committed. Existing-game outcomes match
the frozen manifest and native states match replays; wave/top metadata scores are
also checked. This does not establish detector semantics, perspective correctness,
causal bugs, model calibration, swing moments or any new-bot recommendation.
Resume with threshold registration and D1-D11 validation on calibration games.
