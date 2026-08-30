import { useEffect, useState, useCallback } from "react";
import { getHelp } from "../api/client";
import { Loading } from "../components/Loading";
import "./ApiDocs.css";

interface HelpData {
  version: string;
  endpoints: Record<string, string>;
  responses: Record<string, string>;
  limits?: Record<string, string>;
  command_policy?: {
    blocked_commands: string[];
    block_environment_variable: string;
    note: string;
  };
}

interface EndpointInfo {
  method: "GET" | "POST";
  path: string;
  description: string;
  future?: boolean;
}

const FUTURE_ENDPOINTS: EndpointInfo[] = [
  { method: "POST", path: "/api/files/read", description: "Read file contents (planned)", future: true },
  { method: "POST", path: "/api/files/write", description: "Write file contents (planned)", future: true },
  { method: "POST", path: "/api/files/mkdir", description: "Create directory (planned)", future: true },
  { method: "POST", path: "/api/files/delete", description: "Delete file/directory (planned)", future: true },
  { method: "POST", path: "/api/files/upload", description: "Upload file (planned)", future: true },
  { method: "GET", path: "/api/system/info", description: "Detailed system info (planned)", future: true },
  { method: "GET", path: "/api/system/metrics", description: "System metrics stream (planned)", future: true },
];

function parseEndpoint(key: string): EndpointInfo {
  const [method, ...rest] = key.split(" ");
  return {
    method: (method?.toUpperCase() as "GET" | "POST") ?? "POST",
    path: rest.join(" "),
    description: "",
  };
}

export function ApiDocs() {
  const [help, setHelp] = useState<HelpData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHelp = useCallback(async () => {
    try {
      const res = (await getHelp()) as unknown as { data: HelpData; status: number };
      if (res.status === 200) {
        setHelp(res.data);
      }
    } catch {
      // unavailable
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHelp();
  }, [fetchHelp]);

  if (loading) return <Loading message="Loading API documentation..." />;

  const endpoints = help
    ? Object.entries(help.endpoints).map(([key, desc]) => ({
        ...parseEndpoint(key),
        description: desc,
      }))
    : [];

  return (
    <div>
      <h2 className="page-title">API Documentation</h2>
      <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: 16 }}>
        Version: {help?.version ?? "—"}
      </p>

      <h3 className="section-title">Current Endpoints</h3>
      <div className="apidocs-table-wrap">
        <table className="apidocs-table">
          <thead>
            <tr>
              <th>Method</th>
              <th>Path</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {endpoints.map((ep) => (
              <tr key={ep.path}>
                <td>
                  <span className={`apidocs-method ${ep.method.toLowerCase()}`}>
                    {ep.method}
                  </span>
                </td>
                <td className="apidocs-path">
                  <code>{ep.path}</code>
                </td>
                <td className="apidocs-desc">{ep.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {help?.responses && (
        <>
          <h3 className="section-title">Response Types</h3>
          <div className="apidocs-responses">
            {Object.entries(help.responses).map(([key, desc]) => (
              <div key={key} className="apidocs-response-item">
                <span className="apidocs-response-key">{key}</span>
                <span className="apidocs-response-desc">{desc}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {help?.limits && (
        <>
          <h3 className="section-title">Limits</h3>
          <div className="apidocs-limits">
            {Object.entries(help.limits).map(([key, desc]) => (
              <div key={key} className="apidocs-limit-item">
                <code>{key}</code>
                <span>{desc}</span>
              </div>
            ))}
          </div>
        </>
      )}

      <h3 className="section-title" style={{ color: "var(--text-tertiary)" }}>
        v0.0.5 Planned Endpoints
      </h3>
      <div className="apidocs-table-wrap apidocs-future">
        <table className="apidocs-table">
          <thead>
            <tr>
              <th>Method</th>
              <th>Path</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {FUTURE_ENDPOINTS.map((ep) => (
              <tr key={ep.path} className="apidocs-future-row">
                <td>
                  <span className={`apidocs-method ${ep.method.toLowerCase()}`}>
                    {ep.method}
                  </span>
                </td>
                <td className="apidocs-path">
                  <code>{ep.path}</code>
                </td>
                <td className="apidocs-desc">{ep.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
