"""Instrument World::init's camp-group loop (probe copy only): fuel spent in the group host calls, the GroupRec
emplace, the per-camp host calls and the CampRec work, printed once as INITSPLIT.
usage: instr_init.py WORLD_CPP"""
import sys

p = sys.argv[1]
t = open(p, encoding="utf-8", newline="").read()


def rep(old, new):
    global t
    assert t.count(old) == 1, old[:60]
    t = t.replace(old, new)


rep("    for (std::uint32_t k = 0; k < n_groups; ++k) {\n        const std::uint32_t h = handles[k];\n",
    "    std::uint64_t f_gcalls = 0, f_emplace = 0, f_ccalls = 0, f_crec = 0, f_mark = 0;\n"
    "    for (std::uint32_t k = 0; k < n_groups; ++k) {\n        f_mark = bc::fuel_remaining();\n        const std::uint32_t h = handles[k];\n")
rep("        d::check(d::sdk_map_camp_group_camps(h, spawns, members, &members));\n        GroupRec& rec = groups.emplace_back();\n",
    "        d::check(d::sdk_map_camp_group_camps(h, spawns, members, &members));\n"
    "        f_gcalls += f_mark - bc::fuel_remaining(); f_mark = bc::fuel_remaining();\n"
    "        GroupRec& rec = groups.emplace_back();\n")
rep("        rec.camps.reserve(members);\n        for (std::uint32_t m = 0; m < members; ++m) {\n            d::camp_info spec{};\n            d::check(d::sdk_map_camp_info(spawns[m], &spec));\n",
    "        rec.camps.reserve(members);\n        f_emplace += f_mark - bc::fuel_remaining(); f_mark = bc::fuel_remaining();\n"
    "        for (std::uint32_t m = 0; m < members; ++m) {\n            d::camp_info spec{};\n            d::check(d::sdk_map_camp_info(spawns[m], &spec));\n")
rep("            const d::camp_design& design = designs[kind];\n",
    "            f_ccalls += f_mark - bc::fuel_remaining(); f_mark = bc::fuel_remaining();\n            const d::camp_design& design = designs[kind];\n")
rep("            camps.push_back(cr);\n        }\n    }\n    mark(\"group_loop\");\n",
    "            camps.push_back(cr);\n            f_crec += f_mark - bc::fuel_remaining(); f_mark = bc::fuel_remaining();\n        }\n    }\n"
    "    std::printf(\"INITSPLIT gcalls %llu emplace %llu ccalls %llu crec %llu groups %u sizeof_GroupRec %zu\\n\", "
    "static_cast<unsigned long long>(f_gcalls), static_cast<unsigned long long>(f_emplace), static_cast<unsigned long long>(f_ccalls), "
    "static_cast<unsigned long long>(f_crec), n_groups, sizeof(GroupRec));\n"
    "    mark(\"group_loop\");\n")
open(p, "w", encoding="utf-8", newline="").write(t)
print("instrumented")
