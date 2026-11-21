---
version: 1
slug: "web-src-app-tsx"
primary_target: "web/src/App.tsx"
related_targets: []
---

# Review app (React)

Scope: the whole review app: upload, scan progress, pair queue, the Ask the batch panel, and later the comparison and review screens. Mode: Operate.
Audience and job: a contest judge, live, on a laptop in a bright room, getting to the real copies first. Hackathon judges watch a demo and also try the hosted link.
Constraints: the PRODUCT.md must-not-change list; WCAG 2.2 AA; full keyboard flow. Must not feel accusatory, like a dashboard, like a toy, or like a hacker costume.
Memorable moment: numbered points of agreement on every pair, reused as the Ask panel's citations.
Unresolved: hosting (Render or HF Spaces). Decided 2026-11-21: two themes behind one toggle, replacing the graphite world after the user rejected it as plain.

## Direction contract

THESIS: Show each pair the way an examiner shows a comparison: numbered points of agreement that a human weighs. This refuses the category default of a percentage badge in a grey table, and refuses any verdict styling.

OWN-WORLD: Two warm looks behind one toggle, stored as "dejavu:theme" like the offline report. Coffee ("dark", default) is the Streamlit app's coffee house: #1b1612 ground, #231c17 panels, #e0a36a amber accent, Fraunces display over DM Sans. Cream ("light") is VerifAI's paper: #f5f1eb ground, #fffdf9 panels, #12161a ink primary, #9e7d47 gold for fills and lines with #7d6133 gold ink for text, EB Garamond display over Manrope. Cousine is the shared code face. The score shows as a serif number, its band label and an accent bar that fills in steps, never colour alone. Every colour is a theme token.

STORY: The judge sees the batch, how many pairs there are, and that a human decides. They open the highest-ranked pair with evidence beside its score, decide, and move on. Ask explains the code and never judges it.

FIRST VIEWPORT: Bar: Dejavu in serif, tagline, New scan, All pairs CSV, Offline report, Ask the batch (primary) and the theme toggle. Metric tiles: files, pairs that share code, scan time, reviewed with a meter. "Pairs to check first" with name, decision and score filters, and a table: rank, pair (A over B), score plus band plus bar, circled point count, rename chips and verbatim runs, decision. The focused row gets a tint plus a full outline. The right 420px holds the Ask panel in VerifAI's layout: italic question, serif answer with numbered citation chips, sources heading and cited code cards.

FORM: Examiner's comparison chart (points of agreement), position 3 of 7 on my list, seed:0d7e2827bd30af8f. Raises carried into it: score by tonal ramp plus number, never colour alone (exposure record); one reserved ink for focus (orienteering); every score beside its proof (monochrome product); both panes on one scale and baseline (botanical folio).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
