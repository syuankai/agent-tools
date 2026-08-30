import { useEffect, useState, useCallback } from "react";
import { executeCommand } from "../api/client";
import { Card } from "../components/Card";
import { Loading } from "../components/Loading";
import type { CommandResult } from "../api/types";
import "./System.css";

interface SystemInfo {
  hostname: string;
  platform: string;
  kernel: string;
  arch: string;
  uptime_raw: string;
  load_avg: string;
  ip_address: string;
}

export function System() {
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchInfo = useCallback(async () => {
    try {
      const res = (await executeCommand(
        "hostname && uname -o && uname -r && uname -m && uptime -p && cat /proc/loadavg && hostname -I | awk '{print $1}'"
      )) as unknown as CommandResult;
      if (res.status === 200) {
        const lines = res.output.split("\n");
        setInfo({
          hostname: lines[0] ?? "",
          platform: lines[1] ?? "",
          kernel: lines[2] ?? "",
          arch: lines[3] ?? "",
          uptime_raw: lines[4] ?? "",
          load_avg: lines[5] ?? "",
          ip_address: lines[6] ?? "",
        });
      }
    } catch {
      // unavailable
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInfo();
  }, [fetchInfo]);

  if (loading) return <Loading message="Loading system info..." />;

  return (
    <div>
      <h2 className="page-title">System</h2>
      <div className="system-grid">
        <Card title="Hostname">
          <p className="card-value">{info?.hostname ?? "—"}</p>
        </Card>
        <Card title="Platform">
          <p className="card-value">{info?.platform ?? "—"}</p>
        </Card>
        <Card title="Kernel">
          <p className="card-value">{info?.kernel ?? "—"}</p>
        </Card>
        <Card title="Architecture">
          <p className="card-value">{info?.arch ?? "—"}</p>
        </Card>
        <Card title="Uptime">
          <p className="card-value">{info?.uptime_raw ?? "—"}</p>
        </Card>
        <Card title="Load Average">
          <p className="card-value">{info?.load_avg ?? "—"}</p>
        </Card>
        <Card title="IP Address">
          <p className="card-value">{info?.ip_address ?? "—"}</p>
        </Card>
      </div>
    </div>
  );
}
