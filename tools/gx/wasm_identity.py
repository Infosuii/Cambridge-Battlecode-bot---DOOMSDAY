"""Make an inertly labelled copy for a deterministic replay control."""
import argparse
from pathlib import Path


def uleb(n):
    out = bytearray()
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('dest',type=Path)
    a=p.parse_args()
    b=a.source.read_bytes()
    if b[:8] != b'\0asm\x01\0\0\0':
        p.error('source is not a Wasm module')
    label=b'gx-diagnostic-identity'
    payload=uleb(len(label))+label+b'unchanged executable and data'
    with a.dest.open('xb') as f:
        f.write(b+b'\0'+uleb(len(payload))+payload)


if __name__=='__main__':
    main()
