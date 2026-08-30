import { useEffect, useState, useCallback } from "react";
import { executeFilepc } from "../api/client";
import { Loading } from "../components/Loading";
import type { CommandResult } from "../api/types";
import "./Files.css";

interface FileItem {
  name: string;
  is_dir: boolean;
  size: number;
  modified: string;
}

function formatSize(bytes: number): string {
  if (bytes === 0) return "—";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export function Files() {
  const [path, setPath] = useState("/userfile");
  const [items, setItems] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionResult, setActionResult] = useState<string | null>(null);
  const [mkdirName, setMkdirName] = useState("");

  const fetchFiles = useCallback(async (dir: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = (await executeFilepc(
        `ls -la "${dir}" 2>/dev/null | awk 'NR>1{print $1, $5, $6, $7, $8, $9}'`
      )) as unknown as CommandResult;
      if (res.status === 200 && res.output.trim()) {
        const parsed: FileItem[] = res.output
          .split("\n")
          .filter((l) => l.trim())
          .map((line) => {
            const parts = line.split(/\s+/);
            const perms = parts[0] ?? "";
            const size = parseInt(parts[1] ?? "0", 10);
            const name = parts[parts.length - 1] ?? "";
            return {
              name,
              is_dir: perms.startsWith("d"),
              size,
              modified: `${parts[2] ?? ""} ${parts[3] ?? ""} ${parts[4] ?? ""}`,
            };
          })
          .filter((f) => f.name && f.name !== "." && f.name !== "..");
        setItems(parsed);
      } else {
        setItems([]);
        if (res.output) setError(res.output);
      }
    } catch {
      setError("Unable to list files");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFiles(path);
  }, [path, fetchFiles]);

  function navigateTo(name: string) {
    const sep = path.endsWith("/") ? "" : "/";
    setPath(path + sep + name);
  }

  function goUp() {
    const parts = path.split("/").filter(Boolean);
    parts.pop();
    setPath("/" + parts.join("/"));
  }

  async function handleMkdir() {
    const name = mkdirName.trim();
    if (!name) return;
    setActionResult(null);
    try {
      const res = (await executeFilepc(
        `mkdir -p "${path}/${name}"`
      )) as unknown as CommandResult;
      if (res.status === 200) {
        setActionResult(`Created: ${name}`);
        setMkdirName("");
        fetchFiles(path);
      } else {
        setActionResult(`Error: ${res.output}`);
      }
    } catch (err) {
      setActionResult(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
    }
  }

  return (
    <div>
      <h2 className="page-title">Files</h2>

      <div className="files-toolbar">
        <div className="files-path">
          <button className="files-path-btn" onClick={() => setPath("/userfile")}>
            /userfile
          </button>
          {path
            .replace("/userfile", "")
            .split("/")
            .filter(Boolean)
            .map((segment, i, arr) => (
              <span key={i}>
                <span className="files-path-sep">/</span>
                <button
                  className="files-path-btn"
                  onClick={() =>
                    setPath(
                      "/userfile/" + arr.slice(0, i + 1).join("/")
                    )
                  }
                >
                  {segment}
                </button>
              </span>
            ))}
        </div>
        {path !== "/userfile" && (
          <button className="files-action-btn" onClick={goUp}>
            ↑ Up
          </button>
        )}
      </div>

      <div className="files-actions">
        <div className="files-mkdir">
          <input
            className="files-mkdir-input"
            value={mkdirName}
            onChange={(e) => setMkdirName(e.target.value)}
            placeholder="New folder name..."
            onKeyDown={(e) => e.key === "Enter" && handleMkdir()}
          />
          <button
            className="files-action-btn"
            onClick={handleMkdir}
            disabled={!mkdirName.trim()}
          >
            + Mkdir
          </button>
        </div>
        <div className="files-action-group">
          <button
            className="files-action-btn files-action-delete"
            disabled
            title="Delete is disabled by server security policy."
          >
            Delete
          </button>
          <span className="files-delete-hint">
            Delete is disabled by server security policy.
          </span>
        </div>
      </div>

      {actionResult && (
        <div
          className={`files-action-result ${actionResult.startsWith("Error") ? "error" : "ok"}`}
        >
          {actionResult}
        </div>
      )}

      {error && <div className="files-error">{error}</div>}

      {loading ? (
        <Loading message="Loading files..." />
      ) : items.length === 0 ? (
        <div className="files-empty">This directory is empty.</div>
      ) : (
        <div className="files-table-wrap">
          <table className="files-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Size</th>
                <th>Modified</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.name}
                  className={item.is_dir ? "files-row-dir" : "files-row-file"}
                  onClick={() => item.is_dir && navigateTo(item.name)}
                >
                  <td className="files-name">
                    <span className="files-icon">
                      {item.is_dir ? "📁" : "📄"}
                    </span>
                    {item.name}
                  </td>
                  <td className="files-size">
                    {item.is_dir ? "—" : formatSize(item.size)}
                  </td>
                  <td className="files-modified">{item.modified}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="files-info">
        <h4 className="files-info-title">API Mapping</h4>
        <table className="files-api-map">
          <tbody>
            <tr>
              <td>List / Navigate</td>
              <td><code>POST /filepc</code></td>
              <td><code>ls -la &lt;path&gt;</code></td>
              <td className="files-api-status ok">Available</td>
            </tr>
            <tr>
              <td>Mkdir</td>
              <td><code>POST /filepc</code></td>
              <td><code>mkdir -p &lt;path&gt;</code></td>
              <td className="files-api-status ok">Available</td>
            </tr>
            <tr>
              <td>Delete</td>
              <td colSpan={2}>Disabled by server security policy</td>
              <td className="files-api-status blocked">Disabled</td>
            </tr>
            <tr>
              <td>Download</td>
              <td colSpan={2}>Needs new backend endpoint</td>
              <td className="files-api-status pending">Planned</td>
            </tr>
            <tr>
              <td>Upload</td>
              <td colSpan={2}>Needs new backend endpoint (multipart)</td>
              <td className="files-api-status pending">Planned</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
