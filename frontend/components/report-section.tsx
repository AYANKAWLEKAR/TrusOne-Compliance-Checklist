import { ReactNode } from "react";

type ReportSectionProps = {
  title: string;
  description: string;
  children: ReactNode;
};

export function ReportSection({
  title,
  description,
  children,
}: ReportSectionProps) {
  return (
    <section
      style={{
        background: "var(--bg-panel)",
        border: "1px solid var(--border)",
        borderRadius: 24,
        padding: 24,
        boxShadow: "var(--shadow)",
        backdropFilter: "blur(10px)",
      }}
    >
      <div style={{ marginBottom: 18 }}>
        <h2 style={{ margin: "0 0 8px", fontSize: 28 }}>{title}</h2>
        <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.6 }}>
          {description}
        </p>
      </div>
      {children}
    </section>
  );
}
