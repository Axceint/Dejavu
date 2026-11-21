import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, type Answer, type AskState } from "./api";

type Turn = { q: string; a?: Answer; error?: string };

// Answer text marks its sources as [1] or [1, 2]; each number becomes a button that jumps to its citation.
function Text({ turn, at, onCite }: { turn: Answer; at: number; onCite: (id: string) => void }) {
  const parts = turn.answer.split(/(\[\d+(?:,\s*\d+)*\])/);
  return (
    <p className="answer">
      {parts.map((part, i) =>
        /^\[\d/.test(part)
          ? part.match(/\d+/g)!.map((n) => (
              <button key={i + "-" + n} className="cite" onClick={() => onCite(`c${at}-${n}`)} aria-label={"Source " + n}>{n}</button>
            ))
          : part,
      )}
    </p>
  );
}

export function AskPanel({ id, onClose }: { id: string; onClose: () => void }) {
  const [index, setIndex] = useState<AskState | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [lit, setLit] = useState("");
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let live = true;
    let timer = 0;
    const poll = () =>
      api.status(id).then((s) => {
        if (!live || !s.ask) return;
        setIndex(s.ask);
        if (s.ask.state === "running") timer = window.setTimeout(poll, 700);
      }, (e: Error) => live && setIndex({ state: "error", done: 0, total: 0, error: e.message }));
    api.index(id).then((s) => {
      if (!live) return;
      setIndex(s);
      if (s.state === "running") poll();
    }, (e: Error) => live && setIndex({ state: "error", done: 0, total: 0, error: e.message }));
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [id]);

  useEffect(() => {
    if (index?.state === "done") input.current?.focus();
  }, [index?.state]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const q = question.trim();
    if (!q || busy) return;
    const at = turns.length;
    setTurns((t) => [...t, { q }]);
    setQuestion("");
    setBusy(true);
    api.ask(id, q).then(
      (a) => setTurns((t) => t.map((x, i) => (i === at ? { ...x, a } : x))),
      (err: Error) => setTurns((t) => t.map((x, i) => (i === at ? { ...x, error: err.message } : x))),
    ).finally(() => setBusy(false));
  };

  const cite = (target: string) => {
    setLit(target);
    const el = document.getElementById(target);
    el?.scrollIntoView({ block: "nearest", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    el?.focus();
  };

  const ready = index?.state === "done";
  return (
    <aside className="ask" aria-label="Ask the batch">
      <header>
        <h2>Ask the batch</h2>
        <button className="icon" onClick={onClose} aria-label="Close Ask the batch">
          <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
            <path d="M3.5 3.5l9 9m0-9l-9 9" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
        </button>
      </header>
      <p className="note">Answers come only from this batch's code and cite file and line. It can't mark or rank pairs.</p>

      {!index || index.state === "running" ? (
        <div className="indexing" aria-live="polite">
          <span>Reading the batch</span>
          {index && index.total > 0 && <progress value={index.done} max={index.total} aria-label="Reading the batch" />}
        </div>
      ) : index.state === "error" ? (
        <p className="error" role="alert">{index.error || "The batch couldn't be read for questions."} Close the panel and open it again to retry.</p>
      ) : null}

      <ol className="turns">
        {turns.map((t, at) => (
          <li key={at}>
            <p className="q">{t.q}</p>
            {t.error && <p className="error" role="alert">{t.error}</p>}
            {!t.a && !t.error && <p className="thinking" aria-live="polite">Searching the code…</p>}
            {t.a && (
              <>
                <Text turn={t.a} at={at} onCite={cite} />
                {t.a.citations.length > 0 && (
                  <p className="sources">
                    <span>Sources behind this answer</span>
                    <span className="faint">{t.a.citations.length} {t.a.citations.length === 1 ? "passage" : "passages"}</span>
                  </p>
                )}
                {t.a.citations.map((c) => (
                  <figure key={c.n} id={`c${at}-${c.n}`} tabIndex={-1} className={lit === `c${at}-${c.n}` ? "source lit" : "source"}>
                    <figcaption><span className="cite static">{c.n}</span> {c.file}:{c.start}–{c.end}</figcaption>
                    <pre>
                      {c.code.split("\n").map((line, i) => (
                        <span key={i} className="line"><span className="ln">{c.start + i}</span>{line + "\n"}</span>
                      ))}
                    </pre>
                  </figure>
                ))}
              </>
            )}
          </li>
        ))}
      </ol>

      <form className="askform" onSubmit={submit}>
        <label className="field">
          <span className="label">Question</span>
          <input ref={input} value={question} maxLength={500} disabled={!ready}
            placeholder="Which files read input with a while loop?" onChange={(e) => setQuestion(e.target.value)} />
        </label>
        <button className="btn primary" type="submit" disabled={!ready || busy || !question.trim()}>Ask</button>
      </form>
    </aside>
  );
}
