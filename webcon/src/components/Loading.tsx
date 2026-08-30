import "./Loading.css";

export function Loading({ message }: { message?: string }) {
  return (
    <div className="loading">
      <div className="loading-spinner" />
      {message ?? "Loading..."}
    </div>
  );
}
