"""Comments and docstrings written in a chat-assistant style. A style hint for reviewers, not proof of AI use:
careful students write polished docstrings too."""
import re
import unicodedata

from tree_sitter_language_pack import get_parser

from .engine import _clean

COMMENT = {"comment", "line_comment", "block_comment"}
DASHES = (chr(0x2013), chr(0x2014))  # en and em dash; students rarely type them
FLAG_AT = 2
# (points, reason, test(text, is_docstring)). 2-point rules are clear tells; 1-point rules are polish that
# only counts when combined, so a terse human comment ("checks primality") never trips a single one.
RULES = [
    (2, "chat-assistant phrasing", lambda t, d: re.search(
        r"\b(here'?s|here is|feel free|as requested|let me|i've|you can|example usage)\b|\busage:", t, re.I)),
    (2, "emoji or symbol", lambda t, d: any(unicodedata.category(c) == "So" for c in t)),
    (2, "em or en dash", lambda t, d: any(c in t for c in DASHES)),
    (2, "formal Args/Returns sections", lambda t, d: re.search(
        r"\b(Args|Arguments|Parameters|Returns|Raises|Yields)\s*:", t) or len(re.findall(r"@(param|return|throws)\b", t)) >= 2),
    (2, "markdown formatting", lambda t, d: re.search(r"`[^`]+`|\*\*[^*]+\*\*", t)),
    (2, "step-by-step narration", lambda t, d: re.search(r"\bstep\s*\d", t, re.I)),
    (1, "docstring or Javadoc", lambda t, d: d),
    (1, "polished full sentence", lambda t, d: t[:1].isupper() and t.endswith(".") and len(t.split()) >= 4),
    (1, "describes the code in third person", lambda t, d: re.match(
        r"(returns|counts|computes|calculates|checks|determines|finds|builds|creates|initializes|handles|"
        r"performs|validates|converts|generates|implements|represents)\b", t, re.I)),
    (1, "code notation inside prose", lambda t, d: re.search(r"\w\[\w+\]|[<>=!]=|\(\s*\w+\s*[<>]\s*\w+\s*\)", t)),
    (1, '"this function…" opener', lambda t, d: re.match(
        r"(this (function|method|class|program|code|script)|helper (function |method )?(to|that|for)|"
        r"function (to|that)|utility)\b", t, re.I)),
    (1, "assistant vocabulary", lambda t, d: re.search(
        r"\b(edge cases?|robust\w*|ensures?|gracefully|leverag\w*|utiliz\w*|efficiently|straightforward|"
        r"comprehensive|seamless\w*)\b", t, re.I)),
    (1, "complexity annotation", lambda t, d: re.search(r"\b(time|space) complexity\b|\bO\([^)]*\)", t, re.I)),
]


def _text(raw):
    t = re.sub(r"^[rRuUbBfF]*(\"\"\"|'''|\"|')|(\"\"\"|'''|\"|')$", "", raw.strip())  # Python string quotes
    t = re.sub(r"^\s*(/\*\*?|\*/|\*(?!\*)|//+|#+)", "", t, flags=re.M).replace("*/", "")  # comment markers
    return " ".join(t.split())


def comments(src, lang):
    """Comment and docstring units in document order: [first_line, last_line, text, is_docstring].
    Line comments on consecutive lines are one unit, so a sentence split over lines is judged whole."""
    out, stack = [], [get_parser(lang).parse(_clean(src).encode()).root_node]
    while stack:
        n = stack.pop()
        # a bare string statement (docstring); some grammar versions wrap it in expression_statement, some don't
        doc = ((n.type in ("string", "concatenated_string") and n.parent is not None and n.parent.type in ("block", "module"))
               or (n.type == "expression_statement" and n.named_child_count == 1
                   and n.named_children[0].type in ("string", "concatenated_string")))
        if n.type in COMMENT or doc:
            raw = n.text.decode("utf-8", "replace")
            a, b = n.start_point[0] + 1, n.end_point[0] + 1
            is_doc = doc or raw.startswith("/**")
            if raw.startswith("#!"):
                continue
            if out and not is_doc and not out[-1][3] and out[-1][1] + 1 == a and not raw.startswith("/*"):
                out[-1][1], out[-1][2] = b, out[-1][2] + " " + _text(raw)
            else:
                out.append([a, b, _text(raw), is_doc])
            continue
        stack.extend(reversed(n.children))
    return out


def ai_style(src, lang):
    """Flagged comments: [{"a": first_line, "b": last_line, "reasons": [...]}]."""
    flagged = []
    for a, b, text, doc in comments(src, lang):
        hits = [(p, why) for p, why, test in RULES if text and test(text, doc)]
        if sum(p for p, _ in hits) >= FLAG_AT:
            flagged.append({"a": a, "b": b, "reasons": [why for _, why in hits]})
    return flagged
