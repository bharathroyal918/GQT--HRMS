import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "../context/AuthContext";
import { CreativeStatusBadge } from "../components/creatives/CreativeStatusBadge";
import { DesignChecklistCard } from "../components/creatives/DesignChecklistCard";
import { VersionReviewModal } from "../components/creatives/VersionReviewModal";
import { CreativeStudioDashboardPage } from "../pages/creatives/CreativeStudioDashboardPage";
import { CreativeDirectoryPage } from "../pages/creatives/CreativeDirectoryPage";
import {
  CreativeAssetVersion,
  DesignComplianceCheck,
  CreativeRequestListItem,
} from "../types/creatives";

// Mock creativesApi
vi.mock("../api/creativesApi", () => ({
  creativesApi: {
    getStudioMetrics: vi.fn().mockResolvedValue({
      total_requests: 18,
      triage_queue_count: 3,
      in_design_count: 5,
      in_review_count: 4,
      approved_count: 4,
      ready_for_handoff_count: 2,
      total_asset_versions: 25,
      pending_versions_review: 4,
    }),
    getRequests: vi.fn().mockResolvedValue({
      count: 1,
      results: [
        {
          id: "req-1111-2222",
          request_code: "CR-2026-0001",
          title: "Apex Cloud Campus Hiring Flyer",
          creative_type: "JOB_FLYER",
          aspect_ratio: "4:5",
          deliverable_format: "PNG",
          priority: "HIGH",
          status: "IN_REVIEW",
          target_completion_date: "2026-11-25",
          job_requirement: "job-1111",
          job_title: "Graduate Cloud Engineer",
          company: "comp-1111",
          company_name: "Apex Cloud Technologies",
          created_by: "user-111",
          created_by_name: "John Officer",
          assigned_designer: "user-222",
          assigned_designer_name: "Alex Designer",
          active_version_number: 1,
          versions_count: 1,
          created_at: "2026-11-01T10:00:00Z",
          updated_at: "2026-11-01T10:00:00Z",
        } as CreativeRequestListItem,
      ],
    }),
    getAssetDownloadUrl: (id: string) => `/api/v1/creatives/versions/${id}/download/`,
  },
}));

const mockChecks: DesignComplianceCheck[] = [
  {
    id: "check-1",
    check_type: "FLYER_TEXT_ACCURACY",
    check_type_display: "Job Title, CTC & Eligibility Accuracy",
    status: "PASSED",
    notes: "CTC numbers verified.",
    verified_by: "user-333",
    verified_by_name: "Jane Reviewer",
    verified_at: "2026-11-02T10:00:00Z",
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-02T10:00:00Z",
  },
  {
    id: "check-2",
    check_type: "BRAND_ASSETS_COMPLIANCE",
    check_type_display: "Official GQT & Company Brand Assets",
    status: "PASSED",
    notes: "Official high-res logos used.",
    verified_by: "user-333",
    verified_by_name: "Jane Reviewer",
    verified_at: "2026-11-02T10:00:00Z",
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-02T10:00:00Z",
  },
  {
    id: "check-3",
    check_type: "QR_CODE_INTEGRITY",
    check_type_display: "QR Code Routing & Link Validation",
    status: "PASSED",
    notes: "Scanned QR code leads to portal.",
    verified_by: "user-333",
    verified_by_name: "Jane Reviewer",
    verified_at: "2026-11-02T10:00:00Z",
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-02T10:00:00Z",
  },
  {
    id: "check-4",
    check_type: "CONTACT_DISCLOSURE",
    check_type_display: "Recruiter Contact & Zero-Fee Placement Policy",
    status: "PENDING",
    notes: "",
    verified_by: null,
    verified_by_name: "",
    verified_at: null,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
  },
];

const mockVersion: CreativeAssetVersion = {
  id: "ver-1111",
  version_number: 1,
  original_filename: "apex_flyer_v1.png",
  file_size_bytes: 2048576,
  mime_type: "image/png",
  sha256_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  width: 1080,
  height: 1350,
  designer_notes: "Initial deliverable draft with gradient background.",
  status: "SUBMITTED_FOR_REVIEW",
  uploader: "designer-111",
  uploader_name: "Alex Designer",
  reviewed_by: null,
  reviewed_by_name: "",
  reviewed_at: null,
  review_feedback: "",
  compliance_checks: mockChecks,
  all_checks_passed: false,
  created_at: "2026-11-01T10:00:00Z",
};

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>{ui}</BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

describe("Phase 4 Creative Studio & Asset Approval Frontend", () => {
  it("renders CreativeStatusBadge with correct status label and styling", () => {
    const { rerender } = render(<CreativeStatusBadge status="IN_REVIEW" />);
    expect(screen.getByText("Under Review")).toBeInTheDocument();

    rerender(<CreativeStatusBadge status="APPROVED" />);
    expect(screen.getByText("Approved")).toBeInTheDocument();

    rerender(<CreativeStatusBadge status="READY_FOR_HANDOFF" />);
    expect(screen.getByText("Ready for Handoff")).toBeInTheDocument();
  });

  it("renders DesignChecklistCard with 3/4 passed checks and evaluate button", () => {
    const handleEvaluate = vi.fn();
    render(
      <DesignChecklistCard
        checks={mockChecks}
        canReview={true}
        onEvaluateCheck={handleEvaluate}
      />
    );

    expect(screen.getByText("4-Point Design Compliance Gate")).toBeInTheDocument();
    expect(screen.getByText("3 / 4 Passed")).toBeInTheDocument();
    expect(screen.getByText("1. Job Title, CTC & Eligibility Accuracy")).toBeInTheDocument();
    expect(screen.getByText("2. Official GQT & Corporate Brand Assets")).toBeInTheDocument();
    expect(screen.getByText("3. QR Code Routing & Link Validation")).toBeInTheDocument();
    expect(screen.getByText("4. Recruiter Contact & Zero-Fee Disclaimer")).toBeInTheDocument();
  });

  it("VersionReviewModal alerts on Segregation of Duties if current user is the uploader", () => {
    const handleApprove = vi.fn();
    const handleChanges = vi.fn();

    render(
      <VersionReviewModal
        version={mockVersion}
        isOpen={true}
        onClose={vi.fn()}
        onApprove={handleApprove}
        onRequestChanges={handleChanges}
        currentUserId="designer-111" // Submitter match!
      />
    );

    expect(screen.getByText(/Segregation of Duties Warning:/i)).toBeInTheDocument();
    const approveBtn = screen.getByRole("button", { name: /Confirm Asset Approval/i });
    expect(approveBtn).toBeDisabled();
  });

  it("renders CreativeStudioDashboardPage with metric cards and recent requests", async () => {
    renderWithProviders(<CreativeStudioDashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Creative Studio & Design Operations")).toBeInTheDocument();
      expect(screen.getByText("Total Requisitions")).toBeInTheDocument();
      expect(screen.getByText("18")).toBeInTheDocument();
      expect(screen.getByText("CR-2026-0001")).toBeInTheDocument();
      expect(screen.getByText("Apex Cloud Campus Hiring Flyer")).toBeInTheDocument();
    });
  });

  it("renders CreativeDirectoryPage with search bar and requisitions table", async () => {
    renderWithProviders(<CreativeDirectoryPage />);

    await waitFor(() => {
      expect(screen.getByText("Creative Requisition Directory")).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/search code, title, brief, company/i)).toBeInTheDocument();
      expect(screen.getByText("CR-2026-0001")).toBeInTheDocument();
      expect(screen.getByText("Apex Cloud Technologies")).toBeInTheDocument();
    });
  });
});

