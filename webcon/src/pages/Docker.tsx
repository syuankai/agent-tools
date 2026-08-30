import { useState, useCallback } from "react";
import { executeDocker } from "../api/client";
import { Terminal as TerminalComponent } from "../components/Terminal";
import type { TerminalLine } from "../components/Terminal";
import type { CommandResult } from "../api/types";

export function DockerPage() {
  const [lines, setLines] = useState<TerminalLine[]>([]);
  const [executing, setExecuting] = useState(false);
  const [history, setHistory] = useState<string[]>([]);

  const handleExecute = useCallback(async (command: string) => {
    setExecuting(true);
    setLines((prev) => [...prev, { type: "input", text: command }]);
    setHistory((prev) => [...prev, command]);

    try {
      const start = performance.now();
      const res = (await executeDocker(command)) as unknown as CommandResult;
      const duration = Math.round(performance.now() - start);

      const meta: TerminalLine = {
        type: "meta",
        text: `[HTTP ${res.http_status ?? res.status}] exit: ${res.exit_code ?? 0} | ${duration}ms | req: ${res.request_id ?? "—"}`,
      };

      if (res.output) {
        const outputLines = res.output.split("\n").filter(Boolean);
        for (const line of outputLines) {
          setLines((prev) => [...prev, { type: "stdout", text: line }]);
        }
      }

      if (res.exit_code && res.exit_code !== 0) {
        setLines((prev) => [
          ...prev,
          { type: "exit-fail", text: `exit ${res.exit_code}` },
        ]);
      } else {
        setLines((prev) => [
          ...prev,
          { type: "exit-ok", text: res.output ? "" : "All done." },
        ]);
      }

      setLines((prev) => [...prev, meta]);
    } catch (err) {
      setLines((prev) => [
        ...prev,
        {
          type: "error",
          text: `Error: ${err instanceof Error ? err.message : "Unknown error"}`,
        },
      ]);
    } finally {
      setExecuting(false);
    }
  }, []);

  return (
    <div>
      <h2 className="page-title">Docker</h2>
      <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: 12 }}>
        Execute Docker commands through the mounted socket. Mutations are
        disabled by default.
      </p>
      <TerminalComponent
        lines={lines}
        executing={executing}
        placeholder="docker ps, docker images..."
        history={history}
        onExecute={handleExecute}
      />
    </div>
  );
}
