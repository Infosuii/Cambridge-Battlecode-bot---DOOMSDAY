# Prompt for the agent taking over from Claude

Paste everything below the line into the new agent's first message.

---

You are taking over Claude's work for team DOOMSDAY in Cambridge Battlecode 2026, on the user's Windows laptop. Claude has stopped and none of its jobs are running. The UK qualifier lock is Tue 10 Nov 23:59 GMT.

1. **Work in** `C:\Users\info\neural-networkk-battlecode`, a git repo; use branch `claude/rl-env-1104`. Before doing anything else, read sections 0–4 of `research/rl_env_1104/HANDOVER_2026-11-09.md`.
2. **Ask me for the access in its section 2:**
   - the folders and programs listed there, with network access to github.com and the Battlecode platform;
   - confirmation of the four permissions in section 2d.

   Never ask for passwords or tokens: GitHub and the `cambc` CLI are already logged in on this laptop.
3. **Run the access check** in Git Bash: `bash tools/rl_env_1104/handover_check.sh`. It is read-only and should end with `summary: 0 missing`. Tell me about anything missing or any warning.
4. **Check the ladder before any action on it:**
   - Run `cambc submissions list`.
   - Another workstream, Om's Codex agent, is uploading versions (handover section 4). Don't upload or activate until I've told you who controls the live version.
   - The `cambc` login here expires about Tue 10 Nov 15:33 UTC. Remind me to run `cambc login` before then.
5. **Then work** from section 9 of the handover. Keep GitHub pushes small (text only) and never push to `main` or `build/z-plan`.
