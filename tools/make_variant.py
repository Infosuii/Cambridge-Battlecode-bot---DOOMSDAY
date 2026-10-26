"""Copy a bot and set compile-time switches in its src/common.h, for screening variants with bench3.

Usage: python tools/make_variant.py <base bot dir> <out bot dir> NAME=VALUE [NAME=VALUE ...]
Every `#define NAME ...` line in common.h gets the new value (guarded or not); a name with no such line is defined at
the top of the file. The output directory is replaced.
"""
import os
import re
import shutil
import stat
import sys
from pathlib import Path


def main():
    base, out, *pairs = sys.argv[1:]
    base, out = Path(base), Path(out)
    writable = lambda path: os.chmod(path, os.stat(path).st_mode | stat.S_IWRITE)
    if out.exists():
        shutil.rmtree(out, onerror=lambda fn, path, exc: (writable(path), fn(path)))
    shutil.copytree(base / 'src', out / 'src')
    for f in (out / 'src').iterdir():  # frozen release sources are read-only; the copy must be editable
        writable(f)
    header = out / 'src' / 'common.h'
    text = header.read_text(encoding='utf8')
    prepend = []
    for pair in pairs:
        name, value = pair.split('=', 1)
        pattern = re.compile(rf'^#define {re.escape(name)}\b.*$', re.M)
        text, n = pattern.subn(f'#define {name} {value}', text)
        if not n:
            prepend.append(f'#define {name} {value}')
    if prepend:
        text = '\n'.join(prepend) + '\n' + text
    header.write_text(text, encoding='utf8')
    (out / 'VARIANT.txt').write_text(f'base {base}\n' + '\n'.join(pairs) + '\n', encoding='utf8')
    print(out, pairs)


if __name__ == '__main__':
    main()
