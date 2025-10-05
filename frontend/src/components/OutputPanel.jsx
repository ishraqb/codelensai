// frontend/src/components/OutputPanel.jsx
import { useEffect, useId, useRef, useState } from "react";
import mermaid from "mermaid";

/* Initialize Mermaid once (HMR-safe) with compact padding + dark palette */
let MERMAID_READY = false;
function ensureMermaid() {
  if (!MERMAID_READY) {
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "loose",
      theme: "base",
      flowchart: {
        diagramPadding: 2,
        padding: 0,
        htmlLabels: true,
        useMaxWidth: true,
        nodeSpacing: 36,
        rankSpacing: 36,
      },
      themeVariables: {
        background: "transparent",
        primaryColor: "#0f172a",
        primaryTextColor: "#e5e7eb",
        primaryBorderColor: "#334155",
        secondaryColor: "#0b1220",
        secondaryTextColor: "#e5e7eb",
        tertiaryColor: "#111827",
        tertiaryTextColor: "#e5e7eb",
        lineColor: "#93c5fd",
        textColor: "#e6edf3",
        edgeLabelBackground: "transparent",
        fontFamily:
          "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial",
      },
    });
    MERMAID_READY = true;
  }
}

/* ---------- Explanation renderer ---------- */
function renderExplanation(expl) {
  if (expl == null) return <div>Ready</div>;
  if (typeof expl === "string") return <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.4 }}>{expl}</div>;
  if (Array.isArray(expl)) {
    return (
      <div style={{ lineHeight: 1.4 }}>
        {expl.map((line, i) => {
          if (typeof line === "string") return <div key={i} style={{ whiteSpace: "pre-wrap" }}>{line}</div>;
          if (line && typeof line === "object") {
            const text = line.text ?? JSON.stringify(line);
            const indent = Number(line.indent ?? 0);
            return <div key={i} style={{ paddingLeft: indent * 16, whiteSpace: "pre-wrap" }}>{text}</div>;
          }
          return <div key={i}>{String(line)}</div>;
        })}
      </div>
    );
  }
  if (typeof expl === "object") return <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(expl, null, 2)}</pre>;
  return <div>{String(expl)}</div>;
}

/* ---------- Diagram helpers ---------- */
function joinLinesArray(arr) {
  return arr
    .map((ln) => {
      if (typeof ln === "string") return ln;
      if (ln && typeof ln === "object") {
        const indent = Number(ln.indent ?? 0);
        const text = ln.text ?? "";
        return `${" ".repeat(indent * 2)}${text}`;
      }
      return String(ln ?? "");
    })
    .join("\n");
}
function normalizeDiagram(candidate) {
  if (typeof candidate === "string") return candidate.trim();
  if (Array.isArray(candidate)) return joinLinesArray(candidate).trim();
  if (candidate && typeof candidate === "object") {
    for (const key of ["diagram", "mermaid", "graph", "flowchart", "chart", "diagramText"]) {
      if (key in candidate) {
        const v = normalizeDiagram(candidate[key]);
        if (v) return v;
      }
    }
    if (Array.isArray(candidate.lines)) {
      const v = joinLinesArray(candidate.lines).trim();
      if (v) return v;
    }
  }
  return "";
}
function extractDiagram(result) {
  if (!result) return "";
  const top = normalizeDiagram(result);
  if (top) return top;
  if (typeof result === "object") {
    for (const [, v] of Object.entries(result)) {
      const norm = normalizeDiagram(v);
      if (/^(flowchart|graph)\b/.test(norm)) return norm;
    }
  }
  return "";
}

