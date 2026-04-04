import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import HomePage from "./page";
import {
  createComplianceReport,
  fetchComplianceOptions,
  resolveGeoIP,
} from "@/lib/api";

vi.mock("@/lib/api", () => ({
  createComplianceReport: vi.fn(),
  fetchComplianceOptions: vi.fn(),
  resolveGeoIP: vi.fn(),
}));

const mockedCreateComplianceReport = vi.mocked(createComplianceReport);
const mockedFetchComplianceOptions = vi.mocked(fetchComplianceOptions);
const mockedResolveGeoIP = vi.mocked(resolveGeoIP);

describe("HomePage", () => {
  it("renders the synthesized checklist, filters tasks, and opens the modal", async () => {
    mockedFetchComplianceOptions.mockResolvedValue({
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
    });
    mockedCreateComplianceReport.mockResolvedValue({
      summary: {
        analysis_text: "Two tasks mapped from OSHA and EPA.",
        total_tasks: 2,
        completed_tasks: 1,
        open_tasks: 1,
        mapped_sources: ["OSHA", "EPA"],
      },
      tasks: [
        {
          id: "maintain-sops",
          title: "Maintain SOPs",
          source: "OSHA",
          source_url: "https://example.com/sops",
          priority_label: "High Priority",
          meta_label: "Required by 29 CFR 1910.119",
          default_completed: true,
          citations: ["doc:1"],
          detail: {
            explanation: "Keep SOPs current.",
            next_step: "Review the current SOPs.",
            why_it_matters: "Inspectors expect to see them.",
            notes: "Store the approved version with revision history.",
          },
        },
        {
          id: "implement-training-management",
          title: "Implement Training Management",
          source: "EPA",
          source_url: "https://example.com/training",
          priority_label: "Standard",
          meta_label: "Ongoing workflow",
          default_completed: false,
          citations: ["doc:2"],
          detail: {
            explanation: "Operationalize the workflow.",
            next_step: "Assign an owner and cadence.",
            why_it_matters: "This proves the control is active.",
            notes: "Retain evidence of completions.",
          },
        },
      ],
      sources: [
        {
          source_id: "doc:1",
          source_type: "vector_document",
          title: "Doc 1",
        },
        {
          source_id: "doc:2",
          source_type: "vector_document",
          title: "Doc 2",
        },
      ],
    });
    mockedResolveGeoIP.mockResolvedValue({
      formatted_location: "Oakland, CA",
    });

    const user = userEvent.setup();
    render(<HomePage />);

    await user.click(screen.getByRole("button", { name: /Generate Analysis/i }));
    await user.type(screen.getByLabelText("Work Email"), "ops@example.com");
    await user.click(screen.getByRole("button", { name: /Generate Report/i }));

    expect(await screen.findByText("Maintain SOPs")).toBeInTheDocument();
    expect(screen.getByText("Two tasks mapped from OSHA and EPA.")).toBeInTheDocument();
    expect(screen.getByText("1 completed of 2")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Pending" }));
    expect(screen.queryByText("Maintain SOPs")).not.toBeInTheDocument();
    expect(screen.getByText("Implement Training Management")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "All" }));
    await user.click(screen.getByText("Implement Training Management"));

    expect(await screen.findByText("Requirement Detail")).toBeInTheDocument();
    expect(screen.getByText("Assign an owner and cadence.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Mark as Complete" }));

    await waitFor(() => {
      expect(screen.getByText("2 completed of 2")).toBeInTheDocument();
    });
  });
});
