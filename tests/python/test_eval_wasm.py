"""Wasm reader tests on the real reference original.wasm and on hand-built synthetic modules."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine  # noqa: E402
from nfs.evaluate import wasm as W  # noqa: E402

ORIGINAL = ROOT / 'references/builds/original.wasm'


def leb(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def section(sid, body):
    return bytes([sid]) + leb(len(body)) + body


def name(s):
    return leb(len(s)) + s.encode()


def synthetic(exports=(('memory', 2), ('lab_ctl', 0)), data=(b'hello NFT1 x', b'plain'), custom=b''):
    exp = leb(len(exports)) + b''.join(name(n) + bytes([k]) + leb(0) for n, k in exports)
    # segment 0: active, memory 0, offset i32.const 1024 ; segment 1: passive
    segs = [leb(0) + b'\x41' + leb(1024) + b'\x0b' + leb(len(data[0])) + data[0],
            leb(1) + leb(len(data[1])) + data[1]]
    dat = leb(len(segs)) + b''.join(segs)
    mod = W.MAGIC + section(5, b'\x01\x00\x01') + section(7, exp) + section(11, dat)
    if custom:
        mod += section(0, name('name') + custom)
    return mod


@unittest.skipUnless(ORIGINAL.exists(), 'reference build missing')
class TestRealReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = W.WasmModule.load(ORIGINAL)

    def test_sections_agree_with_engine_helper(self):
        self.assertEqual(self.mod.section_hashes(), engine.wasm_sections(ORIGINAL))
        self.assertEqual(dict(self.mod.section_hashes())[10], engine.code_section_sha(ORIGINAL))

    def test_exports_include_inherited_lab_controls(self):
        names = [n for n, _ in self.mod.exports()]
        self.assertIn('_start', names)
        self.assertIn('memory', names)
        for lab in ('lab_ctl', 'lab_knobs', 'lab_cn_log', 'lab_pol_log', 'lab_builds'):
            self.assertIn(lab, names)
        self.assertEqual(sum(n.startswith('lab_') for n in names), 12)

    def test_imports_are_env_sdk_and_wasi(self):
        imps = self.mod.imports()
        self.assertEqual({m for m, _, _ in imps}, {'env', 'wasi_snapshot_preview1'})
        self.assertIn(('env', 'fuel_remaining', 'func'), imps)
        self.assertIn(('wasi_snapshot_preview1', 'fd_write', 'func'), imps)

    def test_data_strings_and_no_nn_record_tags(self):
        strings = self.mod.data_strings()
        self.assertTrue(any('bot error' in s for s in strings), strings[:20])
        forb = W.find_forbidden(self.mod)
        self.assertEqual(forb, {'NFS1': {'data': 0, 'executable_sections': 0},
                                'NFT1': {'data': 0, 'executable_sections': 0}})

    def test_custom_sections_are_not_executable(self):
        self.assertIn('name', self.mod.custom_sections())
        self.assertLess(len(self.mod.executable_bytes()), len(self.mod.raw))


class TestSynthetic(unittest.TestCase):
    def test_exports_and_data(self):
        mod = W.WasmModule.parse(synthetic())
        self.assertEqual(mod.exports(), [('memory', 'memory'), ('lab_ctl', 'func')])
        self.assertEqual(mod.data_segments(), [b'hello NFT1 x', b'plain'])
        self.assertEqual(W.find_forbidden(mod)['NFT1'], {'data': 1, 'executable_sections': 1})
        self.assertEqual(W.find_forbidden(mod)['NFS1']['data'], 0)

    def test_custom_section_strings_ignored(self):
        mod = W.WasmModule.parse(synthetic(data=(b'aaaa', b'bbbb'), custom=b'NFS1 debug name'))
        self.assertEqual(W.find_forbidden(mod)['NFS1'], {'data': 0, 'executable_sections': 0})
        self.assertEqual(len(mod.section_hashes()), 3)
        self.assertEqual(len(mod.section_hashes(include_custom=True)), 4)

    def test_rejects_non_wasm_and_truncation(self):
        with self.assertRaises(W.WasmError):
            W.WasmModule.parse(b'not wasm')
        with self.assertRaises(W.WasmError):
            W.WasmModule.parse(synthetic()[:-3])


if __name__ == '__main__':
    unittest.main()
