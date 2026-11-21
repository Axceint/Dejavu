"""Scan telemetry for the nightly adapt job: numbers only, never code or file names.
One comment per real scan on the "Scan telemetry" issue. Off without GH_TELEMETRY_TOKEN; never slows or fails a scan."""
import json
import os
import threading
import urllib.request

from . import ask

ISSUE = "https://api.github.com/repos/Axceint/Dejavu/issues/69/comments"


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
