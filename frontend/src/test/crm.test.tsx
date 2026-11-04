import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "../context/AuthContext";
import { CompanyDirectoryPage } from "../pages/crm/CompanyDirectoryPage";
import { CreateCompanyModal } from "../components/crm/CreateCompanyModal";
import { FollowUpDashboardPage } from "../pages/crm/FollowUpDashboardPage";

// Mock crmApi
vi.mock("../api/crmApi", () => ({
  crmApi: {
    getCompanies: vi.fn().mockResolvedValue({
      count: 1,
      results: [
        {
          id: "11111111-1111-1111-1111-111111111111",
          name: "Infosys Technologies",
          canonical_domain: "infosys.com",
          website: "https://www.infosys.com",
          industry: "IT_SERVICES",
          source: "OUTBOUND_CALLING",
          status: "ACTIVE_HIRING_PARTNER",
          tier: "TIER_1",
          assigned_to: null,
          assigned_to_name: "Jane Officer",
          contacts_count: 3,
          outreach_count: 5,
          pending_followups_count: 1,
          created_at: "2026-11-01T10:00:00Z",
          updated_at: "2026-11-01T10:00:00Z",
        },
      ],
    }),
    checkDuplicateCompany: vi.fn().mockResolvedValue({
      is_duplicate: true,
      match_count: 1,
      matches: [
        {
          id: "11111111-1111-1111-1111-111111111111",
          name: "Infosys Technologies",
          canonical_domain: "infosys.com",
          status: "ACTIVE_HIRING_PARTNER",
          match_reason: "EXACT_DOMAIN_MATCH",
        },
      ],
    }),
    createCompany: vi.fn().mockResolvedValue({
      id: "22222222-2222-2222-2222-222222222222",
      name: "TCS Enterprise",
    }),
    getFollowUps: vi.fn().mockResolvedValue({
      count: 1,
      results: [
        {
          id: "33333333-3333-3333-3333-333333333333",
          company: "11111111-1111-1111-1111-111111111111",
          company_name: "Infosys Technologies",
          contact_name: "John Recruiter",
          title: "Follow-up on 2027 recruitment quota",
          description: "Call to confirm dates",
          due_date: "2026-11-10T10:00:00Z",
          priority: "HIGH",
          status: "PENDING",
          is_overdue: false,
          is_due_today: true,
          assigned_to_name: "Calling Executive",
        },
      ],
    }),
  },
}));

const createTestWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>{children}</BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

describe("CompanyDirectoryPage Component", () => {
  it("renders page header and company table with mock records", async () => {
    const Wrapper = createTestWrapper();
    render(
      <Wrapper>
        <CompanyDirectoryPage />
      </Wrapper>
    );

    expect(screen.getByRole("heading", { name: /company & employer directory/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search companies/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Infosys Technologies")).toBeInTheDocument();
      expect(screen.getByText("infosys.com")).toBeInTheDocument();
      expect(screen.getByText("ACTIVE HIRING PARTNER")).toBeInTheDocument();
    });
  });
});

describe("CreateCompanyModal Component", () => {
  it("triggers duplicate detection warning on blur", async () => {
    const Wrapper = createTestWrapper();
    render(
      <Wrapper>
        <CreateCompanyModal isOpen={true} onClose={vi.fn()} onSuccess={vi.fn()} />
      </Wrapper>
    );

    expect(screen.getByRole("heading", { name: /add target company/i })).toBeInTheDocument();

    const nameInput = screen.getByLabelText(/company name \*/i);
    fireEvent.change(nameInput, { target: { value: "Infosys Technologies" } });
    fireEvent.blur(nameInput);

    await waitFor(() => {
      expect(screen.getByText(/potential duplicate detected/i)).toBeInTheDocument();
      expect(screen.getByText(/i confirm this is a separate company/i)).toBeInTheDocument();
    });
  });
});

describe("FollowUpDashboardPage Component", () => {
  it("renders follow-up queue tabs and mock tasks", async () => {
    const Wrapper = createTestWrapper();
    render(
      <Wrapper>
        <FollowUpDashboardPage />
      </Wrapper>
    );

    expect(screen.getByRole("heading", { name: /outreach follow-up action queue/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /due today/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /overdue tasks/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Follow-up on 2027 recruitment quota")).toBeInTheDocument();
      expect(screen.getByText("Infosys Technologies")).toBeInTheDocument();
    });
  });
});
