# EXP-006 mechanics check: 4 November 2026

MEASURED: an official engine 2.0.0 release probe returned submission multiplier 0.1, base duration 0, minimum duration 1, range 1. Thus bags of 1Ã¢â‚¬â€œ10 gems take one channel round. Probe source is a cache copy of v92 with one SDK-settings print at `main()` entry; output is retained in `artifacts/codex-p0/deposit-settings-probe/game/*.repl26a`, member `team-a.stdout`. This diagnostic is never uploaded.

The proposed zero-travel threshold is already covered by v92: `bots/v92/src/common.h:452` sets `APEX_NEAR_DIST=6`; `bots/v92/src/bot.cpp:4803` accepts any positive bag inside that distance, and `:4833` submits when distance is zero. Its lab adjustment is zero in the unmodified release. Combat, recall, hunting and objectives may take precedence; changing those priorities is a separate mechanism that the original card deliberately excluded.

Verdict: reject the proposed threshold change as redundant before a candidate build. A follow-up needs a development trace showing a safe one-turn opportunity lost specifically to a lower-value priority. No local win comparison, no ladder claim, no quota used.
