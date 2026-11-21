// Client for dejavu/api.py. Shapes mirror report.payload() and the scan status.
export type Range = [number, number];
export type Pair = {
  rank: number;
  a: number;
  b: number;
  score: number;
  m: [Range, Range][]; // matched line blocks: computed for the top MATCH_TOP pairs only
  cov?: [number, number];
  ren?: [string, string, number][];
  verb?: unknown[];
  beats: number;
};
export type FileInfo = { name: string; lang: string; src: string; flags: unknown[]; ai: unknown[] };
export type Result = { id: string; files: FileInfo[]; pairs: Pair[]; totalPairs: number; totalFiles: number; seconds: number };
export type AskState = { state: "running" | "done" | "error"; done: number; total: number; error?: string };
export type Status = {
  state: "running" | "done" | "error";
  name: string;
  stage: "read" | "parse" | "compare" | "explain";
  done: number;
  total: number;
  error?: string;
  ask?: AskState;
};
export type Citation = { n: number; file: string; start: number; end: number; code: string };
export type Answer = { answer: string; citations: Citation[] };

async function call<T>(url: string, init?: RequestInit): Promise<T> {
  let r: Response;
  try {
    r = await fetch(url, init);
  } catch {
    throw new Error("Couldn't reach the Dejavu server. Check that it is running, then try again.");
  }
  if (!r.ok) {
    const body = await r.json().catch(() => null);
    throw new Error(typeof body?.detail === "string" ? body.detail : `The server returned an error (${r.status}).`);
  }
  return r.json();
}

const post = { method: "POST" };

export const api = {
  upload(zip: File, starter?: File | null) {
    const form = new FormData();
    form.append("submissions", zip);
    if (starter) form.append("starter", starter);
    return call<{ id: string }>("/api/scans", { method: "POST", body: form });
  },
  demo: () => call<{ id: string }>("/api/scans/demo", post),
  status: (id: string) => call<Status>(`/api/scans/${id}`),
  result: (id: string) => call<Result>(`/api/scans/${id}/result`),
  askAvailable: () => call<{ available: boolean }>("/api/ask/available"),
  index: (id: string) => call<AskState>(`/api/scans/${id}/index`, post),
  ask: (id: string, question: string) =>
    call<Answer>(`/api/scans/${id}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),
  csvUrl: (id: string) => `/api/scans/${id}/pairs.csv`,
  reportUrl: (id: string) => `/api/scans/${id}/report.html`,
};

// Saved decisions are shared with the offline report: key "dejavu:<payload id>", pair key "fileA\nfileB".
export type Decision = { s?: "copy" | "clear"; note?: string };
export function loadDecisions(id: string): Record<string, Decision> {
  try {
    return JSON.parse(localStorage.getItem("dejavu:" + id) || "{}") || {};
  } catch {
    return {};
  }
}
export const pairKey = (r: Result, p: Pair) => r.files[p.a].name + "\n" + r.files[p.b].name;
