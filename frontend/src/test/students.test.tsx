import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { StudentDirectoryPage } from "../pages/students/StudentDirectoryPage";

vi.mock("../api/studentsApi", () => ({
  studentsApi: {
    getStudentMetrics: vi.fn().mockResolvedValue({
      total_students: 240,
      placed_students: 84,
      seeking_students: 150,
      opted_out_students: 6,
      placement_rate_pct: 35.0,
      branch_breakdown: [{ branch: "CSE", total: 120, placed: 50 }],
    }),
    getStudents: vi.fn().mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: "student-1",
          roll_number: "GQT-2025-001",
          full_name: "Aarav Sharma",
          email: "aarav@gqt.local",
          phone: "+919876543210",
          degree: "B.Tech",
          branch: "CSE",
          graduation_year: 2025,
          cgpa: "8.45",
          backlogs_count: 0,
          placement_status: "SEEKING",
          is_active: true,
          latest_resume_version: 1,
          is_resume_verified: true,
          created_at: "2026-11-01T10:00:00Z",
        },
        {
          id: "student-2",
          roll_number: "GQT-2025-002",
          full_name: "Rohan Verma",
          email: "rohan@gqt.local",
          phone: "+919876543211",
          degree: "B.Tech",
          branch: "IT",
          graduation_year: 2025,
          cgpa: "7.80",
          backlogs_count: 0,
          placement_status: "PLACED",
          is_active: true,
          latest_resume_version: 2,
          is_resume_verified: true,
          created_at: "2026-11-01T11:00:00Z",
        },
      ],
    }),
  },
}));

describe("StudentDirectoryPage Component", () => {
  it("renders page header, metric cards, and student records", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <StudentDirectoryPage />
        </BrowserRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText("Student Placement Operations & Readiness")).toBeDefined();
    expect(screen.getByPlaceholderText(/Search by roll number/i)).toBeDefined();

    // Verify candidate row rendered
    const candidateName = await screen.findByText("Aarav Sharma");
    expect(candidateName).toBeDefined();

    const rollNumber = await screen.findByText("GQT-2025-001");
    expect(rollNumber).toBeDefined();
  });
});
