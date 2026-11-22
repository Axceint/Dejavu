"""Scan telemetry for the nightly adapt job: numbers only, never code or file names.
One comment per real scan on the "Scan telemetry" issue. Off without GH_TELEMETRY_TOKEN; never slows or fails a scan.
Also files in-app problem reports as issues, which the autofix workflow drafts fixes for."""
import json
import os
import re
import threading
import time
import urllib.request

from . import ask

ISSUE = "https://api.github.com/repos/Axceint/Dejavu/issues/69/comments"
REPORTS = "https://api.github.com/repos/Axceint/Dejavu/issues"
WHERE = ("Upload or scan", "Pair review", "Ask AI", "Export (report or CSV)", "Other")
MAX_CHARS, PER_DAY = 2000, 10
MARK = "<!-- dejavu:app-report -->"  # .github/workflows/autofix.yml starts a fix for trusted issues that begin with it
_sent, _lock = [], threading.Lock()  # shortcut: per-process daily cap, reset when the app restarts or sleeps


def stats(files, seconds):
    """Only counts and sizes; the nightly job compares them with fixed thresholds."""
    lines = [s.count("\n") + 1 for s in files.values()]
    cs = ask.chunks(files)
    return {
        "files": len(files),
        "max_lines": max(lines, default=0),
        "max_bytes": max((len(s.encode()) for s in files.values()), default=0),
        "chunks": len(cs),
        "chunks_at_span": sum(c["end"] - c["start"] + 1 == ask.SPAN for c in cs),  # pieces of a function cut at SPAN
        "span": ask.SPAN,
        "seconds": seconds,
    }


def _post(token, files, seconds):
    try:
        body = json.dumps({"body": "```json\n" + json.dumps(stats(files, seconds)) + "\n```"}).encode()
        req = urllib.request.Request(ISSUE, body, {"Authorization": f"Bearer {token}",
                                                   "Accept": "application/vnd.github+json"})
        urllib.request.urlopen(req, timeout=3).close()
    except Exception:  # telemetry must never surface to the reviewer
        pass


def send(files, seconds, token=None):
    """Post in the background; returns the thread, or None when telemetry is off."""
    token = token if token is not None else os.getenv("GH_TELEMETRY_TOKEN", "")
    if not token:
        return None
    t = threading.Thread(target=_post, args=(token, dict(files), seconds), daemon=True)
    t.start()
    return t


def report(text, where, token=None):
    """File an in-app report as a GitHub issue and return its number.
    Raises ValueError with a fixed message that is safe to show (never the server's reply)."""
    token = token if token is not None else os.getenv("GH_TELEMETRY_TOKEN", "")
    text = text.strip()[:MAX_CHARS]
    if not text or where not in WHERE:
        raise ValueError("Write what happened first.")
    if not token:
        raise ValueError("Reporting isn't set up on this copy of the app.")
    # a fence longer than any backtick run in the text: links, images and @mentions show as plain text
    fence = "`" * max(3, 1 + max(map(len, re.findall("`+", text)), default=0))
    issue = {"title": f"App report ({where}): {text.splitlines()[0][:60]}",
             "body": f"{MARK}\nReported from the app ({where}).\n\n{fence}text\n{text}\n{fence}",
             "labels": ["bug", "from-app"]}
    with _lock:  # reports are rare; holding it through the request keeps the cap exact
        now = time.time()
        _sent[:] = [t for t in _sent if now - t < 86400]
        if len(_sent) >= PER_DAY:
            raise ValueError(f"The app has sent its {PER_DAY} reports for today. Try again tomorrow.")
        req = urllib.request.Request(REPORTS, json.dumps(issue).encode(), {"Authorization": f"Bearer {token}",
                                                                          "Accept": "application/vnd.github+json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                n = int(json.load(r)["number"])
        except Exception:
            raise ValueError("Couldn't reach GitHub. Try again in a minute.") from None
        _sent.append(now)  # only sent reports count toward the cap
    return n
