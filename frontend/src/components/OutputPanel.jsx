import { useEffect, useRef } from "react";
import mermaid from "mermaid";

/**
 * OutputPanel
 * - 'explain': indented natural-language explanation
 * - 'flow': Mermaid flowchart
 * - 'output': program stdout/stderr from /run
 */
export default function OutputPanel({
  result,
  error,
  loading,
  activeTab = "explain",
  runResult,
}) {
  const diagramRef = useRef(null);

  // Render Mermaid flowchart when needed
  useEffect(() => {
    if (activeTab !== "flow") return;
    const diagram = result?.diagram || result?.mermaid;
    if (!diagram || !diagramRef.current) {
      if (diagramRef.current) diagramRef.current.innerHTML = "";
      return;
    }

    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "loose",
      theme: "dark",
    });

    diagramRef.current.innerHTML = "";
    const id = "m" + Math.random().toString(36).slice(2);
    mermaid
      .render(id, diagram)
      .then(({ svg }) => (diagramRef.current.innerHTML = svg))
      .catch((e) => {
        diagramRef.current.innerHTML =
          `<pre class="block error">Mermaid render error:\n${String(
            e?.message || e
          )}</pre>`;
        console.error(e);
      });
  }, [activeTab, result?.diagram, result?.mermaid]);

  // Loading / error (non-output tabs)
  if (loading && activeTab !== "output") return <div className="text-xs">Analyzing code…</div>;
  if (error && activeTab !== "output") return <pre className="block error">{String(error)}</pre>;

  const explanation = Array.isArray(result?.explanation) ? result.explanation : [];

  return (
    <div>
      {/* Explanation */}
      {activeTab === "explain" && (
        <div className="block" style={{ maxHeight: "60vh" }}>
          {explanation.length ? (
            explanation.map((row, i) => (
              <div
                key={i}
                style={{
                  paddingLeft: `${(row?.indent ?? 0) * 24}px`,
                  marginBottom: "4px",
                  whiteSpace: "pre-wrap",
                }}
              >
                {row?.text ?? ""}
              </div>
            ))
          ) : (
            <div className="text-xs">No explanation available.</div>
          )}
        </div>
      )}

      {/* Flowchart */}
      {activeTab === "flow" && (
        <div className="block" style={{ overflow: "auto" }}>
          {!result?.diagram && !result?.mermaid && (
            <div className="text-xs">No flowchart available.</div>
          )}
          <div ref={diagramRef} />
        </div>
      )}

      {/* Program Output */}
      {activeTab === "output" && (
        <div>
          <div className="kv">exit code: {runResult?.exit_code ?? "—"}</div>

          <div className="kv">stdout</div>
          <pre className="block">{runResult?.stdout ? runResult.stdout : "—"}</pre>

          <div className="kv" style={{ marginTop: 10 }}>stderr</div>
          <pre className={`block ${runResult?.stderr ? "error" : ""}`}>
            {runResult?.stderr ? runResult.stderr : "—"}
          </pre>
        </div>
      )}
    </div>
  );
}
