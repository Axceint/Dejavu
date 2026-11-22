"""Streamlit host: takes the upload, runs scan(), and embeds the review app from dejavu/review.html."""
import csv
import io
import re
import os
import tempfile
import time
import zipfile
from html import escape
from urllib.parse import quote
from pathlib import Path

import streamlit as st

from dejavu import ask, telemetry
from dejavu.engine import scan
from dejavu.report import payload, render, theme_toggle

DEMO = Path(__file__).parent / "tests" / "problems"

st.set_page_config("Dejavu", layout="wide", initial_sidebar_state="collapsed")
st.html("""<style>
@import url("https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&display=swap");
header[data-testid="stHeader"], footer {display:none}
/* type: warm sans for text, serif for headings and the wordmark; code keeps its monospace */
.stApp :is(p, li, label, button, input, small):not(pre *):not(code *) {font-family:"DM Sans", system-ui, sans-serif}
[data-testid="stHeading"] :is(h1, h2, h3) {font-family:"Fraunces", Georgia, serif; font-weight:600; letter-spacing:-.01em}
.st-key-brand strong {font-family:"Fraunces", Georgia, serif; font-size:22px; font-weight:600; letter-spacing:-.01em;
  color:var(--dj-text, inherit)}
.st-key-brand p {color:var(--dj-muted, inherit)}
/* progress bars: thin and caramel, whatever the theme state */
[data-testid="stProgressBarTrack"] {height:6px; border-radius:3px; background:var(--dj-sunk, rgba(128,128,128,.18))}
[data-testid="stProgressBarTrack"] > div {border-radius:3px; background:var(--dj-accent, #a0522d)}
.block-container {padding:12px 20px; max-width:none}
/* The review screen fills the window under the top bar: 12px pad + 40px top bar + 16px gap + 12px pad = 80px.
   The unzip/scan bars only exist while a scan runs. */
.st-key-phases:not(:has([data-testid="stProgress"])) {display:none}
/* "Maximise" in the review screen sets data-dejavu-max here: the frame gives it the whole window */
html[data-dejavu-max] .st-key-topbar, html[data-dejavu-max] .st-key-phases {display:none}
/* Streamlit wraps each keyed block; hide the wrapper too, or its 16px gap still makes the page scroll */
html[data-dejavu-max] [data-testid="stLayoutWrapper"]:has(> :is(.st-key-topbar, .st-key-phases)) {display:none}
html[data-dejavu-max] .st-key-review iframe {height:calc(100dvh - 24px) !important}
.st-key-review iframe {display:block; height:calc(100dvh - 80px) !important; min-height:520px;
  border:1px solid var(--dj-line, rgba(128,128,128,.25)); border-radius:10px}
/* a new scan from the review shows its bars above the old review: the frame gives up their row (32px + 16px gap) */
html:not([data-dejavu-max]):has(.st-key-phases [data-testid="stProgress"]) .st-key-review iframe {height:calc(100dvh - 128px) !important}
.st-key-review [data-testid="stElementContainer"] {flex:0 0 auto !important; height:auto !important}
.st-key-theme iframe {display:block; border:0}

/* Streamlit can't switch its own theme from code, so the theme toggles (review.html, toggle.html) set
   data-dejavu-theme on this page and these rules repaint it (same palette as review.html and config.toml). */
html {color-scheme:light; --dj-bg:#f6f1e9; --dj-panel:#fffcf7; --dj-sunk:#efe7db;
  --dj-line:#d6c8b4; --dj-text:#2a1f17; --dj-muted:#6f5f4f; --dj-accent:#a0522d; --dj-on-accent:#fffcf7; --dj-accent-ink:#a0522d;
  --dj-kw:#8a4b1f; --dj-str:#4f6b2f; --dj-com:#9c8b78; --dj-num:#b0621e; --dj-ok:#3f6b3a; --dj-bad:#a8322a}
html[data-dejavu-theme=dark] {color-scheme:dark; --dj-bg:#1b1612; --dj-panel:#231c17; --dj-sunk:#2c241e;
  --dj-line:#4a3d33; --dj-text:#f3e9dc; --dj-muted:#c2b09c; --dj-accent:#e0a36a; --dj-on-accent:#1b1612; --dj-accent-ink:#e0a36a;
  --dj-kw:#e7b07a; --dj-str:#b9d08a; --dj-com:#8f7d6a; --dj-num:#f0b27a; --dj-ok:#a7cf8f; --dj-bad:#f19a8f}
html[data-dejavu-theme] [data-testid="stHeading"] :is(h1, h2, h3) {color:var(--dj-text)}
html[data-dejavu-theme] [data-testid="stCaptionContainer"] {color:var(--dj-muted)}
html[data-dejavu-theme] [data-testid="stCode"] pre {background:var(--dj-sunk); color:var(--dj-text)}
html[data-dejavu-theme] [data-testid="stCode"] .token.keyword {color:var(--dj-kw)}
html[data-dejavu-theme] [data-testid="stCode"] .token.string {color:var(--dj-str)}
html[data-dejavu-theme] [data-testid="stCode"] .token.number {color:var(--dj-num)}
html[data-dejavu-theme] [data-testid="stCode"] .token.comment {color:var(--dj-com)}
html[data-dejavu-theme] [data-testid="stCode"] .token.function {color:var(--dj-text)}
html[data-dejavu-theme] [data-testid="stCode"] :is(.token.operator, .token.punctuation) {color:var(--dj-muted)}
html[data-dejavu-theme] :is([data-testid="stApp"], [data-testid="stPopoverBody"]) {
  background:var(--dj-bg); color:var(--dj-text)}
html[data-dejavu-theme] [data-testid="stPopoverBody"] {border:1px solid var(--dj-line)}
html[data-dejavu-theme] :is([data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"]) {color:var(--dj-text)}
/* error boxes follow the OS theme like the rest of Streamlit; repaint them so their text stays readable */
html[data-dejavu-theme] [data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {
  background:color-mix(in srgb, var(--dj-bad) 12%, var(--dj-panel)); border:1px solid color-mix(in srgb, var(--dj-bad) 40%, transparent)}
html[data-dejavu-theme] [data-testid="stMarkdownContainer"] code {background:var(--dj-sunk); color:var(--dj-muted)}
html[data-dejavu-theme] [data-testid="stFileUploaderDropzone"] {background:var(--dj-sunk); color:var(--dj-text); border-color:var(--dj-line)}
html[data-dejavu-theme] [data-testid="stFileUploaderDropzoneInstructions"] * {color:var(--dj-muted)}
html[data-dejavu-theme] :is([data-testid="stBaseButton-secondary"], [data-testid="stPopoverButton"]) {
  background:var(--dj-panel); border-color:var(--dj-line); color:var(--dj-text)}
html[data-dejavu-theme] :is([data-testid="stBaseButton-secondary"], [data-testid="stPopoverButton"]):hover {
  background:var(--dj-sunk); border-color:var(--dj-text); color:var(--dj-text)}
/* One accent and one foreground treatment for every primary action, including Ask AI. */
html :is([data-testid="stBaseButton-primary"], .st-key-askai [data-testid="stPopoverButton"]) {
  background:var(--dj-accent); border-color:var(--dj-accent); color:var(--dj-on-accent); font-weight:600}
html :is([data-testid="stBaseButton-primary"], .st-key-askai [data-testid="stPopoverButton"]) * {
  color:var(--dj-on-accent) !important}
html :is([data-testid="stBaseButton-primary"]:not(:disabled), .st-key-askai [data-testid="stPopoverButton"]):hover {
  background:var(--dj-accent); border-color:var(--dj-accent); color:var(--dj-on-accent); filter:brightness(1.08)}
html [data-testid="stBaseButton-primary"]:disabled {opacity:.55; cursor:not-allowed}

/* Start page: the headline and the upload card */
.st-key-intro [data-testid="stHeading"] h1 {font-size:2rem; line-height:1.15; padding:8px 0 12px; text-wrap:balance}  /* no lone last word */
.st-key-intro [data-testid="stMarkdownContainer"] p {color:var(--dj-muted, inherit); font-size:1.0625rem}
.st-key-upload {background:var(--dj-panel, transparent); border-color:var(--dj-line, rgba(128,128,128,.25)) !important}

/* Ask AI: a button in the top bar; it opens as a panel under the bar, so closed it covers nothing */
.st-key-actions > :has(.st-key-askai) {flex:0 0 fit-content; width:fit-content}  /* its fragment wrapper would otherwise stretch */
/* start page: a centred column instead of the full width; the demo gets its own accent block */
.block-container:has(.st-key-intro):not(:has(.st-key-review)) {max-width:1120px; margin:0 auto; padding-top:24px}
/* the old start page lingers (faded) until the run after a scan ends; hide it once the review is drawn */
.block-container:has(.st-key-review) :is(.st-key-intro, .st-key-how) {display:none}
.st-key-how {position:sticky; top:16px; align-self:flex-start}
@media (max-width:900px) {.st-key-how {position:static}}
.st-key-demo {background:color-mix(in srgb, var(--dj-accent, #a0522d) 12%, transparent);
  border-color:var(--dj-accent, #a0522d) !important}
/* two body sizes: the lede at 1.0625rem, everything else at 1rem */
.st-key-demo [data-testid="stMarkdownContainer"] p, .st-key-upload [data-testid="stWidgetLabel"] p,
  .st-key-how [data-testid="stMarkdownContainer"] :is(p, li) {font-size:1rem}
.st-key-how [data-testid="stHeading"] h3 {font-size:1.25rem; padding:10px 0 8px}  /* section labels, under the title */
.st-key-how [data-testid="stCode"] pre code {font-size:13px}  /* the two-column example fits a 400px column */
.st-key-demo > :has([data-testid="stMarkdown"]) {flex:1 1 0; min-width:0}  /* text and button on one row */
.st-key-askai_body {width:min(420px, calc(100vw - 72px))}
[data-testid="stPopoverBody"]:has(.st-key-askai_body) {box-shadow:0 12px 32px rgba(0,0,0,.22)}
/* every menu fades and rises in, and buttons press down */
[data-testid="stPopoverBody"] {animation:dj-fade .2s ease-out}
@keyframes dj-fade {0%, 40% {opacity:0; translate:0 4px} to {opacity:1; translate:none}}  /* hidden while the popover is still being positioned */
[data-testid^="stBaseButton"]:active:not(:disabled) {transform:translateY(1px)}
@media (prefers-reduced-motion: reduce) {[data-testid="stPopoverBody"] {animation:none}}
/* AI status chip, in the middle of the top bar: off (grey), ready (green), error (red), indexing (red, pulsing) */
/* centred in the free space between the name and the buttons */
/* brand and buttons get equal shares, so the chip sits at the page centre (it moves only when the buttons need the room) */
.st-key-topbar > :has([class*="st-key-aichip"], .dj-ai-busy) {flex:0 0 auto; width:fit-content}
.st-key-topbar:has(.st-key-actions) > :has(.st-key-brand) {flex:1 1 0; width:auto; min-width:0}
.st-key-topbar > :has(.st-key-actions), .st-key-actions {flex:1 1 0; min-width:max-content; flex-wrap:nowrap}
/* one row at any desktop width: the name gives way (ellipsis) before the buttons wrap */
.st-key-topbar:has(.st-key-askai, [class*="st-key-aichip"]) {flex-wrap:nowrap}
.st-key-topbar > :has(.st-key-brand) {min-width:0}
.st-key-brand {min-width:0; overflow:hidden}
.st-key-brand p {white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
.st-key-brand code {white-space:nowrap}
[class*="st-key-aichip"] [data-testid="stPopoverButton"] {border-radius:999px; padding:2px 12px; min-height:0; font-size:.85rem}
html[data-dejavu-theme] [data-testid="stTextInput"] :is([data-baseweb="base-input"], input, button) {background:var(--dj-sunk); color:var(--dj-text)}
/* key box: one bordered field with the eye inside it, same colours as the rest; no browser autofill blue */
[data-testid="stPopoverBody"] [data-testid="stTextInputRootElement"] {border:1px solid var(--dj-line); border-radius:8px;
  background:var(--dj-sunk); overflow:hidden}
[data-testid="stPopoverBody"] [data-testid="stTextInputRootElement"]:focus-within {border-color:var(--dj-accent);
  box-shadow:0 0 0 3px color-mix(in srgb, var(--dj-accent) 22%, transparent)}
[data-testid="stPopoverBody"] [data-testid="stTextInputRootElement"] :is(input, button) {background:transparent !important;
  color:var(--dj-text); border:0}
[data-testid="stPopoverBody"] [data-testid="stTextInputRootElement"] button {color:var(--dj-muted)}
[data-testid="stPopoverBody"] [data-testid="stTextInputRootElement"] button:hover {color:var(--dj-accent)}
[data-testid="stPopoverBody"] input:-webkit-autofill {-webkit-box-shadow:0 0 0 40px var(--dj-sunk) inset; -webkit-text-fill-color:var(--dj-text)}
.st-key-aichip_off [data-testid="stPopoverButton"] {border-style:dashed; color:var(--dj-muted, inherit)}
.st-key-aichip_ready [data-testid="stIconMaterial"] {color:var(--dj-ok, #3f6b3a)}
.st-key-aichip_error :is([data-testid="stIconMaterial"], [data-testid="stMarkdownContainer"] p) {color:var(--dj-bad, #a8322a)}
.dj-ai-busy {display:inline-flex; align-items:center; gap:8px; padding:4px 12px; border-radius:999px; white-space:nowrap;
  font-size:.85rem; font-weight:600; color:var(--dj-bad, #a8322a); border:1px solid currentColor;
  background:color-mix(in srgb, var(--dj-bad, #a8322a) 10%, transparent)}
.dj-ai-busy i {width:8px; height:8px; border-radius:50%; background:currentColor; animation:dj-pulse 1s ease-in-out infinite}
@keyframes dj-pulse {50% {opacity:.25}}
@media (prefers-reduced-motion: reduce) {.dj-ai-busy i {animation:none}}
/* citation numbers: small accent badges, so they stand apart from the file name */
.dj-cite {display:inline-flex; align-items:center; gap:8px; max-width:100%; margin:2px 0; padding:4px 10px;
  font:inherit; font-size:.85rem; text-align:left; cursor:pointer; color:var(--dj-text, inherit);
  background:var(--dj-sunk, rgba(128,128,128,.12)); border:1px solid var(--dj-line, rgba(128,128,128,.35)); border-radius:8px}
.dj-cite:hover {border-color:var(--dj-accent-ink, #a0522d)}
.dj-cite .n {flex:none; min-width:1.4em; padding:0 5px; border-radius:6px; font-size:.75rem; font-weight:700;
  text-align:center; color:var(--dj-on-accent, #fff); background:var(--dj-accent, #a0522d)}
.st-key-askai_body .stMarkdownBadge {background:var(--dj-accent, #a0522d) !important; color:var(--dj-on-accent, #fff) !important;
  font-size:.75rem !important; font-weight:700; padding:0 6px; border-radius:6px; vertical-align:1px;
  display:inline}  /* same as the chip numbers; inline, not inline-block, so the nbsp keeps it on its word's line */
.dj-cite code {overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:.8rem}
.dj-cite .go {flex:none; color:var(--dj-accent-ink, #a0522d); font-weight:600}
html[data-dejavu-theme] .st-key-askai_body [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background:var(--dj-sunk)}
html[data-dejavu-theme] .st-key-askai_body [data-testid="stChatInput"] > div {background:var(--dj-sunk);
  border-color:var(--dj-line)}
html[data-dejavu-theme] .st-key-askai_body textarea::placeholder {color:var(--dj-muted)}
html[data-dejavu-theme] .st-key-askai_body [data-testid="stChatInputSubmitButton"] {color:var(--dj-muted)}
</style>""")


