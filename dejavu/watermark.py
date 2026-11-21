"""AI watermarks: traces a chat tool or code assistant left in the file itself. A hint, not proof, and never scored.
Statistical watermarks (SynthID, green-list tokens) need the vendor's secret key, so only text marks are checked."""
import re

AI = (r"(the\s+|github\s+|google\s+)?(chat\s?gpt|gpt-?[345][\w.-]*|openai|claude|anthropic|copilot|gemini|bard|"
      r"deepseek|codeium|tabnine|llama|mistral|an?\s+(ai|llm|language\s+model|ai\s+assistant)|ai|llm)\b")
RULES = [
    ("AI attribution", re.compile(
        rf"\b(generated|written|created|produced|authored|assisted|completed|suggested|made)\s+(by|with|using|via)\s+{AI}"
        r"|\bas an ai\b|\bai[- ]generated\b|co-authored-by:[^\n]*\b(claude|copilot|chatgpt|openai|anthropic)\b", re.I)),
    ("LLM control token", re.compile(r"<\|[a-z_]{3,}\|>")),  # <|endoftext|>, <|im_start|> ...
]
FENCE = re.compile(r"^[ \t]*```[\w+#.-]*[ \t]*$")  # markdown fence from a chat answer
TAGS = re.compile("[\U000E0000-\U000E007F]+")  # invisible "ASCII smuggling" letters
VS = re.compile("[\ufe00-\ufe0f\U000E0100-\U000E01EF]{2,}")  # a run of variation selectors encodes bytes


def _vs_byte(c):
    return ord(c) - 0xFE00 if ord(c) <= 0xFE0F else ord(c) - 0xE0100 + 16


def watermarks(src):
    """[{"line": n, "kind": ..., "text": ...}] sorted by line."""
    out = []
    line = lambda i: src.count("\n", 0, i) + 1
    if not src.isascii():
        for m in TAGS.finditer(src):
            if src[m.start() - 1:m.start()] == "\U0001F3F4":  # England/Scotland/Wales flag emoji are tag sequences
                continue
            if text := "".join(chr(ord(c) - 0xE0000) for c in m.group() if 0xE0020 <= ord(c) <= 0xE007E):
                out.append({"line": line(m.start()), "kind": "hidden text (Unicode tags)", "text": text})
        for m in VS.finditer(src):  # one selector after an emoji is normal; a run of them is a payload
            text = bytes(_vs_byte(c) for c in m.group()).decode("utf-8", "replace")
            out.append({"line": line(m.start()), "kind": "hidden text (variation selectors)", "text": text})
    for kind, rx in RULES:
        for m in rx.finditer(src):
            a, b = src.rfind("\n", 0, m.start()) + 1, src.find("\n", m.end())
            out.append({"line": line(m.start()), "kind": kind, "text": src[a:b if b >= 0 else None].strip()[:120]})
    lines = src.split("\n")
    used = [i for i, s in enumerate(lines) if s.strip()]
    for i in {used[0], used[-1]} if used else ():  # a pasted chat answer wraps the code in fences
        if FENCE.match(lines[i]):
            out.append({"line": i + 1, "kind": "chat code fence", "text": lines[i].strip()})
    return sorted(out, key=lambda x: x["line"])
