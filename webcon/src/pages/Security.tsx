import { useEffect, useState, useCallback } from "react";
import { getHelp } from "../api/client";
import { Tag } from "../components/Tag";
import { Loading } from "../components/Loading";
import "./Security.css";

interface HelpData {
  command_policy?: {
    blocked_commands: string[];
    block_environment_variable: string;
    note: string;
  };
}

export function Security() {
  const [policy, setPolicy] = useState<HelpData["command_policy"] | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchPolicy = useCallback(async () => {
    try {
      const res = (await getHelp()) as unknown as { data: HelpData; status: number };
      if (res.status === 200 && res.data.command_policy) {
        setPolicy(res.data.command_policy);
      }
    } catch {
      // unavailable
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPolicy();
  }, [fetchPolicy]);

  if (loading) return <Loading message="Loading security policy..." />;

  const blocked = policy?.blocked_commands ?? [];

  return (
    <div>
      <h2 className="page-title">Security / Block</h2>

      <div className="security-section">
        <h3 className="section-title">Blocked Commands</h3>
        <p className="security-desc">
          These commands are blocked by the global command policy and cannot be
          executed through any command endpoint.
        </p>
        {blocked.length === 0 ? (
          <div className="security-empty">No commands are currently blocked.</div>
        ) : (
          <div className="security-tags">
            {blocked.map((cmd) => (
              <Tag key={cmd} label={cmd} variant="blocked" />
            ))}
          </div>
        )}
      </div>

      <div className="security-section">
        <h3 className="section-title">Configuration</h3>
        <div className="security-config">
          <div className="security-config-row">
            <span className="security-config-label">Environment Variable</span>
            <code>{policy?.block_environment_variable ?? "BLOCK"}</code>
          </div>
          <div className="security-config-row">
            <span className="security-config-label">Note</span>
            <span>{policy?.note ?? "—"}</span>
          </div>
        </div>
      </div>

      <div className="security-section">
        <h3 className="section-title">How It Works</h3>
        <ul className="security-info-list">
          <li>
            The <code>BLOCK</code> environment variable controls which commands
            are denied.
          </li>
          <li>
            <code>rm</code> is permanently blocked and cannot be removed from
            the policy.
          </li>
          <li>
            The policy applies to <code>/command</code>, <code>/file</code>,{" "}
            <code>/filepc</code>, <code>/commandpc</code>, and{" "}
            <code>/docker</code>.
          </li>
          <li>
            Shell nesting (e.g. <code>bash -c 'rm ...'</code>) is also detected.
          </li>
        </ul>
      </div>
    </div>
  );
}
