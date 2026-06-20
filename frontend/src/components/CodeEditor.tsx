import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { EditorView } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import type { Extension } from "@codemirror/state";
import { oneDark } from "@codemirror/theme-one-dark";
import { javascript } from "@codemirror/lang-javascript";
import { python } from "@codemirror/lang-python";

/**
 * Thin CodeMirror 6 wrapper for CodeLensAI.
 *  - Controlled value with light debouncing
 *  - Python / JavaScript / TypeScript grammars
 *  - Theme follows the app (One Dark in dark mode, default in light mode)
 *  - Cmd/Ctrl+Enter triggers analysis
 */

export type SupportedLanguage = "javascript" | "typescript" | "python";

export interface CodeEditorProps {
  language?: SupportedLanguage;
  value?: string;
  onChange?: (next: string) => void;
  onAnalyze?: () => void;
  readOnly?: boolean;
  theme?: "dark" | "light";
  height?: string;
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
  language = "python",
  value = "",
  onChange,
  onAnalyze,
  readOnly = false,
  theme = "dark",
  height = "440px",
  debounceMs = 80,
}: CodeEditorProps) {
  const [internal, setInternal] = useState<string>(value);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    setInternal(value ?? "");
  }, [value]);

  const extensions = useMemo<Extension[]>(
    () => [
      EditorView.lineWrapping,
      EditorView.theme({
        "&": { backgroundColor: "transparent" },
        ".cm-content": { fontFamily: "var(--font-mono)" },
        ".cm-scroller": { lineHeight: "1.6" },
      }),
      EditorState.readOnly.of(readOnly),
      ...langExtension(language),
    ],
    [readOnly, language]
  );

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
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        onAnalyze?.();
      }
    },
    [onAnalyze]
  );

  return (
    <div onKeyDown={onKeyDown} role="group" aria-label="Code editor">
      <CodeMirror
        value={internal}
        height={height}
        extensions={extensions}
        theme={theme === "dark" ? oneDark : "light"}
        basicSetup={{
          lineNumbers: true,
          foldGutter: true,
          highlightActiveLine: true,
          autocompletion: false,
          bracketMatching: true,
        }}
        onChange={handleChange}
      />
    </div>
  );
}
