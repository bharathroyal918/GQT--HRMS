import React from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Clock, ArrowLeft, ArrowRight, ShieldCheck } from "lucide-react";
import { jobsApi } from "../../api/jobsApi";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { JobStatusBadge } from "../../components/jobs/JobStatusBadge";

export const VerificationQueuePage: React.FC = () => {
  const navigate = useNavigate();

  const {
    data: queueData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["verificationQueue"],
    queryFn: jobsApi.getVerificationQueue,
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate("/jobs")}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Job Directory</span>
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-amber-50 text-amber-700 rounded-lg">
              <Clock className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold text-slate-900">5-Point Verification Review Queue</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Job requirements awaiting review across Eligibility, Salary, Company, Process, and Deadline checks.
          </p>
        </div>

        <div className="text-right">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Queue Total</div>
          <div className="text-2xl font-bold text-amber-700">{queueData?.results?.length ?? 0} Pending</div>
        </div>
      </div>

      {isLoading ? (
        <LoadingState message="Loading verification review queue..." />
      ) : isError ? (
        <ErrorState
          title="Error loading queue"
          message={(error as any)?.message || "Failed to load verification queue."}
          onRetry={refetch}
        />
      ) : !queueData?.results || queueData.results.length === 0 ? (
        <EmptyState
          title="Verification queue is empty"
          description="There are currently no job requirements pending 5-point verification review."
          actionText="View Job Directory"
          onAction={() => navigate("/jobs")}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Role Title & Company</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Verification Progress</th>
                  <th className="py-3 px-4">Assigned Verifier</th>
                  <th className="py-3 px-4">Cutoff Deadline</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                {queueData.results.map((job) => {
                  const verifiedCount = job.verification_summary?.verified_count || 0;

                  return (
                    <tr
                      key={job.id}
                      className="hover:bg-slate-50/70 transition-colors cursor-pointer"
                      onClick={() => navigate(`/jobs/${job.id}`)}
                    >
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900">{job.title}</div>
                        <div className="text-slate-500 text-[11px]">{job.company_name}</div>
                      </td>

                      <td className="py-3 px-4 font-medium text-slate-800">
                        {job.role_category.replace(/_/g, " ")}
                      </td>

                      <td className="py-3 px-4">
                        <JobStatusBadge status={job.status} />
                      </td>

                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                          <ShieldCheck className="w-3.5 h-3.5 text-amber-600" />
                          {verifiedCount} / 5 Checks
                        </span>
                      </td>

                      <td className="py-3 px-4 text-slate-600">
                        {job.assigned_verifier_name || <span className="text-slate-400 italic">Unassigned</span>}
                      </td>

                      <td className="py-3 px-4 text-slate-600">
                        {new Date(job.registration_deadline).toLocaleDateString()}
                      </td>

                      <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => navigate(`/jobs/${job.id}`)}
                          className="text-xs py-1 px-3 bg-indigo-600 hover:bg-indigo-700"
                        >
                          <span>Review Checks</span>
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

