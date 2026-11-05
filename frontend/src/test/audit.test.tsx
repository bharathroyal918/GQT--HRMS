import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { AuditLogViewerPage } from "../pages/audit/AuditLogViewerPage";

vi.mock("../api/auditApi", () => ({
  auditApi: {
    getAuditSummary: vi.fn().mockResolvedValue({
      total_count: 142,
      today_count: 18,
      unique_actors: 6,
      unique_resource_types: 4,
      top_actions: [{ action: "JOB_REQUIREMENT_APPROVED", count: 12 }],
      recent_critical_actions: [{ action: "JOB_REQUIREMENT_APPROVED", count: 12 }],
    }),
    getAuditLogs: vi.fn().mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: "log-1",
          user: { id: "u-1", email: "admin@gqt.local", full_name: "Admin User" },
          action: "JOB_REQUIREMENT_APPROVED",
          resource_type: "JobRequirement",
          resource_id: "job-1234",
          ip_address: "127.0.0.1",
          user_agent: "Mozilla/5.0",
          changes: { status: ["PENDING_APPROVAL", "APPROVED"] },
          correlation_id: "corr-111",
          created_at: "2026-11-05T08:00:00Z",
        },
        {
          id: "log-2",
          user: null,
          action: "SECURITY_ALERT",
          resource_type: "System",
          resource_id: "sys-warn",
          ip_address: "10.0.0.1",
          user_agent: "HealthBot",
          changes: {},
          correlation_id: "corr-222",
          created_at: "2026-11-05T08:30:00Z",
        },
      ],
    }),
    exportAuditCsvUrl: vi.fn().mockReturnValue("/api/v1/audit-logs/export/"),
  },
}));

describe("AuditLogViewerPage Component", () => {
  it("renders page header and metric KPI summaries", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuditLogViewerPage />
        </BrowserRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText("Audit Logs & Compliance Oversight")).toBeDefined();
    expect(screen.getByPlaceholderText(/Search by action/i)).toBeDefined();

    // Verify audit log item rendered
    const actionCell = await screen.findByText("JOB_REQUIREMENT_APPROVED");
    expect(actionCell).toBeDefined();

    const systemCell = await screen.findByText("SYSTEM");
    expect(systemCell).toBeDefined();
  });
});
