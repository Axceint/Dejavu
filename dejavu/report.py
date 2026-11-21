"""Turns scan() output into one self-contained HTML review app (also usable offline as a downloaded report)."""
import csv
import io
import json
import zlib
from bisect import bisect_left
from pathlib import Path

from .aistyle import ai_style
from .engine import LANG, _quiet
from .explain import context, evidence

TEMPLATE = Path(__file__).with_name("review.html")
LIMIT = 500  # shortcut: the app lists the top 500 pairs; reviewers never get that far, the CSV has all


def payload(r, limit=LIMIT, progress=_quiet):
    """progress(stage, done, total) reports stage "explain": evidence for top pairs, then per-file comment checks."""
    pairs = r["pairs"][:limit]
    names = sorted({n for p in pairs for n in (p["a"], p["b"])} | set(r["flags"]))
    idx = {n: i for i, n in enumerate(names)}
    ctx = context(r)
    steps, done = sum(1 for p in pairs if p["matches"]) + len(names), 0
    out = []
    for rank, p in enumerate(pairs, 1):
        d = {"rank": rank, "a": idx[p["a"]], "b": idx[p["b"]], "score": p["score"], "m": p["matches"]}
        if p["matches"]:
            e = evidence(r, p, ctx)
            d["cov"] = [round(c, 3) for c in e["coverage"]]
            d["ren"] = e["renames"]
            d["verb"] = e["verbatim"]
            done += 1
            progress("explain", done, steps)
        d["beats"] = round(bisect_left(ctx["scores"], p["score"]) / max(len(ctx["scores"]) - 1, 1), 3)
        out.append(d)
    files = []
    for n in names:
        lang = LANG[Path(n).suffix.lower()]
        files.append({"name": n, "lang": lang, "src": r["files"][n], "flags": r["flags"].get(n, []),
                      "ai": ai_style(r["files"][n], lang)})
        done += 1
        progress("explain", done, steps)
    # stable id per batch, so review decisions saved in the browser come back for the same upload
    key = zlib.crc32(json.dumps([names, [p["score"] for p in pairs]]).encode())
    return {
        "id": f"{key:08x}",
        "files": files,
        "pairs": out,
        "totalPairs": len(r["pairs"]),
        "totalFiles": len(r["files"]),
        "seconds": r["seconds"],
    }


def _host(theme):
    return json.dumps(theme if theme in ("light", "dark") else None)


def render(data, theme=None):
    """theme: the host app's "light" or "dark", used until the reviewer picks one with the toggle."""
    # "<" escaped so code like "</script>" inside a submission can't close the data block
    blob = json.dumps(data, separators=(",", ":")).replace("<", "\\u003c")
    return TEMPLATE.read_text("utf-8").replace("/*__THEME__*/null", _host(theme), 1).replace("/*__DATA__*/null", blob, 1)


def theme_toggle(theme=None):
    """The light/dark button for pages without the review screen; shares the review's saved choice."""
    return Path(__file__).with_name("toggle.html").read_text("utf-8").replace("/*__THEME__*/null", _host(theme), 1)


def all_pairs_csv(r):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["rank", "score", "file_a", "file_b"])
    # leading = + - @ would run as a formula in Excel; file names come from students
    safe = lambda s: "'" + s if s[:1] in "=+-@" else s
    w.writerows([i, p["score"], safe(p["a"]), safe(p["b"])] for i, p in enumerate(r["pairs"], 1))
    return out.getvalue()
