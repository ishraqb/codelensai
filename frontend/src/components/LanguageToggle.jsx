export default function LanguageToggle({ value, onChange }) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <label className="text-zinc-400">Language</label>
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="bg-zinc-900 text-zinc-100 border border-zinc-800 rounded-xl px-2 py-1"
        >
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
          <option value="typescript">TypeScript</option>
        </select>
      </div>
    );
  }
  