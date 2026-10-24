"""Lead bisection of neutral_credit divergence: build neutral_credit variants with parts disabled and compare each with
the original on A's equivalence fixtures (6 maps x 2 sides vs original). Variants are scratch-only edits.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
sys.path.insert(0, str(ROOT / 'tools'))
from nfs import engine  # noqa: E402
import lead_profile_check as lpc  # noqa: E402

VARIANTS = {
    # no teacher captures at all (only runtime turn hooks + linked runtime)
    'no_captures': [('nn_teacher.h', 'constexpr bool on(nncfg::H h) { return nncfg::mode(h) != nncfg::Mode::off; }',
                     'constexpr bool on(nncfg::H h) { return (void)h, false; }')],
    # captures, but no turn hooks (begin_turn kept)
    'no_hooks': [('main.cpp', '                    nnh::turn_start();\n', ''),
                 ('main.cpp', '                nnh::idle();\n', ''),
                 ('main.cpp', '                nnh::warmup(); // after the draft decision: verify installed model checksums with the 10x draft fuel\n', '')],
    # neither
    'bare': [('nn_teacher.h', 'constexpr bool on(nncfg::H h) { return nncfg::mode(h) != nncfg::Mode::off; }',
              'constexpr bool on(nncfg::H h) { return (void)h, false; }'),
             ('main.cpp', '                    nnh::turn_start();\n', ''),
             ('main.cpp', '                nnh::idle();\n', ''),
             ('main.cpp', '                nnh::warmup(); // after the draft decision: verify installed model checksums with the 10x draft fuel\n', '')],
    # bare and no fuel credit (teacher_left == fuel_remaining exactly)
    'bare_nocredit': [('nn_teacher.h', 'constexpr bool on(nncfg::H h) { return nncfg::mode(h) != nncfg::Mode::off; }',
                       'constexpr bool on(nncfg::H h) { return (void)h, false; }'),
                      ('main.cpp', '                    nnh::turn_start();\n', ''),
                      ('main.cpp', '                nnh::idle();\n', ''),
                      ('main.cpp', '                nnh::warmup(); // after the draft decision: verify installed model checksums with the 10x draft fuel\n', ''),
                      ('nn_config.h', 'inline constexpr bool kFuelCredit = true;', 'inline constexpr bool kFuelCredit = false;')],
    # control on the ORIGINAL: ~40 fuel burned at the start of every gameplay turn (sensitivity to tiny pre-decision spend)
    'orig_burn40': 'ORIG',
}
ORIG_BURN = ('main.cpp', '                bot.play_turn();\n',
             '                { volatile unsigned s = 0; for (unsigned i = 0; i < 4; ++i) s = s + i; }\n'
             '                bot.play_turn();\n')


def main():
    names = sys.argv[1:] or list(VARIANTS)
    out = {}
    for v in names:
        lpc.build_profile('neutral_credit')
        base = ROOT / 'artifacts/tmp/profiles/neutral_credit'
        d = ROOT / 'artifacts/tmp/bisect' / v
        edits = VARIANTS[v]
        if edits == 'ORIG':
            base, edits = None, [ORIG_BURN]
        engine.make_bot_dir(base / 'src' if base else ROOT / 'references/original-src', d)
        for f, old, new in edits:
            p = d / 'src' / f
            s = p.read_text(encoding='utf-8')
            if old not in s:
                raise SystemExit(f'{v}: pattern missing in {f}: {old[:60]}')
            p.write_text(s.replace(old, new), encoding='utf-8', newline='\n')
        w = engine.official_build(d, d / f'{v}.wasm')
        rep = d / 'eq.json'
        subprocess.run([sys.executable, str(ROOT / 'tools/audit_equivalence.py'), 'compare', '--candidate', str(w),
                        '--label', f'bisect_{v}', '--opponents', 'original', '--maps', '6', '--out', str(rep)],
                       cwd=ROOT, capture_output=True, text=True)
        r = json.loads(rep.read_text(encoding='utf-8'))
        out[v] = {k: r.get(k) for k in ('n_cells', 'n_equal', 'outcome_changes')}
        print(v, out[v], flush=True)
    engine.write_json(ROOT / 'evaluation/results/neutral_bisect.json', out)


if __name__ == '__main__':
    main()
