// Minimal Node driver for the visualiser's engine WASM (replay decoding).
const fs = require("fs");
const path = require("path");
const { WASI } = require("wasi");

function load() {
  const wasi = new WASI({ version: "preview1", args: [], env: {}, returnOnExit: true });
  const wasmPath = process.env.ENGWASM || path.join(__dirname, "engine.wasm");
  const mod = new WebAssembly.Module(fs.readFileSync(wasmPath));
  const inst = new WebAssembly.Instance(mod, {
    wasi_snapshot_preview1: wasi.wasiImport,
    deep_wasm: { on_assert_fail_impl: () => 1 },
  });
  const ex = inst.exports;
  wasi.initialize(inst);
  const E = {
    ex,
    outBuf: ex.Engine_Malloc(64),
    args: ex.Engine_Malloc(1024),
    get mem() {
      return new DataView(ex.memory.buffer);
    },
    cstr(p) {
      const u = new Uint8Array(ex.memory.buffer);
      let s = "";
      while (u[p]) s += String.fromCharCode(u[p++]);
      return s;
    },
    check(code, what) {
      if (code !== 0) throw new Error(`${what}: engine error ${code}: ${E.cstr(ex.GetLastErrorMsg())}`);
    },
    alloc(n) {
      return ex.Engine_Malloc(n);
    },
    loadReplay(file) {
      const bytes = fs.readFileSync(file);
      const p = ex.Engine_Malloc(bytes.length);
      new Uint8Array(ex.memory.buffer, p, bytes.length).set(bytes);
      E.check(ex.Game_FromReplayFileBytes(p, bytes.length, E.outBuf), "FromReplay");
      ex.Engine_Free(p);
      return E.mem.getBigUint64(E.outBuf, true);
    },
    persp(team, champion) {
      const t = E.args + 48;
      E.mem.setUint32(t, team >>> 0, true);
      E.mem.setUint32(t + 4, champion >>> 0, true);
      return t;
    },
  };
  return E;
}

module.exports = { load };
