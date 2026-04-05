import { describe, expect, it, vi } from "vitest";

import { createComplianceReport, fetchComplianceOptions } from "./api";

describe("api client", () => {
  it("posts a compliance report request", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        summary: {
          analysis_text: "Mapped one task.",
          total_tasks: 1,
          completed_tasks: 0,
          open_tasks: 1,
          mapped_sources: ["OSHA"],
        },
        tasks: [],
        sources: [],
      }),
    });

    vi.stubGlobal("fetch", fetchMock);

    await createComplianceReport({
      location: "California",
      industry: "Chemical",
      company_size: "51-250",
    });

    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock.mock.calls[0]?.[0]).toContain("/api/compliance/report");
  });

  it("loads live compliance options", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        industries: ["Chemical"],
        locations: [
          {
            value: "Berkeley, California",
            display_label: "Berkeley, California",
            city: "Berkeley",
            county: "Alameda County",
            state: "California",
            aliases: ["Berkeley", "Berkeley, CA"],
          },
        ],
      }),
    });

    vi.stubGlobal("fetch", fetchMock);

    const response = await fetchComplianceOptions();

    expect(response.locations[0]?.city).toBe("Berkeley");
    expect(fetchMock.mock.calls[0]?.[0]).toContain("/api/compliance/options");
  });
});
