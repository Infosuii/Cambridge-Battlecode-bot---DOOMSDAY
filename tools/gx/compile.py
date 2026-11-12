"""Build one frozen source and print its release digest."""
import argparse
from pathlib import Path
import re
import shutil
from dz import build, sha


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source', type=Path)
    cli.add_argument('output', type=Path)
    cli.add_argument('--set', action='append', default=[])
    args = cli.parse_args()
    output = args.output.resolve()
    frozen = output.with_suffix('')
    shutil.copytree(args.source/'src', frozen/'src')
    for flag in args.set:
        key, sep, val = flag.partition('=')
        if not sep or not re.fullmatch(r'[A-Z][A-Z0-9_]+',key) or not re.fullmatch(r'-?\d+(\.\d+f?)?',val):
            cli.error(f'Invalid definition: {flag}')
        path = frozen/'src'/('gx_config.h' if key.startswith('GX_') else 'x1_config.h')
        source = path.read_bytes()
        keyline = rb'(?m)^#define '+key.encode()+rb'[ \t]+[^\r\n]+'
        revised, count = re.subn(keyline, b'#define '+key.encode()+b' '+val.encode(), source)
        if count != 1:
            cli.error(f'Expected exactly one definition of {key}')
        path.write_bytes(revised)
    build(frozen,output)
    print(sha(output),output)


if __name__ == '__main__':
    main()
