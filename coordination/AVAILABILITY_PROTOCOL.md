# DOOMSDAY agent availability and reassignment

User instruction, 4 Nov 2026: reallocate work only after an agent has been inactive for **more than 30 minutes**, and detect its return without clashes. This protocol covers agent availability; it is not a job-completion monitor.

## Authority and source of truth

The canonical machine-readable registry is `coordination/availability.json` on branch `johndoe/agent-coordination`. The branch's latest registry blob SHA is the concurrency guard. Issue #6 contains control heartbeats, handoffs and alerts; issue #5 retains its existing JOHNDOE/CLAUDE format and ladder-lock protocol.

JOHNDOE is the primary dispatcher; Claude is the backup. Both may inspect availability, but **every ownership mutation must replace the registry using the currently fetched blob SHA**. GitHub rejects a stale-SHA update. On conflict, reload and recalculate; never force overwrite. Announce a handoff only after the registry mutation succeeds. Include a deterministic transition ID in the comment; retries must not duplicate a handoff. Local caches are not authoritative.

Each task has one current owner/session, an increasing `epoch`, required capabilities, a branch and its last accepted checkpoint. Branches and integration approvals are scoped to that epoch. A reassignment increments the epoch and revokes the previous owner. This fences cooperating workers; it cannot physically terminate a process on an unreachable computer. Nobody may integrate an old-epoch result or operate another owner's branch.

## Worker registration and proof of availability

All workers, including managers and Agent 2, should ACK this protocol in #6 and register a unique session ID. Initial participants get a 30-minute adoption window from publication; **do not retroactively label them offline from old sparse comments**.

Post a new comment at most every 10 minutes while the agent/controller can respond:

`[CONTROL] {"agent":"builder-g5070-1104","session":"unique-session","seq":1,"status":"ACTIVE","task_epochs":{"candidate-integration":1},"branch":"johndoe/qualifier-builder-g5070-1104","checkpoint":"commit-or-none","job_ids":[]}`

Use the exact registered agent/account/session and increasing sequence number. A new session first posts status `READY` with capabilities and waits for the current assignment before touching contested work. Accepted statuses are READY, ACTIVE, WAITING, USAGE_LIMIT and STOPPED. WAITING still requires controller heartbeats. USAGE_LIMIT/STOPPED reports are useful, but the 30-minute rule still applies unless the worker explicitly RELEASEs its tasks earlier.

Use GitHub's immutable **comment `created_at`**, not a timestamp inside the body, edit time, a future ETA or a commit's author date. Ignore edited/replayed/duplicate/old-sequence/unknown-session messages for lease renewal. Validate the posting account against registration; shared GitHub accounts alone do not distinguish agents, so agent/session fields matter. A new commit is a wake-up clue, not proof a controller is currently able to respond. Ask for a fresh READY response before assigning new work.

Automated job/process heartbeats are a different channel (`[RUNNER]`, job ID, PID, process start time, host and checkpoint). They **never renew the controller lease**: a long training job can outlive an agent's usage allowance. A returning manager must inspect actual checkpoint/job state before launching anything else.

## Timing and reassignment

Check every five minutes. Activity timeout is strictly `now - last_verified_controller_activity > 1,800 seconds`; exactly 30 minutes is not enough. With five-minute polling, detection is normally between 30 and 35 minutes after the last control activity, subject to the watcher running and API availability.

1. At 20 minutes without control activity, post one challenge in #6 with a fresh nonce. It does not revoke ownership. A valid fresh control response renews the lease; no alert for brief silence.
2. Only after the strict 30-minute threshold, and only after successful fresh reads of all relevant event pages and the registry, mark the controller `UNAVAILABLE_30M`. This means unavailable to the team, not a claim to know its physical device state or usage balance.
3. In the **same compare-and-swap registry write**, increment every affected task epoch, revoke its old owner and preserve the last accepted checkpoint. Do not leave both owners valid during a transfer.
4. Assign the work to a recently responsive, registered worker with matching capabilities, free capacity and no conflicting claim. Prefer the strong builder for heavy implementation/training; managers take coordination/review. If nobody suitable is available, mark the task READY_UNASSIGNED, post the exact blocker and retain it for the next available worker. Never pretend an assignment starts an offline computer.
5. A replacement ACKs the current epoch, checks original jobs/checkpoints and starts in a **new branch/run directory for that epoch**. Reuse completed artifacts only after provenance checks. Do not launch a second job over the same checkpoint, output directory or platform quota. Existing healthy jobs may continue; the replacement takes control only through verified access, otherwise it requests a safe handoff and works independently.

Loss of GitHub/network access is `MONITOR_UNKNOWN`, not evidence every worker is offline. Do not revoke/reallocate on failed or partial reads, missing pagination, an unparseable registry or clock uncertainty. Retry and report a prolonged monitoring failure. Backlogs are processed in server-time order after recovery; a real >30-minute control gap is still handled even if its late heartbeat arrives before the next poll.

## Return detection — only after a >30-minute absence

Only workers previously transitioned to UNAVAILABLE_30M are eligible for a return notification. New comments/registered-branch pushes can trigger a challenge; a valid fresh controller READY response establishes `RETURNING`. Short gaps never emit OFFLINE or RETURNED events.

Returning workers **do not reclaim old tasks**. They must read the current registry, stop/quarantine obsolete writers, report live jobs/checkpoints and ACK a current epoch/new assignment. Their old commits remain on their old branch for review; they cannot replace the replacement's work. Renewing an old-epoch task is forbidden, even if a late response was queued before the handoff.

## Ladder and emergency handling

Task reassignment is not a ladder-lock takeover. If an unavailable worker could still be submitting, uploading, activating or running a duel, set platform state QUARANTINED. Claude/current authorized coordinator verifies active version and outstanding operations through the platform before any new ladder holder operates. Preserve the latest #5 promotion/restoration policy. Never auto-UNLOCK a possibly running operation solely because its owner is silent.

If JOHNDOE becomes unavailable, Claude can dispatch using the same CAS/epochs. If Claude becomes unavailable, JOHNDOE takes its coordination tasks subject to existing platform authority and verified state. If all available agents or their schedulers stop, automatic reassignment cannot run until one returns; the shared registry preserves what must happen next.

## Rollout

The user authorized this availability protocol. Workers need to ACK/adopt its checks for fencing to work; until then report adoption as pending, not guaranteed. Existing workload, deadlines and frozen baselines remain in force. Keep current candidate ownership until an explicit release or a verified >30-minute lapse. Notify the user only on an actual lapse, reassignment, confirmed return or a material blocker—not every poll.
