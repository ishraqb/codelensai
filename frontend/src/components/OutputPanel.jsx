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
  