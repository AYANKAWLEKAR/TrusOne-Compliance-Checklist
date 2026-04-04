type CitationPillProps = {
  citation: string;
};

export function CitationPill({ citation }: CitationPillProps) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "4px 10px",
        borderRadius: 999,
        background: "rgba(10, 108, 116, 0.1)",
        color: "var(--accent-strong)",
        fontSize: 12,
        fontWeight: 700,
        letterSpacing: "0.03em",
      }}
    >
      {citation}
    </span>
  );
}
