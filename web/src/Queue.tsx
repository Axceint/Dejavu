import { useEffect, useMemo, useState } from "react";
import { api, loadDecisions, pairKey, type Pair, type Result } from "./api";
import { Shell } from "./Shell";
import { AskPanel } from "./AskPanel";

// Same bands and labels as the offline report (review.html).
const BANDS = [[0.4, "high", "Review first"], [0.2, "mid", "Worth a look"], [0, "low", "Low"]] as const;
const band = (score: number) => BANDS.find(([min]) => score >= min)!;
const LABEL = { copy: "Likely copy", clear: "Not a copy", open: "To review" } as const;
const CHIPS = 3;

// Long paths wrap only after a slash, never inside a file name.
const path = (n: string) => n.split("/").map((s, i, all) => (i < all.length - 1 ? <span key={i}>{s}/<wbr /></span> : s));

function Evidence({ p }: { p: Pair }) {
  const ren = p.ren ?? [];
  const runs = p.verb?.length ?? 0;
  if (!ren.length && !runs) return <span className="faint">Structure only</span>;
  return (
    <span className="chips">
      {ren.slice(0, CHIPS).map(([a, b]) => <code key={a + b} className="chip">{a} → {b}</code>)}
      {ren.length > CHIPS && <span className="faint">+{ren.length - CHIPS} renames</span>}
      {runs > 0 && <span className="chip run">{runs} verbatim {runs === 1 ? "run" : "runs"}</span>}
    </span>
  );
}

export function Queue({ result, scan, onNew }: { result: Result; scan: string; onNew: () => void }) {
  const decisions = useMemo(() => loadDecisions(result.id), [result.id]);
  const [query, setQuery] = useState("");
  const [state, setState] = useState<"all" | keyof typeof LABEL>("all");
  const [level, setLevel] = useState("all");
  const [focus, setFocus] = useState(result.pairs[0]?.rank ?? 0);
  const [canAsk, setCanAsk] = useState(false);
  const [asking, setAsking] = useState(false);

  useEffect(() => {
    api.askAvailable().then((r) => setCanAsk(r.available), () => setCanAsk(false));
  }, []);

  const name = (i: number) => result.files[i].name;
  const decided = (p: Pair) => decisions[pairKey(result, p)]?.s ?? "open";
  const reviewed = result.pairs.filter((p) => decided(p) !== "open").length;
  const q = query.trim().toLowerCase();
  const rows = result.pairs.filter(
    (p) =>
      (!q || name(p.a).toLowerCase().includes(q) || name(p.b).toLowerCase().includes(q)) &&
      (state === "all" || decided(p) === state) &&
      (level === "all" || band(p.score)[1] === level),
  );

  return (
    <Shell
      actions={
        <>
          <button className="btn" onClick={onNew}>New scan</button>
          <a className="btn" href={api.csvUrl(scan)} download>All pairs CSV</a>
          {/* The report opens in the look picked here. */}
          <a className="btn" href={api.reportUrl(scan)} download
            onClick={(e) => (e.currentTarget.href = api.reportUrl(scan) + "?theme=" + document.documentElement.dataset.theme)}>
            Offline report
          </a>
          {canAsk && (
            <button className="btn primary" aria-expanded={asking} onClick={() => setAsking(!asking)}>Ask the batch</button>
          )}
        </>
      }
    >
      <div className={asking ? "review with-ask" : "review"}>
        <main className="queue">
          <dl className="tiles">
            <div><dt>Files</dt><dd>{result.totalFiles.toLocaleString()}</dd></div>
            <div><dt>Pairs share code</dt><dd>{result.totalPairs.toLocaleString()}</dd></div>
            <div><dt>Scan time</dt><dd>{result.seconds}<small>s</small></dd></div>
            <div>
              <dt>Reviewed</dt>
              <dd>{reviewed}<small> / {result.pairs.length}</small></dd>
              <meter min={0} max={result.pairs.length || 1} value={reviewed} aria-label="Pairs reviewed" />
            </div>
          </dl>

          <div className="head">
            <div>
              <h1>Pairs to check first</h1>
              <p className="sub">
                {result.pairs.length.toLocaleString()} of {result.totalPairs.toLocaleString()} pairs, ranked by shared
                structure. A person decides each one.
              </p>
            </div>
            <div className="filters">
              <input type="search" aria-label="Filter by file name" placeholder="Filter by file name" value={query}
                onChange={(e) => setQuery(e.target.value)} />
              <select aria-label="Decision" value={state} onChange={(e) => setState(e.target.value as typeof state)}>
                <option value="all">All decisions</option>
                <option value="open">To review</option>
                <option value="copy">Likely copy</option>
                <option value="clear">Not a copy</option>
              </select>
              <select aria-label="Score" value={level} onChange={(e) => setLevel(e.target.value)}>
                <option value="all">All scores</option>
                {BANDS.map(([, k, label]) => <option key={k} value={k}>{label}</option>)}
              </select>
            </div>
          </div>

          {rows.length === 0 ? (
            <p className="empty card">No pairs match these filters. Clear the file name or pick All decisions and All scores.</p>
          ) : (
            <div className="card table">
              <table className="pairs">
                <thead>
                  <tr>
                    <th scope="col" className="num">#</th>
                    <th scope="col">Pair</th>
                    <th scope="col">Score</th>
                    <th scope="col" className="num">Points</th>
                    <th scope="col">Evidence</th>
                    <th scope="col">Decision</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((p) => {
                    const fill = Math.ceil(p.score * 5);
                    const [, level, label] = band(p.score);
                    const d = decided(p);
                    return (
                      <tr key={p.rank} className={p.rank === focus ? "focused" : undefined}>
                        <td className="num">
                          <button className="rank" aria-current={p.rank === focus} onClick={() => setFocus(p.rank)}
                            aria-label={`Pair ${p.rank}: ${name(p.a)} and ${name(p.b)}`}>{p.rank}</button>
                        </td>
                        <td className="file">
                          <span>{path(name(p.a))}</span>
                          <span className="faint">{path(name(p.b))}</span>
                        </td>
                        <td className="nowrap">
                          <span className="score">{p.score.toFixed(2)}</span>
                          <span className={"band " + level}>{label}</span>
                          <span className={"ramp s" + fill} aria-hidden="true">
                            {[0, 1, 2, 3, 4].map((i) => <i key={i} className={i < fill ? "on" : undefined} />)}
                          </span>
                        </td>
                        <td className="num">
                          {p.m.length ? (
                            <span className="pt">{p.m.length}</span>
                          ) : (
                            <span className="faint" title="Matched lines are worked out for the top 100 pairs only.">—</span>
                          )}
                        </td>
                        <td><Evidence p={p} /></td>
                        <td className={"dec " + d}>{LABEL[d]}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </main>
        {asking && <AskPanel id={scan} onClose={() => setAsking(false)} />}
      </div>
    </Shell>
  );
}
