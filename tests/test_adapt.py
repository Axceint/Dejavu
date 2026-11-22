"""Nightly adapt rules: trusted, well-formed telemetry only; SPAN rises in steps, never past the cap."""
import json

from scripts import adapt


def c(span=80, cut=10, chunks=100, who="OWNER", **extra):
    s = {"files": 4, "max_lines": 300, "max_bytes": 9000, "chunks": chunks, "chunks_at_span": cut,
         "span": span, "seconds": 1.5, **extra}
    return {"author_association": who, "body": "```json\n" + json.dumps(s) + "\n```"}


# untrusted authors, prose, broken JSON, extra keys and non-numbers are all ignored
bad = [c(who="NONE"), c(who="CONTRIBUTOR"), {"author_association": "OWNER", "body": "looks good"},
       {"author_association": "OWNER", "body": "```json\n{nope\n```"}, c(evil=1),
       {"author_association": "OWNER", "body": "```json\n" + json.dumps({k: "1" for k in adapt.KEYS}) + "\n```"}]
assert adapt.scans(bad) == [], adapt.scans(bad)
assert len(adapt.scans(bad + [c(), c(who="MEMBER")])) == 2

ok = adapt.scans([c(), c(), c()])
assert adapt.propose(ok[:2], 80) == (80, None)  # fewer than 3 scans
new, why = adapt.propose(ok, 80)
assert new == 100 and "10%" in why, (new, why)
assert adapt.propose(adapt.scans([c(cut=5)] * 3), 80) == (80, None)  # 5% is not over the limit
assert adapt.propose(adapt.scans([c(span=60)] * 5), 80) == (80, None)  # scans from an older SPAN don't count
assert adapt.propose(adapt.scans([c(span=110)] * 3), 110)[0] == adapt.CAP  # step stops at the cap
assert adapt.propose(adapt.scans([c(span=120)] * 3), 120) == (120, None)
assert adapt.propose(adapt.scans([c(chunks=0, cut=0)] * 3), 80) == (80, None)

src = open(adapt.ASK, encoding="utf-8").read()
out = adapt.rewrite(src, 100)
changed = [(a, b) for a, b in zip(src.splitlines(), out.splitlines()) if a != b]
assert len(changed) == 1 and changed[0][1].startswith("SPAN = 100  #"), changed  # only the SPAN line
try:
    adapt.rewrite("x = 1\n", 100)
    raise SystemExit("rewrite must refuse a file without a SPAN line")
except AssertionError:
    pass
print("adapt ok")