/* ---------------- Component ---------------- */
export default function OutputPanel({ result, error, loading, activeTab, runResult }) {
  const rid = useId();                            // unique id prefix for this instance
  const OWN_PREFIX = `m-${rid}`;                  // used for mermaid render ids
  const chartRef = useRef(null);
  const [diagText, setDiagText] = useState("");
  const [diagError, setDiagError] = useState("");

  // Hard cleanup: remove any Mermaid nodes with our id prefix (defensive)
  function hardCleanup() {
    try {
      // 1) Clear our container
      if (chartRef.current) chartRef.current.innerHTML = "";
      // 2) Remove any global element Mermaid might have left
      const stray = Array.from(document.querySelectorAll(`[id^="${OWN_PREFIX}"]`));
      stray.forEach((n) => n.parentNode && n.parentNode.removeChild(n));
    } catch {}
  }

  // On any switch AWAY from flow, clean aggressively
  useEffect(() => {
    if (activeTab !== "flow") {
      hardCleanup();
    }
  }, [activeTab]); // eslint-disable-line react-hooks/exhaustive-deps

  // Render Mermaid ONLY on Flow tab
  useEffect(() => {
    if (activeTab !== "flow") return;

    ensureMermaid();

    const diagram = extractDiagram(result);
    setDiagText(diagram);
    setDiagError("");
    if (!diagram) return;

    let canceled = false;

    // Clear before rendering
    if (chartRef.current) chartRef.current.innerHTML = "";

    // Hidden off-screen host for layout measuring
    const tempHost = document.createElement("div");
    tempHost.style.position = "absolute";
    tempHost.style.left = "-100000px";
    tempHost.style.top = "0";
    tempHost.style.visibility = "hidden";
    document.body.appendChild(tempHost);

    const renderId = `${OWN_PREFIX}-${Date.now()}`;

    const raf = requestAnimationFrame(async () => {
      try {
        const looksMermaid = /^(flowchart|graph)\b/.test(diagram.trim());
        if (!looksMermaid) {
          setDiagError("Diagram text does not look like Mermaid (should start with 'flowchart' or 'graph').");
          return;
        }

        mermaid.parse(diagram);
        const { svg } = await mermaid.render(renderId, diagram, tempHost);

        if (!canceled && chartRef.current) {
          chartRef.current.innerHTML = svg;

          // Tight/transparent SVG so no stray backgrounds
          const svgEl = chartRef.current.querySelector("svg");
          if (svgEl) {
            svgEl.style.display = "block";
            svgEl.style.margin = "0";
            svgEl.style.padding = "0";
            svgEl.style.width = "100%";
            svgEl.style.height = "auto";
            svgEl.style.background = "transparent";
            const bgRect =
              svgEl.querySelector('rect.background') ||
              svgEl.querySelector('rect[class*="background"]') ||
              svgEl.querySelector("svg > rect");
            if (bgRect) {
              bgRect.setAttribute("fill", "transparent");
              bgRect.setAttribute("stroke", "transparent");
            }
          }
        }
      } catch (e) {
        if (!canceled) {
          setDiagError(String(e?.message || e));
          if (chartRef.current) chartRef.current.innerHTML = "";
        }
      } finally {
        if (tempHost && tempHost.parentNode) tempHost.parentNode.removeChild(tempHost);
      }
    });

    return () => {
      cancelAnimationFrame(raf);
      canceled = true;
      hardCleanup();
    };
  }, [activeTab, result]); // eslint-disable-line react-hooks/exhaustive-deps

  // Top-level states
  if (loading) return <div>Working…</div>;
  if (error) return <pre style={{ color: "#ff6b6b", whiteSpace: "pre-wrap" }}>{error}</pre>;

  // Tabs
  if (activeTab === "explain") {
    const explanation = result?.explanation ?? result;
    return renderExplanation(explanation);
  }

  if (activeTab === "flow") {
    return (
      <div>
        <div
          ref={chartRef}
          className="flowchart-box"
          style={{
            width: "100%",
            overflow: "auto",
            background: "var(--panel-2)",
            borderRadius: 10,
            padding: 0,
            border: "1px solid var(--border)",
            minHeight: 120,
          }}
        />
        <details style={{ marginTop: 8 }}>
          <summary style={{ cursor: "pointer", color: "var(--muted)" }}>
            {diagError ? "Show error & raw diagram" : "Show raw diagram"}
          </summary>
          {diagError && (
            <div style={{ color: "#ff6b6b", marginTop: 6, whiteSpace: "pre-wrap" }}>{diagError}</div>
          )}
          <pre
            style={{
              marginTop: 6,
              whiteSpace: "pre-wrap",
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
              fontSize: 12,
              background: "var(--panel-2)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: 8,
            }}
          >
{diagText || "No diagram text found."}
          </pre>
        </details>
      </div>
    );
  }

  // Output tab — chart is fully cleaned up by now
  return (
    <div
      style={{
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
        fontSize: 12,
      }}
    >
      <div>exit code:{runResult?.exit_code ?? "—"}</div>
      <div><b>stdout</b></div>
      <pre style={{ whiteSpace: "pre-wrap" }}>{runResult?.stdout || "—"}</pre>
      <div><b>stderr</b></div>
      <pre style={{ whiteSpace: "pre-wrap", color: "#ff9f43" }}>{runResult?.stderr || "—"}</pre>
    </div>
  );
}
