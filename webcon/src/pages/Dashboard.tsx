import { useEffect, useState, useCallback } from "react";
import { getHealth, getStats, executeCommand } from "../api/client";
import { Card } from "../components/Card";
import { Loading } from "../components/Loading";
import type { HealthResponse, StatsResponse } from "../api/types";
import "./Dashboard.css";

interface DashboardProps {
  onVersion: (v: string) => void;
}

interface SystemMetrics {
  cpu_count: number;
  memory_total: number;
  memory_used: number;
  disk_total: number;
  disk_used: number;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export function Dashboard({ onVersion }: DashboardProps) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [system, setSystem] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [healthRes, statsRes] = await Promise.allSettled([
        getHealth() as Promise<{ data: HealthResponse; status: number }>,
        getStats() as Promise<{ data: StatsResponse; status: number }>,
      ]);

      if (healthRes.status === "fulfilled" && healthRes.value.status === 200) {
        const h = healthRes.value.data;
        setHealth(h);
        onVersion(h.version);
      }

      if (statsRes.status === "fulfilled" && statsRes.value.status === 200) {
        setStats(statsRes.value.data);
      }

      // Try to get system metrics via a command
      try {
        const cmdRes = (await executeCommand(
          "cat /proc/cpuinfo | grep processor | wc -l && free -b | awk '/Mem:/{print $2,$3,$4}' && df -B1 / | awk 'NR==2{print $2,$3,$4}'"
        )) as unknown as { data: { output: string; status: number }; status: number };
        if (cmdRes.status === 200 && cmdRes.data.status === 200) {
          const lines = cmdRes.data.output.split("\n");
          const cpuCount = parseInt(lines[0]?.trim() ?? "0", 10);
          const memParts = (lines[1] ?? "").split(/\s+/).map(Number);
          const diskParts = (lines[2] ?? "").split(/\s+/).map(Number);
          setSystem({
            cpu_count: cpuCount,
            memory_total: memParts[0] ?? 0,
            memory_used: memParts[1] ?? 0,
            disk_total: diskParts[0] ?? 0,
            disk_used: diskParts[1] ?? 0,
          });
        }
      } catch {
        // System metrics unavailable
      }

      setError(null);
    } catch {
      setError("Unable to connect to API server");
    } finally {
      setLoading(false);
    }
  }, [onVersion]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) return <Loading message="Loading dashboard..." />;

  return (
    <div className="dashboard">
      <h2 className="page-title">Dashboard</h2>
      {error && <div className="dashboard-error">{error}</div>}

      <div className="dashboard-grid">
        <Card title="Status">
          <p className="card-value" style={{ color: health ? "#22c55e" : "#ef4444" }}>
            {health ? "Online" : "Offline"}
          </p>
        </Card>

        <Card title="Version">
          <p className="card-value">{health?.version ?? "—"}</p>
        </Card>

        <Card title="Uptime">
          <p className="card-value">
            {stats ? formatUptime(stats.uptime_seconds) : "—"}
          </p>
        </Card>

        <Card title="Requests">
          <p className="card-value">{stats?.requests ?? "—"}</p>
          {stats && stats.errors > 0 && (
            <p className="card-sub" style={{ color: "#f85149" }}>
              {stats.errors} errors
            </p>
          )}
        </Card>

        <Card title="Tool Calls">
          <p className="card-value">{stats?.tool_calls ?? "—"}</p>
        </Card>

        <Card title="Rate Limited">
          <p className="card-value">{stats?.rate_limited ?? "—"}</p>
        </Card>

        <Card title="CPU">
          <p className="card-value">{system?.cpu_count ?? "—"} cores</p>
        </Card>

        <Card title="Memory">
          <p className="card-value">
            {system ? formatBytes(system.memory_used) : "—"}
          </p>
          {system && (
            <p className="card-sub">
              {formatBytes(system.memory_total)} total
            </p>
          )}
        </Card>

        <Card title="Disk">
          <p className="card-value">
            {system ? formatBytes(system.disk_used) : "—"}
          </p>
          {system && (
            <p className="card-sub">
              {formatBytes(system.disk_total)} total
            </p>
          )}
        </Card>
      </div>

      <h3 className="section-title">Services</h3>
      <div className="dashboard-grid dashboard-grid-3">
        <Card title="Docker">
          <p className="card-sub">Socket mounted</p>
        </Card>

        <Card title="SSH">
          <p className="card-sub">/commandpc available</p>
        </Card>

        <Card title="/userfile">
          <p className="card-sub">Host bind mount</p>
        </Card>

        <Card title="/aifile">
          <p className="card-sub">Download target</p>
        </Card>

        <Card title="/proc">
          <p className="card-sub">Read-only host proc</p>
        </Card>
      </div>

      {stats?.statuses && Object.keys(stats.statuses).length > 0 && (
        <>
          <h3 className="section-title">Response Codes</h3>
          <div className="dashboard-statuses">
            {Object.entries(stats.statuses).map(([code, count]) => (
              <div key={code} className="dashboard-status-item">
                <span className={`status-code ${Number(code) < 400 ? "ok" : "err"}`}>
                  {code}
                </span>
                <span className="status-count">{count}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
