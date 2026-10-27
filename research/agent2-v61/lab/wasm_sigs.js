// Print parameter/result types of selected exported functions of a wasm module (reads the type/function/export sections).
// usage: node wasm_sigs.js engine.wasm [regex]
const fs = require("fs");
const buf = fs.readFileSync(process.argv[2]);
const re = new RegExp(process.argv[3] || ".");
let p = 8;
const u32 = () => {
  let r = 0, s = 0, b;
  do { b = buf[p++]; r |= (b & 0x7f) << s; s += 7; } while (b & 0x80);
  return r >>> 0;
};
const types = [], funcTypes = [], exportsList = [];
let nImportedFuncs = 0;
const VT = { 0x7f: "i32", 0x7e: "i64", 0x7d: "f32", 0x7c: "f64", 0x7b: "v128", 0x70: "funcref", 0x6f: "externref" };
while (p < buf.length) {
  const id = buf[p++];
  const size = u32();
  const end = p + size;
  if (id === 1) {
    const n = u32();
    for (let i = 0; i < n; i++) {
      p++; // 0x60
      const np = u32(); const params = []; for (let k = 0; k < np; k++) params.push(VT[buf[p++]]);
      const nr = u32(); const res = []; for (let k = 0; k < nr; k++) res.push(VT[buf[p++]]);
      types.push({ params, res });
    }
  } else if (id === 2) {
    const n = u32();
    for (let i = 0; i < n; i++) {
      const ml = u32(); p += ml; const fl = u32(); p += fl;
      const kind = buf[p++];
      if (kind === 0) { u32(); nImportedFuncs++; }
      else if (kind === 1) { p++; const f = u32(); u32(); if (f & 1) u32(); }
      else if (kind === 2) { const f = u32(); u32(); if (f & 1) u32(); }
      else if (kind === 3) { p += 2; }
      else if (kind === 4) { p++; u32(); }
    }
  } else if (id === 3) {
    const n = u32(); for (let i = 0; i < n; i++) funcTypes.push(u32());
  } else if (id === 7) {
    const n = u32();
    for (let i = 0; i < n; i++) {
      const l = u32(); const name = buf.slice(p, p + l).toString(); p += l;
      const kind = buf[p++]; const idx = u32();
      exportsList.push({ name, kind, idx });
    }
  }
  p = end;
}
for (const e of exportsList) {
  if (e.kind !== 0 || !re.test(e.name)) continue;
  const t = types[funcTypes[e.idx - nImportedFuncs]];
  console.log(`${e.name}(${t.params.join(", ")}) -> ${t.res.join(", ") || "void"}`);
}
