import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "../context/AuthContext";
import { VerificationChecklistCard } from "../components/jobs/VerificationChecklistCard";
import { ApprovalModal } from "../components/jobs/ApprovalModal";
import { UpdateCheckModal } from "../components/jobs/UpdateCheckModal";
import { JobDirectoryPage } from "../pages/jobs/JobDirectoryPage";
import { JobVerificationCheck, JobRequirementDetail } from "../types/jobs";

// Mock jobsApi
vi.mock("../api/jobsApi", () => ({
  jobsApi: {
    getJobs: vi.fn().mockResolvedValue({
      count: 1,
      results: [
        {
          id: "job-1111-2222",
          company: "comp-1111",
          company_name: "Apex Cloud Systems",
          company_canonical_domain: "apexcloud.io",
          title: "Graduate Software Engineer",
          role_category: "SOFTWARE_ENGINEERING",
          job_location: "Bengaluru",
          work_arrangement: "HYBRID",
          min_ctc_lpa: "6.50",
          max_ctc_lpa: "9.00",
          vacancies_count: 10,
          registration_deadline: "2026-12-01T18:00:00Z",
          interview_date: "2026-12-10",
          status: "PENDING_APPROVAL",
          revision_number: 1,
          submitted_by: "user-111",
          submitted_by_name: "John Officer",
          assigned_verifier: "user-222",
          assigned_verifier_name: "Alice Verifier",
          verification_summary: {
            total_mandatory_checks: 5,
            verified_count: 5,
            flagged_count: 0,
            rejected_count: 0,
            pending_count: 0,
            is_all_verified: true,
          },
          created_at: "2026-11-01T10:00:00Z",
          updated_at: "2026-11-01T10:00:00Z",
        },
      ],
    }),
    getWorkflowMetrics: vi.fn().mockResolvedValue({
      total_jobs: 12,
      draft_jobs: 2,
      pending_verification_jobs: 3,
      under_verification_jobs: 1,
      changes_requested_jobs: 1,
      pending_approval_jobs: 2,
      approved_jobs: 3,
      rejected_jobs: 0,
      verification_stats: {
        total_checks: 60,
        verified_checks: 45,
        pending_checks: 10,
        flagged_checks: 3,
        rejected_checks: 2,
      },
    }),
  },
}));

const mockChecks: JobVerificationCheck[] = [
  {
    id: "check-1",
    check_type: "ELIGIBILITY",
    status: "VERIFIED",
    verified_by: "user-1",
    verified_by_name: "Alice Reviewer",
    verified_by_email: "alice@gqt.test",
    verified_at: "2026-11-02T10:00:00Z",
    notes: "Meets 6.50 CGPA norms.",
    evidence_reference: "GQT-ACAD-2025",
    requires_reverification: false,
    invalidation_reason: "",
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-02T10:00:00Z",
  },
  {
    id: "check-2",
    check_type: "SALARY_AUTHENTICITY",
    status: "VERIFIED",
    verified_by: "user-1",
    verified_by_name: "Alice Reviewer",
    verified_by_email: "alice@gqt.test",
    verified_at: "2026-11-02T10:00:00Z",
    notes: "Verified with prior batch offer letter.",
    evidence_reference: "OFFER-2024-APEX",
    requires_reverification: false,
    invalidation_reason: "",
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-02T10:00:00Z",
  },
  {
    id: "check-3",
    check_type: "COMPANY_AUTHENTICITY",
    status: "VERIFIED",
    verified_by: "user-1",
    verified_by_name: "Alice Reviewer",
    verified_by_email: "alice@gqt.test",
    verified_at: "2026-11-02T10:00:00Z",
    notes: "Active CIN and domain match.",
    evidence_reference: "CIN-U72200KA2015PTC",
    requires_reverification: false,
    invalidation_reason: "",
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-02T10:00:00Z",
  },
  {
    id: "check-4",
    check_type: "INTERVIEW_PROCESS",
    status: "VERIFIED",
    verified_by: "user-1",
    verified_by_name: "Alice Reviewer",
    verified_by_email: "alice@gqt.test",
    verified_at: "2026-11-02T10:00:00Z",
    notes: "No fee disclosure confirmed.",
    evidence_reference: "HR-CONFIRMATION-EMAIL",
    requires_reverification: false,
    invalidation_reason: "",
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-02T10:00:00Z",
  },
  {
    id: "check-5",
    check_type: "REGISTRATION_DEADLINE",
    status: "PENDING",
    verified_by: null,
    verified_by_name: "",
    verified_by_email: "",
    verified_at: null,
    notes: "",
    evidence_reference: "",
    requires_reverification: false,
    invalidation_reason: "",
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
  },
];

