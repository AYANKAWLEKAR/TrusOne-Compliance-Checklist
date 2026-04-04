"use client";

import { FormEvent, useState } from "react";

import { CitationPill } from "@/components/citation-pill";
import { ReportSection } from "@/components/report-section";
import { SourceList } from "@/components/source-list";
import { createComplianceReport, resolveGeoIP } from "@/lib/api";
import { ComplianceReportResponse } from "@/lib/types";

const companySizes = ["1-10", "11-50", "51-250", "251-1000", "1000+"];

export default function HomePage() {
  const [location, setLocation] = useState("");
  const [industry, setIndustry] = useState("");
  const [companySize, setCompanySize] = useState(companySizes[2]);
  const [report, setReport] = useState<ComplianceReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAutoDetecting, setIsAutoDetecting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await createComplianceReport({
        location,
        industry,
        company_size: companySize,
      });
      setReport(response);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Unable to generate report.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function onAutoDetect() {
    setError(null);
    setIsAutoDetecting(true);
    try {
      const response = await resolveGeoIP();
      setLocation(response.formatted_location);
    } catch (geoError) {
      setError(
        geoError instanceof Error
          ? geoError.message
          : "Unable to auto-detect location.",
      );
    } finally {
      setIsAutoDetecting(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        padding: "48px 20px 80px",
      }}
    >
      <div
        style={{
          maxWidth: 1180,
          margin: "0 auto",
          display: "grid",
          gap: 28,
        }}
      >
        <section
          style={{
            display: "grid",
            gap: 18,
            padding: 32,
            borderRadius: 28,
            background:
              "linear-gradient(135deg, rgba(255,255,255,0.72), rgba(255,246,235,0.86))",
            border: "1px solid var(--border)",
            boxShadow: "var(--shadow)",
          }}
        >
          <div>
            <p
              style={{
                margin: "0 0 8px",
                color: "var(--accent-strong)",
                fontSize: 13,
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                fontWeight: 700,
              }}
            >
              Chemical Compliance MVP
            </p>
            <h1 style={{ margin: 0, fontSize: "clamp(2.5rem, 4vw, 4.4rem)" }}>
              Structured regulatory guidance for chemical operations.
            </h1>
          </div>

          <p
            style={{
              margin: 0,
              maxWidth: 760,
              color: "var(--muted)",
              lineHeight: 1.7,
              fontSize: 18,
            }}
          >
            Enter a company profile and generate a four-part compliance report
            with requirements, dependencies, document obligations, workflow
            expectations, and source citations.
          </p>

          <form
            onSubmit={onSubmit}
            style={{
              display: "grid",
              gap: 18,
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              alignItems: "end",
            }}
          >
            <label style={{ display: "grid", gap: 8 }}>
              <span style={{ fontWeight: 700 }}>Location</span>
              <input
                value={location}
                onChange={(event) => setLocation(event.target.value)}
                placeholder="Oakland, CA or 94607"
                required
                style={inputStyle}
              />
            </label>

            <label style={{ display: "grid", gap: 8 }}>
              <span style={{ fontWeight: 700 }}>Industry</span>
              <input
                value={industry}
                onChange={(event) => setIndustry(event.target.value)}
                placeholder="chemical manufacturing"
                required
                style={inputStyle}
              />
            </label>

            <label style={{ display: "grid", gap: 8 }}>
              <span style={{ fontWeight: 700 }}>Company size</span>
              <select
                value={companySize}
                onChange={(event) => setCompanySize(event.target.value)}
                style={inputStyle}
              >
                {companySizes.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </label>

            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <button type="submit" disabled={isSubmitting} style={primaryButtonStyle}>
                {isSubmitting ? "Generating..." : "Generate report"}
              </button>
              <button
                type="button"
                onClick={onAutoDetect}
                disabled={isAutoDetecting}
                style={secondaryButtonStyle}
              >
                {isAutoDetecting ? "Detecting..." : "Auto-detect location"}
              </button>
            </div>
          </form>

          {error ? (
            <div
              style={{
                padding: 14,
                borderRadius: 16,
                background: "rgba(180, 60, 47, 0.08)",
                border: "1px solid rgba(180, 60, 47, 0.2)",
                color: "var(--danger)",
              }}
            >
              {error}
            </div>
          ) : null}
        </section>

        {!report ? (
          <section
            style={{
              padding: 28,
              borderRadius: 24,
              border: "1px dashed rgba(31, 26, 23, 0.18)",
              color: "var(--muted)",
              background: "rgba(255, 255, 255, 0.45)",
            }}
          >
            Submit a company profile to render the structured compliance report.
          </section>
        ) : (
          <div style={{ display: "grid", gap: 24 }}>
            <ReportSection
              title="Compliance and Certification Requirements"
              description="Applicable regulations and certification-oriented clauses mapped to business activities."
            >
              <SectionList>
                {report.compliance_certification_requirements.map((item) => (
                  <li key={`${item.regulation_id}-${item.business_activity}`} style={cardStyle}>
                    <div style={titleRowStyle}>
                      <strong>{item.regulation_id}</strong>
                      <CitationRow citations={item.citations} />
                    </div>
                    <p style={bodyCopyStyle}>{item.certification_clause}</p>
                    <div style={metaCopyStyle}>Mapped activity: {item.business_activity}</div>
                  </li>
                ))}
              </SectionList>
            </ReportSection>

            <ReportSection
              title="Regulatory Dependencies"
              description="Agency and program relationships that shape compliance scope."
            >
              <SectionList>
                {report.regulatory_dependencies.map((item) => (
                  <li key={`${item.primary_agency}-${item.related_agency}`} style={cardStyle}>
                    <div style={titleRowStyle}>
                      <strong>
                        {item.primary_agency} → {item.related_agency}
                      </strong>
                      <CitationRow citations={item.citations} />
                    </div>
                    <p style={bodyCopyStyle}>{item.relationship}</p>
                  </li>
                ))}
              </SectionList>
            </ReportSection>

            <ReportSection
              title="Required Documents"
              description="Documentation the facility should maintain, along with the source requirement."
            >
              <SectionList>
                {report.required_documents.map((item) => (
                  <li key={`${item.document_type}-${item.required_by}`} style={cardStyle}>
                    <div style={titleRowStyle}>
                      <strong>{item.document_type}</strong>
                      <CitationRow citations={item.citations} />
                    </div>
                    <p style={bodyCopyStyle}>{item.description}</p>
                    <div style={metaCopyStyle}>Required by: {item.required_by}</div>
                  </li>
                ))}
              </SectionList>
            </ReportSection>

            <ReportSection
              title="Required Workflows"
              description="Operational processes the company should implement and maintain."
            >
              <SectionList>
                {report.required_workflows.map((item) => (
                  <li key={`${item.workflow_name}-${item.frequency}`} style={cardStyle}>
                    <div style={titleRowStyle}>
                      <strong>{item.workflow_name}</strong>
                      <CitationRow citations={item.citations} />
                    </div>
                    <p style={bodyCopyStyle}>{item.description}</p>
                    <div style={metaCopyStyle}>
                      {item.frequency} • {item.responsible_party}
                    </div>
                  </li>
                ))}
              </SectionList>
            </ReportSection>

            <SourceList sources={report.sources} />
          </div>
        )}
      </div>
    </main>
  );
}

function SectionList({ children }: { children: React.ReactNode }) {
  return (
    <ul
      style={{
        listStyle: "none",
        margin: 0,
        padding: 0,
        display: "grid",
        gap: 16,
      }}
    >
      {children}
    </ul>
  );
}

function CitationRow({ citations }: { citations: string[] }) {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {citations.map((citation) => (
        <CitationPill key={citation} citation={citation} />
      ))}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  minHeight: 52,
  borderRadius: 16,
  border: "1px solid rgba(31, 26, 23, 0.16)",
  padding: "0 16px",
  background: "rgba(255,255,255,0.74)",
};

const primaryButtonStyle: React.CSSProperties = {
  minHeight: 52,
  borderRadius: 16,
  border: "none",
  padding: "0 18px",
  background: "var(--accent)",
  color: "white",
  fontWeight: 700,
  cursor: "pointer",
};

const secondaryButtonStyle: React.CSSProperties = {
  minHeight: 52,
  borderRadius: 16,
  border: "1px solid rgba(31, 26, 23, 0.16)",
  padding: "0 18px",
  background: "rgba(255,255,255,0.64)",
  color: "var(--ink)",
  fontWeight: 700,
  cursor: "pointer",
};

const cardStyle: React.CSSProperties = {
  borderRadius: 18,
  border: "1px solid rgba(31, 26, 23, 0.08)",
  padding: 18,
  background: "rgba(255,255,255,0.64)",
};

const titleRowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  alignItems: "center",
  flexWrap: "wrap",
};

const bodyCopyStyle: React.CSSProperties = {
  margin: "12px 0 8px",
  lineHeight: 1.7,
  color: "var(--muted)",
};

const metaCopyStyle: React.CSSProperties = {
  fontSize: 14,
  color: "var(--ink)",
  fontWeight: 600,
};
