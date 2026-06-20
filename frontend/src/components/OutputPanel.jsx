import { useEffect, useId, useRef, useState } from "react";
import mermaid from "mermaid";

// Re-initialise Mermaid whenever the theme flips so the diagram palette matches
// the surrounding UI instead of fighting it.
function initMermaid(theme) {
  const dark = theme !== "light";
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "loose",
    theme: "base",
    flowchart: { htmlLabels: true, useMaxWidth: true, nodeSpacing: 36, rankSpacing: 40, padding: 6 },
    themeVariables: {
      background: "transparent",
      primaryColor: dark ? "#16181d" : "#ffffff",
      primaryTextColor: dark ? "#e7e8ec" : "#16181d",
      primaryBorderColor: dark ? "#313640" : "#c7c2b1",
      lineColor: dark ? "#7cc7ff" : "#2b6cb0",
      fontFamily: "JetBrains Mono, ui-monospace, monospace",
      fontSize: "13px",
    },
  });
}

function Insight({ result }) {
  const hasSummary = Boolean(result.summary);
  return (
    <div className="insight">
      <div className="insight-top">
        <span className="eyebrow">summary</span>
        <span className={`badge ${result.ai ? "live" : ""}`}>
          {result.ai ? "● ai generated" : "built-in analysis"}
        </span>
      </div>
      {hasSummary ? (
        <p className="insight-text">{result.summary}</p>
      ) : (
        <p className="insight-text empty">
          AI summary unavailable right now — showing the deterministic breakdown below.
        </p>
      )}
      {result.complexity && (
        <span className="chip">
          time complexity <b>{result.complexity}</b>
        </span>
      )}
    </div>
  );
}

function Steps({ steps }) {
  if (!steps?.length) return <div className="placeholder">No steps to show.</div>;
  return (
    <ol className="steps">
      {steps.map((s, i) => (
        <li className="step" key={i} style={{ paddingLeft: (s.indent || 0) * 18 }}>
          <span className="ln">{s.line ? `L${s.line}` : ""}</span>
          <span className="txt">{s.text}</span>
        </li>
      ))}
    </ol>
  );
}

function Flowchart({ diagram, active }) {
  const rid = useId().replace(/[:]/g, "");
  const boxRef = useRef(null);
  const [renderError, setRenderError] = useState("");

  useEffect(() => {
    if (!active) return;
    const theme = document.documentElement.getAttribute("data-theme") || "dark";
    initMermaid(theme);
    setRenderError("");

    if (!diagram) {
      if (boxRef.current) boxRef.current.innerHTML = "";
      return;
    }

    let cancelled = false;
    const renderId = `flow-${rid}-${Date.now()}`;
    mermaid
      .render(renderId, diagram)
      .then(({ svg }) => {
        if (!cancelled && boxRef.current) boxRef.current.innerHTML = svg;
      })
      .catch((e) => {
        if (!cancelled) setRenderError(String(e?.message || e));
      });

    return () => {
      cancelled = true;
    };
  }, [diagram, active, rid]);

  if (!diagram) return <div className="placeholder">No flowchart for this snippet.</div>;

  return (
    <div>
      <div className="flow-box" ref={boxRef} />
      <details className="raw-toggle">
        <summary>{renderError ? "render failed — show source" : "show diagram source"}</summary>
        {renderError && <pre style={{ color: "var(--danger)" }}>{renderError}</pre>}
        <pre>{diagram}</pre>
      </details>
    </div>
  );
}

export default function OutputPanel({ result, error, loading, activeTab }) {
  if (loading) {
    return (
      <div className="loading">
        reading your code<span className="blink">_</span>
      </div>
    );
  }
  if (error) return <div className="error">{error}</div>;
  if (!result) {
    return (
      <div className="placeholder">
        Paste code on the left and hit <b>analyze</b> to see a plain-English
        breakdown, a complexity estimate, and a flowchart.
      </div>
    );
  }

  return (
    <div>
      <Insight result={result} />
      {activeTab === "flow" ? (
        <Flowchart diagram={result.diagram} active={activeTab === "flow"} />
      ) : (
        <Steps steps={result.steps} />
      )}
    </div>
  );
}
