# 0003: findings protocol (from Rishik)

Rishik's instruction: **any findings file you push, the PC handles what happens next and the changes to the plan.**

- Put findings in g5060/results/Jnnn.md (job results) or g5060/findings/nnnn-title.md (anything else you notice:
  bugs, odd games, tool problems, ideas). State facts and numbers; a proposal is welcome but marked as a proposal.
- The PC reads every one, decides, updates research/x1/PLAN_TWO_MACHINES.md / RETRY_QUEUE.md on build/z-plan, and
  answers in pc/STATUS.md (and a pc/msgs reply when it changes your queue). You don't change the plan yourself and
  don't wait for approval on jobs already posted: keep running the queue.
- Also new: research/x1-audit-2026-11-02 (branch, by ishanp765) audited x1 from 35 replays; its fixes are J007.
  Read its REPORT.md for context. Note: many v81hl switches are set unconditionally in common.h's profile block
  (e.g. A2_KITFIX 25, A2_BRIDGES 1, A2_APPROACHFIX 1), so a sweep entry "same binary as x1" can mean "already on /
  not overridable by --set", not dead code. For J002, list those separately instead of as dead.
