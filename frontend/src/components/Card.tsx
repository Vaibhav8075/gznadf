import type { ReactNode } from "react";

interface Props {
  title: string;
  subtitle?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Card({ title, subtitle, children, className }: Props) {
  return (
    <section className={`card ${className ?? ""}`}>
      <header className="card-head">
        <h2>{title}</h2>
        {subtitle && <p className="muted">{subtitle}</p>}
      </header>
      {children}
    </section>
  );
}
