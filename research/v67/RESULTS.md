# v67 experiments

Fixed 120-slot schedule. Margins are v67 minus opponent.

| Run | Change | Opponent | Seeds | Wins/games | Margin | Deaths/game | Kills/game | Gold/game | Fuel v67/opp | Faults v67/opp |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| b00-baseline | Unmodified v65 source fork; side/initiative baseline | v65 | [1, 2] | 136/240 | +81.9 | 14.07 | 12.84 | 6245 | 947/358 | 0/0 |
| b01-early-stats | Short jungle/damage opening then Bruiser damage and health stacks | v65 | [1, 2] | 110/240 | -19.2 | 14.53 | 12.30 | 5840 | 112/242 | 0/0 |
| b02-team-commander | Baseline items; enable shared team fight commander and focus orders | v65 | [1, 2] | 131/240 | +63.6 | 14.42 | 12.22 | 6205 | 598/135 | 0/0 |
| b03-economy-director | Baseline items; shared repeated camp jobs with primary and parallel crew | v65 | [1, 2] | 108/240 | -21.7 | 14.50 | 12.23 | 6150 | 111/112 | 0/0 |
| b04b-fish-meta | Fish per-map drafts and item milestones on baseline executor | v65 | [1, 2] | 81/240 | -159.3 | 19.94 | 12.30 | 6167 | 218/194 | 0/0 |
| b05-direct-combat | New bounded local-power controller, shared focus and early retreat; baseline draft/items | v65 | [1, 2] | 25/240 | -485.5 | 6.45 | 4.83 | 3920 | 74/95 | 0/0 |
| b06-life15 | Lower tactical life value; retain the baseline fight controller | v65 | [1, 2] | 137/240 | +108.0 | 14.02 | 12.95 | 6343 | 335/295 | 0/0 |
| b07-no-verdict-search | Use the existing analytic fight decision without playout override | v65 | [1, 2] | 121/240 | -2.5 | 14.72 | 12.13 | 6097 | 132/194 | 0/0 |
| b08-opening-rush | Opening pack invades enemy-side camp routes for 250 rounds | v65 | [1, 2] | 44/240 | -428.2 | 17.81 | 11.01 | 4343 | 151/142 | 0/0 |
| b09-original-item-path | Bypass the unconditional passive-heavy item opening | v65 | [1, 2] | 113/240 | +20.7 | 14.31 | 12.94 | 6460 | 476/283 | 0/0 |
| b10-melee-micro | Use the existing damage-risk tile micro for melee as well as ranged | v65 | [1, 2] | 95/240 | -147.3 | 17.57 | 9.76 | 5596 | 132/153 | 0/0 |
| b11-team-foundation | New shared positions/focus/rally protocol and one coordinated farm-combat-reset controller | v65 | [1, 2] | 0/240 | -803.3 | 15.30 | 1.81 | 1886 | 19/91 | 0/0 |
| b12-team-camp-execution | Team positions and economic controller with proven camp execution | v65 | [1, 2] | 3/240 | -732.5 | 16.85 | 1.98 | 2432 | 38/133 | 0/0 |
| b13b-team-local-economy | Shared positions and single combat controller; baseline local farm chooser with inferred on-site work and brain setup | v65 | [1, 2] | 6/240 | -836.9 | 15.72 | 1.69 | 1488 | 2087/84 | 0/0 |
| b14-winning-map-openings | Winning-team per-map drafts and coherent opening routes plus item milestones; baseline gameplay execution | v65 | [1, 2] | 77/240 | -189.4 | 14.71 | 10.39 | 5697 | 171/130 | 0/0 |
| b15-winning-drafts | Winning replay map drafts only | v65 | [1, 2] | 81/240 | -177.3 | 15.94 | 10.98 | 5729 | 396/317 | 0/0 |
| b16-winning-draft-items | Winning replay drafts and exact opening item milestones | v65 | [1, 2] | 76/240 | -206.2 | 16.50 | 10.62 | 5629 | 416/294 | 0/0 |
| b17-winning-draft-routes | Winning replay drafts and coordinated camp opening routes | v65 | [1, 2] | 80/240 | -182.5 | 14.94 | 10.25 | 5559 | 174/118 | 0/0 |
| b18-public-camp-state | Baseline with legal out-of-vision camp state and cooldown queries | v65 | [1, 2] | 126/240 | +55.7 | 14.35 | 12.82 | 6262 | 941/359 | 0/0 |
| b19-team-startup-fix | Fix new controller startup: always enter bounded field-building pass, allowing farm first job | v65 | [1, 2] | 7/240 | -749.2 | 17.88 | 1.95 | 2107 | 2077/103 | 0/0 |
| b20-tagged-team-foundation | Tagged position/job mailboxes and timed focus location in established gameplay pipeline; coordination actions off | v65 | [1, 2] | 95/240 | -119.1 | 15.11 | 11.95 | 5850 | 299/241 | 0/0 |
| b21-tagged-team-coordination | Tagged job/position sharing with fresh battle-location reinforcement trips and explicit focus target | v65 | [1, 2] | 91/240 | -139.3 | 16.43 | 12.83 | 5384 | 604/435 | 0/0 |
| b22-map-portfolio | One bot selects intact tested policies per map from seed1/2 training evidence; fresh combined-code validation, predicted222 only | v65 | [1, 2] | 195/240 | +409.1 | 12.86 | 15.75 | 7082 | 270/130 | 0/0 |
| b23-portfolio-calibration-base | Same map portfolio with volatile diagnostic policy control default -1; all choices still use map plan | v65 | [1, 2] | 196/240 | +409.8 | 12.85 | 15.75 | 7076 | 276/136 | 0/0 |
| b24-stable-map-selector | Stable data-only map/side policy assignment, selected from training results; complete fresh run, no holdout use | v65 | [1, 2] | 197/240 | +405.7 | 12.30 | 15.45 | 7034 | 263/142 | 0/0 |
| b26-calibrated-map-policy | Map/side assignment calibrated on identical executable code using only seeds1/2; predicted235, full rebuilt acceptance run | v65 | [1, 2] | 235/240 | +566.7 | 10.68 | 16.00 | 7099 | 356/125 | 0/0 |
| g28-frozen-vs-v61 | Frozen b26 source; required older-lineage guard | v61 | [1, 2] | 138/240 | +128.0 | 12.20 | 11.41 | 6044 | 311/83 | 0/0 |
| g28-frozen-vs-v58 | Frozen b26 source; required older-lineage guard | v58 | [1, 2] | 153/240 | +133.2 | 14.07 | 13.96 | 6428 | 339/108 | 0/0 |
| g28-frozen-vs-v66b | Frozen b26 source; required older-lineage guard | v66b | [1, 2] | 128/240 | +46.2 | 14.39 | 10.84 | 5949 | 329/130 | 0/0 |
| v27-fresh-seeds56 | Frozen b26 source on fresh development seeds; overfitting check, not reserved holdout | v65 | [5, 6] | 142/240 | +76.0 | 15.16 | 13.04 | 6136 | 326/134 | 0/0 |
| b33-arrival-fix | Fix arrived-on-site acknowledgement and stale arrival clearing in both tagged policies; preserve all current map assignments | v65 | [1, 2] | 223/240 | +530.3 | 10.97 | 15.75 | 7001 | 348/125 | 0/0 |
| v34-arrival-fix-seeds56 | First arrival-ack fix source snapshot on development seeds5/6; later cache-clear correction not included | v65 | [5, 6] | 135/240 | +76.3 | 15.27 | 13.20 | 6199 | 303/134 | 0/0 |
| b35-arrival-cache-complete | Complete arrival contract: authenticated acknowledgements, stale clearing, and job-change cache clearing in both tagged policies | v65 | [1, 2] | 226/240 | +541.4 | 10.85 | 15.69 | 7004 | 352/123 | 0/0 |
| v36-arrival-cache-seeds56 | Complete arrival-cache correction on development seeds5/6; exact frozen source audited | v65 | [5, 6] | 136/240 | +71.4 | 15.32 | 13.12 | 6180 | 303/132 | 0/0 |
