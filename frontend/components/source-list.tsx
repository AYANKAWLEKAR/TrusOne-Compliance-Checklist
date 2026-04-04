import React from "react";

import { SourceCitation } from "@/lib/types";

export function SourceList({ sources }: { sources: SourceCitation[] }) {
  return (
    <div
      style={{
        background: "rgba(255,255,255,0.58)",
        border: "1px solid var(--border)",
        borderRadius: 20,
        padding: 20,
      }}
    >
      <h3 style={{ marginTop: 0 }}>Sources</h3>
      <div style={{ display: "grid", gap: 14 }}>
        {sources.map((source) => (
          <article
            key={source.source_id}
            style={{
              paddingBottom: 14,
              borderBottom: "1px solid rgba(31, 26, 23, 0.08)",
            }}
          >
            <div style={{ fontWeight: 700 }}>{source.title}</div>
            <div style={{ fontSize: 13, color: "var(--muted)" }}>
              {source.source_id} • {source.source_type}
            </div>
            {source.excerpt ? (
              <p style={{ marginBottom: 8, color: "var(--muted)" }}>
                {source.excerpt}
              </p>
            ) : null}
            {source.url ? (
              <a href={source.url} target="_blank" rel="noreferrer">
                View source
              </a>
            ) : null}
          </article>
        ))}
      </div>
    </div>
  );
}
