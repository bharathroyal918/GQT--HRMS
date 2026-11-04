import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Briefcase,
  Plus,
  Search,
  CheckCircle2,
  Clock,
  ShieldAlert,
  ArrowRight,
  Filter,
} from "lucide-react";
import { jobsApi } from "../../api/jobsApi";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { JobStatusBadge } from "../../components/jobs/JobStatusBadge";

export const JobDirectoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  const { data: metricsData } = useQuery({
    queryKey: ["jobWorkflowMetrics"],
    queryFn: jobsApi.getWorkflowMetrics,
  });

  const {
    data: jobsData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["jobsList", search, statusFilter, categoryFilter],
    queryFn: () =>
      jobsApi.getJobs({
        search: search || undefined,
        status: statusFilter || undefined,
        role_category: categoryFilter || undefined,
      }),
  });

  const canCreate = user?.roles.some((r) =>
    ["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER"].includes(r)
  );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-indigo-50 text-indigo-700 rounded-lg">
              <Briefcase className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">Job Requirements & Approvals</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Structured job descriptions, mandatory 5-point verification, and segregated sign-off pipeline.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/jobs/verification-queue">
            <Button variant="outline" size="sm" className="flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-amber-500" />
              <span>Verification Queue</span>
              {metricsData?.pending_verification_jobs ? (
                <span className="ml-1 px-1.5 py-0.2 bg-amber-100 text-amber-800 rounded-full text-xs font-semibold">
                  {metricsData.pending_verification_jobs}
                </span>
              ) : null}
            </Button>
          </Link>

          <Link to="/jobs/approval-queue">
            <Button variant="outline" size="sm" className="flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-indigo-600" />
              <span>Approval Queue</span>
              {metricsData?.pending_approval_jobs ? (
                <span className="ml-1 px-1.5 py-0.2 bg-indigo-100 text-indigo-800 rounded-full text-xs font-semibold">
                  {metricsData.pending_approval_jobs}
                </span>
              ) : null}
            </Button>
          </Link>

          {canCreate && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate("/jobs/new")}
              className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700"
            >
              <Plus className="w-4 h-4" />
              <span>New Job Requirement</span>
            </Button>
          )}
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Requirements</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{metricsData?.total_jobs ?? 0}</div>
          <div className="text-xs text-slate-400 mt-1">Active corporate pipelines</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-amber-200/80 bg-amber-50/20 shadow-sm">
          <div className="text-xs font-semibold text-amber-800 uppercase tracking-wider">Under Verification</div>
          <div className="text-2xl font-bold text-amber-700 mt-1">
            {(metricsData?.pending_verification_jobs ?? 0) + (metricsData?.under_verification_jobs ?? 0)}
          </div>
          <div className="text-xs text-amber-600 mt-1">Awaiting 5-point sign-off</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-indigo-200/80 bg-indigo-50/20 shadow-sm">
          <div className="text-xs font-semibold text-indigo-800 uppercase tracking-wider">Pending Approval</div>
          <div className="text-2xl font-bold text-indigo-700 mt-1">{metricsData?.pending_approval_jobs ?? 0}</div>
          <div className="text-xs text-indigo-600 mt-1">All 5 checks passed</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-emerald-200/80 bg-emerald-50/20 shadow-sm">
          <div className="text-xs font-semibold text-emerald-800 uppercase tracking-wider">Approved Jobs</div>
          <div className="text-2xl font-bold text-emerald-700 mt-1">{metricsData?.approved_jobs ?? 0}</div>
          <div className="text-xs text-emerald-600 mt-1">Published for placement drives</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by role, company, skills..."
            className="pl-9"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs rounded-lg border border-slate-300 p-2 bg-white text-slate-700 outline-none focus:border-indigo-500"
            >
              <option value="">All Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="PENDING_VERIFICATION">Pending Verification</option>
              <option value="UNDER_VERIFICATION">Under Verification</option>
              <option value="CHANGES_REQUESTED">Changes Requested</option>
              <option value="PENDING_APPROVAL">Pending Approval</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="text-xs rounded-lg border border-slate-300 p-2 bg-white text-slate-700 outline-none focus:border-indigo-500"
          >
            <option value="">All Categories</option>
            <option value="SOFTWARE_ENGINEERING">Software Engineering</option>
            <option value="DATA_ANALYTICS">Data Analytics</option>
            <option value="CLOUD_DEVOPS">Cloud / DevOps</option>
            <option value="QA_TESTING">QA / Testing</option>
            <option value="PRODUCT_SUPPORT">Product Support</option>
            <option value="BUSINESS_ANALYST">Business Analyst</option>
          </select>
        </div>
      </div>

      {/* Main Data Content */}
      {isLoading ? (
        <LoadingState message="Loading job requirements directory..." />
      ) : isError ? (
        <ErrorState
          title="Error loading job directory"
          message={(error as any)?.message || "Failed to load jobs."}
          onRetry={refetch}
        />
      ) : !jobsData?.results || jobsData.results.length === 0 ? (
        <EmptyState
          title="No job requirements found"
          description="Create a new job requirement to initiate the 5-point verification and approval process."
          actionText={canCreate ? "Create Requirement" : undefined}
          onAction={canCreate ? () => navigate("/jobs/new") : undefined}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Role Title & Company</th>
                  <th className="py-3 px-4">Category & Location</th>
                  <th className="py-3 px-4">CTC Package</th>
                  <th className="py-3 px-4">5-Check Verification</th>
                  <th className="py-3 px-4">Workflow Status</th>
                  <th className="py-3 px-4">Reg. Deadline</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                {jobsData.results.map((job) => {
                  const verifiedCount = job.verification_summary?.verified_count || 0;
                  const isAllPass = job.verification_summary?.is_all_verified;

                  return (
                    <tr
                      key={job.id}
                      className="hover:bg-slate-50/70 transition-colors cursor-pointer"
                      onClick={() => navigate(`/jobs/${job.id}`)}
                    >
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900 hover:text-indigo-600 transition-colors">
                          {job.title}
                        </div>
                        <div className="text-slate-500 text-[11px] mt-0.5">{job.company_name}</div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-medium text-slate-800">{job.role_category.replace(/_/g, " ")}</div>
                        <div className="text-slate-400 text-[11px]">
                          {job.job_location || "Not specified"} ({job.work_arrangement})
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900">
                          ₹{job.min_ctc_lpa} - ₹{job.max_ctc_lpa} LPA
                        </div>
                        {job.vacancies_count ? (
                          <div className="text-slate-400 text-[11px]">{job.vacancies_count} vacancies</div>
                        ) : null}
                      </td>

                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            isAllPass
                              ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                              : verifiedCount > 0
                              ? "bg-amber-100 text-amber-800 border border-amber-300"
                              : "bg-slate-100 text-slate-700 border border-slate-300"
                          }`}
                        >
                          {isAllPass ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          ) : (
                            <Clock className="w-3.5 h-3.5 text-amber-600" />
                          )}
                          {verifiedCount} / 5 Verified
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <JobStatusBadge status={job.status} />
                        {job.revision_number > 1 && (
                          <span className="ml-1 text-[10px] text-slate-400 font-mono">
                            v{job.revision_number}
                          </span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-slate-600">
                        {new Date(job.registration_deadline).toLocaleDateString()}
                      </td>

                      <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/jobs/${job.id}`)}
                          className="text-xs py-1 px-2 text-indigo-600 hover:text-indigo-800"
                        >
                          <span>Review</span>
                          <ArrowRight className="w-3.5 h-3.5 ml-1" />
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

