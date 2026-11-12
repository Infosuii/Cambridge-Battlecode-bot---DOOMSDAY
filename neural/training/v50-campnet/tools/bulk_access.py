"""Read authorized public match archives through the existing official CLI login.

The CLI's Windows-protected session remains in memory. No credential is logged,
copied to the project, or sent outside the official platform origin.
"""
import ctypes, json, re, urllib.request, urllib.parse
from pathlib import Path

ORIGIN = 'https://2026a.battlecode.co.uk'
ROOT = Path(__file__).resolve().parents[1]

class Blob(ctypes.Structure):
    _fields_ = [('size', ctypes.c_uint32), ('data', ctypes.POINTER(ctypes.c_ubyte))]

def cli_session():
    p = next(Path('C:/Users/omdha/AppData/Roaming/cambc').glob('session-*.json'))
    raw = p.read_bytes()
    if raw.startswith(b'{'): return json.loads(raw)
    buf = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    source, dest = Blob(len(raw), buf), Blob()
    ok = ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(dest))
    if not ok: raise RuntimeError('Official CLI session could not be opened with this Windows account')
    try: return json.loads(ctypes.string_at(dest.data, dest.size))
    finally: ctypes.windll.kernel32.LocalFree(dest.data)

def request(url, session=None):
    if not url.startswith(ORIGIN + '/'): raise ValueError('Credentials restricted to official platform origin')
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': ORIGIN + '/game/match-database'}
    if session:
        token = next((session[k] for k in ('token', 'access_token', 'accessToken', 'session_token', 'sessionToken') if k in session), None)
        if token: headers['Authorization'] = 'Bearer ' + token
    return urllib.request.Request(url, headers=headers)

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected and urllib.parse.urlsplit(newurl).netloc != urllib.parse.urlsplit(req.full_url).netloc:
            redirected.remove_header('Authorization')
            redirected.remove_header('Cookie')
        return redirected

def open_url(req, timeout=60):
    return urllib.request.build_opener(SafeRedirect()).open(req, timeout=timeout)

if __name__ == '__main__':
    session = cli_session()
    print('Session field names:', sorted(session.keys()))
    # Asset URL observed in the official page HTML, not guessed.
    url = ORIGIN + '/service/assets/service-Dw7QII-4.js'
    raw = urllib.request.urlopen(request(url, session), timeout=30).read().decode()
    (ROOT / 'data/service.js').write_text(raw, encoding='utf-8')
    print('Official interface bytes:', len(raw))
    for term in ('match-database', 'database/daily', 'daily-bundles', 'matchDatabase'):
        for m in list(re.finditer(re.escape(term), raw))[:8]:
            print(term, raw[max(0, m.start() - 200):m.end() + 400])
