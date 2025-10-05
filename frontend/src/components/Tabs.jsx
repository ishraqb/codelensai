export default function Tabs({ tabs = [], value, onChange }) {
    const list = Array.isArray(tabs) ? tabs : [];
    return (
      <div className="tabs-row">
        {list.map((t) => {
          const active = t.key === value;
          return (
            <button
              key={t.key}
              onClick={() => onChange?.(t.key)}
              className={`tab-btn ${active ? "active" : ""}`}
            >
              {t.label}
            </button>
          );
        })}
      </div>
    );
  }
  