export default function Tabs({ value, onChange, items }) {
    return (
      <div className="inline-flex rounded-xl border border-zinc-800 overflow-hidden">
        {items.map((it) => (
          <button
            key={it.value}
            onClick={() => onChange(it.value)}
            className={
              "px-3 py-1.5 text-sm " +
              (value === it.value
                ? "bg-zinc-800 text-zinc-100"
                : "bg-transparent text-zinc-400 hover:text-zinc-200")
            }
          >
            {it.label}
          </button>
        ))}
      </div>
    );
  }
  