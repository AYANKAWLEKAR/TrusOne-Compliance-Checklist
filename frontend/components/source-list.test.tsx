import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { SourceList } from "./source-list";

describe("SourceList", () => {
  it("renders provided sources", () => {
    render(
      <SourceList
        sources={[
          {
            source_id: "doc:1",
            source_type: "vector_document",
            title: "PSM Standard",
            url: "https://example.com",
            excerpt: "Excerpt",
          },
        ]}
      />,
    );

    expect(screen.getByText("PSM Standard")).toBeInTheDocument();
    expect(screen.getByText(/doc:1/)).toBeInTheDocument();
  });
});
