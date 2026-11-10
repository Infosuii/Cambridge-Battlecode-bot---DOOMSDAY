"""CL_BUMP for v137 (v135 lineage): a tile a move bounced off (move_absolute false: an unseen unit or ward holds it;
the engine reveals it for one round only) is remembered for CL_BUMP rounds. follow_field and greedy_step skip it, and
when the only way on is such a tile, follow_field steps around it at the same field distance instead of bumping
into it every turn (03twisty ladder game: Vendetta tried the same tile 67 rounds running).
usage: bump_patch.py SRC"""
import sys


def patch(path, old, new, count=1):
    t = open(path, encoding="utf-8", newline="").read()
    assert t.count(old) == count, (path, old[:70], t.count(old))
    open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new))


src = sys.argv[1]
patch(src + "/common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_BUMP 12\n")
patch(src + "/bot.h", "    bool walked = false;\n",
      "    // CL_BUMP: tiles a move bounced off (an unseen unit or ward holds them), kept for CL_BUMP rounds.\n"
      "    std::array<vec2, 8> bump_tile{};\n"
      "    std::array<int, 8> bump_until{{-1, -1, -1, -1, -1, -1, -1, -1}};\n"
      "    int bump_next = 0;\n"
      "    bool bumped(vec2 q) const {\n"
      "        for (int i = 0; i < 8; ++i)\n"
      "            if (bump_until[i] >= round && bump_tile[i] == q) return true;\n"
      "        return false;\n"
      "    }\n"
      "    void note_bump(vec2 q) {\n"
      "        bump_tile[bump_next] = q;\n"
      "        bump_until[bump_next] = round + CL_BUMP;\n"
      "        bump_next = (bump_next + 1) & 7;\n"
      "    }\n"
      "    bool walked = false;\n")
B = src + "/bot.cpp"
patch(B, "    std::array<Cand, 8> cands{};\n    int n = 0;\n    for (vec2 dir : kDirs) {\n        const vec2 q = pos + dir;\n"
         "        if (!in_bounds(q, w.width, w.height) || bit(blocked, q)) continue;\n"
         "        const std::uint16_t dq = fdist(field, q);\n        if (dq == kUnreach || dq >= here) continue;\n",
      "    std::array<Cand, 8> cands{};\n    int n = 0;\n    bool bump_skipped = false;\n    for (vec2 dir : kDirs) {\n        const vec2 q = pos + dir;\n"
      "        if (!in_bounds(q, w.width, w.height) || bit(blocked, q)) continue;\n"
      "        const std::uint16_t dq = fdist(field, q);\n        if (dq == kUnreach || dq >= here) continue;\n"
      "        if (CL_BUMP && bumped(q)) {\n            bump_skipped = true;\n            continue;\n        }\n")
patch(B, "        cands[n++] = {q, dq * 4 + ((dir.x != 0 && dir.y != 0) ? 0 : 1)};\n    }\n"
         "    std::sort(cands.begin(), cands.begin() + n, [](const Cand& a, const Cand& b) { return a.score < b.score; });\n",
      "        cands[n++] = {q, dq * 4 + ((dir.x != 0 && dir.y != 0) ? 0 : 1)};\n    }\n"
      "    if (CL_BUMP && n == 0 && bump_skipped)\n"
      "        for (vec2 dir : kDirs) {\n"
      "            // CL_BUMP: the way on is a tile a move bounced off; step around it at the same distance.\n"
      "            const vec2 q = pos + dir;\n"
      "            if (!in_bounds(q, w.width, w.height) || bit(blocked, q) || bumped(q)) continue;\n"
      "            if (fdist(field, q) == here) cands[n++] = {q, here * 4};\n"
      "        }\n"
      "    std::sort(cands.begin(), cands.begin() + n, [](const Cand& a, const Cand& b) { return a.score < b.score; });\n")
t = open(B, encoding="utf-8", newline="").read()
old_mv = ("            if (me.move_absolute(cands[i].p)) {\n                pos = cands[i].p;\n                walked = true;\n"
          "                return true;\n            }\n        } catch (const std::exception& e) {\n")
n_mv = t.count(old_mv)
assert n_mv >= 1, "move loop not found"
patch(B, old_mv, old_mv.replace("            }\n        } catch", "            }\n            if (CL_BUMP) note_bump(cands[i].p);\n        } catch"), count=n_mv)
patch(B, "        if (!in_bounds(q, w.width, w.height) || bit(blocked, q)) continue;\n        const int d = cheb(q, goal);\n",
      "        if (!in_bounds(q, w.width, w.height) || bit(blocked, q) || (CL_BUMP && bumped(q))) continue;\n        const int d = cheb(q, goal);\n")
patch(B, "        if (me.move_absolute(best)) {\n            pos = best;\n            walked = true;\n            return true;\n        }\n"
         "    } catch (const std::exception& e) {\n        LOG(\"greedy step error %s\\n\", e.what());\n",
      "        if (me.move_absolute(best)) {\n            pos = best;\n            walked = true;\n            return true;\n        }\n"
      "        if (CL_BUMP) note_bump(best);\n"
      "    } catch (const std::exception& e) {\n        LOG(\"greedy step error %s\\n\", e.what());\n")
print("applied bump (move loops patched: %d)" % n_mv)
