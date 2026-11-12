# EXP-011 result

MEASURED. The unsubmitted `codex-nostage` release reproduced SHA-256 `4590e220824fa76e870d1c8e994b287bcc9aab1922aa127575d73714ec05e57f` in two independent directories. Disabling `CODEX_NO_STAGE` reproduced platform v80 / repo v92 / local SHA-256 `5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47`. The source diff from v92 contains only the switch and the alive-group call. Use `prepare_nostage.py` from the worktree and `cambc build --release` on each output.

The [frozen pool safety screen](NOSTAGE_POOL_SAFETY.json) paired 172 map/side cells against the hash-verified v92 opponent on engine 2.0.0. The candidate won 89 versus 86 (b/c 30/27, +1.74 percentage points in this single local draw). Zero faults and zero diagnostic codes in both arms. Total fuel suspensions fell from 160 to 133, with 28 each in round one and no round-one cell increase. Eight individual cells increased, including three that had no baseline suspensions. The largest change was 8 to 27 on 02the-pack, side B.

Verdict: L0 fails the frozen per-cell gate. Stop before the separate mechanism diagnostic, L1/L2 or ladder. There is no measured change in early camp damage or waiting from this run, and no evidence of pinned ladder strength. No ladder actions or holdout use. Do not derive a map exception or tune the requirement from the pool.
