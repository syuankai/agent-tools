import { useRef, useEffect, useState } from "react";
import "./Terminal.css";

export interface TerminalLine {
  type: "input" | "stdout" | "stderr" | "meta" | "error" | "exit-ok" | "exit-fail";
  text: string;
}

interface TerminalProps {
  lines: TerminalLine[];
  executing: boolean;
  placeholder?: string;
  history: string[];
  onExecute: (command: string) => void;
}

export function Terminal({ lines, executing, placeholder, history, onExecute }: TerminalProps) {
  const [input, setInput] = useState("");
  const [histIdx, setHistIdx] = useState(-1);
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [lines]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const cmd = input.trim();
    if (!cmd || executing) return;
    onExecute(cmd);
    setInput("");
    setHistIdx(-1);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (history.length === 0) return;
      const next = histIdx < history.length - 1 ? histIdx + 1 : histIdx;
      setHistIdx(next);
      setInput(history[history.length - 1 - next] ?? "");
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (histIdx <= 0) {
        setHistIdx(-1);
        setInput("");
        return;
      }
      const next = histIdx - 1;
      setHistIdx(next);
      setInput(history[history.length - 1 - next] ?? "");
    }
  }

  return (
    <div className="terminal">
      <div className="terminal-header">
        <span>Terminal</span>
        {executing && <span>executing...</span>}
      </div>
      <div className="terminal-body" ref={bodyRef}>
        {lines.length === 0 && (
          <div className="terminal-empty">No output yet. Type a command below.</div>
        )}
        {lines.map((line, i) => (
          <div key={i} className={line.type}>
            {line.type === "input" ? (
              <span>
                <span className="meta">$ </span>
                {line.text}
              </span>
            ) : (
              line.text
            )}
          </div>
        ))}
      </div>
      <form className="terminal-input-row" onSubmit={handleSubmit}>
        <input
          className="terminal-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder ?? "Enter command..."}
          disabled={executing}
          autoFocus
        />
      </form>
    </div>
  );
}
