"""Human-readable evidence for one pair from scan(): why it ranks where it does. Hints for a reviewer, not proof."""
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from tree_sitter_language_pack import get_parser

from .engine import LANG, NAME, SKIP, _clean

TRIVIAL = ("import ", "from ", "#include", "using ", "package ", "return ", "}", "{", "else", "public static void main")


def _leaves(src, lang):
    """(kind, text, line) for each leaf, names collapsed to ID like the engine does, comments kept for verbatim checks."""
    out, stack = [], [get_parser(lang).parse(src.encode()).root_node]
    while stack:
        n = stack.pop()
        if n.type in SKIP:
            continue
        if n.child_count == 0:
            out.append(("ID" if n.type in NAME else n.type, n.text.decode("utf-8", "replace"), n.start_point[0] + 1))
        else:
            stack.extend(reversed(n.children))
    return out


def _in(blocks, toks):
    return [t for t in toks if any(a <= t[2] <= b for a, b in blocks)]


def renames(src_a, src_b, lang, matches):
    """Name pairs used in the same structural position in both files, most consistent first: [(a, b, times)]."""
    ta = _in([m[0] for m in matches], _leaves(_clean(src_a), lang))
    tb = _in([m[1] for m in matches], _leaves(_clean(src_b), lang))
    seen = Counter()
    sm = SequenceMatcher(None, [k for k, _, _ in ta], [k for k, _, _ in tb], autojunk=False)
    for tag, i0, i1, j0, j1 in sm.get_opcodes():
        if tag == "equal":
            seen.update((x[1], y[1]) for x, y in zip(ta[i0:i1], tb[j0:j1]) if x[0] == "ID")
    tot_a, tot_b = Counter(), Counter()
    for (a, b), c in seen.items():
        tot_a[a] += c
        tot_b[b] += c
    # A swap must recur and be each name's main partner on both sides; stray alignments
    # (grid -> sc because both sit in a call's first slot twice) would mislead the "B's names" view.
    best = {}
    for (a, b), c in seen.most_common():
        if a != b and c >= 2 and c >= 0.6 * tot_a[a] and c >= 0.6 * tot_b[b] and a not in best and b not in best.values():
            best[a] = b
    return [(a, b, seen[a, b]) for a, b in best.items()]


def verbatim(src_a, src_b, common=frozenset()):
    """Non-trivial lines identical in both files and absent from `common` (boilerplate): [(line_a, line_b, text)]."""
    where = {}
    for i, line in enumerate(src_b.split("\n"), 1):
        where.setdefault(line.strip(), i)
    out = []
    for i, line in enumerate(src_a.split("\n"), 1):
        s = line.strip()
        if len(s) >= 12 and not s.startswith(TRIVIAL) and s in where and s not in common:
            out.append((i, where[s], s))
    return out


def coverage(src, blocks):
    lines = [i for i, l in enumerate(src.split("\n"), 1) if l.strip()]
    return sum(any(a <= i <= b for a, b in blocks) for i in lines) / max(len(lines), 1)


def context(result):
    """Batch-wide facts evidence() needs; compute once when explaining many pairs."""
    # a line in 3+ submissions is boilerplate (class Main, Scanner setup), not evidence about this pair
    df = Counter(s for src in result["files"].values() for s in {l.strip() for l in src.split("\n")})
    return {"common": {s for s, c in df.items() if c > 2}, "scores": sorted(p["score"] for p in result["pairs"])}


def evidence(result, pair, ctx=None):
    """Everything the UI needs to justify one pair. `result` is scan() output, `pair` one of its pairs."""
    a, b, m = pair["a"], pair["b"], pair["matches"]
    sa, sb = result["files"][a], result["files"][b]
    ctx = ctx or context(result)
    return {
        "coverage": (coverage(sa, [x for x, _ in m]), coverage(sb, [y for _, y in m])),
        "renames": renames(sa, sb, LANG[Path(a).suffix.lower()], m) if m else [],
        "verbatim": verbatim(sa, sb, ctx["common"]),
    }
