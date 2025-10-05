import { useEffect, useRef } from "react";
import mermaid from "mermaid";

export default function OutputPanel({ result, error, loading, activeTab = "explain" }) {
  const diagramRef = useRef(null);

  // Render Mermaid when diagram changes
  useEffect(() => {
    if (activeTab !== "flow") return;
    const diagram = result?.diagram || result?.mermaid;
    if (!diagram || !diagramRef.current) {
      if (diagramRef.current) diagramRef.current.innerHTML = "";
      return;
    }
    mermaid.initialize({ startOnLoad: false, securityLevel: "loose", theme: "dark" });
    diagramRef.current.innerHTML = "";
    const id = "m" + Math.random().toString(36).slice(2);
    mermaid
      .render(id, diagram)
      .then(({ svg }) => (diagramRef.current.innerHTML = svg))
      .catch((e) => {
        diagramRef.current.innerHTML =
          `<pre style="color:#f88;white-space:pre-wrap">Mermaid render error:\n${String(e?.message || e)}</pre>`;
        console.error(e);
      });
  }, [activeTab, result?.diagram, result?.mermaid]);

  if (loading) return <div className="text-zinc-400 text-sm">Explaining…</div>;
  if (error)
    return <pre className="text-red-400 whitespace-pre-wrap text-sm">{error}</pre>;
  if (!result) return <div className="text-zinc-500 text-sm">No results yet.</div>;

  const explanation = Array.isArray(result.explanation) ? result.explanation : [];

  return (
    <div className="grid gap-4">
      {activeTab === "explain" && (
        <div className="rounded-xl bg-zinc-900 ring-1 ring-zinc-800 p-4 overflow-auto">
          {explanation.length ? (
            <ul className="text-sm leading-6">
              {explanation.map((row, i) => (
                <li key={i} style={{ paddingLeft: `${(row?.indent ?? 0) * 16}px` }}>
                  <span className="text-zinc-500 pr-2">
                    {row?.line != null ? String(row.line).padStart(2, " ") : "  "}
                  </span>
                  <span className="text-zinc-100">{row?.text ?? ""}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-zinc-500 text-sm">No explanation returned.</div>
          )}
        </div>
      )}

      {activeTab === "flow" && (
        <div className="rounded-xl bg-white text-black p-4 overflow-auto min-h-[240px]">
          {!result?.diagram && !result?.mermaid && (
            <div className="text-zinc-600 text-sm">No diagram returned.</div>
          )}
          <div ref={diagramRef} />
        </div>
      )}
    </div>
  );
}
