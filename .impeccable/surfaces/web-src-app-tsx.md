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
Unresolved: hosting (Render or HF Spaces); dark theme rendition (light is primary).

## Direction contract

THESIS: Show each pair the way an examiner shows a comparison: numbered points of agreement that a human weighs. This refuses the category default of a percentage badge in a grey table, and refuses any verdict styling.

OWN-WORLD: Cool white card ground (#f7f8fa) with a graphite ink shell bar (#1c2430). One five-step graphite tonal ramp carries the score together with its number. Cobalt (#2f4bd1) is reserved for the pair or citation in focus. Circled tabular numerals mark the points, set in a system UI face with a monospace for code. No red anywhere except real errors.

STORY: The judge sees the batch, how many pairs there are, and that a human decides. They open the highest-ranked pair with evidence beside its score, decide, and move on. Ask explains the code and never judges it.

FIRST VIEWPORT: Graphite top bar: Dejavu, batch facts, CSV, report, and Ask the batch (cobalt, primary). The left area is "Pairs to check first" with language and status filters, and a table: rank, file A, file B, ramp plus score, circled point count, evidence summary, decision. The focused row gets a cobalt inset rule. The right 400px holds the Ask panel: question, answer with cobalt circled citations, and cited code cards.

FORM: Examiner's comparison chart (points of agreement), position 3 of 7 on my list, seed:0d7e2827bd30af8f. Raises carried into it: score by tonal ramp plus number, never colour alone (exposure record); one reserved ink for focus (orienteering); every score beside its proof (monochrome product); both panes on one scale and baseline (botanical folio).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
