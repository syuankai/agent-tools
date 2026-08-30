import "./StatusBadge.css";

interface StatusBadgeProps {
  online: boolean;
  loading?: boolean;
  label?: string;
}

export function StatusBadge({ online, loading, label }: StatusBadgeProps) {
  const dotClass = loading ? "loading" : online ? "online" : "offline";
  const text = loading ? "Checking..." : online ? (label ?? "Online") : (label ?? "Offline");

  return (
    <span className="status-badge">
      <span className={`status-dot ${dotClass}`} />
      {text}
    </span>
  );
}
