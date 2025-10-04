// frontend/src/components/Mermaid.jsx
import { useEffect, useRef } from "react";
import mermaid from "mermaid";

// Configure mermaid once (no auto-start; we control rendering)
mermaid.initialize({
  startOnLoad: false,
  securityLevel: "loose",   // allows quotes/brackets we generate
  fontFamily: "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
});

let instanceCounter = 0;

export default function Mermaid({ chart }) {
  const containerRef = useRef(null);
  const idRef = useRef(`mermaid-${++instanceCounter}`);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    if (!chart) {
      el.innerHTML = "<p style='color:#888'>No diagram yet.</p>";
      return;
    }

    // Validate diagram first to avoid throwing in render
    try {
      mermaid.parse(chart);
    } catch (err) {
      el.innerHTML = `<pre style="color:#c00; white-space:pre-wrap;">Mermaid parse error:\n${err?.message || err}</pre>`;
      return;
    }

    // Render to SVG and inject
    mermaid
      .render(idRef.current, chart)
      .then(({ svg }) => {
        el.innerHTML = svg;
      })
      .catch((err) => {
        el.innerHTML = `<pre style="color:#c00; white-space:pre-wrap;">Render error:\n${err?.message || err}</pre>`;
      });
  }, [chart]);

  return (
    <div
      ref={containerRef}
      aria-label="Mermaid diagram"
      style={{ minHeight: 200 }}
    />
  );
}
