import { describe, expect, it, vi } from "vitest";

import { createComplianceReport } from "./api";

describe("api client", () => {
  it("posts a compliance report request", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        compliance_certification_requirements: [],
        regulatory_dependencies: [],
        required_documents: [],
        required_workflows: [],
        sources: [],
      }),
    });

    vi.stubGlobal("fetch", fetchMock);

    await createComplianceReport({
      location: "Oakland, CA",
      industry: "chemical manufacturing",
      company_size: "51-250",
    });

    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock.mock.calls[0]?.[0]).toContain("/api/compliance/report");
  });
});
