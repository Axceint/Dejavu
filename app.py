import csv
import html
import io
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from dejavu.engine import MATCH_TOP, scan
from dejavu.explain import evidence

DEMO = Path(__file__).parent / "tests" / "problems"
# Rough cut-offs from our hand-made test set (true copies 0.23-0.64, worst false pair 0.20). Not calibrated.
BANDS = [(0.4, "Review first"), (0.2, "Worth a look"), (0.0, "Low")]


def band(score):
    return next(label for cut, label in BANDS if score >= cut)


def md(name):
    """File and variable names come from uploads: show them as inline code so markdown can't format them."""
    return "`" + str(name).replace("`", "'") + "`"


def code_html(src, blocks):
    """Numbered source with matched lines highlighted. Submissions are untrusted: every line is escaped."""
    hot = {i for a, b in blocks for i in range(a, b + 1)}
    rows = "".join(
        f'<div class="ln{" hot" if i in hot else ""}"><span class="no">{i}</span>{html.escape(line) or " "}</div>'
        for i, line in enumerate(src.split("\n"), 1)
    )
    return f'<div class="src"><pre>{rows}</pre></div>'


CODE_CSS = """<style>
.src{overflow:auto;max-height:560px;border:1px solid rgba(128,128,128,.25);border-radius:6px}
.src pre{margin:0;padding:6px 0;font-size:12.5px;line-height:1.5;width:max-content;min-width:100%}
.ln{padding-right:12px}.ln.hot{background:rgba(234,179,8,.22)}
.no{display:inline-block;width:3em;text-align:right;padding-right:1em;opacity:.45;user-select:none}
</style>"""


def run(path, base=None):
    try:
        st.session_state.r = scan(path, base)
    except (FileNotFoundError, ValueError, zipfile.BadZipFile) as e:
        st.session_state.pop("r", None)
        st.error(f"Couldn't scan that upload: {e}")


st.set_page_config("Dejavu", layout="wide")

with st.sidebar:
    st.header("Submissions")
    up = st.file_uploader("Zip of .py, .cpp or .java files", type="zip")
    starter = st.file_uploader("Starter code (optional)", type=["py", "cpp", "java", "zip"],
                               help="Code every student was given. Matches inside it are ignored.")
    if st.button("Scan", type="primary", disabled=up is None, width="stretch"):
        with tempfile.TemporaryDirectory() as d, st.spinner("Scanning…"):
            sub = Path(d, "submissions.zip")
            sub.write_bytes(up.getvalue())
            base = None
            if starter:
                (Path(d) / "base").mkdir()
                base = Path(d, "base", Path(starter.name).name)  # keep the suffix: scan() picks the language from it
                base.write_bytes(starter.getvalue())
            run(sub, base)
    st.divider()
    st.caption("No zip at hand? Scan 18 sample solutions, including AI-disguised copies.")
    if st.button("Try the demo set", width="stretch"):
        run(DEMO)

st.title("Dejavu")
st.write("Finds pairs of code submissions that share logic, even after renaming, reordering or an AI rewrite.")

r = st.session_state.get("r")
if not r:
    st.info("Upload a zip of submissions in the sidebar, or try the demo set.")
    with st.expander("How it works", expanded=True):
        st.markdown(
            "Student B renamed everything to hide the copy:\n"
            "```python\n"
            "# Student A                      # Student B\n"
            "def total(nums):                 def add_all(values):\n"
            "    s = 0                            result = 0\n"
            "    for x in nums:                   for v in values:\n"
            "        s += x                           result += v\n"
            "    return s                         return result\n"
            "```\n"
            "Dejavu erases the disguise: every name becomes `ID`, every number `LIT`, every loop `LOOP`. "
            "Both files now read `def ID ( ID ) : ID = LIT LOOP ID in ID : ID += ID return ID`.\n\n"
            "It then compares short runs of these tokens across every pair. Runs that few students share count "
            "more than code everyone writes, such as reading input. Pairs are ranked by score. "
            "**A score ranks pairs for review. It is not proof of copying.**"
        )
    st.stop()

pairs, flags = r["pairs"], r["flags"]
st.caption(f"{len(r['files'])} files · {len(pairs)} pairs share code · {len(flags)} files with hidden characters"
           f" · {r['seconds']} s")
if not pairs:
    st.info("No two submissions in the same language share any code.")
    st.stop()

rows = [{"Rank": i, "Score": p["score"], "Band": band(p["score"]), "File A": p["a"], "File B": p["b"],
         "Flags": "Hidden chars" if p["a"] in flags or p["b"] in flags else ""}
        for i, p in enumerate(pairs, 1)]
