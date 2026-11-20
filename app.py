import html
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from dejavu.engine import scan

DEMO = Path(__file__).parent / "tests" / "problems"


def code_html(src, ranges):
    """Numbered source with matched line ranges highlighted. Submissions are untrusted, so every line is escaped."""
    hot = {i for a, b in ranges for i in range(a, b + 1)}
    rows = "".join(
        f'<div style="background:{"rgba(255,190,0,.28)" if i in hot else "transparent"}">'
        f'<span style="opacity:.5;user-select:none">{i:>4}  </span>{html.escape(line)}</div>'
        for i, line in enumerate(src.split("\n"), 1)
    )
    pre = f'<pre style="font-size:13px;line-height:1.45;margin:0;width:max-content;min-width:100%">{rows}</pre>'
    return f'<div style="overflow:auto;max-height:640px">{pre}</div>'  # highlight spans long lines when scrolled


st.set_page_config("Dejavu", layout="wide")
st.title("Dejavu")
st.caption("Ranks pairs of code submissions to review first. A score ranks pairs; it is not proof of copying.")

up = st.file_uploader("Submissions (.zip of .py / .cpp / .java files)", type="zip")
starter = st.file_uploader("Starter code given to everyone (optional, ignored when matching)", type=["py", "cpp", "java", "zip"])
left, right = st.columns(2)
if left.button("Scan upload", type="primary", disabled=up is None):
    with tempfile.TemporaryDirectory() as d, st.spinner("Scanning..."):
        sub = Path(d, "submissions.zip")
        sub.write_bytes(up.getvalue())
        base = None
        if starter:
            (Path(d) / "base").mkdir()
            base = Path(d, "base", Path(starter.name).name)  # keep the suffix: scan() picks the language from it
            base.write_bytes(starter.getvalue())
        try:
            st.session_state.r = scan(sub, base)
        except (FileNotFoundError, ValueError, zipfile.BadZipFile) as e:
            st.session_state.pop("r", None)
            st.error(f"Could not scan: {e}")
if right.button("Try the demo set"):
    st.session_state.r = scan(DEMO)

r = st.session_state.get("r")
if not r:
    st.stop()
if not r["pairs"]:
    st.info(f"{len(r['files'])} files scanned, no pairs share any code.")
    st.stop()

st.subheader("Pairs to review first")
st.caption(f"{len(r['files'])} files, {len(r['pairs'])} pairs with shared code, {r['seconds']} s. "
           "⚠ = a file contains hidden characters. Click a row to compare.")
rows = [{"rank": i, "score": p["score"], "file A": p["a"], "file B": p["b"],
         "⚠": "⚠" if p["a"] in r["flags"] or p["b"] in r["flags"] else ""}
        for i, p in enumerate(r["pairs"], 1)]
pick = st.dataframe(rows, hide_index=True, width="stretch", height=320,
                    on_select="rerun", selection_mode="single-row")
p = r["pairs"][(pick.selection.rows or [0])[0]]

st.subheader(f"{p['a']}  vs  {p['b']}  (score {p['score']})")
if not p["matches"]:
    st.caption("Matched lines are only computed for the top 100 pairs.")
for col, name, side in zip(st.columns(2), (p["a"], p["b"]), (0, 1)):
    with col:
        st.markdown(f"**{name}**")
        st.html(code_html(r["files"][name], [m[side] for m in p["matches"]]))
        for f in r["flags"].get(name, []):
            st.warning(f"Line {f['line']}: hidden character {f['char']} ({f['name']}). A hint, not proof.")
