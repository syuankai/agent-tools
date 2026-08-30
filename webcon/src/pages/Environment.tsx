import { useEffect, useState, useCallback } from "react";
import { getEnv } from "../api/client";
import { Loading } from "../components/Loading";
import "./Environment.css";

interface EnvData {
  status: number;
  variables: Record<string, string>;
}

export function Environment() {
  const [env, setEnv] = useState<EnvData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showMasked, setShowMasked] = useState<Record<string, boolean>>({});

  const fetchEnv = useCallback(async () => {
    try {
      const res = (await getEnv()) as unknown as { data: EnvData; status: number };
      if (res.status === 200) {
        setEnv(res.data);
        setError(null);
      } else {
        setError("Unable to load environment variables");
      }
    } catch {
      setError("API unavailable");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEnv();
  }, [fetchEnv]);

  function toggleMask(key: string) {
    setShowMasked((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  if (loading) return <Loading message="Loading environment..." />;

  const vars = env?.variables ?? {};
  const entries = Object.entries(vars);

  return (
    <div>
      <h2 className="page-title">Environment</h2>
      {error && <div className="env-error">{error}</div>}
      {entries.length === 0 && !error && (
        <div className="env-empty">
          No environment variables available. Set <code>ENV_ALLOWLIST</code> in
          the backend to expose variables.
        </div>
      )}
      <div className="env-table-wrap">
        <table className="env-table">
          <thead>
            <tr>
              <th>Variable</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([key, value]) => {
              const isRedacted = value === "[REDACTED]";
              const revealed = showMasked[key];
              return (
                <tr key={key}>
                  <td className="env-key">{key}</td>
                  <td className="env-value">
                    {isRedacted && !revealed ? (
                      <span className="env-masked">
                        <span className="env-masked-text">••••••••</span>
                        <button
                          className="env-toggle"
                          onClick={() => toggleMask(key)}
                        >
                          Show
                        </button>
                      </span>
                    ) : (
                      <span className="env-plain">
                        <code>{value}</code>
                        {isRedacted && (
                          <button
                            className="env-toggle"
                            onClick={() => toggleMask(key)}
                          >
                            Hide
                          </button>
                        )}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