head = st.columns([3, 1])
head[0].subheader("Pairs, most similar first")
buf = io.StringIO()
csv.DictWriter(buf, rows[0].keys()).writeheader()
csv.DictWriter(buf, rows[0].keys()).writerows(rows)
head[1].download_button("Download CSV", buf.getvalue(), "dejavu_pairs.csv", "text/csv", width="stretch")
pick = st.dataframe(
    rows, hide_index=True, width="stretch", height=300, on_select="rerun", selection_mode="single-row",
    column_config={
        "Rank": st.column_config.NumberColumn(width="small"),
        "Score": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1, width="small"),
        "Band": st.column_config.TextColumn(width="small", help="Rough cut-offs: 0.4+ review first, "
                                                                "0.2-0.4 worth a look. Not calibrated."),
    },
)
st.caption("Select a row to see the evidence.")
idx = (pick.selection.rows or [0])[0]
p = pairs[idx]
e = evidence(r, p)

st.divider()
st.subheader(f"Pair {idx + 1}: {md(p['a'])} and {md(p['b'])}")

# --- Evidence: each line is a check a reviewer can verify in the code below ---
pct = lambda x: f"{x:.0%}"
points = [f"**Score {p['score']:.2f}, {band(p['score']).lower()}.** "
          + ("Highest in this batch." if idx == 0 else f"Higher than {pct(e['beats'])} of the {len(pairs)} pairs.")]
if p["matches"]:
    big = e["blocks"][0]
    points.append(f"**Matching structure covers {pct(e['coverage'][0])} of {md(p['a'])} and "
                  f"{pct(e['coverage'][1])} of {md(p['b'])}** across {len(e['blocks'])} fragments. "
                  f"The longest spans {big['lines']} lines "
                  f"(A {big['a'][0]}-{big['a'][1]}, B {big['b'][0]}-{big['b'][1]}).")
else:
    points.append(f"Line-level evidence is computed for the top {MATCH_TOP} pairs only.")
if e["renames"]:
    shown = ", ".join(f"{md(a)} → {md(b)}" for a, b, _ in e["renames"][:4])
    more = f" and {len(e['renames']) - 4} more" if len(e["renames"]) > 4 else ""
    points.append(f"**{len(e['renames'])} names fill the same roles**: {shown}{more}. "
                  f"Read {md(p['a'])} with these swaps and compare it to {md(p['b'])}.")
if e["verbatim"]:
    points.append(f"**{len(e['verbatim'])} identical lines** that appear in no other submission.")
for name in (p["a"], p["b"]):
    if name in flags:
        points.append(f"{md(name)} contains **{len(flags[name])} hidden or look-alike characters**, often left by "
                      "text pasted from a chat tool. A hint, not proof.")
st.markdown("\n".join(f"- {x}" for x in points))
st.caption("Evidence for a reviewer, not a verdict. The score is the main signal because it weighs code few "
           "students share; the details show where it comes from. Independent solutions to the same task also "
           "share structure and name roles, so judge them against the other pairs in this batch.")

tabs = st.tabs(["Side by side", f"Renamed names ({len(e['renames'])})",
                f"Identical lines ({len(e['verbatim'])})", f"Matching fragments ({len(e['blocks'])})"])
with tabs[0]:
    st.html(CODE_CSS)
    for col, name, side in zip(st.columns(2), (p["a"], p["b"]), ("a", "b")):
        with col:
            st.markdown(md(name))
            st.html(code_html(r["files"][name], [blk[side] for blk in e["blocks"]]))
            for f in flags.get(name, []):
                st.warning(f"Line {f['line']}: {f['char']} {f['name']}. A hint, not proof.")
    st.caption("Highlighted lines have the same structure in both files, after names and numbers are ignored.")
with tabs[1]:
    if e["renames"]:
        st.dataframe([{f"In {p['a']}": a, f"In {p['b']}": b, "Times aligned": n} for a, b, n in e["renames"]],
                     hide_index=True, width="stretch")
        st.caption("Each pair of names fills the same position in matching code at least twice. Common in copies, "
                   "but independent solutions to one task can show it too.")
    else:
        st.write("No consistent renames found.")
with tabs[2]:
    if e["verbatim"]:
        st.dataframe([{"Line in A": la, "Line in B": lb, "Text": t} for la, lb, t in e["verbatim"]],
                     hide_index=True, width="stretch")
    else:
        st.write("No identical lines beyond code that other submissions also contain.")
with tabs[3]:
    if e["blocks"]:
        st.dataframe([{"Fragment": k,"Lines in A": f"{b['a'][0]}-{b['a'][1]}", "Lines in B": f"{b['b'][0]}-{b['b'][1]}",
                       "Length": b["lines"]} for k, b in enumerate(e["blocks"], 1)], hide_index=True, width="stretch")
    else:
        st.write(f"Not computed: only the top {MATCH_TOP} pairs get line-level matches.")
