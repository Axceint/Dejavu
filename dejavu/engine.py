"""Structural similarity: tree-sitter tokens -> k-gram fingerprints -> rarity-weighted overlap."""
import math
import re
import time
import unicodedata
import zipfile
import zlib
from collections import Counter
from itertools import combinations
from pathlib import Path

from tree_sitter_language_pack import get_parser

from .watermark import TAGS as TAG, watermarks

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
K = 6  # tokens per fingerprint (6 beat 5 on the separation margin once Python type hints and docstrings were dropped)
MAX_BYTES = 1_000_000  # per file; real submissions are a few KB
RING = 0.4  # pair score that links files into a copy ring: tests.test_engine keeps loop->recursion copies above 0.4, independent solutions below 0.3
MAX_TOTAL = 20_000_000  # all files together: parsing costs ~1.5 s per MB, so a tiny zip of 1 MB entries stalls the server
MAX_FILES = 2_000  # pairs grow with the square: 2,000 files = 2M pairs (~9 s); 5,000 made a 633 MB CSV
MATCH_TOP = 100  # shortcut: line matches only for the top 100 pairs, raise if the UI shows more
# Cf = zero-width and bidi ("Trojan Source") controls; Zs/Zl/Zp = any space or line break except a plain space.
HIDDEN = {"Cf", "Zs", "Zl", "Zp"}
FILLERS = "\u115f\u1160\u3164\uffa0"  # Hangul fillers: letters that draw nothing, so they pass as part of a name
VSEL = re.compile("[\ufe00-\ufe0f\U000e0100-\U000e01ef]+")  # variation selectors (category Mn, also invisible)
# Java and C++ grammars reject both inside names: selectors go; a filler is a letter to a compiler, so it becomes "x".
UNSEEN = {**dict.fromkeys([*range(0xFE00, 0xFE10), *range(0xE0100, 0xE01F0)]), **dict.fromkeys(map(ord, FILLERS), "x")}
WORD = re.compile(r"[^\W\d_]+")  # runs of letters


def _junk(name):  # macOS zip metadata (__MACOSX/, ._file) is binary, not a submission
    return "__MACOSX" in Path(name).parts or Path(name).name.startswith("._")


def _check_size(name, size, total=0):  # a 4 KB zip can unpack to megabytes; parsing it would stall the shared server
    if size > MAX_BYTES:
        raise ValueError(f"{name} is over {MAX_BYTES // 1_000_000} MB, too big for a hand-written submission")
    if total > MAX_TOTAL:
        raise ValueError(f"the files add up to over {MAX_TOTAL // 1_000_000} MB, too much for one scan")


def _check_count(every, names):  # every: all file names inside, for saying what was found instead
    if not names:  # e.g. a zip of per-student zips, or .c files: a silent "no copies" would be wrong
        found = sorted({s for n in every if (s := Path(n).suffix.lower()) and not _junk(n)})
        raise ValueError("no .py, .java or .cpp files inside" + (f" (found {', '.join(found[:6])})" if found else ""))
    if len(names) > MAX_FILES:
        raise ValueError(f"{len(names):,} source files; one scan takes up to {MAX_FILES:,}")


def _quiet(stage, done, total):
    pass


def load(path, progress=_quiet):
    """progress(stage, done, total) is called with stage "read" after each file, for a progress bar."""
    path, files, total = Path(path), {}, 0
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            every = z.namelist()
            names = [n for n in every if Path(n).suffix.lower() in LANG and not _junk(n)]
            _check_count(every, names)
            for i, n in enumerate(names, 1):
                try:
                    with z.open(n) as f:
                        data = f.read(MAX_BYTES + 1)  # bounded read: the zip header's size can lie
                except (zlib.error, EOFError) as e:  # damaged compressed data inside an otherwise valid zip
                    raise ValueError(f"{n} is damaged inside the zip ({e})") from e
                total += len(data)
                _check_size(n, len(data), total)
                files[n] = data.decode("utf-8", "replace")
                progress("read", i, len(names))
    else:
        every = [p for p in sorted(path.rglob("*")) if p.is_file()]
        paths = [p for p in every if p.suffix.lower() in LANG and not _junk(p.relative_to(path))]
        _check_count([p.relative_to(path).as_posix() for p in every], paths)
        for i, p in enumerate(paths, 1):
            total += p.stat().st_size
            _check_size(p.name, p.stat().st_size, total)
            files[p.relative_to(path).as_posix()] = p.read_text("utf-8", "replace")
            progress("read", i, len(paths))
    return files


