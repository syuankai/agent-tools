import "./Card.css";

interface CardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

export function Card({ title, children, className }: CardProps) {
  return (
    <div className={`card ${className ?? ""}`}>
      <h3 className="card-title">{title}</h3>
      {children}
    </div>
  );
}
