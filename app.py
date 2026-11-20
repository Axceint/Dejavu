"""Streamlit host: takes the upload, runs scan(), and embeds the review app from dejavu/review.html."""
import csv
import io
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from dejavu.engine import scan
from dejavu.report import payload, render

DEMO = Path(__file__).parent / "tests" / "problems"

st.set_page_config("Dejavu", layout="wide", initial_sidebar_state="collapsed")
st.html("""<style>
header[data-testid="stHeader"], footer {display:none}
.block-container {padding:12px 20px 0; max-width:none}
iframe {border:1px solid rgba(128,128,128,.25); border-radius:6px}
</style>""")


def all_pairs_csv(r):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["rank", "score", "file_a", "file_b"])
    # leading = + - @ would run as a formula in Excel; file names come from students
    safe = lambda s: "'" + s if s[:1] in "=+-@" else s
    w.writerows([i, p["score"], safe(p["a"]), safe(p["b"])] for i, p in enumerate(r["pairs"], 1))
    return out.getvalue()


def run(path, base, label):
    try:
        r = scan(path, base)
    except (FileNotFoundError, ValueError, zipfile.BadZipFile) as e:
        st.session_state.err = f"Couldn't scan {label}: {e}"
        return
    st.session_state.update(data=payload(r), csv=all_pairs_csv(r), label=label, err=None)


def upload_form(key):
    up = st.file_uploader("Submissions: one .zip of .py, .cpp or .java files", type="zip", key=f"z{key}")
    starter = st.file_uploader("Starter code everyone received (optional). Matches inside it are ignored.",
                               type=["py", "cpp", "java", "zip"], key=f"s{key}")
    if st.button("Scan", type="primary", disabled=up is None, key=f"b{key}"):
        with tempfile.TemporaryDirectory() as d, st.spinner("Scanning…"):
            sub = Path(d, "submissions.zip")
            sub.write_bytes(up.getvalue())
            base = None
            if starter:
                (Path(d) / "base").mkdir()
                base = Path(d, "base", Path(starter.name).name)  # keep the suffix: scan() picks the language from it
                base.write_bytes(starter.getvalue())
            run(sub, base, up.name)
        st.rerun()


data = st.session_state.get("data")
# rendered per run so the review screen opens in the frame's current light/dark theme
html = render(data, st.context.theme.type) if data else None
bar =st.columns([5, 1.2, 1.2, 1.4, 1.2], vertical_alignment="center")
label = st.session_state.get("label", "").replace("`", "'")  # upload name is untrusted: keep it inline code
bar[0].markdown("**Dejavu** · code similarity review" + (f" · `{label}`" if html else ""))
if html:
    with bar[1].popover("New scan", width="stretch"):
        upload_form("bar")
    if bar[2].button("Demo set", width="stretch"):
        run(DEMO, None, "demo set")
        st.rerun()
    bar[3].download_button("Offline report", html, "dejavu-report.html", "text/html", width="stretch",
                           help="The same review screen as one HTML file. Opens without a server.")
    bar[4].download_button("All pairs CSV", st.session_state.csv, "dejavu-pairs.csv", "text/csv", width="stretch")

if st.session_state.get("err"):
    st.error(st.session_state.err)

if html:
    # html is our own template; uploaded code only enters it as escaped JSON data (see dejavu/report.py)
    st.iframe(html, height=880)
else:
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.subheader("Find submissions that share logic, even after renaming or an AI rewrite")
        st.write("Upload every student's file for one assignment. Dejavu ranks each pair by how much rare "
                 "structure they share, shows the matching lines side by side, and lets you mark each pair "
                 "as you review. A score ranks pairs for review; it is not proof of copying.")
        upload_form("main")
        st.caption("No zip at hand?")
        if st.button("Try the demo set"):
            run(DEMO, None, "demo set")
            st.rerun()
    with right:
        st.markdown("**How it works**")
        st.code("# Student A                # Student B\n"
                "def total(nums):           def add_all(values):\n"
                "    s = 0                      result = 0\n"
                "    for x in nums:             for v in values:\n"
                "        s += x                     result += v\n"
                "    return s                   return result", language="python")
        st.markdown("Both become `def ID ( ID ) : ID = LIT LOOP ID in ID : ID += ID return ID`. Names, numbers "
                    "and loop styles stop mattering. Short runs of these tokens are compared across every pair, "
                    "and runs that few students share count most.")
