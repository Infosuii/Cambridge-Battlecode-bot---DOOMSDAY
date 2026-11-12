# From meta evidence to a future decision system

This is an implementation brief, not an implemented bot. All performance expectations below are hypotheses unless explicitly described as mechanics or measured replay behaviour. A deterministic hierarchical controller is a reasonable starting point; this dataset does not establish a need for a neural network. The dominant requirements are coherent state, feasible jobs, bounded compute and correct conversion timing.

## 1. Draft and static map plan

Inputs: full draft-visible terrain, spawn regions, camp-group membership and rewards, altar fronts, pick count, own/revealed enemy picks. Enumerate 220/495/792 own-unique sets for 3/4/5 slots. Evaluate a small number of mechanically defined roles: repeated clear damage, neutral survival, reward receiver, durable delivery, access specialist and support. A body may cover several jobs; Cassi & Issac supplies two linked bodies.

Score whether each set can complete representative opening groups, reach safe banking tiles and solve mandatory gates within the likely horizon. Discount redundant roles and linked-bag risk. Use actual cluster shares when pricing Prospector and carried-gem Focus when pricing Prism. Candidate complexity is O(number of legal sets × representative jobs), with cached static distances. Draft receives substantial extra fuel, but the search should have an incumbent legal set at all times. Failure modes: wrong damage assumptions, unobserved enemy responses, overfitting dimensions instead of geometry. No future enemy pick is a legal input.

Write a compact static plan to 1024-byte draft memory: route-front anchors, group associations, opener role preferences and a few mobility edges. Keep ordinary play's shared 8-byte state for current claims/role changes, not a full global world model.

## 2. Objective allocator

Inputs: personal observed state, immutable map data, own body inventory, recent sightings with age, shared claims. Candidate jobs: clear a group; finish/maintain a capture; shop/recover; bank; open/deny access; protect a valuable carrier. Score expected *delivered* gem value plus downstream income/positioning, divided by travel+clear+capture+delivery cost, minus death/bag risk and displacement of another useful worker.

Estimate costs for one or a small coalition. Separate who supplies damage from who should be on the region at payout. Additional allies do not speed capture; a Capture holder can change the remaining timer. Prefer a nearby suitable receiver to a long transfer to an ideal passive. Use actual same-group membership and reset rules. Candidate count O(groups × small coalition templates); cache static terms, refresh threat-dependent terms once per turn. Failure modes: hidden ally assignments, stale claims, enemy contest and underestimated gate HP.

Keep an incumbent objective and require a material gain before switching, except for imminent death or a winning bank. Hysteresis must not prevent a known access change or near-finished useful capture. Existing DOOMSDAY already has claims, route search and dormant planning code; improve a measured binding model before adding another controller layer.

## 3. Role-conditioned purchasing

Inputs: exact own gold/equipment, shopping legality, next feasible jobs and expected horizon. Candidate actions: finish one useful emblem, add immediate main-stat/health shards, buy a crystal/lock, or defer a trip. Compare the marginal change in the next two objective cycles, including survival, route travel and channel time.

Rules worth isolated tests: Prospector only when expected qualifying cluster shares justify it; Jungle when neutral HP loss forces costly recovery; Monster/Power when clear time is limiting; Capture when region waiting is material; Tribute when long channels constrain delivered score; Treasure when future income horizon and opportunity cost justify it. Choose stat variants from the actual champion kit. Do not repeatedly buy a passive merely to obtain its effect twice.

This can be O(number of next milestones × cached job estimates). It should run at shopping decisions, not inside every camp-scoring loop. Failure modes: overoptimistic income horizon, an early death before repayment and ignoring a soon-completing capture. The study provides observed build examples and arithmetic, not a validated universal order.

## 4. Banking and access scheduler

Inputs: own bag/passive, submitted scores, remaining rounds, feasible altar fronts, current locks/capture states, nearby observed threats, planned teammate delivery if communicated. Candidates: direct bank, another capture then bank, start tribute while maintaining capture, open gate, reroute, or retain scaling gems while another body scores.

Compare completion time and probability of a delivered win. A safe winning completion should dominate gross farming. Near the limit, optimise the actual tiebreak order. A retained Prism bag has damage value; a Marcella bank has gold feedback. An escorted channel can be worth another body's lost farm when it changes completion probability materially.

Special candidate: if the actor has a positive bag and stands on a capturable region adjacent to a usable altar, start tribute before the imminent payout when safe. Duration is set from the starting bag, and later capture rewards enter the completed bag. The boss_battle traces verify 109→309 and 49→249. Simulate phase order and lock/stun threats before treating it as a generally safe exploit. An empty bag cannot start a tribute. Complexity O(reachable fronts + a few short plans); retain a simple feasible fallback.

## 5. Combat sequence evaluator

Inputs: personal visible enemies/camps, own cooldowns/abilities/stats, legal action masks, bag value, escape-front accessibility. Enumerate a small grammar of move, basic attack, one cast, reset follow-up, retreat or channel. Preserve ranged shared allowances and the one-cast limit. Evaluate threat removed, bag transfer/denial, expected incoming damage, objective access and next-turn safety.

Vendetta can reset on a camp monster kill; Heart's shield/missing-health state can alter risk; stuns and altar locks affect a tribute differently from damage. Counter linked bodies and exposed carriers by their actual objective value. Avoid using omniscient enemy inventory or invisible cooldowns. Complexity O(local targets × a bounded sequence set), gated by contact and a fuel reserve. Failure modes: hidden attackers, stale sightings, ground-effect undercount and greedy kills that lose the scoring race.

## 6. Coordination and limited information

Use roles and shared claims as compact commitments with expiry. Priority can schedule next round, not reorder the current one. Communicate only information that fits the 8-byte budget; a small claim/role/generation protocol is more credible than a large team blackboard. Personal ward placement should reveal a useful route or objective threat. A researcher's union of allied views is not the acting bot's observation.

Do not infer opponent intent with certainty. A team/champion's recurring first-emblem family predicts 89/103 later-body observations in a retrospective temporal diagnostic, but map and unknown submission changes explain exceptions. That result is useful for hypothesis generation, not a clean model-validation result. A future opponent model should output uncertainty and prefer a robust legal response.

## 7. Compute and experiment boundaries

C++ has 100k normal-turn fuel. Put static work in draft, cache repeated metadata/distances, update expensive risk/objective values once per turn, and always have a cheap legal action before deeper search. Fuel suspension resumes execution, so stale intermediate assumptions are a distinct hazard from a crash. Budget profiling must measure decision freshness and accepted actions as well as suspension count.

Implement nothing from this document without separate instruction. When implementation is authorised, first verify source identity, reproduce the baseline trajectory and isolate one mechanism. Use the repository's development-map/default-fuel gates and map/group-clustered uncertainty. Final maps and historical research confirmation sets with prior exposure are not fresh holdouts. A first-gate success is not a ladder-strength claim; external-opponent evidence is eventually necessary, but no new match requests were made here.
