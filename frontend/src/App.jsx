import { useEffect, useState } from "react";
import CodeEditor from "./components/CodeEditor";
import OutputPanel from "./components/OutputPanel.jsx";
import LanguageToggle from "./components/LanguageToggle.jsx";
import Tabs from "./components/Tabs.jsx";

function ThemeToggle({ theme, onChange }) {
  const next = theme === "dark" ? "light" : "dark";
  return (
    <button
      onClick={() => onChange(next)}
      className="px-3 py-1 rounded-xl border border-zinc-700 text-sm text-zinc-200 hover:bg-zinc-800"
      title={`Switch to ${next} theme`}
    >
      {theme === "dark" ? "🌙 Dark" : "☀️ Light"}
    </button>
  );
}

export default function App() {
  // Theme
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");
  useEffect(() => {
    localStorage.setItem("theme", theme);
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  // Editor
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(
`def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []`
  );

  // Results
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  // UI state
  const [tab, setTab] = useState("explain"); // 'explain' | 'flow'
  const [useAI, setUseAI] = useState(true);  // AI-enhanced explanation toggle

  async function explain() {
    setLoading(true);
    setError("");
    setResult(null);

    const isPython = language === "python";
    const endpoint = useAI ? "/explain_plus" : (isPython ? "/explain" : "/explain_plus");

    try {
      const res = await fetch(`http://127.0.0.1:8000${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, language }),
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
      // switch tabs if diagram is available
      if (data.diagram) setTab("flow");
      else setTab("explain");
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }

  function run() {
    alert("Run not implemented yet — coming next.");
  }

  const page =
    theme === "dark"
      ? "min-h-screen bg-black text-zinc-100"
      : "min-h-screen bg-white text-zinc-900";

  return (
    <div className={`${page} p-6 space-y-4 transition-colors`}>
      {/* Header */}
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="text-xl font-semibold">CodeLensAI</div>
          <div className="text-xs opacity-60">AI-powered code explainer & flowchart</div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm opacity-70">
            ⌘/Ctrl+Enter → Run · ⌥/Alt+Enter → Explain
          </div>
          <LanguageToggle value={language} onChange={setLanguage} />
          <ThemeToggle theme={theme} onChange={setTheme} />
        </div>
      </header>

      {/* Editor Card */}
      <section className="rounded-2xl border border-zinc-800 overflow-hidden">
        <div className="flex items-center justify-between px-3 py-2 bg-zinc-900/50">
          <div className="text-sm text-zinc-300">Editor</div>
          <div className="flex items-center gap-3">
            <label className="text-sm text-zinc-400 flex items-center gap-2">
              <input
                type="checkbox"
                checked={useAI}
                onChange={(e) => setUseAI(e.target.checked)}
              />
              AI enhance
            </label>
            <button
              onClick={run}
              className="px-3 py-1.5 text-sm rounded-xl border border-zinc-700 hover:bg-zinc-800"
            >
              ▶ Run
            </button>
            <button
              onClick={explain}
              className="px-3 py-1.5 text-sm rounded-xl border border-emerald-700 text-emerald-200 hover:bg-emerald-900/30"
            >
              ✨ Explain
            </button>
          </div>
        </div>
        <div className="p-3 bg-zinc-950">
          <CodeEditor
            language={language}
            value={code}
            onChange={setCode}
            onRun={run}
            onExplain={explain}
            height="420px"
            placeholder={`Paste your ${language} function…`}
          />
        </div>
      </section>

      {/* Results Card */}
      <section className="rounded-2xl border border-zinc-800 overflow-hidden">
        <div className="flex items-center justify-between px-3 py-2 bg-zinc-900/50">
          <Tabs
            value={tab}
            onChange={setTab}
            items={[
              { value: "explain", label: "Explanation" },
              { value: "flow", label: "Flowchart" },
            ]}
          />
          <div className="text-xs text-zinc-500">
            {loading ? "Explaining…" : error ? "Error" : result ? "Ready" : "Idle"}
          </div>
        </div>

        <div className="p-3 bg-zinc-950">
          <OutputPanel
            result={result}
            error={error}
            loading={loading}
            activeTab={tab}
          />
        </div>
      </section>
    </div>
  );
}
