"""Compose separate source variants into a fresh bot tree for an interaction check."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def file_map(root):
    return {p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}


def merge_three(old, x, y, name):
    with tempfile.TemporaryDirectory(prefix='gx-compose-') as scratch:
        scratch = Path(scratch)
        for label, data in (('active', x),('base', old),('addition', y)):
            (scratch/label).write_bytes(data)
        p = subprocess.run(['git','merge-file','-p',str(scratch/'active'),str(scratch/'base'),
                            str(scratch/'addition')], capture_output=True)
        if p.returncode == 0:
            return p.stdout
        # Git can report two additions at the same include anchor when both
        # add gx_config.h and one also adds its private implementation header.
        # Accept that specific conflict and leave all source conflicts for review.
        conflict = re.compile(rb'^<<<<<<< [^\n]+\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]+\n', re.M | re.S)
        def extra_include(m):
            first, second = m.group(1,2)
            only = first or second
            if (not first or not second) and re.fullmatch(rb'(?:#include "gx_[a-z0-9_]+\.h"\n)+', only):
                return only
            return m.group()
        merged, seen = conflict.subn(extra_include,p.stdout)
        if not seen or conflict.search(merged):
            raise ValueError(f'{name}: overlapping edits require a source review')
        return merged


def compose(base, inputs):
    config = Path('gx_config.h')
    dst = file_map(base)
    stock = dict(dst)
    defs = {}
    for bot in inputs:
        for name, content in file_map(bot).items():
            if name == config:
                content = re.sub(rb'(?m)^#pragma once\s*',b'',content)
                for macro in re.findall(rb'(?m)^#define\s+(GX_[A-Z0-9_]+)\s', content):
                    if macro in defs:
                        raise ValueError(f'{bot} duplicates {macro.decode()} from {defs[macro]}')
                    defs[macro] = bot
                dst[config] = dst.get(config,b'#pragma once\n\n') + content.strip() + b'\n\n'
                continue
            old = stock.get(name)
            cur = dst.get(name)
            if content == old or content == cur:
                continue
            if cur == old:
                dst[name] = content
            elif old is not None:
                dst[name] = merge_three(old,cur,content,name)
            else:
                raise ValueError(f'{name}: conflicting new file')
    if config in dst:
        dst[config] = dst[config].rstrip() + b'\n'
    return dst


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('baseline_src',type=Path)
    p.add_argument('dest_bot',type=Path)
    p.add_argument('variant_src',type=Path,nargs='+')
    a=p.parse_args()
    if a.dest_bot.exists():
        p.error('Choose a fresh bot directory')
    files=compose(a.baseline_src,a.variant_src)
    dst = a.dest_bot/'src'
    dst.mkdir(parents=True)
    try:
        for name,content in files.items():
            out = dst/name
            out.parent.mkdir(exist_ok=True,parents=True)
            out.write_bytes(content)
    except BaseException:
        shutil.rmtree(a.dest_bot)
        raise


if __name__ == '__main__':
    main()
