export default function OutputPanel({ result, error, loading }) {
    if (loading) {
      return (
        <div className="text-zinc-400 text-sm mt-4">⏳ Analyzing code...</div>
      );
    }
  
    if (error) {
      return (
        <div className="text-red-400 text-sm mt-4 whitespace-pre-wrap">
          ❌ {error}
        </div>
      );
    }
  
    if (!result) {
      return (
        <div className="text-zinc-500 text-sm mt-4">
          Results will appear here after you click “Explain”.
        </div>
      );
    }
  
    const explanation = result.explanation || [];
    const diagram = result.mermaid || result.diagram || "";
  
    return (
      <div className="mt-6 space-y-4">
        {/* Explanation Section */}
        <section>
          <h2 className="text-lg font-medium mb-2">Explanation</h2>
          {explanation.length > 0 ? (
            <ul className="list-disc list-inside space-y-1 text-zinc-200">
              {explanation.map((step, i) => (
                <li key={i} style={{ marginLeft: `${step.indent * 1.25}rem` }}>
                  <span className="text-zinc-400">{step.line}</span>{" "}
                  {step.text}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-zinc-500 text-sm">No explanation returned.</p>
          )}
        </section>
  
        {/* Flowchart Section */}
        <section>
          <h2 className="text-lg font-medium mb-2">Flowchart</h2>
          {diagram ? (
            <div className="bg-white rounded-xl p-4">
              <div className="mermaid">{diagram}</div>
            </div>
          ) : (
            <p className="text-zinc-500 text-sm">No diagram returned.</p>
          )}
        </section>
      </div>
    );
  }
  
import { useEffect, useRef } from "react";
import mermaid from "mermaid";

/**
 * OutputPanel
 * Renders:
 *  - Explanation list (expects result.explanation: Array<{ line?: number, text: string, indent?: number }>)
 *  - Mermaid diagram (expects result.diagram: string)
 */
export default function OutputPanel({ result, error, loading }) {
  const diagramRef = useRef(null);

  // Render Mermaid whenever the diagram string changes
  useEffect(() => {
    if (!result?.diagram) return;
    // Safe defaults for local dev; you can tighten later
    mermaid.initialize({ startOnLoad: false, securityLevel: "loose", theme: "dark" });

    const host = diagramRef.current;
    if (host) {
      host.innerHTML = `<div class="mermaid">${result.diagram}</div>`;
      mermaid.run({ nodes: [host] });
    }
  }, [result?.diagram]);

  return (
    <div className="mt-4 grid gap-4 md:grid-cols-2">
      {/* Explanation column */}
      <div className="rounded-2xl bg-zinc-900 ring-1 ring-zinc-800 p-4 overflow-auto">
        <div className="text-sm font-medium text-zinc-300 mb-2">Explanation</div>
        {loading && <div className="text-zinc-400 text-sm">Explaining…</div>}
        {error && (
          <pre className="text-red-400 whitespace-pre-wrap text-sm">{error}</pre>
        )}
        {!loading && !error && (!result?.explanation || result.explanation.length === 0) && (
          <div className="text-zinc-500 text-sm">No explanation yet.</div>
        )}
        {Array.isArray(result?.explanation) && result.explanation.length > 0 && (
          <ul className="text-sm leading-6">
            {result.explanation.map((row, i) => (
              <li key={i} style={{ paddingLeft: `${(row?.indent ?? 0) * 16}px` }}>
                <span className="text-zinc-500 pr-2">
                  {row?.line != null ? String(row.line).padStart(2, " ") : "  "}
                </span>
                <span className="text-zinc-100">{row?.text ?? ""}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Diagram column */}
      <div className="rounded-2xl bg-zinc-900 ring-1 ring-zinc-800 p-4 overflow-auto">
        <div className="text-sm font-medium text-zinc-300 mb-2">Flowchart</div>
        {!result?.diagram && (
          <div className="text-zinc-500 text-sm">No diagram returned.</div>
        )}
        <div ref={diagramRef} />
      </div>
    </div>
  );
}
