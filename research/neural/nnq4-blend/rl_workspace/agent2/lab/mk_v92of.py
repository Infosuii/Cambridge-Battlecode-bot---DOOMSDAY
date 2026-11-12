"""v4/bots/v92of = v92 with the official-map check fixed: v92's is_official_map() (old nova_map_id table) recognises
only 15 of the 70 current ladder maps, so on 55 ladder maps v92 runs its unseen-map rules (NOVA_GOLD_UNSEEN gold weight,
NOVA_DUO_MAPS). The fix also accepts v92's own ladfit fingerprints (width, height, camp groups, total group gems) of all
70 ladder maps. Note: ladfit's per-map corrections were fitted with the old behaviour, so this must be measured.
usage (project root): python -P agent2/lab/mk_v92of.py"""
import os, shutil, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = os.path.join(ROOT, "v4", "bots")
shutil.rmtree(os.path.join(B, "v92of"), ignore_errors=True)
shutil.copytree(os.path.join(B, "v92"), os.path.join(B, "v92of"), ignore=shutil.ignore_patterns(".cambc"))
p = os.path.join(B, "v92of", "src", "bot.cpp")
s = open(p, encoding="utf-8").read()
old = """        official_map = nova_map_id(static_cast<int>(bc::map::width()), static_cast<int>(bc::map::height()), picks, ng) >= 0;
    }"""
new = """        official_map = nova_map_id(static_cast<int>(bc::map::width()), static_cast<int>(bc::map::height()), picks, ng) >= 0;
        if (official_map == 0 && inited) {
            // the current 70-map ladder pool (ladfit fingerprints), which the old table above mostly misses
            unsigned total = 0;
            for (const auto& g : w.groups) total += g.gems;
            for (int m = 0; m < 70; ++m) {
                const auto& fp = ladfit::kFp[m];
                if (fp.w == w.width && fp.h == w.height && fp.groups == static_cast<int>(w.groups.size()) && fp.gems == total) official_map = 1;
            }
        }
    }"""
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="\n").write(s)
r = subprocess.run([os.path.join(ROOT, "v4", "cambc.exe"), "build", "bots/v92of", "--release"], cwd=os.path.join(ROOT, "v4"), capture_output=True, text=True)
ok = r.returncode == 0 and os.path.exists(os.path.join(B, "v92of", ".cambc", "build-release", "bot.wasm"))
print("v92of", "built" if ok else "BUILD FAILED\n" + "\n".join(l for l in (r.stdout + r.stderr).splitlines() if "error" in l)[:2000])
