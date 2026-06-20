import { useEffect, useMemo, useRef, useState } from "react";
import CodeEditor from "./components/CodeEditor";
import OutputPanel from "./components/OutputPanel";

// Same-origin in production (the API lives at /api on the same Vercel deploy).
// Override with VITE_API_BASE only if you run the API somewhere else.
const API_BASE = (import.meta.env && import.meta.env.VITE_API_BASE) || "";

// Starter snippets so the app is never staring at an empty editor.
const SAMPLES = {
  python: {
    code: `def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []`,
  },
  javascript: {
    code: `function twoSum(nums, target) {
  const seen = {};
  for (let i = 0; i < nums.length; i++) {
    const x = nums[i];
    if ((target - x) in seen) return [seen[target - x], i];
    seen[x] = i;
  }
  return [];
}`,
  },
  typescript: {
    code: `function twoSum(nums: number[], target: number): number[] {
  const seen: Record<number, number> = {};
  for (let i = 0; i < nums.length; i++) {
    const x = nums[i];
    if ((target - x) in seen) return [seen[target - x], i];
    seen[x] = i;
  }
  return [];
}`,
  },
};

// Map a dropped/uploaded filename to one of our supported languages.
function langFromFilename(name = "") {
  const ext = name.toLowerCase().split(".").pop();
  if (ext === "py") return "python";
  if (["js", "mjs", "cjs", "jsx"].includes(ext)) return "javascript";
  if (["ts", "tsx"].includes(ext)) return "typescript";
  return null;
}

function LensMark() {
  return (
    <svg className="lens" viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="var(--surface-2)" stroke="var(--border-strong)" />
      <circle cx="14" cy="14" r="7" fill="none" stroke="var(--accent)" strokeWidth="2.4" />
      <line x1="19" y1="19" x2="26" y2="26" stroke="var(--accent)" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");
  useEffect(() => {
    localStorage.setItem("theme", theme);
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(SAMPLES.python.code);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [tab, setTab] = useState("steps");

  const fileInputRef = useRef(null);
  const MAX_MB = 2;

  // Swap the sample when the language changes, but only if the user hasn't
  // started writing their own code (so we never clobber real work).
  const isUntouched = useMemo(
    () => Object.values(SAMPLES).some((s) => s.code.trim() === code.trim()),
    [code]
  );
  useEffect(() => {
    if (isUntouched) setCode(SAMPLES[language].code);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language]);

  async function analyze() {
    if (!code.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, language }),
      });
      const data = await res.json();
      if (!res.ok || data.error) throw new Error(data.error || `Request failed (${res.status})`);
      setResult(data);
      setTab(data.diagram ? "steps" : "steps");
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }

  async function onPickFile(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`That file is too large (limit ${MAX_MB} MB).`);
      return;
    }
    setCode(await file.text());
    const inferred = langFromFilename(file.name);
    if (inferred) setLanguage(inferred);
    setResult(null);
    setError("");
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <LensMark />
          <div>
            <span className="wordmark">codelens<span className="ai">ai</span></span>
            <span className="tag">read code like a map</span>
          </div>
        </div>
        <div className="topbar-actions">
          <select
            className="select"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            aria-label="Language"
          >
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
            <option value="typescript">TypeScript</option>
          </select>
          <button
            className="btn"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label="Toggle theme"
          >
            {theme === "dark" ? "◐ dark" : "◑ light"}
          </button>
        </div>
      </header>

      <div className="workspace">
        <section className="panel">
          <div className="panel-head">
            <span className="label">
              <span className="dot" />
              <span className="eyebrow">source</span>
            </span>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn" onClick={() => fileInputRef.current?.click()}>
                ↑ upload
              </button>
              <button className="btn primary" onClick={analyze} disabled={loading}>
                {loading ? "analyzing…" : "▷ analyze"}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".py,.js,.mjs,.cjs,.jsx,.ts,.tsx,.txt"
                style={{ display: "none" }}
                onChange={onPickFile}
              />
            </div>
          </div>
          <div className="panel-body">
            <div className="editor-shell">
              <CodeEditor
                language={language}
                value={code}
                onChange={setCode}
                onAnalyze={analyze}
                theme={theme}
                height="440px"
              />
            </div>
            <div className="editor-hint">
              <kbd>⌘</kbd>
              <span>/</span>
              <kbd>Ctrl</kbd>
              <span>+</span>
              <kbd>Enter</kbd>
              <span>to analyze</span>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <span className="label">
              <span className="dot" />
              <span className="eyebrow">analysis</span>
            </span>
            <div className="segmented">
              <button
                className={tab === "steps" ? "active" : ""}
                onClick={() => setTab("steps")}
              >
                steps
              </button>
              <button
                className={tab === "flow" ? "active" : ""}
                onClick={() => setTab("flow")}
              >
                flowchart
              </button>
            </div>
          </div>
          <div className="panel-body">
            <OutputPanel result={result} error={error} loading={loading} activeTab={tab} />
          </div>
        </section>
      </div>

      <footer className="footer">
        <span>codelensai · built by Ishraq Basher</span>
        <a href="https://github.com/ishraqb/codelensai" target="_blank" rel="noreferrer">
          source on github ↗
        </a>
      </footer>
    </div>
  );
}
