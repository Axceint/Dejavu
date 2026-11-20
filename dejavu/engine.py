"""Structural similarity: tree-sitter tokens -> k-gram fingerprints -> rarity-weighted overlap."""
import math
import time
import zipfile
import zlib
from collections import Counter
from itertools import combinations
from pathlib import Path

from tree_sitter_language_pack import get_parser

LANG = {".py": "python", ".java": "java", ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".h": "cpp", ".hpp": "cpp"}
# Names and types collapse to ID so renames and int->long swaps don't matter.
NAME = {"identifier", "type_identifier", "field_identifier", "namespace_identifier", "property_identifier",
        "primitive_type", "integral_type", "floating_point_type", "boolean_type", "void_type",
        "sized_type_specifier", "auto"}
LITERAL = {"string", "integer", "float", "true", "false", "none", "number_literal", "string_literal",
           "char_literal", "raw_string_literal", "concatenated_string", "decimal_integer_literal",
           "decimal_floating_point_literal", "hex_integer_literal", "character_literal", "null_literal", "nullptr"}
# Comments and qualifiers (const, static, final, public...) carry no logic.
SKIP = {"comment", "line_comment", "block_comment", "type_qualifier", "storage_class_specifier", "modifiers"}
LOOP = {"for_statement", "while_statement", "do_statement", "for_range_loop", "enhanced_for_statement"}
# Loop keywords are covered by LOOP; braces/semicolons vary with style (`if (x) y;` vs `if (x) { y; }`).
DROP_LEAF = {"for", "while", "do", "{", "}", ";"}
FUNC = {"function_definition", "method_declaration", "constructor_declaration"}
CALL = {"call": "function", "call_expression": "function", "method_invocation": "name"}
K = 5  # tokens per fingerprint
MATCH_TOP = 100  # shortcut: line matches only for the top 100 pairs, raise if the UI shows more


def _junk(name):  # macOS zip metadata (__MACOSX/, ._file) is binary, not a submission
    return "__MACOSX" in Path(name).parts or Path(name).name.startswith("._")


def load(path):
    path, files = Path(path), {}
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if Path(n).suffix.lower() in LANG and not _junk(n):
                    files[n] = z.read(n).decode("utf-8", "replace")
    else:
        for p in sorted(path.rglob("*")):
            if p.is_file() and p.suffix.lower() in LANG and not _junk(p.relative_to(path)):
                files[p.relative_to(path).as_posix()] = p.read_text("utf-8", "replace")
    return files


def _fn_name(node):
    n, d = node.child_by_field_name("name"), node
    while n is None and d is not None:  # C++: function_definition -> declarator chain -> identifier
        d = d.child_by_field_name("declarator")
        if d is not None and d.type in NAME:
            n = d
    return n.text if n is not None else None


def tokens(src, lang):
    """Normalized (token, line) stream. Loops and self-recursive calls both emit LOOP."""
    out, stack = [], [(get_parser(lang).parse(src.encode()).root_node, None)]
    while stack:
        node, fn = stack.pop()
        t, line = node.type, node.start_point[0] + 1
        if t in SKIP:
            continue
        if t in FUNC:
            fn = _fn_name(node)
        if t in LOOP:
            out.append(("LOOP", line))
        elif t in CALL and fn:
            callee = node.child_by_field_name(CALL[t])
            if callee is not None and callee.text == fn:
                out.append(("LOOP", line))
        if t in LITERAL:
            out.append(("LIT", line))
            continue
        if t == "update_expression":  # ++x and x++ become the same token
            out.append(("UPD", line))
            stack.extend((c, fn) for c in reversed(node.named_children))
            continue
        if node.child_count == 0:
            if t in NAME:
                out.append(("ID", line))
            elif t not in DROP_LEAF:
                out.append((t, line))
            continue
        stack.extend((c, fn) for c in reversed(node.children))
    return out


def fingerprints(toks):
    """hash of every K-token window -> (first_line, last_line) of its first occurrence."""
    fps = {}
    for i in range(len(toks) - K + 1):
        h = zlib.crc32(" ".join(t for t, _ in toks[i:i + K]).encode())  # stable across runs, unlike hash()
        fps.setdefault(h, (toks[i][1], toks[i + K - 1][1]))
    return fps


def _blocks(fa, fb, shared):
    out = []
    for (a0, a1), (b0, b1) in sorted((fa[h], fb[h]) for h in shared):
        if out and a0 <= out[-1][0][1] + 1 and out[-1][1][0] - 1 <= b0 <= out[-1][1][1] + 1:
            out[-1][0][1] = max(out[-1][0][1], a1)
            out[-1][1][1] = max(out[-1][1][1], b1)
        else:
            out.append([[a0, a1], [b0, b1]])
    return out


def scan(path):
    start = time.perf_counter()
    files = load(path)
    fps = {n: fingerprints(tokens(src, LANG[Path(n).suffix.lower()])) for n, src in files.items()}
    pairs = []
    by_lang = {}
    for n in files:
        by_lang.setdefault(LANG[Path(n).suffix.lower()], []).append(n)
    for names in by_lang.values():
        df = Counter(h for n in names for h in fps[n])
        # Rare shared code is strong evidence; code everyone writes (I/O, loops) is weak.
        w = {h: math.log(1 + len(names) / c) for h, c in df.items()}
        total = {n: sum(w[h] for h in fps[n]) for n in names}
        for a, b in combinations(names, 2):
            shared = fps[a].keys() & fps[b].keys()
            if not shared:
                continue
            inter = sum(w[h] for h in shared)
            union = total[a] + total[b] - inter
            # Containment rewards a copy padded with extra code, but its denominator never drops below half
            # the bigger file, so a tiny boilerplate file can't look "fully contained" in a real solution.
            small = max(min(total[a], total[b]), 0.5 * max(total[a], total[b]))
            score = 0.5 * (inter / union + inter / small)
            pairs.append({"a": a, "b": b, "score": round(score, 4), "shared": shared})
    pairs.sort(key=lambda p: -p["score"])
    for i, p in enumerate(pairs):
        shared = p.pop("shared")
        p["matches"] = _blocks(fps[p["a"]], fps[p["b"]], shared) if i < MATCH_TOP else []
    return {"files": files, "pairs": pairs, "seconds": round(time.perf_counter() - start, 3)}
