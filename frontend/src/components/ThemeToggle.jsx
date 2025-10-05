// Prop-driven toggle to match App.jsx state & data-theme usage
export default function ThemeToggle({ theme = "dark", onChange }) {
    const next = theme === "dark" ? "light" : "dark";
    return (
      <button
        onClick={() => onChange?.(next)}
        className="btn"
        aria-label="Toggle theme"
        title={`Switch to ${next} mode`}
      >
        {theme === "dark" ? "🌙 Dark" : "🌞 Light"}
      </button>
    );
  }
  