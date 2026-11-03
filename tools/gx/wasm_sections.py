"""Compare release modules while excluding data and custom sections."""
from hashlib import sha256
from pathlib import Path
import sys


def sections(path):
    blob = Path(path).read_bytes()
    if blob[:8] != bytes.fromhex('0061736d01000000'):
        raise ValueError(f'{path}: invalid Wasm header')
    p = 8
    while p < len(blob):
        sid = blob[p]
        p += 1
        n, shift = 0, 0
        while True:
            b = blob[p]
            p += 1
            n |= (b & 127) << shift
            if b < 128:
                break
            shift += 7
            if shift >= 35:
                raise ValueError(f'{path}: section length overflow')
        if p+n > len(blob):
            raise ValueError(f'{path}: truncated section')
        if sid not in (0, 11):
            yield sid, sha256(blob[p:p+n]).hexdigest()
        p += n


if __name__ == '__main__':
    base = list(sections(sys.argv[1]))
    for name in sys.argv[2:]:
        if list(sections(name)) != base:
            raise SystemExit(f'Non-data section differs: {name}')
    print(f'{len(sys.argv)-1} modules have identical executable sections')
