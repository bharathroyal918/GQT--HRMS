import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { PlacementDrivesPage } from "../pages/interviews/PlacementDrivesPage";

vi.mock("../api/interviewsApi", () => ({
  interviewsApi: {
    getDrives: vi.fn().mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: "drive-1",
          drive_code: "DRV-2026-001",
          title: "Infosys Mega Recruitment Drive",
          job: "job-1",
          job_title: "Full Stack SDE",
          company_name: "Infosys Limited",
          drive_date: "2026-11-20T10:00:00Z",
          venue_or_link: "Virtual (Microsoft Teams)",
          drive_mode: "VIRTUAL",
          status: "SCHEDULED",
          coordinator_name: "Lead Coordinator",
          rounds_count: 3,
          created_at: "2026-11-01T10:00:00Z",
        },
      ],
    }),
    getSubmissions: vi.fn().mockResolvedValue({ count: 0, results: [] }),
    getOffers: vi.fn().mockResolvedValue({ count: 0, results: [] }),
  },
}));

describe("PlacementDrivesPage Component", () => {
  it("renders page header and scheduled drives table", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <PlacementDrivesPage />
        </BrowserRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText("Interviews, Drives & Placement Outcomes")).toBeDefined();
    expect(screen.getByText("Placement Drives & Rounds")).toBeDefined();

    // Verify scheduled drive rendered
    const driveTitle = await screen.findByText("Infosys Mega Recruitment Drive");
    expect(driveTitle).toBeDefined();

    const driveCode = await screen.findByText("DRV-2026-001");
    expect(driveCode).toBeDefined();
  });
});
