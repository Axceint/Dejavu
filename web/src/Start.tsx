import { useState, type FormEvent } from "react";
import { api } from "./api";
import { Shell } from "./Shell";

const EXAMPLE = `# Student A                # Student B
def total(nums):           def add_all(values):
    s = 0                      result = 0
    for x in nums:             for v in values:
        s += x                     result += v
    return s                   return result`;

export function Start({ onScan }: { onScan: (id: string) => void }) {
  const [zip, setZip] = useState<File | null>(null);
  const [starter, setStarter] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const run = (job: Promise<{ id: string }>) => {
    setBusy(true);
    setError("");
    job.then((r) => onScan(r.id)).catch((e: Error) => {
      setError(e.message);
      setBusy(false);
    });
  };
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (zip) run(api.upload(zip, starter));
  };

  return (
    <Shell>
      <main className="start">
        <section className="intro">
          <h1>Find submissions that share logic, even after renaming or an AI rewrite</h1>
          <p className="lede">
            Upload every student's file for one assignment. Dejavu ranks each pair by how much rare structure they share,
            shows the matching lines side by side, and lets you mark each pair as you review. A score ranks pairs for
            review; it is not proof of copying.
          </p>
          <form className="upload card" onSubmit={submit}>
            <label className="field">
              <span className="label">Submissions: one .zip of .py, .cpp or .java files</span>
              <input type="file" accept=".zip" required onChange={(e) => setZip(e.target.files?.[0] ?? null)} />
              <span className="hint">Up to 200 MB.</span>
            </label>
            <label className="field">
              <span className="label">Starter code everyone received (optional)</span>
              <input type="file" accept=".py,.cpp,.cc,.cxx,.h,.hpp,.java,.zip" onChange={(e) => setStarter(e.target.files?.[0] ?? null)} />
              <span className="hint">Matches inside it are ignored.</span>
            </label>
            {error && <p className="error" role="alert">{error}</p>}
            <div className="actions">
              <button className="btn primary" type="submit" disabled={!zip || busy}>Scan submissions</button>
              <button className="btn" type="button" disabled={busy} onClick={() => run(api.demo())}>Try the demo set</button>
            </div>
          </form>
        </section>
        <aside className="how">
          <h2>How it works</h2>
          <pre className="code card">{EXAMPLE}</pre>
          <p>
            Both become <code>def ID ( ID ) : ID = LIT LOOP ID in ID : ID += ID return ID</code>. Names, numbers and loop
            styles stop mattering. Short runs of these tokens are compared across every pair, and runs that few students
            share count most.
          </p>
        </aside>
      </main>
    </Shell>
  );
}
