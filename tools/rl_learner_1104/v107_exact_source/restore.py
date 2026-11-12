"""Reassemble and verify the exact uploaded v107 source ZIP. No extraction or execution."""
import base64, hashlib, json
from pathlib import Path
root = Path(__file__).resolve().parent
m = json.loads((root / "manifest.json").read_text())
chunks = []
for part in m["parts"]:
    data = (root / part["path"]).read_bytes()
    assert len(data) == part["bytes"], part["path"]
    assert hashlib.sha256(data).hexdigest() == part["sha256"], part["path"]
    chunks.append(data)
data = base64.b64decode(b"".join(chunks), validate=True)
assert len(data) == m["archive_bytes"]
assert hashlib.sha256(data).hexdigest() == m["archive_sha256"]
out = root / m["archive_name"]
if out.exists():
    assert out.read_bytes() == data, "Refusing to overwrite a different archive"
else:
    out.write_bytes(data)
print(str(out), m["archive_sha256"])
