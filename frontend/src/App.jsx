// frontend/src/App.jsx
import { useEffect, useState } from "react";
import axios from "axios";
import Mermaid from "./components/Mermaid.jsx";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [code, setCode] = useState(
`def classify(x):
    if x < 0:
        return 'negative'
    elif x == 0:
        return 'zero'
    return 'positive'`
  );
  const [explanation, setExplanation] = useState([]);
  const [diagram, setDiagram] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  async function analyze() {
    try {
      setLoading(true);
      setErrorMsg("");
      const res = await axios.post(`${API_BASE}/analyze`, { code });
      setExplanation(res.data.explanation || []);
      setDiagram(res.data.mermaid || "");
    } catch (e) {
      const msg = e?.response?.data?.detail || e.message || "Unknown error";
      setErrorMsg(`Analyze failed: ${msg}`);
      setExplanation([]);
      setDiagram("");
    } finally {
      setLoading(false);
    }
  }

  async function handleFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    setCode(text);
  }

  function loadExample(which) {
    if (which === "evens") {
      setCode(
`def sum_of_evens(nums):
    total = 0
    for x in nums:
        if x % 2 == 0:
            total += x
    return total`
      );
    } else {
      setCode(
`def classify(x):
    if x < 0:
        return 'negative'
    elif x == 0:
        return 'zero'
    return 'positive'`
      );
    }
  }

  // Optional: auto-run once on first load
  useEffect(() => {
    // analyze();
  }, []);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, height: "100vh", padding: 16 }}>
      {/* LEFT: input panel */}
      <section style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
        <h2 style={{ margin: 0 }}>CodeLensAI 🧠</h2>
        <div style={{ display: "flex", gap: 8, alignItems: "center", margin: "8px 0", flexWrap: "wrap" }}>
          <input type="file" accept=".py" onChange={handleFile} />
          <button onClick={() => loadExample("classify")}>Load classify()</button>
          <button onClick={() => loadExample("evens")}>Load sum_of_evens()</button>
          <button onClick={analyze} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          spellCheck={false}
          style={{
            flex: 1,
            width: "100%",
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            fontSize: 14,
            padding: 8,
            lineHeight: 1.4,
            borderRadius: 6,
            border: "1px solid #ddd",
          }}
        />
      </section>

      {/* MIDDLE: explanation */}
      <section style={{ overflow: "auto", borderLeft: "1px solid #eee", paddingLeft: 16, minWidth: 0 }}>
        <h3 style={{ marginTop: 0 }}>Explanation</h3>
        {errorMsg && (
          <div style={{ color: "#c00", background: "#fee", padding: 8, borderRadius: 6, marginBottom: 8 }}>
            {errorMsg}
          </div>
        )}
        {!explanation.length ? (
          <p style={{ color: "#888" }}>Run “Analyze” to see results.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {explanation.map((line, i) => (
              <li key={i} style={{ marginLeft: (line.indent || 0) * 20, whiteSpace: "pre-wrap", marginBottom: 4 }}>
                {line.text}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* RIGHT: flowchart */}
      <section style={{ overflow: "auto", borderLeft: "1px solid #eee", paddingLeft: 16, minWidth: 0 }}>
        <h3 style={{ marginTop: 0 }}>Flowchart</h3>
        {!diagram ? (
          <p style={{ color: "#888" }}>Run “Analyze” to render the flowchart.</p>
        ) : (
          <Mermaid chart={diagram} />
        )}
      </section>
    </div>
  );
}