def all_pairs_csv(r):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["rank", "score", "file_a", "file_b", "ring"])
    ring = {n: k for k, g in enumerate(r["rings"], 1) for n in g["files"]}
    # leading = + - @ tab or CR would run as a formula in Excel (OWASP); file names come from students
    safe = lambda s: "'" + s if s[:1] and s[:1] in "=+-@\t\r" else s
    w.writerows([i, p["score"], safe(p["a"]), safe(p["b"]), k if (k := ring.get(p["a"])) and k == ring.get(p["b"]) else ""]
                for i, p in enumerate(r["pairs"], 1))
    return out.getvalue()


DEMO_JOB = {"name": "demo set"}
# Where each scan stage sits on the scanning bar, and its live label.
STAGES = {"parse": (0.0, 0.6, "parsing **{:,}** / {:,} files"), "compare": (0.6, 0.85, "comparing **{:,}** / {:,} pairs"),
          "explain": (0.85, 1.0, "preparing evidence **{:,}** / {:,}")}


def run(job, area):
    """Scan an upload (or the demo set) with live unzip and scan bars in `area`. They go away with the rerun
    that shows the results; the scan time is on the review screen."""
    zipped = "zip" in job
    now_verb, done_verb = ("Unzipping", "Unzipped") if zipped else ("Reading files", "Read")
    read_bar = area.progress(0.0, text=f"{now_verb}…")
    scan_bar = area.progress(0.0, text="Scanning · waiting for files")
    t = {"read": None, "shown": 0.0, "start": time.perf_counter()}

    def tick(stage, done, total):
        now = time.perf_counter()
        if stage != "read" and t["read"] is None:
            t["read"] = now
            read_bar.progress(1.0, text=f"{done_verb} all files")
        if now - t["shown"] < 0.05 and done < total:  # repaint at most 20 times a second
            return
        t["shown"] = now
        frac, clock = done / total if total else 1.0, f" · {now - t['start']:.1f} s"  # counts up while it runs
        if stage == "read":
            read_bar.progress(frac, text=f"{now_verb} · **{done:,}** / {total:,} files" + clock)
        else:
            lo, hi, label = STAGES[stage]
            scan_bar.progress(lo + (hi - lo) * frac, text="Scanning · " + label.format(done, total) + clock)

    try:
        with tempfile.TemporaryDirectory() as d:
            path, base = DEMO, None
            if zipped:
                path = Path(d, "submissions.zip")
                path.write_bytes(job["zip"])
                if job["starter"]:
                    (Path(d) / "base").mkdir()
                    base = Path(d, "base", job["starter_name"])  # keep the suffix: scan() picks the language from it
                    base.write_bytes(job["starter"])
            r = scan(path, base, tick, job.get("by_folder", False))
            data = payload(r, progress=tick)
            # the whole wait (unzip, scan and evidence), not just scan()'s comparison step
            data["seconds"] = round(time.perf_counter() - t["start"], 3)
    # RuntimeError: password-protected zip; NotImplementedError: unsupported compression (Deflate64)
    except (FileNotFoundError, ValueError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as e:
        st.session_state.err = f"Couldn't scan {job['name']}: {e}"
        return
    # every file goes to Ask AI (payload() keeps only the top pairs' files); a new scan drops the old index and chat
    st.session_state.update(data=data, csv=all_pairs_csv(r), label=job["name"], err=None,
                            files=r["files"], ask_index=None, ask_err=None, chat=[])
    if zipped:  # the demo set would skew the thresholds
        telemetry.send(r["files"], data["seconds"])


def upload_form(key):
    """The upload widgets; returns a scan job when Scan is clicked (run later, so its bars sit in one place)."""
    up = st.file_uploader("Submissions: one .zip of .py, .cpp or .java files", type="zip", key=f"z{key}")
    starter = st.file_uploader("Starter code everyone received (optional). Matches inside it are ignored.",
                               type=["py", "cpp", "java", "zip"], key=f"s{key}")
    by_folder = st.checkbox("Each folder is one student", key=f"f{key}",
                            help="Files in the same folder are never compared with each other.")
    if st.button("Scan", type="primary", disabled=up is None, key=f"b{key}"):
        return {"name": up.name, "zip": up.getvalue(), "starter": starter.getvalue() if starter else None,
                "starter_name": Path(starter.name).name if starter else None, "by_folder": by_folder}
    return None


BOARD_A = ["<k>def</k> <f>total</f>(nums):", "    s = <n>0</n>", "    <k>for</k> x <k>in</k> nums:", "        s += x",
           "    <k>return</k> s"]
BOARD_B = ["<c># adds up the list</c>", "<k>def</k> <f>add_all</f>(values):", "    result = <n>0</n>",
           "    <k>for</k> v <k>in</k> values:", "        result += v", "    <k>return</k> result"]
BOARD_CSS = """<style>
.djb{--lh:22px;--top:34px;font:12.5px/var(--lh) "JetBrains Mono",ui-monospace,monospace;color:var(--dj-text)}
.djb .row{display:grid;grid-template-columns:minmax(0,1fr) 44px minmax(0,1fr);align-items:start}
.djb .card{border:1px solid var(--dj-line);border-radius:10px;background:var(--dj-panel);padding:0 0 6px;min-width:0;overflow:hidden}
.djb .hd{height:var(--top);display:flex;align-items:center;gap:6px;padding:0 10px;font:600 11px/1 "DM Sans",sans-serif;
  color:var(--dj-muted);letter-spacing:.02em;border-bottom:1px solid var(--dj-line);margin-bottom:6px}
.djb .hd b{color:var(--dj-accent-ink);font:700 12px/1 "JetBrains Mono",monospace}
.djb .ln{height:var(--lh);white-space:pre;padding:0 10px 0 0;display:flex;transition:background .15s ease-out}
.djb .ln i{font-style:normal;width:26px;flex:none;text-align:right;padding-right:8px;color:var(--dj-com);user-select:none}
.djb .ln.m{background:color-mix(in srgb,var(--dj-accent) 11%,transparent)}
.djb .ln.x{opacity:.55}
.djb .k{color:var(--dj-kw);font-weight:600}.djb .f{font-weight:600}.djb .n{color:var(--dj-num)}.djb .c{color:var(--dj-com);font-style:italic}
.djb .gap{align-self:stretch;background:no-repeat 0 0/44px auto}
.djb .tags{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 0}
.djb .tag{border:1px solid var(--dj-line);border-radius:6px;padding:2px 8px;background:var(--dj-sunk);font-size:12px;line-height:20px}
.djb .tag.hot{border-color:var(--dj-accent);color:var(--dj-accent-ink);background:color-mix(in srgb,var(--dj-accent) 9%,transparent)}
.djb .tok{margin-top:14px;padding:10px 12px;border-radius:10px;background:var(--dj-sunk);line-height:1.9;word-spacing:2px}
.djb .tok p{margin:0 0 4px;font:500 13px/1.4 "DM Sans",sans-serif;color:var(--dj-muted)}
.djb .tok .t{color:var(--dj-accent-ink);font-weight:700}
/*HOVER*/
</style>"""


def evidence_board():
    """The start page's worked example, drawn the way the review screen shows evidence: matched lines, the
    curves that pair them, the range tag, the renamed names and the shared tokens. Hover a line to see its partner."""
    lh, top, pad = 22, 34, 6
    y = lambda i: top + pad + i * lh + lh / 2  # centre of line i (0-based) inside a card
    pairs = [(i, i + 1) for i in range(len(BOARD_A))]  # B has one extra comment line on top, which is ignored
    h = top + pad + len(BOARD_B) * lh + 6
    # Streamlit's sanitiser drops inline <svg>, so the curves are an SVG image; it draws itself in once (motion allowing)
    curves = "".join(f'<path d="M0 {y(a)} C22 {y(a)} 22 {y(b)} 44 {y(b)}" style="animation-delay:{.15 + a * .07:.2f}s"/>'
                     for a, b in pairs)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="44" height="{h}"><style>path{{fill:none;stroke:STROKE;'
           'stroke-width:1.5;stroke-linecap:round;stroke-dasharray:70;animation:d .9s cubic-bezier(.16,1,.3,1) both}'
           '@keyframes d{from{stroke-dashoffset:70;opacity:.25}}@media (prefers-reduced-motion:reduce){path{animation:none}}'
           f'</style>{curves}</svg>')
    img = lambda c: 'url("data:image/svg+xml,' + quote(svg.replace("STROKE", c)) + '")'
    gap = (f".djb .gap{{background-image:{img('#a0522d')}}}"
           f"html[data-dejavu-theme=dark] .djb .gap{{background-image:{img('#e0a36a')}}}")
    hover = "\n".join(f".djb:has(.a{a}:hover,.b{b}:hover) :is(.a{a},.b{b}){{background:color-mix(in srgb,var(--dj-accent) 26%,transparent)}}"
                      for a, b in pairs) + gap
    ln = lambda side, i, code, cls: f'<div class="ln {cls} {side}{i}"><i>{i + 1}</i><span>{code}</span></div>'
    a = "".join(ln("a", i, c, "m") for i, c in enumerate(BOARD_A))
    b = "".join(ln("b", i, c, "x" if i == 0 else "m") for i, c in enumerate(BOARD_B))
    tok = " ".join(f'<span class="t">{t}</span>' if t in ("ID", "LIT", "LOOP") else t
                   for t in "def ID ( ID ) : ID = LIT LOOP ID in ID : ID += ID return ID".split())
    span = lambda html: re.sub(r"<([kfnc])>(.*?)</\1>", r'<span class="\1">\2</span>', html)  # sanitiser-safe markup
    a, b = span(a), span(b)
    return (BOARD_CSS.replace("/*HOVER*/", hover) + '<div class="djb" role="img" aria-label="Two renamed functions matched line by line">'
            f'<div class="row"><div class="card"><div class="hd"><b>A</b> student_a.py</div>{a}</div>'
            '<div class="gap"></div>'
            f'<div class="card"><div class="hd"><b>B</b> student_b.py</div>{b}</div></div>'
            '<div class="tags"><span class="tag hot">A 1–5 ≡ B 2–6</span><span class="tag">nums → values</span>'
            '<span class="tag">s → result</span><span class="tag">x → v</span><span class="tag">total → add_all</span></div>'
            f'<div class="tok"><p>Both become the same tokens; the comment is ignored.</p>{tok}</div></div>')


def code_label(s):
    return "`" + s.replace("`", "'") + "`"  # file names are untrusted: keep them inline code


GLUED_MARKER = re.compile(r"\s*" + ask.MARKER.pattern)  # the marker and the space before it
STOP = {"the", "and", "for", "with", "that", "this", "from", "are", "not", "its", "into", "file", "files", "line", "lines"}


def cite_words(said, code):
    """Names in the cited code that the question or answer mentions: the review flashes them inside the cited block."""
    want = {w.lower() for w in re.findall(r"\w{3,}", said)} - STOP
    return sorted({w for w in re.findall(r"[A-Za-z_]\w{2,}", code) if w.lower() in want})[:6]


@st.fragment
def ask_ai():
    """Read-only questions about the batch. Reruns only itself, so the review screen keeps its place."""
    ask.use_key(st.session_state.get("llm_key", ""))  # a fragment rerun skips the top of the script
    if not st.session_state.get("files") or not ask.available():
        return  # no scan, no key or no internet: no box
    in_review = {f["name"] for f in st.session_state.data["files"]}  # payload() keeps only the top pairs' files
    with st.container(key="askai", width="content"), st.popover("Ask AI", icon=":material/auto_awesome:", type="primary", key="askai_open"), \
            st.container(key="askai_body"):
        # one click handler: a citation tells the review frame to open that file at that line, then closes this panel
        st.html("""<script>if (!window.djCite) { window.djCite = 1; document.addEventListener("click", (e) => {
  const b = e.target.closest(".dj-cite"), f = document.querySelector(".st-key-review iframe");
  if (!b || !f) return;
  f.contentWindow.postMessage({type: "dejavu:open", file: b.dataset.file, line: +b.dataset.line, end: +b.dataset.end,
    words: (b.dataset.words || "").split(" ").filter(Boolean)}, "*");
  document.querySelector(".st-key-askai button").click();
}); }</script>""", unsafe_allow_javascript=True)
        st.caption("Answers come only from this batch's code and cite file and line. It can't mark or rank pairs.")
        chat = st.session_state.chat
        with st.container(height=340, border=False):
            for turn in chat:
                st.chat_message("user").markdown(turn["q"])
                with st.chat_message("assistant"):
                    if "error" in turn:
                        st.error(turn["error"])
                        continue
                    st.markdown(GLUED_MARKER.sub(lambda m: f"\u00a0:orange-badge[{m[1]}]", turn["answer"]))  # nbsp: a badge never starts a line
                    for c in turn["citations"]:
                        lines = f"lines {c['start']}–{c['end']}"
                        if c["file"] in in_review:  # click to open the file in the review screen
                            st.html(f'<button type="button" class="dj-cite" data-file="{escape(c["file"])}" '
                                    f'data-line="{c["start"]}" data-end="{c["end"]}" '
                                    f'data-words="{escape(" ".join(cite_words(turn["q"] + " " + turn["answer"], c["code"])))}"><span class="n">{c["n"]}</span>'
                                    f'<code>{escape(c["file"])}</code>{lines}<span class="go">Open ↗</span></button>')
                            continue
                        with st.popover(f":orange-badge[{c['n']}] {code_label(c['file'])} {lines}"):  # not in the review: show the lines here
                            st.code("\n".join(f"{c['start'] + i:>4}  {line}" for i, line in enumerate(c["code"].split("\n"))),
                                    language=Path(c["file"]).suffix[1:] or None)
        q = st.chat_input("Which files read input with a while loop?", max_chars=500, key="askai_q")
        if q and q.strip():
            try:
                if st.session_state.ask_index is None:
                    with st.spinner("Reading the batch…"):
                        st.session_state.ask_index = ask.build(st.session_state.files)
                with st.spinner("Searching the code…"):
                    chat.append({"q": q.strip(), **ask.answer(st.session_state.ask_index, q.strip())})
            except ask.Unavailable as e:
                chat.append({"q": q.strip(), "error": str(e)})
            st.rerun(scope="fragment")


def ai_chip(slot):
    """AI status in the middle of the top bar. Its menu holds the key box, or the index details and a rebuild.
    Returns True when the index still has to be built (after the page is drawn, with progress in `slot`)."""
    if not ask.available():
        has_key = bool(ask.key())
        with slot.container(key="aichip_off"), st.popover("AI RAG offline" if has_key else "AI RAG off", icon=":material/cloud_off:"):
            st.caption("Couldn't reach the model, or it rejected the key." if has_key else "Ask AI needs a Gemini API key.")
            if not os.getenv("LLM_API_KEY"):  # a server secret can't be replaced from the page
                with st.form("aikey", border=False):
                    k = st.text_input("API key", type="password", placeholder="Paste your Gemini key", autocomplete="off")
                    st.caption("Kept in memory for this browser tab only. Never saved.")
                    if st.form_submit_button("Use key", type="primary") and k.strip():
                        st.session_state.update(llm_key=k.strip(), ask_index=None, ask_err=None)
                        st.rerun()
        return False
    idx, err = st.session_state.get("ask_index"), st.session_state.get("ask_err")
    if idx is None and not err:
        return True
    with slot.container(key="aichip_error" if err else "aichip_ready"),             st.popover("AI RAG error" if err else "AI RAG ready",icon=":material/error:" if err else ":material/check_circle:"):
        if err:
            st.error(err)
        else:
            st.caption(f"Ask AI searches **{len(idx['chunks']):,}** chunks (one per function) from "
                       f"**{len({c['file'] for c in idx['chunks']}):,}** files of this scan.")
        row = st.container(horizontal=True)
        if row.button("Rebuild index", icon=":material/refresh:"):
            st.session_state.update(ask_index=None, ask_err=None)
            st.rerun()
        # a used-up quota is per key; dropping the pasted key brings back the key box (a server secret can't be swapped)
        if not os.getenv("LLM_API_KEY") and row.button("Use another key", icon=":material/key:"):
            st.session_state.update(llm_key="", ask_index=None, ask_err=None)
            st.rerun()
    return False


job = need_index = None
ask.use_key(st.session_state.get("llm_key", ""))
data = st.session_state.get("data")
# light is the default look; a theme the reviewer picked with the toggle (saved in the browser) still wins
html = render(data, "light") if data else None
# One bar: name on the left, actions grouped on the right at their own width.
bar = st.container(key="topbar", horizontal=True, vertical_alignment="center")
label = code_label(st.session_state.get("label", ""))  # upload name is untrusted
bar.container(key="brand").markdown("**Dejavu** · code similarity review" + (f" · {label}" if html else ""))
if html:
    ai_slot = bar.empty()
    need_index = ai_chip(ai_slot)
    acts = bar.container(key="actions", horizontal=True, horizontal_alignment="right", vertical_alignment="center")
    if st.session_state.get("bbar"):  # Scan was just clicked in this menu: close it so the bars and review show
        st.session_state.newscan = False
    with acts.popover("New scan", key="newscan", on_change="rerun"):  # rerun: tracks open state, so Scan can close it
        job = upload_form("bar")
    if acts.button("Demo set"):
        job = DEMO_JOB
    acts.download_button("Offline report", html, "dejavu-report.html", "text/html",
                        help="The same review screen as one HTML file. Opens without a server.")
    acts.download_button("All pairs CSV", st.session_state.csv, "dejavu-pairs.csv", "text/csv")
    with acts:
        ask_ai()
else:
    # the review screen has its own toggle; this one covers the landing page
    with bar.container(key="theme", width="content"):
        st.iframe(theme_toggle("light"), width=32, height=32)

if st.session_state.get("err"):
    st.error(st.session_state.err)

# Unzip and scan bars: shown only while a scan runs.
area = st.container(key="phases", horizontal=True, gap="large")

if html:
    # html is our own template; uploaded code only enters it as escaped JSON data (see dejavu/report.py)
    with st.container(key="review"):
        st.iframe(html, height=880)
else:
    left, right = st.columns([1.2, 1], gap="large")
    with left.container(key="intro"):
        st.title("Find submissions that share logic, even after renaming or an AI rewrite")
        st.write("Upload every student's file for one assignment. Dejavu ranks each pair by how much rare "
                 "structure they share, shows the matching lines side by side, and lets you mark each pair "
                 "as you review. A score ranks pairs for review; it is not proof of copying.")
        with st.container(border=True, key="demo", horizontal=True, vertical_alignment="center"):
            st.markdown("**No zip at hand?** Scan the built-in demo: small assignments with AI-rewritten copies.")
            if st.button("Try the demo set", type="primary"):
                job = DEMO_JOB
        with st.container(border=True, key="upload"):
            job = upload_form("main") or job
    with right.container(key="how"):
        st.subheader("How it works")
        st.html(evidence_board())
        st.markdown("Names, numbers and loop styles stop mattering. Short runs of these tokens are compared across "
                    "every pair, and runs that few students share count most.")
        st.subheader("What you get")
        st.markdown("1. Pairs ranked by shared rare structure, highest first.\n"
                    "2. Matching lines side by side, and why each pair ranks where it does.\n"
                    "3. Decisions saved in your browser, plus an offline report and a CSV.")

if job:
    run(job, area)
    st.rerun()

if need_index:  # after the page is drawn, so the review is usable while the index builds
    def busy(text):
        ai_slot.html(f'<div class="dj-ai-busy" role="status"><i></i>{text}</div>')
    busy("Chunking the code…")
    try:
        st.session_state.ask_index = ask.build(st.session_state.files, lambda d, n: busy(f"Indexing {d:,} / {n:,} chunks"))
    except ask.Unavailable as e:
        st.session_state.ask_err = str(e)
    st.rerun()
