"""Extract a native replay from a committed DZ capsule for offline readers."""
import argparse
import io
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--map', required=True)
    parser.add_argument('--side', choices=('A', 'B'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not all(re.fullmatch(r'[A-Za-z0-9_-]+', value) for value in (args.run, args.map)):
        parser.error('Run and map names must be simple identifiers')
    prefix = f'games/{args.map}-{args.side}/'
    with zipfile.ZipFile(ROOT/'research/dz/runs'/args.run/'evidence.zip') as archive:
        bundles = [name for name in archive.namelist() if name.startswith(prefix)
                   and name.endswith('.repl26a')
                   and Path(name).name not in ('lifecycle.repl26a', 'priority.repl26a')]
        if len(bundles) != 1:
            raise ValueError(f'Expected one replay bundle, found {len(bundles)}')
        with zipfile.ZipFile(io.BytesIO(archive.read(bundles[0]))) as bundle:
            payload = bundle.read('replay.repl26a')
    output = args.output.resolve()
    if output.is_relative_to((ROOT/'research/dz/runs').resolve()):
        raise ValueError('Completed experiment capsules are immutable; use artifacts/tmp')
    if output.exists() and output.read_bytes() != payload:
        raise FileExistsError('Refusing to overwrite different existing content')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    print(f'{len(payload)} bytes -> {output}')


if __name__ == '__main__':
    main()
