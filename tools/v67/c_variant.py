"""Make a variant bot folder from a base: macro overrides in common.h and A2_KNOBS entries by index.

Usage: c_variant.py --base artifacts/tmp/v67/c-b06 --out artifacts/tmp/v67/NAME [--set NAME=VALUE] [--knob I=VALUE]
The base folder is never modified. --knob replaces knob I of the baked A2_KNOBS list (0-based).
"""
import argparse
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--set', action='append', default=[], metavar='NAME=VALUE')
    ap.add_argument('--knob', action='append', default=[], metavar='I=VALUE')
    a = ap.parse_args()
    base, out = ROOT / a.base, ROOT / a.out
    assert out.resolve().is_relative_to(ROOT / 'artifacts/tmp/v67') and not out.exists()
    shutil.copytree(base / 'src', out / 'src', copy_function=shutil.copyfile)
    common = out / 'src/common.h'
    code = common.read_bytes().decode('utf8')
    end = '\r\n' if '\r\n' in code else '\n'
    for setting in a.set:
        name, value = setting.split('=', 1)
        pattern = rf'(^#define {name} )[^\r\n]*'
        if re.search(pattern, code, flags=re.M):
            code = re.sub(pattern, lambda m: m[1] + value, code, count=1, flags=re.M)
        else:
            code = f'#define {name} {value}{end}' + code
    if a.knob:
        m = re.search(r'^#define A2_KNOBS ([^\r\n]*)', code, flags=re.M)
        knobs = m[1].split(',')
        for setting in a.knob:
            i, value = setting.split('=', 1)
            knobs[int(i)] = value
        code = code[:m.start(1)] + ','.join(knobs) + code[m.end(1):]
    common.write_bytes(code.encode('utf8'))
    (out / 'VARIANT.txt').write_text(f'base {a.base}\nset {a.set}\nknob {a.knob}\n', encoding='utf8')
    print('prepared', out)


if __name__ == '__main__':
    main()
