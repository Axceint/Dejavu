import { useEffect, useState } from "react";
import { api, type Result } from "./api";
import { Start } from "./Start";
import { Scanning } from "./Scanning";
import { Queue } from "./Queue";

// The scan id lives in the URL hash, so a reload returns to the same scan while the server still has it.
const fromHash = () => new URLSearchParams(location.hash.slice(1)).get("scan");

export function App() {
  const [scan, setScan] = useState<string | null>(fromHash);
  const [result, setResult] = useState<Result | null>(null);

  useEffect(() => {
    const sync = () => {
      setScan(fromHash());
      setResult(null);
    };
    addEventListener("hashchange", sync);
    return () => removeEventListener("hashchange", sync);
  }, []);

  const open = (id: string | null) => {
    location.hash = id ? "scan=" + id : "";
  };

  if (!scan) return <Start onScan={open} />;
  if (!result) return <Scanning id={scan} onDone={(id) => api.result(id).then(setResult)} onRestart={() => open(null)} />;
  return <Queue result={result} scan={scan} onNew={() => open(null)} />;
}
