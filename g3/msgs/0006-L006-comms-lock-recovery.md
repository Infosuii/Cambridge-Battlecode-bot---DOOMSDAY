# 0006: L006 communications lock interruption recovered

At07:55 UTC the heartbeat pull overlapped the campaign's iteration5 push on00great-wall, causing an index-lock error. All six iterations/state and local evidence are preserved; no evaluation rerun is needed. No fit process remains running before restart.
Added a g3-only OS file-lock wrapper tools/x3_g3_comms.py and switched the campaign to it. Future heartbeat pulls use that same wrapper. Completed+reported maps are skipped on resume; the finished great-wall state is reported/committed on restart, then map5 follows. No stale lock is deleted and no work is discarded.
