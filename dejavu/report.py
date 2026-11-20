"""Turns scan() output into one self-contained HTML review app (also usable offline as a downloaded report)."""
import json
import zlib
from bisect import bisect_left
from pathlib import Path

from .engine import LANG
from .explain import context, evidence

TEMPLATE = Path(__file__).with_name("review.html")
LIMIT = 500  # shortcut: the app lists the top 500 pairs; reviewers never get that far, the CSV has all


def payload(r, limit=LIMIT):
    pairs = r["pairs"][:limit]
    names = sorted({n for p in pairs for n in (p["a"], p["b"])} | set(r["flags"]))
    idx = {n: i for i, n in enumerate(names)}
    ctx = context(r)
    out = []
    for rank, p in enumerate(pairs, 1):
        d = {"rank": rank, "a": idx[p["a"]], "b": idx[p["b"]], "score": p["score"], "m": p["matches"]}
        if p["matches"]:
            e = evidence(r, p, ctx)
            d["cov"] = [round(c, 3) for c in e["coverage"]]
            d["ren"] = e["renames"]
            d["verb"] = e["verbatim"]
        d["beats"] = round(bisect_left(ctx["scores"], p["score"]) / max(len(ctx["scores"]) - 1, 1), 3)
        out.append(d)
    # stable id per batch, so review decisions saved in the browser come back for the same upload
    key = zlib.crc32(json.dumps([names, [p["score"] for p in pairs]]).encode())
    return {
        "id": f"{key:08x}",
        "files": [{"name": n, "lang": LANG[Path(n).suffix.lower()], "src": r["files"][n],
                   "flags": r["flags"].get(n, [])} for n in names],
        "pairs": out,
        "totalPairs": len(r["pairs"]),
        "totalFiles": len(r["files"]),
        "seconds": r["seconds"],
    }


def render(data):
    # "<" escaped so code like "</script>" inside a submission can't close the data block
    blob = json.dumps(data, separators=(",", ":")).replace("<", "\\u003c")
    return TEMPLATE.read_text("utf-8").replace("/*__DATA__*/null", blob, 1)