def hidden_chars(src):
    """Invisible or look-alike characters, often left by text pasted from chat UIs. A hint, not proof."""
    out = []
    for i, line in enumerate(src.removeprefix("\ufeff").split("\n"), 1):  # a leading BOM is normal on Windows
        if line.isascii():
            continue
        for c in dict.fromkeys(line):
            if c != " " and (unicodedata.category(c) in HIDDEN or c in FILLERS) and not TAG.match(c):
                out.append({"line": i, "char": f"U+{ord(c):04X}", "name": unicodedata.name(c, "UNNAMED")})
        for m in TAG.finditer(line):  # invisible copies of ASCII letters: one flag per run, not one per letter
            if line[m.start() - 1:m.start()] != "\U0001f3f4":  # England/Scotland/Wales flag emoji are tag runs
                out.append({"line": i, "char": f"U+{ord(m.group()[0]):04X}", "name": f"TAG CHARACTER x{len(m.group())}"})
        for m in VSEL.finditer(line):  # one selector right after an emoji picks its style; anything else hides data
            run = m.group()
            if len(run) > 1 or unicodedata.category(line[m.start() - 1:m.start()] or " ") != "So":
                out.append({"line": i, "char": f"U+{ord(run[0]):04X}",
                            "name": unicodedata.name(run[0]) + (f" x{len(run)}" if len(run) > 1 else "")})
        for w in WORD.findall(line):  # one word mixing Latin with Cyrillic/Greek, e.g. "data" with a Cyrillic "a"
            odd = [c for c in w if unicodedata.name(c, "").startswith(("CYRILLIC", "GREEK"))]
            if odd and any(c.isascii() for c in w):
                out.append({"line": i, "char": f"U+{ord(odd[0]):04X}", "name": f"{unicodedata.name(odd[0])} in '{w}'"})
    return out


def _clean(src):  # hidden characters break parsing, which would let them hide a copy
    if src.isascii():
        return src
    src = src.translate(UNSEEN)
    return "".join("" if (k := unicodedata.category(c)) == "Cf" else " " if k in HIDDEN else c for c in src)


def _fn_name(node):
    n, d = node.child_by_field_name("name"), node
    while n is None and d is not None:  # C++: function_definition -> declarator chain -> identifier
        d = d.child_by_field_name("declarator")
        if d is not None and d.type in NAME:
            n = d
    return n.text if n is not None else None


def _py_noise(node):
    """Type hints and docstrings carry no logic, but AI rewrites add both everywhere: left in, they make two
    AI files about different problems look alike and an AI copy look less like its hint-free original."""
    if node.type == "type":  # `x: int`, `-> list[int]`
        return True
    p = node.parent  # a bare string statement is a docstring (some grammar versions wrap it, some don't)
    return (node.type == "string" and p is not None
            and (p.type in ("block", "module") or (p.type == "expression_statement" and p.named_child_count == 1)))


def tokens(src, lang):
    """Normalized (token, line) stream. Loops and self-recursive calls both emit LOOP."""
    out, stack, after_self = [], [(get_parser(lang).parse(src.encode()).root_node, None)], False
    while stack:
        node, fn = stack.pop()
        t, line = node.type, node.start_point[0] + 1
        if t in SKIP or (lang == "python" and _py_noise(node)):
            continue
        if t in FUNC:
            fn = _fn_name(node)
        if t in LOOP:
            out.append(("LOOP", line))
        elif t in CALL and fn:
            callee = node.child_by_field_name(CALL[t])
            if callee is not None and re.split(rb"\.|->", callee.text)[-1] == fn:  # go(), self.go(), this->go()
                out.append(("LOOP", line))
        if t in LITERAL:
            out.append(("LIT", line))
            continue
        if t == "update_expression":  # ++x and x++ become the same token
            out.append(("UPD", line))
            stack.extend((c, fn) for c in reversed(node.named_children))
            continue
        if node.child_count == 0:
            # `self` and its "." or "," are class plumbing: a copy moved into `class Solution` must still match
            if lang == "python" and t == "identifier" and node.text == b"self":
                after_self = True
                continue
            if after_self:
                after_self = False
                if t in (".", ","):
                    continue
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


