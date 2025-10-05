// frontend/src/App.jsx
import { useEffect, useRef, useState } from "react";
import CodeEditor from "./components/CodeEditor";
import OutputPanel from "./components/OutputPanel";
import ThemeToggle from "./components/ThemeToggle";
import LanguageToggle from "./components/LanguageToggle";
import Tabs from "./components/Tabs";
import "./App.css";

// Infer editor language from filename
function langFromFilename(name = "") {
  const ext = name.toLowerCase().split(".").pop();
  switch (ext) {
    case "py": return "python";
    case "js":
    case "mjs":
    case "cjs": return "javascript";
    case "ts":
    case "tsx": return "typescript";
    case "java": return "java";
    case "cpp":
    case "cc":
    case "cxx":
    case "hpp":
    case "h": return "cpp";
    case "go": return "go";
    case "rs": return "rust";
    case "rb": return "ruby";
    case "php": return "php";
    case "cs": return "csharp";
    case "swift": return "swift";
    case "kt":
    case "kts": return "kotlin";
    default: return null;
  }
}

export default function App() {
  // Theme
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");
  useEffect(() => {
    localStorage.setItem("theme", theme);
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  // Editor state
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
  const [runAfter, setRunAfter] = useState("print(two_sum([2,7,11,15], 9))");

  // Results state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [runResult, setRunResult] = useState(null);
  const [tab, setTab] = useState("explain");

  // File upload
  const fileInputRef = useRef(null);
  const MAX_SIZE_MB = 2;

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  async function onPickFile(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File too large. Max ${MAX_SIZE_MB} MB.`);
      setTab("output");
      setRunResult({
        stdout: "",
        stderr: `Upload blocked: file is ${(file.size / (1024 * 1024)).toFixed(2)} MB (limit ${MAX_SIZE_MB} MB).`,
        exit_code: 1,
      });
      return;
    }

    try {
      const text = await file.text();
      setCode(text);

      const inferred = langFromFilename(file.name);
      if (inferred) setLanguage(inferred);

      setTab("explain");
      setResult(null);
      setRunResult(null);
      setError("");
    } catch (err) {
      const msg = String(err?.message || err);
      setError(msg);
      setTab("output");
      setRunResult({ stdout: "", stderr: msg, exit_code: 1 });
    }
  }

  // Backend actions
  async function explain() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, language }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResult(data);
      setTab(data?.diagram ? "flow" : "explain");
    } catch (e) {
      setError(String(e.message || e));
      setTab("explain");
    } finally {
      setLoading(false);
    }
  }

  async function run() {
    setError("");
    setRunResult(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, language, postlude: runAfter }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setRunResult(data);
      setTab("output");
    } catch (e) {
      setRunResult({ stdout: "", stderr: String(e.message || e), exit_code: 1 });
      setTab("output");
    }
  }

  return (
    <div className="page">
      <div className="container">
        {/* Header */}
        <header className="header">
          <div>
            <h1 className="title">CodeLensAI</h1>
            <p className="subtitle">AI-powered code explainer &amp; flowchart</p>
          </div>
          <div className="controls-row">
            <LanguageToggle value={language} onChange={setLanguage} />
            <ThemeToggle theme={theme} onChange={setTheme} />
          </div>
        </header>

        {/* Editor */}
        <section className="card">
          <div className="card-bar">
            <div className="card-title">Editor</div>
            <div className="controls-row">
              <button className="btn" onClick={run}>▶ Run</button>
              <button className="btn primary" onClick={explain}>✨ Explain</button>
              <button className="btn" onClick={openFilePicker}>📂 Upload File</button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".py,.js,.mjs,.cjs,.ts,.tsx,.java,.cpp,.cc,.cxx,.hpp,.h,.go,.rs,.rb,.php,.cs,.swift,.kt,.kts,.json,.txt"
                style={{ display: "none" }}
                onChange={onPickFile}
              />
            </div>
          </div>

          <div className="card-body">
            <CodeEditor
              language={language}
              value={code}
              onChange={setCode}
              onRun={run}
              onExplain={explain}
              height="420px"
            />

            <div className="run-after">
              <label className="text-xs">Run after:</label>
              <input
                value={runAfter}
                onChange={(e) => setRunAfter(e.target.value)}
                placeholder="print(two_sum([2,7,11,15], 9))"
              />
            </div>
          </div>
        </section>

        {/* Results */}
        <section className="card">
          <div className="card-bar">
            <Tabs
              value={tab}
              onChange={setTab}
              tabs={[
                { key: "explain", label: "Explanation" },
                { key: "flow", label: "Flowchart" },
                { key: "output", label: "Output" },
              ]}
            />
            <div className="text-xs status">
              {loading ? "Working…" : error ? "Error" : (result || runResult) ? "Ready" : "Idle"}
            </div>
          </div>
          <div className="card-body">
            <OutputPanel
              result={result}
              error={error}
              loading={loading}
              activeTab={tab}
              runResult={runResult}
            />
          </div>
        </section>
      </div>
    </div>
  );
}
