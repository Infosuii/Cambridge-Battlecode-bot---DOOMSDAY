# Continue on a fresh Windows or Linux laptop

Clone https://github.com/Infosuii/neural-networkk-battlecode and check out branch `dev/botx3-team-economy-20261102`. Run all commands from the repository root. Read AGENTS.md and HANDOFF.md first. Use the root latest files, not older historical handoffs. No ladder login/submission is authorized or required.

Install Git and Python3.12 (3.12.10 was used). Normal build/match/verification helpers use only Python's standard library. On Windows use the supplied `tools/vendor/cambc.exe`; on Linux install the official native Cambridge Battlecode CLI version4.0.0 and put `cambc` on PATH, or set `DZ_CAMBC` to its executable. Do not run the Windows executable as the native Linux tool. Match engine must be2.0.0, project SDK4.0.0 (`cambc.toml`), WASI SDK33/Clang22.1.0. First official build provisions the WASI SDK; this needs network access. Preserve the repository `cmake/` and `sdk/`; build through the CLI rather than assuming a root CMakeLists.txt exists. For local C++ unit tests install g++ or clang++ with C++20; use environment variable `DZ_CXX` if it is not on PATH. No GPU or training packages are needed.

```sh
python tools/botx3_resume.py verify
python tools/botx3_resume.py host-tests
python tools/botx3_resume.py build --bot bots/botx3_11 --name fresh_v11
```

The paused handoff verifies source and prebuilt Wasm without building. The latter two commands are for a resumed development session. Use a new build name each time. Rebuild on a new platform and compare a frozen local game's engine/results before treating old benchmark data as equivalent; native CLI hashes differ by platform. Frozen Wasm remains the exact historical comparison reference.

After the user resumes development, examples:

```sh
python tools/botx3_resume.py match --candidate bots/botx3_11/bot.wasm --opponent research/botx3-20261102/portable-opponents/x1.wasm --map maps/local-benchmarks/00rows.map26a --side A --name fresh_smoke
python tools/botx3_resume.py benchmark --candidate bots/botx3_11/bot.wasm --reference bots/botx3_1/bot.wasm --suite dev --name fresh_dev --workers 4
```

Check the desired map exists before using the example. `--suite broad` uses the46 spent maps; `--include-original` adds original x1. A full dev matrix is expensive: run a targeted game first. `--resume` checks exact input hashes before accepting existing results. Never silently mix different toolchains or inputs under a prior output name. `--set KEY=VALUE` changes a frozen new build; use matching runtime controls when isolating mechanisms. Release diagnostic flags must stay off.

For native replay analysis install Node>=20. `tools/replay/*.mjs` require engine assets. Set `NFS_REPLAY_ENGINE=2.0.0` and `NFS_REPLAY_ASSETS` to the actual CLI visualiser/assets directory; the default lookup is Windows-specific and engine default may be1.0.3. The CLI `view` command can unpack visualiser assets; close the viewer afterwards. Outer `.repl26a` is a ZIP: extract its inner `replay.repl26a` before passing it to binary readers. Read the chosen script's help/imports for entry points; native replay analysis is offline omniscient diagnosis only, never hidden bot input.

Optional map generation needs wasmtime50.0.1 and `BC_ENGINE_WASM` pointing at the actual engine2 mapeditor WASM. `cambc mapeditor --no-browser` unpacks assets; stop its server when finished. Inspect the generator's environment variables; do not copy the old machine's absolute dependency paths. Supplied maps suffice to resume without generation.

`handoff-botx3-latest/BOTX3_CONTINUATION_LATEST.zip` can overlay the clone if needed; verify its SHA256 against `ARCHIVE_SHA256.txt` and then run the helper's `verify`. Compact per-game archives can be extracted into the root to inspect logs. Large raw native game summaries/replays and machine toolchains are deliberately excluded. Linux continuation is supported by the portable helpers; this paused packaging has not executed a Linux build.
