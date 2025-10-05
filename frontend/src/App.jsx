import { useState } from "react";
import CodeEditor from "./components/CodeEditor";

export default function App() {
  const [code, setCode] = useState(
`def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []`
  );

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function explain() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setResult(data); // whatever your FastAPI returns (explanation rows, diagram, etc.)
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }

  // Optional stub if you add a /run endpoint later
  async function run() {
    alert("Run not implemented yet — focus on Explain first.");
  }

  return (
    <div className="min-h-screen bg-black text-zinc-100 p-6 space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">CodeLensAI</h1>
        <div className="text-sm text-zinc-400">
          ⌘/Ctrl+Enter → Run · ⌥/Alt+Enter → Explain
        </div>
      </header>

      <CodeEditor
        language="python"
        value={code}
        onChange={setCode}
        onRun={run}          // ⌘/Ctrl+Enter (stub for now)
        onExplain={explain}  // ⌥/Alt+Enter
        height="480px"
        placeholder="Paste your Python function…"
      />

      <div className="mt-4">
        {loading && <div className="text-sm text-zinc-400">Explaining…</div>}
        {error && (
          <pre className="mt-2 p-3 rounded-xl bg-zinc-900 ring-1 ring-zinc-800 text-red-400 whitespace-pre-wrap">
            {error}
          </pre>
        )}
        {result && (
          <pre className="mt-2 p-3 rounded-xl bg-zinc-900 ring-1 ring-zinc-800 overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
