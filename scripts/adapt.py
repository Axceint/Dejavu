"""Nightly adapt: reads scan telemetry from the Scan telemetry issue and proposes a larger ask.SPAN
when real uploads keep cutting functions at the limit. Stdlib only. Never merges; the workflow opens one PR.

python -m scripts.adapt            # rewrite dejavu/ask.py if a change is due, print the PR body
python -m scripts.adapt --dry-run  # print the proposal only"""
import json
import re
import subprocess
import sys

ASK = "dejavu/ask.py"
TRUSTED = {"OWNER", "MEMBER", "COLLABORATOR"}  # the issue is public; anyone else could post fake numbers
KEYS = {"files", "max_lines", "max_bytes", "chunks", "chunks_at_span", "span", "seconds"}
MIN_SCANS, SHARE, STEP, CAP = 3, 0.05, 20, 120  # cap: ask.build embeds only the first 4000 chars (~100 lines) of a chunk


def scans(comments):
    """Telemetry dicts from trusted comments; anything malformed is skipped."""
    out = []
    for c in comments:
        if c.get("author_association") not in TRUSTED:
            continue
        m = re.fullmatch(r"```json\n(.*)\n```", (c.get("body") or "").strip(), re.S)
        try:
            s = json.loads(m.group(1)) if m else None
        except ValueError:
            continue
        if isinstance(s, dict) and set(s) == KEYS and all(type(v) in (int, float) for v in s.values()):
            out.append(s)
    return out


def propose(stats, span):
    """New SPAN and the reason, or (span, None). Only scans made with the current SPAN count."""
    now = [s for s in stats if s["span"] == span]
    chunks = sum(s["chunks"] for s in now)
    if len(now) < MIN_SCANS or not chunks or span >= CAP:
        return span, None
    share = sum(s["chunks_at_span"] for s in now) / chunks
    if share <= SHARE:
        return span, None
    new = min(span + STEP, CAP)
    return new, f"{share:.0%} of chunks in the last {len(now)} scans were cut at SPAN={span} (limit {SHARE:.0%})."


def rewrite(src, new):
    out, n = re.subn(r"^SPAN = \d+", f"SPAN = {new}", src, flags=re.M)
    assert n == 1, "expected exactly one SPAN line in dejavu/ask.py"
    return out


def comments():
    raw = subprocess.run(["gh", "api", "--paginate", "repos/Axceint/Dejavu/issues/69/comments",
                          "--jq", ".[] | {author_association, body}"],  # one JSON object per line, across pages
                         check=True, capture_output=True, text=True).stdout
    return [json.loads(line) for line in raw.splitlines() if line]


def main(dry):
    src = open(ASK, encoding="utf-8").read()
    span = int(re.search(r"^SPAN = (\d+)", src, re.M).group(1))
    new, why = propose(scans(comments()), span)
    if not why:
        print(f"No change: SPAN={span}")
        return
    print(f"SPAN {span} -> {new}. {why}")
    if not dry:
        open(ASK, "w", encoding="utf-8", newline="").write(rewrite(src, new))


if __name__ == "__main__":
    main("--dry-run" in sys.argv)
