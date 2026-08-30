import "./Tag.css";

interface TagProps {
  label: string;
  variant?: "default" | "blocked";
  onRemove?: () => void;
}

export function Tag({ label, variant, onRemove }: TagProps) {
  return (
    <span className={`tag ${variant ?? ""}`}>
      {label}
      {onRemove && (
        <button className="tag-remove" onClick={onRemove} aria-label={`Remove ${label}`}>
          ×
        </button>
      )}
    </span>
  );
}
