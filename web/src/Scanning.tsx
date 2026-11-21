import { useEffect, useState } from "react";
import { api, type Status } from "./api";
import { Shell } from "./Shell";

const STAGES = [
  ["read", "Reading files"],
  ["parse", "Parsing code into trees"],
  ["compare", "Comparing every pair"],
  ["explain", "Collecting evidence"],
] as const;

export function Scanning({ id, onDone, onRestart }: { id: string; onDone: (id: string) => Promise<void>; onRestart: () => void }) {
  const [s, setS] = useState<Status | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let live = true;
    let timer = 0;
    const tick = () =>
      api.status(id).then(
        (st) => {
          if (!live) return;
          setS(st);
          if (st.state === "running") timer = window.setTimeout(tick, 400);
          else if (st.state === "done") onDone(id).catch((e: Error) => setError(e.message));
          else setError(st.error || "The scan failed.");
        },
        (e: Error) => live && setError(e.message),
      );
    tick();
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [id, onDone]);

  const at = STAGES.findIndex(([k]) => k === s?.stage);
  return (
    <Shell tag={s?.name}>
      <main className="scanning card">
        <h1>{error ? "The scan stopped" : "Scanning " + (s?.name ?? "")}</h1>
        {error ? (
          <>
            <p className="error" role="alert">{error}</p>
            <div className="actions">
              <button className="btn primary" onClick={onRestart}>Start over</button>
            </div>
          </>
        ) : (
          <ol className="stages" aria-live="polite">
            {STAGES.map(([k, label], i) => (
              <li key={k} className={i < at ? "past" : i === at ? "now" : ""} aria-current={i === at ? "step" : undefined}>
                <span className="stage">{label}</span>
                {i === at && s && s.total > 0 && (
                  <>
                    <progress value={s.done} max={s.total} aria-label={label} />
                    <span className="count">{s.done.toLocaleString()} of {s.total.toLocaleString()}</span>
                  </>
                )}
              </li>
            ))}
          </ol>
        )}
      </main>
    </Shell>
  );
}