def _owners(names):
    """Each file's student: the folder right below the folders every file shares (a zip's wrapper folder is
    skipped). A file directly in that shared folder is its own student."""
    dirs = [Path(n).parts[:-1] for n in names]
    r = 0
    while all(len(d) > r for d in dirs) and len({d[r] for d in dirs}) == 1:
        r += 1
    return {n: d[r] if len(d) > r else n for n, d in zip(names, dirs)}


def scan(path, base=None, progress=_quiet, by_folder=False):
    """base: starter code every student got (file, folder or .zip). Code found in it is ignored, like MOSS -b.
    progress(stage, done, total) reports stages "read", "parse" and "compare" for a progress bar.
    by_folder: each folder is one student, so files in the same student folder are never paired (off by default:
    in the demo set a folder is an assignment)."""
    start = time.perf_counter()
    files = load(path, progress)
    fp = lambda n, src: fingerprints(tokens(_clean(src), LANG[Path(n).suffix.lower()]))
    fps = {}
    for i, (n, src) in enumerate(files.items(), 1):
        fps[n] = fp(n, src)
        progress("parse", i, len(files))
    if base:
        bp = Path(base)
        if bp.suffix.lower() in LANG:
            _check_size(bp.name, bp.stat().st_size)
            bfiles = {bp.name: bp.read_text("utf-8", "replace")}
        else:
            bfiles = load(bp)  # raises when it holds no code
        skip = {h for n, src in bfiles.items() for h in fp(n, src)}
        fps = {n: {h: v for h, v in f.items() if h not in skip} for n, f in fps.items()}
    pairs, owner = [], _owners(list(files)) if by_folder else None
    by_lang = {}
    for n in files:
        by_lang.setdefault(LANG[Path(n).suffix.lower()], []).append(n)
    todo, done = sum(len(v) * (len(v) - 1) // 2 for v in by_lang.values()), 0
    for names in by_lang.values():
        df = Counter(h for n in names for h in fps[n])
        # Rare shared code is strong evidence; code everyone writes (I/O, loops) is weak.
        w = {h: math.log(1 + len(names) / c) for h, c in df.items()}
        total = {n: sum(w[h] for h in fps[n]) for n in names}
        for a, b in combinations(names, 2):
            done += 1
            if done % 2000 == 0:  # 45k pairs for 300 files; every pair would flood the progress bar
                progress("compare", done, todo)
            if owner and owner[a] == owner[b]:  # one student's own files
                continue
            shared = fps[a].keys() & fps[b].keys()
            if not shared:
                continue
            inter = sum(w[h] for h in shared)
            union = total[a] + total[b] - inter
            # Containment rewards a copy padded with extra code, but its denominator never drops below half
            # the bigger file, so a tiny boilerplate file can't look "fully contained" in a real solution.
            small = max(min(total[a], total[b]), 0.5 * max(total[a], total[b]))
            score = 0.5 * (inter / union + inter / small)
            pairs.append({"a": a, "b": b, "score": round(score, 4)})
    progress("compare", todo, todo)
    pairs.sort(key=lambda p: -p["score"])
    for i, p in enumerate(pairs):  # shared sets are rebuilt for the top pairs only: keeping all of them cost ~0.6 GB at 900 files
        fa, fb = fps[p["a"]], fps[p["b"]]
        p["matches"] = _blocks(fa, fb, fa.keys() & fb.keys()) if i < MATCH_TOP else []
    flags = {n: f for n, src in files.items() if (f := hidden_chars(src))}
    marks = {n: m for n, src in files.items() if (m := watermarks(src))}
    return {"files": files, "pairs": pairs, "rings": rings(pairs), "flags": flags, "marks": marks,
            "seconds": round(time.perf_counter() - start, 3)}


def rings(pairs, cut=RING):
    """Groups of 3+ files linked by pairs scoring >= cut, biggest first: a hint that they share one source."""
    root = {}

    def find(n):
        while root.setdefault(n, n) != n:
            n = root[n]
        return n

    links = [p for p in pairs if p["score"] >= cut]
    for p in links:
        root[find(p["a"])] = find(p["b"])
    members, scores = {}, {}
    for n in list(root):
        members.setdefault(find(n), []).append(n)
    for p in links:
        scores.setdefault(find(p["a"]), []).append(p["score"])
    out = [{"files": sorted(members[r]), "score": round(sum(s) / len(s), 4)}
           for r, s in scores.items() if len(members[r]) >= 3]
    return sorted(out, key=lambda g: (-len(g["files"]), -g["score"]))
