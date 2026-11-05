import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  GraduationCap,
  Search,
  CheckCircle,
  Clock,
  AlertCircle,
  FileCheck,
  ChevronRight,
} from "lucide-react";
import { studentsApi } from "../../api/studentsApi";
import { StudentFilterParams } from "../../types/students";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorState } from "../../components/ui/ErrorState";

export const StudentDirectoryPage: React.FC = () => {
  const [filters, setFilters] = useState<StudentFilterParams>({
    page: 1,
    page_size: 20,
    search: "",
    branch: "",
    placement_status: "",
  });

  const {
    data: metricsData,
    isLoading: isMetricsLoading,
  } = useQuery({
    queryKey: ["studentMetrics"],
    queryFn: () => studentsApi.getStudentMetrics(),
  });

  const {
    data: studentsData,
    isLoading: isStudentsLoading,
    isError,
  } = useQuery({
    queryKey: ["studentsList", filters],
    queryFn: () => studentsApi.getStudents(filters),
  });

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters((prev) => ({ ...prev, search: e.target.value, page: 1 }));
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PLACED":
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">Placed</span>;
      case "SEEKING":
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800">Seeking</span>;
      case "OPTED_OUT":
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700">Opted Out</span>;
      case "INELIGIBLE":
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800">Ineligible</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <GraduationCap className="h-7 w-7 text-brand-navy" />
            <h1 className="text-2xl font-bold text-brand-dark">Student Placement Operations & Readiness</h1>
          </div>
          <p className="text-sm text-brand-muted mt-1">
            Student directory, academic profile audits, resume vaults, and deterministic eligibility evaluation engine.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 border-l-4 border-l-brand-blue bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Enrolled</span>
            <GraduationCap className="h-4 w-4 text-brand-blue" />
          </div>
          <p className="text-2xl font-bold text-brand-dark mt-2">
            {isMetricsLoading ? "..." : metricsData?.total_students ?? 0}
          </p>
          <p className="text-xs text-brand-muted mt-1">Active placement pool</p>
        </Card>

        <Card className="p-4 border-l-4 border-l-indigo-600 bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Seeking Drives</span>
            <Clock className="h-4 w-4 text-indigo-600" />
          </div>
          <p className="text-2xl font-bold text-brand-dark mt-2">
            {isMetricsLoading ? "..." : metricsData?.seeking_students ?? 0}
          </p>
          <p className="text-xs text-brand-muted mt-1">Ready for participation</p>
        </Card>

        <Card className="p-4 border-l-4 border-l-emerald-600 bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Placed Candidates</span>
            <CheckCircle className="h-4 w-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-brand-dark mt-2">
            {isMetricsLoading ? "..." : metricsData?.placed_students ?? 0}
          </p>
          <p className="text-xs text-emerald-600 font-semibold mt-1">
            {isMetricsLoading ? "..." : `${metricsData?.placement_rate_pct ?? 0}% Placement Rate`}
          </p>
        </Card>

        <Card className="p-4 border-l-4 border-l-amber-500 bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Opted Out / Other</span>
            <AlertCircle className="h-4 w-4 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-brand-dark mt-2">
            {isMetricsLoading ? "..." : metricsData?.opted_out_students ?? 0}
          </p>
          <p className="text-xs text-brand-muted mt-1">Higher studies or entrepreneurial</p>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <Card className="p-4 bg-white">
        <div className="flex flex-col md:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by roll number, student name, email, or branch..."
              value={filters.search}
              onChange={handleSearchChange}
              className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-blue"
            />
          </div>
          <div className="flex items-center gap-2 w-full md:w-auto">
            <select
              value={filters.branch}
              onChange={(e) => setFilters((prev) => ({ ...prev, branch: e.target.value, page: 1 }))}
              className="px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-brand-blue"
            >
              <option value="">All Branches</option>
              <option value="CSE">CSE</option>
              <option value="IT">IT</option>
              <option value="ECE">ECE</option>
              <option value="ME">ME</option>
              <option value="CE">CE</option>
              <option value="MCA">MCA</option>
            </select>
            <select
              value={filters.placement_status}
              onChange={(e) => setFilters((prev) => ({ ...prev, placement_status: e.target.value, page: 1 }))}
              className="px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-brand-blue"
            >
              <option value="">All Statuses</option>
              <option value="SEEKING">Seeking</option>
              <option value="PLACED">Placed</option>
              <option value="OPTED_OUT">Opted Out</option>
              <option value="INELIGIBLE">Ineligible</option>
            </select>
            {(filters.search || filters.branch || filters.placement_status) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setFilters({ page: 1, page_size: 20, search: "", branch: "", placement_status: "" })}
                className="text-xs text-brand-muted hover:text-brand-dark"
              >
                Clear
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Students Table */}
      <Card className="overflow-hidden bg-white shadow-sm border border-slate-200">
        {isStudentsLoading ? (
          <div className="p-8">
            <LoadingState message="Loading student records..." />
          </div>
        ) : isError ? (
          <div className="p-8">
            <ErrorState message="Failed to load student directory." />
          </div>
        ) : !studentsData?.results || studentsData.results.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No Students Found"
              description="No student profiles match your search criteria."
            />
          </div>
        ) : (
          <div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                    <th className="py-3 px-4">Roll Number</th>
                    <th className="py-3 px-4">Candidate Name</th>
                    <th className="py-3 px-4">Branch & Degree</th>
                    <th className="py-3 px-4">Grad Batch</th>
                    <th className="py-3 px-4">CGPA</th>
                    <th className="py-3 px-4">Backlogs</th>
                    <th className="py-3 px-4">Placement Status</th>
                    <th className="py-3 px-4">Resume</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {studentsData.results.map((student) => (
                    <tr key={student.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-4 font-mono font-medium text-brand-blue whitespace-nowrap">
                        <Link to={`/students/${student.id}`} className="hover:underline">
                          {student.roll_number}
                        </Link>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900">{student.full_name}</div>
                        <div className="text-[11px] text-slate-500">{student.email}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-medium text-slate-800">{student.branch}</span>
                        <span className="text-slate-400 ml-1">({student.degree})</span>
                      </td>
                      <td className="py-3 px-4 text-slate-600 font-medium">
                        {student.graduation_year}
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-900">
                        {student.cgpa}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-semibold ${
                            student.backlogs_count > 0 ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {student.backlogs_count}
                        </span>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        {getStatusBadge(student.placement_status)}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        {student.latest_resume_version ? (
                          <div className="flex items-center gap-1">
                            <span className="text-[11px] text-slate-600">v{student.latest_resume_version}</span>
                            {student.is_resume_verified && (
                              <span title="ATS Verified">
                                <FileCheck className="h-3.5 w-3.5 text-emerald-600" />
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">None</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link
                          to={`/students/${student.id}`}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-brand-blue hover:text-brand-dark"
                        >
                          View Profile
                          <ChevronRight className="h-3.5 w-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between p-4 border-t border-slate-200 text-xs text-slate-500">
              <div>
                Showing page {filters.page} of {Math.ceil((studentsData.count || 1) / (filters.page_size || 20))} (
                {studentsData.count} total records)
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!studentsData.previous}
                  onClick={() => setFilters((prev) => ({ ...prev, page: Math.max(1, (prev.page || 1) - 1) }))}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!studentsData.next}
                  onClick={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) + 1 }))}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
