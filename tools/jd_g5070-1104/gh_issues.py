#!/usr/bin/env python3
"""Read/post GitHub issue comments for the DOOMSDAY coordination issues (#5, #6).

No secrets live in this file. The token is fetched at runtime from Git Credential
Manager via `git credential fill` (non-interactive) and only ever sent in the
Authorization header. It is never printed, logged or written to disk.

Usage (run with `py`):
  py tools/jd_g5070-1104/gh_issues.py whoami
  py tools/jd_g5070-1104/gh_issues.py read 6 [--last 15] [--since 2026-11-04T01:00Z] [--no-body]
  py tools/jd_g5070-1104/gh_issues.py next-seq
  py tools/jd_g5070-1104/gh_issues.py post 6 --file body.md

Posting is restricted to issue #6 and the body must start with
`[BUILDER g5070-1104] <seq> `. Issue #5 is JOHNDOE/CLAUDE only; ask a
collaborator to relay there.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "Infosuii/neural-networkk-battlecode"
API = "https://api.github.com"
RUN_ID = "g5070-1104"
PREFIX_RE = re.compile(r"^\[BUILDER " + re.escape(RUN_ID) + r"\] (\d+) \S")
POST_ALLOWED = {6}


def _token():
    env = dict(os.environ, GCM_INTERACTIVE="never", GIT_TERMINAL_PROMPT="0")
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, env=env, timeout=60,
    )
    if p.returncode != 0:
        sys.exit("credential fill failed (exit %d); no token available" % p.returncode)
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            tok = line[len("password="):].strip()
            if tok:
                return tok
    sys.exit("credential fill returned no password for github.com")


_TOK = None


def api(method, path, body=None):
    global _TOK
    if _TOK is None:
        _TOK = _token()
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Authorization", "Bearer " + _TOK)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "jd-g5070-1104-coord")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode() or "null"), dict(r.headers)
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")[:300]
        sys.exit("HTTP %d on %s %s: %s" % (e.code, method, path, msg))


def all_comments(issue, since=None):
    out, page = [], 1
    while True:
        q = "/repos/%s/issues/%d/comments?per_page=100&page=%d" % (REPO, issue, page)
        if since:
            q += "&since=" + since
        batch, _ = api("GET", q)
        out.extend(batch)
        if len(batch) < 100:
            return out
        page += 1


def cmd_whoami(a):
    u, h = api("GET", "/user")
    print("login:", u.get("login"))
    print("rate-remaining:", h.get("X-RateLimit-Remaining") or h.get("x-ratelimit-remaining"))


def cmd_read(a):
    if not a.no_body:
        iss, _ = api("GET", "/repos/%s/issues/%d" % (REPO, a.issue))
        print("=== #%d %s [%s] by %s, updated %s" % (
            iss["number"], iss["title"], iss["state"], iss["user"]["login"], iss["updated_at"]))
        print(iss.get("body") or "")
    cs = all_comments(a.issue, a.since)
    print("=== %d comments%s; showing last %d" % (
        len(cs), " since " + a.since if a.since else "", min(a.last, len(cs))))
    for c in cs[-a.last:] if a.last else []:
        print("--- id=%d %s %s %s" % (c["id"], c["user"]["login"], c["created_at"], c["html_url"]))
        print(c["body"])


def _builder_seqs():
    return [int(m.group(1)) for c in all_comments(6)
            for m in [PREFIX_RE.match(c["body"] or "")] if m]


def cmd_next_seq(a):
    s = _builder_seqs()
    print(max(s) + 1 if s else 1)


def cmd_post(a):
    if a.issue not in POST_ALLOWED:
        sys.exit("refusing to post to #%d: builder posts go to #6 only" % a.issue)
    with open(a.file, encoding="utf-8") as f:
        body = f.read().strip()
    m = PREFIX_RE.match(body)
    if not m:
        sys.exit("body must start with '[BUILDER %s] <seq> <topic>'" % RUN_ID)
    seq = int(m.group(1))
    used = _builder_seqs()
    if used and seq <= max(used):
        sys.exit("sequence %d not above last used %d" % (seq, max(used)))
    c, _ = api("POST", "/repos/%s/issues/%d/comments" % (REPO, a.issue), {"body": body})
    print("posted seq %d: %s" % (seq, c["html_url"]))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("whoami").set_defaults(fn=cmd_whoami)
    r = sp.add_parser("read")
    r.add_argument("issue", type=int)
    r.add_argument("--last", type=int, default=15)
    r.add_argument("--since", help="ISO-8601 UTC, e.g. 2026-11-04T01:00:00Z")
    r.add_argument("--no-body", action="store_true")
    r.set_defaults(fn=cmd_read)
    sp.add_parser("next-seq").set_defaults(fn=cmd_next_seq)
    p = sp.add_parser("post")
    p.add_argument("issue", type=int)
    p.add_argument("--file", required=True)
    p.set_defaults(fn=cmd_post)
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a.fn(a)


if __name__ == "__main__":
    main()
