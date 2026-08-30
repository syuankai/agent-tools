import { useEffect, useState, useCallback } from "react";
import { executeCommand, downloadFile } from "../api/client";
import { Loading } from "../components/Loading";
import type { CommandResult } from "../api/types";
import "./Downloads.css";

interface FileItem {
  name: string;
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

export function Downloads() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [downloadResult, setDownloadResult] = useState<string | null>(null);

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    try {
      const res = (await executeCommand(
        "ls -la /aifile 2>/dev/null | awk 'NR>1{print $5, $6, $7, $8, $9}'"
      )) as unknown as CommandResult;
      if (res.status === 200 && res.output.trim()) {
        const parsed: FileItem[] = res.output
          .split("\n")
          .filter((l) => l.trim())
          .map((line) => {
            const parts = line.split(/\s+/);
            return {
              name: parts[parts.length - 1] ?? "",
              size: parseInt(parts[0] ?? "0", 10),
              modified: `${parts[1] ?? ""} ${parts[2] ?? ""} ${parts[3] ?? ""}`,
            };
          })
          .filter((f) => f.name && f.name !== "." && f.name !== "..");
        setFiles(parsed);
        setError(null);
      } else {
        setFiles([]);
        if (res.output) setError(res.output);
      }
    } catch {
      setError("Unable to list files");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  async function handleDownload() {
    if (!downloadUrl.trim()) return;
    setDownloading(true);
    setDownloadResult(null);
    try {
      const res = (await downloadFile(downloadUrl.trim())) as unknown as CommandResult;
      if (res.status === 200) {
        setDownloadResult(`Downloaded: ${res.output}`);
        setDownloadUrl("");
        fetchFiles();
      } else {
        setDownloadResult(`Error: ${res.output}`);
      }
    } catch (err) {
      setDownloadResult(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div>
      <h2 className="page-title">Downloads</h2>

      <div className="dl-section">
        <h3 className="section-title">Download URL</h3>
        <div className="dl-input-row">
          <input
            className="dl-input"
            value={downloadUrl}
            onChange={(e) => setDownloadUrl(e.target.value)}
            placeholder="https://example.com/file.zip"
            disabled={downloading}
          />
          <button
            className="dl-btn"
            onClick={handleDownload}
            disabled={downloading || !downloadUrl.trim()}
          >
            {downloading ? "Downloading..." : "Download"}
          </button>
        </div>
        {downloadResult && (
          <div
            className={`dl-result ${downloadResult.startsWith("Error") ? "error" : "ok"}`}
          >
            {downloadResult}
          </div>
        )}
      </div>

      <h3 className="section-title">Files in /aifile</h3>
      {loading ? (
        <Loading message="Loading files..." />
      ) : error ? (
        <div className="dl-error">{error}</div>
      ) : files.length === 0 ? (
        <div className="dl-empty">No files in /aifile yet.</div>
      ) : (
        <div className="dl-table-wrap">
          <table className="dl-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Size</th>
                <th>Modified</th>
              </tr>
            </thead>
            <tbody>
              {files.map((f) => (
                <tr key={f.name}>
                  <td className="dl-name">
                    <span className="dl-icon">📄</span>
                    {f.name}
                  </td>
                  <td className="dl-size">{formatSize(f.size)}</td>
                  <td className="dl-modified">{f.modified}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
