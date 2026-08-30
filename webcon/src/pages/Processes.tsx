import { useEffect, useState, useCallback } from "react";
import { executeCommand } from "../api/client";
import { Loading } from "../components/Loading";
import type { CommandResult } from "../api/types";
import "./Processes.css";

interface ProcessRow {
  pid: string;
  user: string;
  cpu: string;
  mem: string;
  stat: string;
  start: string;
  command: string;
}

export function Processes() {
  const [procs, setProcs] = useState<ProcessRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProcs = useCallback(async () => {
    setLoading(true);
    try {
      const res = (await executeCommand(
        "ps aux --sort=-%cpu | head -30"
      )) as unknown as CommandResult;
      if (res.status === 200 && res.output) {
        const lines = res.output.split("\n").filter(Boolean);
        const header = lines[0];
        const rows = lines.slice(1).map((line) => {
          const parts = line.split(/\s+/);
          return {
            pid: parts[1] ?? "",
            user: parts[0] ?? "",
            cpu: parts[2] ?? "",
            mem: parts[3] ?? "",
            stat: parts[7] ?? "",
            start: parts[8] ?? "",
            command: parts.slice(10).join(" ").substring(0, 100),
          };
        });
        setProcs(rows);
        void header;
        setError(null);
      } else {
        setError(res.output || "Unable to fetch processes");
      }
    } catch {
      setError("API unavailable");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProcs();
    const interval = setInterval(fetchProcs, 10000);
    return () => clearInterval(interval);
  }, [fetchProcs]);

  return (
    <div>
      <h2 className="page-title">Processes</h2>
      <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: 12 }}>
        Read-only view of top processes sorted by CPU usage. Auto-refreshes
        every 10 seconds.
      </p>
      {error && <div className="proc-error">{error}</div>}
      {loading ? (
        <Loading message="Loading processes..." />
      ) : (
        <div className="proc-table-wrap">
          <table className="proc-table">
            <thead>
              <tr>
                <th>PID</th>
                <th>User</th>
                <th>CPU%</th>
                <th>MEM%</th>
                <th>STAT</th>
                <th>Started</th>
                <th>Command</th>
              </tr>
            </thead>
            <tbody>
              {procs.map((p, i) => (
                <tr key={`${p.pid}-${i}`}>
                  <td className="proc-pid">{p.pid}</td>
                  <td>{p.user}</td>
                  <td>{p.cpu}</td>
                  <td>{p.mem}</td>
                  <td>{p.stat}</td>
                  <td>{p.start}</td>
                  <td className="proc-cmd">{p.command}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
