import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { EditorView } from "@codemirror/view";
import { EditorState, Extension } from "@codemirror/state";
import { oneDark } from "@codemirror/theme-one-dark";
import { javascript } from "@codemirror/lang-javascript";
import { python } from "@codemirror/lang-python";

/**
 * CodeLensAI CodeEditor
 *
 * A modern CodeMirror 6 editor wrapper with:
 *  - Controlled value
 *  - Language switching (JS/TS + Python)
 *  - One Dark theme
 *  - Shortcuts: ⌘/Ctrl+Enter → Run, ⌥/Alt+Enter → Explain
 */

export type SupportedLanguage = "javascript" | "typescript" | "python";

export interface CodeEditorProps {
  language?: SupportedLanguage;
  value?: string;
  onChange?: (next: string) => void;
  onRun?: () => void;
  onExplain?: () => void;
  readOnly?: boolean;
  placeholder?: string;
  height?: string;
  minHeight?: string;
  className?: string;
  debounceMs?: number;
}

function langExtension(language: SupportedLanguage | undefined): Extension[] {
  switch (language) {
    case "typescript":
      return [javascript({ jsx: true, typescript: true })];
    case "javascript":
      return [javascript({ jsx: true })];
    case "python":
    default:
      return [python()];
  }
}

export default function CodeEditor({
  language = "javascript",
  value = "",
  onChange,
  onRun,
  onExplain,
  readOnly = false,
  placeholder,
  height = "420px",
  minHeight = "280px",
  className,
  debounceMs = 80,
}: CodeEditorProps) {
  const [internal, setInternal] = useState<string>(value);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    setInternal(value ?? "");
  }, [value]);

  const baseExtensions = useMemo<Extension[]>(() => {
    return [
      EditorView.lineWrapping,
      EditorView.theme({
        ".cm-content": {
          fontFamily:
            "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
          fontSize: "0.95rem",
        },
        ".cm-scroller": { lineHeight: 1.55 },
      }),
      EditorState.readOnly.of(readOnly),
    ];
  }, [readOnly]);

  const extensions = useMemo<Extension[]>(() => {
    return [oneDark, ...baseExtensions, ...langExtension(language)];
  }, [baseExtensions, language]);

  const handleChange = useCallback(
    (doc: string) => {
      setInternal(doc);
      if (!onChange) return;
      if (timer.current) window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => onChange(doc), debounceMs);
    },
    [onChange, debounceMs]
  );

  const onKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const isMod = e.metaKey || e.ctrlKey;
      if (isMod && e.key === "Enter") {
        if (onRun) onRun();
        e.preventDefault();
        return;
      }
      if (e.altKey && e.key === "Enter") {
        if (onExplain) onExplain();
        e.preventDefault();
      }
    },
    [onRun, onExplain]
  );

  return (
    <div
      className={"w-full " + (className ?? "")}
      onKeyDown={onKeyDown}
      role="group"
      aria-label="Code editor"
    >
      {placeholder && !internal && (
        <div className="text-sm text-zinc-400 pb-1">{placeholder}</div>
      )}
      <div className="rounded-2xl overflow-hidden shadow-sm ring-1 ring-zinc-800">
        <CodeMirror
          value={internal}
          height={height}
          minHeight={minHeight}
          extensions={extensions}
          theme={oneDark}
          basicSetup={{
            lineNumbers: true,
            foldGutter: true,
            highlightActiveLine: true,
            highlightSelectionMatches: true,
            autocompletion: true,
            bracketMatching: true,
          }}
          onChange={handleChange}
        />
      </div>
      <div className="flex items-center gap-2 pt-2 text-xs text-zinc-400">
        <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700">
          ⌘
        </kbd>
        <span>or</span>
        <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700">
          Ctrl
        </kbd>
        <span>+</span>
        <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700">
          Enter
        </kbd>
        <span>to run · </span>
        <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700">
          ⌥
        </kbd>
        <span>+</span>
        <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700">
          Enter
        </kbd>
        <span>to explain</span>
      </div>
    </div>
  );
}
