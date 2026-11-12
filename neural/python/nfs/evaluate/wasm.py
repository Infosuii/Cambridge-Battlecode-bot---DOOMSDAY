"""Minimal, dependency-free WebAssembly binary reader for release audits.

Parses the section table, the export section (id 7), the import section (id 2) and the data section (id 11), and
extracts printable strings from data segments. Only what the release verifier needs; it never executes anything.
Reference: WebAssembly core spec 1.0 binary format (+ bulk-memory passive/explicit-memory data segments).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

MAGIC = b'\0asm\x01\0\0\0'
SECTION_NAMES = {0: 'custom', 1: 'type', 2: 'import', 3: 'function', 4: 'table', 5: 'memory', 6: 'global',
                 7: 'export', 8: 'start', 9: 'element', 10: 'code', 11: 'data', 12: 'datacount', 13: 'tag'}
EXPORT_KINDS = {0: 'func', 1: 'table', 2: 'memory', 3: 'global', 4: 'tag'}


class WasmError(ValueError):
    pass


def _leb_u(buf: bytes, off: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        if off >= len(buf):
            raise WasmError('truncated LEB128')
        b = buf[off]
        off += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, off
        shift += 7
        if shift > 63:
            raise WasmError('LEB128 too long')


def _name(buf: bytes, off: int) -> tuple[str, int]:
    n, off = _leb_u(buf, off)
    if off + n > len(buf):
        raise WasmError('truncated name')
    return buf[off:off + n].decode('utf-8', 'replace'), off + n


def _skip_const_expr(buf: bytes, off: int) -> int:
    """Skip a constant expression (i32.const/i64.const/global.get/ref.null/ref.func ... end)."""
    while True:
        op = buf[off]
        off += 1
        if op == 0x0B:  # end
            return off
        if op in (0x41, 0x42, 0x23, 0xD2):  # i32.const, i64.const (signed LEB, skip same way), global.get, ref.func
            while buf[off] & 0x80:
                off += 1
            off += 1
        elif op == 0x44:  # f64.const
            off += 8
        elif op == 0x43:  # f32.const
            off += 4
        elif op == 0xD0:  # ref.null t
            off += 1
        elif op in (0x6A, 0x6B, 0x6C, 0x7C, 0x7D, 0x7E):  # extended-const arithmetic
            continue
        else:
            raise WasmError(f'unsupported opcode 0x{op:02x} in constant expression')


@dataclass
class Section:
    id: int
    offset: int  # payload offset in the file
    size: int
    name: str = ''  # custom section name

    @property
    def kind(self) -> str:
        return SECTION_NAMES.get(self.id, f'unknown{self.id}')


@dataclass
class WasmModule:
    raw: bytes
    sections: list[Section] = field(default_factory=list)

    @classmethod
    def load(cls, path) -> 'WasmModule':
        return cls.parse(Path(path).read_bytes())

    @classmethod
    def parse(cls, raw: bytes) -> 'WasmModule':
        if raw[:8] != MAGIC:
            raise WasmError('not a wasm v1 module')
        mod = cls(raw=raw)
        off = 8
        while off < len(raw):
            sid = raw[off]
            size, p = _leb_u(raw, off + 1)
            if p + size > len(raw):
                raise WasmError('truncated section')
            name = ''
            if sid == 0:
                name, _ = _name(raw[p:p + size], 0)
            mod.sections.append(Section(sid, p, size, name))
            off = p + size
        return mod

    def payload(self, sid: int) -> bytes:
        for s in self.sections:
            if s.id == sid:
                return self.raw[s.offset:s.offset + s.size]
        return b''

    def section_hashes(self, include_custom: bool = False) -> list[tuple[int, str]]:
        return [(s.id, hashlib.sha256(self.raw[s.offset:s.offset + s.size]).hexdigest())
                for s in self.sections if include_custom or s.id != 0]

    def custom_sections(self) -> list[str]:
        return [s.name for s in self.sections if s.id == 0]

    def exports(self) -> list[tuple[str, str]]:
        body = self.payload(7)
        if not body:
            return []
        n, off = _leb_u(body, 0)
        out = []
        for _ in range(n):
            nm, off = _name(body, off)
            kind = body[off]
            off += 1
            _, off = _leb_u(body, off)
            out.append((nm, EXPORT_KINDS.get(kind, str(kind))))
        return out

    def imports(self) -> list[tuple[str, str, str]]:
        body = self.payload(2)
        if not body:
            return []
        n, off = _leb_u(body, 0)
        out = []
        for _ in range(n):
            mod, off = _name(body, off)
            nm, off = _name(body, off)
            kind = body[off]
            off += 1
            if kind == 0:
                _, off = _leb_u(body, off)
            elif kind == 1:
                off += 1
                flags = body[off]
                off += 1
                _, off = _leb_u(body, off)
                if flags & 1:
                    _, off = _leb_u(body, off)
            elif kind == 2:
                flags = body[off]
                off += 1
                _, off = _leb_u(body, off)
                if flags & 1:
                    _, off = _leb_u(body, off)
            elif kind == 3:
                off += 2
            elif kind == 4:
                off += 1
                _, off = _leb_u(body, off)
            else:
                raise WasmError(f'unknown import kind {kind}')
            out.append((mod, nm, EXPORT_KINDS.get(kind, str(kind))))
        return out

    def data_segments(self) -> list[bytes]:
        body = self.payload(11)
        if not body:
            return []
        n, off = _leb_u(body, 0)
        out = []
        for _ in range(n):
            flags, off = _leb_u(body, off)
            if flags == 0:
                off = _skip_const_expr(body, off)
            elif flags == 1:
                pass
            elif flags == 2:
                _, off = _leb_u(body, off)
                off = _skip_const_expr(body, off)
            else:
                raise WasmError(f'unknown data segment flags {flags}')
            size, off = _leb_u(body, off)
            out.append(body[off:off + size])
            off += size
        return out

    def data_bytes(self) -> bytes:
        return b''.join(self.data_segments())

    def data_strings(self, min_len: int = 4) -> list[str]:
        return [m.group().decode('ascii') for m in re.finditer(rb'[\x20-\x7e]{%d,}' % min_len, self.data_bytes())]

    def executable_bytes(self) -> bytes:
        """Every non-custom section payload concatenated (what the engine actually loads)."""
        return b''.join(self.raw[s.offset:s.offset + s.size] for s in self.sections if s.id != 0)


def find_forbidden(mod: WasmModule, needles=(b'NFS1', b'NFT1')) -> dict[str, dict[str, int]]:
    """Occurrences of each needle in the data section and in all executable (non-custom) sections."""
    data = mod.data_bytes()
    exe = mod.executable_bytes()
    return {n.decode(): {'data': data.count(n), 'executable_sections': exe.count(n)} for n in needles}
