import React from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ShieldCheck, ArrowLeft, ArrowRight, CheckCircle2 } from "lucide-react";
import { jobsApi } from "../../api/jobsApi";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";

export const ApprovalQueuePage: React.FC = () => {
  const navigate = useNavigate();

  const {
    data: queueData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["approvalQueue"],
    queryFn: jobsApi.getApprovalQueue,
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
            <div className="p-2 bg-emerald-50 text-emerald-700 rounded-lg">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold text-slate-900">Placement Head Final Approval Queue</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Requirements with all five mandatory checks verified awaiting independent sign-off. Segregation of duties applies.
          </p>
        </div>

        <div className="text-right">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Awaiting Sign-Off</div>
          <div className="text-2xl font-bold text-emerald-700">{queueData?.results?.length ?? 0} Ready</div>
        </div>
      </div>

      {isLoading ? (
        <LoadingState message="Loading pending approval queue..." />
      ) : isError ? (
        <ErrorState
          title="Error loading approval queue"
          message={(error as any)?.message || "Failed to load approval queue."}
          onRetry={refetch}
        />
      ) : !queueData?.results || queueData.results.length === 0 ? (
        <EmptyState
          title="Approval queue is clear"
          description="There are currently no job requirements awaiting Placement Head authorization."
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
                  <th className="py-3 px-4">CTC Package</th>
                  <th className="py-3 px-4">Verification Gate</th>
                  <th className="py-3 px-4">Submitted By</th>
                  <th className="py-3 px-4">Deadline</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                {queueData.results.map((job) => (
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

                    <td className="py-3 px-4 font-semibold text-slate-900">
                      ₹{job.min_ctc_lpa} - ₹{job.max_ctc_lpa} LPA
                    </td>

                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        5 of 5 Checks Passed
                      </span>
                    </td>

                    <td className="py-3 px-4 text-slate-700">
                      {job.submitted_by_name || "Unknown"}
                    </td>

                    <td className="py-3 px-4 text-slate-600">
                      {new Date(job.registration_deadline).toLocaleDateString()}
                    </td>

                    <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => navigate(`/jobs/${job.id}`)}
                        className="text-xs py-1 px-3 bg-emerald-600 hover:bg-emerald-700"
                      >
                        <span>Authorize</span>
                        <ArrowRight className="w-3.5 h-3.5 ml-1" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