const mockJobDetail: JobRequirementDetail = {
  id: "job-1111-2222",
  company: "comp-1111",
  company_name: "Apex Cloud Systems",
  company_canonical_domain: "apexcloud.io",
  company_industry: "CLOUD_COMPUTING",
  title: "Graduate Software Engineer",
  description: "Core backend engineering with Python.",
  role_category: "SOFTWARE_ENGINEERING",
  required_skills: ["Python", "Django", "PostgreSQL"],
  min_cgpa: "6.50",
  min_percentage: "60.00",
  eligible_batches: ["2025"],
  eligible_branches: ["CSE", "ISE"],
  max_backlogs_allowed: 0,
  min_ctc_lpa: "6.50",
  max_ctc_lpa: "9.00",
  stipend_amount: null,
  salary_details: "Fixed CTC 7.0 LPA + 2.0 LPA bonus",
  job_location: "Bengaluru",
  work_arrangement: "HYBRID",
  has_bond: false,
  bond_duration_months: null,
  bond_details: "",
  interview_rounds: [],
  interview_process_notes: "Aptitude -> Tech -> HR",
  interview_date: "2026-12-10",
  registration_deadline: "2026-12-01T18:00:00Z",
  vacancies_count: 10,
  status: "PENDING_APPROVAL",
  revision_number: 1,
  submitted_by: "user-111",
  submitted_by_name: "John Officer",
  submitted_by_email: "john@gqt.test",
  assigned_verifier: "user-222",
  assigned_verifier_name: "Alice Verifier",
  assigned_verifier_email: "alice@gqt.test",
  approved_by: null,
  approved_by_name: "",
  approved_at: null,
  rejected_by: null,
  rejected_by_name: "",
  rejected_at: null,
  rejection_reason: "",
  changes_requested_reason: "",
  verification_checks: mockChecks,
  workflow_history: [],
  is_all_checks_verified: false,
  verification_summary: {
    total_mandatory_checks: 5,
    verified_count: 4,
    flagged_count: 0,
    rejected_count: 0,
    pending_count: 1,
    is_all_verified: false,
  },
  created_at: "2026-11-01T10:00:00Z",
  updated_at: "2026-11-01T10:00:00Z",
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

describe("Phase 3 Job Requirements & 5-Point Verification Frontend", () => {
  it("renders VerificationChecklistCard with 4/5 verified checks and progress indicator", () => {
    const handleUpdate = vi.fn();
    render(
      <VerificationChecklistCard
        checks={mockChecks}
        canVerify={true}
        isJobLocked={false}
        onUpdateCheck={handleUpdate}
      />
    );

    expect(screen.getByText("5-Point Verification Checklist")).toBeInTheDocument();
    expect(screen.getByText("4 / 5 Verified")).toBeInTheDocument();
    expect(screen.getByText("1. Candidate Eligibility Compliance")).toBeInTheDocument();
    expect(screen.getByText("2. Salary Authenticity & Plausibility")).toBeInTheDocument();
    expect(screen.getByText("3. Corporate Legitimacy & Recruiter Identity")).toBeInTheDocument();
    expect(screen.getByText("4. Interview Process & Fee Disclosure")).toBeInTheDocument();
    expect(screen.getByText("5. Application Deadline Validity")).toBeInTheDocument();
  });

  it("ApprovalModal alerts on Segregation of Duties if current user is the submitter", () => {
    const handleConfirm = vi.fn();
    render(
      <ApprovalModal
        job={mockJobDetail}
        isOpen={true}
        onClose={vi.fn()}
        onConfirm={handleConfirm}
        currentUserId="user-111" // Submitter match!
      />
    );

    expect(screen.getByText(/Segregation of Duties Warning:/i)).toBeInTheDocument();
    const confirmBtn = screen.getByRole("button", { name: /Confirm Approval/i });
    expect(confirmBtn).toBeDisabled();
  });

  it("UpdateCheckModal validates that flagged or rejected checks require notes", async () => {
    const handleSubmit = vi.fn();
    render(
      <UpdateCheckModal
        check={mockChecks[0] ?? null}
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={handleSubmit}
      />
    );

    // Click FLAGGED button
    const flaggedBtn = screen.getByRole("button", { name: "FLAGGED" });
    fireEvent.click(flaggedBtn);

    // Clear notes textarea
    const notesInput = screen.getByPlaceholderText(/Record observations/i);
    fireEvent.change(notesInput, { target: { value: "" } });

    // Click Save
    const saveBtn = screen.getByRole("button", { name: /Save Evaluation/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/Documented reviewer notes are required when flagging or rejecting a check/i)
      ).toBeInTheDocument();
    });
    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it("renders JobDirectoryPage with metrics cards and jobs table", async () => {
    renderWithProviders(<JobDirectoryPage />);

    await waitFor(() => {
      expect(screen.getByText("Job Requirements & Approvals")).toBeInTheDocument();
      expect(screen.getByText("Graduate Software Engineer")).toBeInTheDocument();
      expect(screen.getByText("Apex Cloud Systems")).toBeInTheDocument();
      expect(screen.getAllByText("Under Verification").length).toBeGreaterThanOrEqual(1);
    });
  });
});

