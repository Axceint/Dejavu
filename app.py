"""Streamlit host: takes the upload, runs scan(), and embeds the review app from dejavu/review.html."""
import csv
import io
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from dejavu.engine import scan
from dejavu.report import payload, render, theme_toggle

DEMO = Path(__file__).parent / "tests" / "problems"

st.set_page_config("Dejavu", layout="wide", initial_sidebar_state="collapsed")
st.html("""<style>
header[data-testid="stHeader"], footer {display:none}
.block-container {padding:12px 20px; max-width:none}
/* The review screen fills the window under the top bar: 12px pad + 40px bar + 16px gap + 12px pad = 80px. */
.st-key-review iframe {display:block; height:calc(100dvh - 80px) !important; min-height:520px;
  border:1px solid var(--dj-line, rgba(128,128,128,.25)); border-radius:6px}
.st-key-review [data-testid="stElementContainer"] {flex:0 0 auto !important; height:auto !important}
.st-key-theme iframe {display:block; border:0}

/* Streamlit can't switch its own theme from code, so the theme toggles (review.html, toggle.html) set
   data-dejavu-theme on this page and these rules repaint it (same palette as review.html and config.toml). */
html[data-dejavu-theme=light] {color-scheme:light; --dj-bg:#fafaf9; --dj-panel:#fff; --dj-sunk:#f3f3f1;
  --dj-line:#cfcfca; --dj-text:#1b1b19; --dj-muted:#65655f; --dj-accent:#b45309; --dj-on-accent:#fff;
  --dj-kw:#1d4f91; --dj-str:#1f6f43; --dj-com:#8b8b84; --dj-num:#9a4a12}
html[data-dejavu-theme=dark] {color-scheme:dark; --dj-bg:#141413; --dj-panel:#1b1b1a; --dj-sunk:#222220;
  --dj-line:#3d3d39; --dj-text:#ecece8; --dj-muted:#a3a39b; --dj-accent:#f0a33a; --dj-on-accent:#141413;
  --dj-kw:#8ab4f8; --dj-str:#8fd19e; --dj-com:#7c7c75; --dj-num:#f2a96b}
html[data-dejavu-theme] [data-testid="stHeading"] :is(h1, h2, h3) {color:var(--dj-text)}
html[data-dejavu-theme] [data-testid="stCaptionContainer"] {color:var(--dj-muted)}
html[data-dejavu-theme] [data-testid="stCode"] pre {background:var(--dj-sunk); color:var(--dj-text)}
html[data-dejavu-theme] [data-testid="stCode"] .token.keyword {color:var(--dj-kw)}
html[data-dejavu-theme] [data-testid="stCode"] .token.string {color:var(--dj-str)}
html[data-dejavu-theme] [data-testid="stCode"] .token.number {color:var(--dj-num)}
html[data-dejavu-theme] [data-testid="stCode"] .token.comment {color:var(--dj-com)}
html[data-dejavu-theme] [data-testid="stCode"] .token.function {color:var(--dj-text)}
html[data-dejavu-theme] [data-testid="stCode"] :is(.token.operator, .token.punctuation) {color:var(--dj-muted)}
html[data-dejavu-theme] [data-testid="stBaseButton-primary"] {background:var(--dj-accent); border-color:var(--dj-accent);
  color:var(--dj-on-accent)}
html[data-dejavu-theme] [data-testid="stBaseButton-primary"]:disabled {background:transparent; border-color:var(--dj-line);
  color:var(--dj-muted)}
html[data-dejavu-theme] :is([data-testid="stApp"], [data-testid="stPopoverBody"]) {
  background:var(--dj-bg); color:var(--dj-text)}
html[data-dejavu-theme] [data-testid="stPopoverBody"] {border:1px solid var(--dj-line)}
html[data-dejavu-theme] :is([data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"]) {color:var(--dj-text)}
html[data-dejavu-theme] [data-testid="stMarkdownContainer"] code {background:var(--dj-sunk); color:var(--dj-muted)}
html[data-dejavu-theme] [data-testid="stFileUploaderDropzone"] {background:var(--dj-sunk); color:var(--dj-text)}
html[data-dejavu-theme] [data-testid="stFileUploaderDropzoneInstructions"] * {color:var(--dj-muted)}
html[data-dejavu-theme] :is([data-testid="stBaseButton-secondary"], [data-testid="stPopoverButton"]) {
  background:var(--dj-panel); border-color:var(--dj-line); color:var(--dj-text)}
html[data-dejavu-theme] :is([data-testid="stBaseButton-secondary"], [data-testid="stPopoverButton"]):hover {
  background:var(--dj-sunk); border-color:var(--dj-text); color:var(--dj-text)}
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
bar = st.columns([5, 1.2, 1.2, 1.4, 1.2], vertical_alignment="center")
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
else:
    # the review screen has its own toggle; this one covers the landing page
    with bar[4].container(key="theme", horizontal=True, horizontal_alignment="right"):
        st.iframe(theme_toggle(st.context.theme.type), width=32, height=32)

if st.session_state.get("err"):
    st.error(st.session_state.err)

if html:
    # html is our own template; uploaded code only enters it as escaped JSON data (see dejavu/report.py)
    with st.container(key="review"):
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
