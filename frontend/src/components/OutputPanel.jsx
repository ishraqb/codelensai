import { useRef, useEffect } from "react";

export default function OutputPanel({ result, error, loading }) {
  const diagramRef = useRef(null);

  useEffect(() => {
    if (result?.mermaid && diagramRef.current) {
      import("mermaid").then((mermaid) => {
        mermaid.default.initialize({ startOnLoad: false });
        mermaid.default.render("mermaid-diagram", result.mermaid, (svg) => {
          diagramRef.current.innerHTML = svg;
        });
      });
    }
  }, [result?.mermaid]);

  if (loading) {
    return <div className="text-zinc-400 text-sm mt-4">⏳ Analyzing code...</div>;
  }

  if (error) {
    return (
      <div className="text-red-400 text-sm mt-4 whitespace-pre-wrap">❌ {error}</div>
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
  const diagram = result.mermaid || "";

  return (
    <div className="mt-6 space-y-4">
      <section>
        <h2 className="text-lg font-medium mb-2">Explanation</h2>
        {explanation.length > 0 ? (
          <ul className="list-disc list-inside space-y-1 text-zinc-200">
            {explanation.map((step, i) => (
              <li key={i}>
                {step.line}
                {step.text ? " " + step.text : ""}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-zinc-500">No explanation yet.</p>
        )}
      </section>

      <section>
        <h2 className="text-lg font-medium mb-2">Flowchart</h2>
        {diagram ? (
          <div ref={diagramRef} className="bg-zinc-900 p-4 rounded-lg" />
        ) : (
          <p className="text-zinc-500">No diagram returned.</p>
        )}
      </section>
    </div>
  );
}
