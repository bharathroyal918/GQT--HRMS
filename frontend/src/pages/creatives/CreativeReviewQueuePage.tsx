import React from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ShieldCheck, ArrowLeft, ArrowRight } from "lucide-react";
import { creativesApi } from "../../api/creativesApi";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";

export const CreativeReviewQueuePage: React.FC = () => {
  const navigate = useNavigate();

  const {
    data: queueData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["creativeReviewQueue"],
    queryFn: creativesApi.getReviewQueue,
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back link */}
      <div>
        <button
          type="button"
          onClick={() => navigate("/creatives/dashboard")}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Creative Studio</span>
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-purple-50 text-purple-700 rounded-lg">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold text-slate-900">4-Point Compliance Review Queue</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Deliverable versions awaiting brand compliance evaluation and segregated authorization.
          </p>
        </div>

        <div className="text-right">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Awaiting Review</div>
          <div className="text-2xl font-bold text-purple-700">{queueData?.length ?? 0} In Review</div>
        </div>
      </div>

      {isLoading ? (
        <LoadingState message="Loading review queue..." />
      ) : isError ? (
        <ErrorState
          title="Error loading review queue"
          message={(error as any)?.message || "Failed to load review queue."}
          onRetry={refetch}
        />
      ) : !queueData || queueData.length === 0 ? (
        <EmptyState
          title="Review queue is clear"
          description="There are currently no design asset versions awaiting compliance evaluation."
          actionText="View Requisition Directory"
          onAction={() => navigate("/creatives/directory")}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Version & Deliverable</th>
                  <th className="py-3 px-4">Format / MIME</th>
                  <th className="py-3 px-4">Designer / Uploader</th>
                  <th className="py-3 px-4">Compliance Gate</th>
                  <th className="py-3 px-4">Uploaded At</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                {queueData.map((v) => {
                  const passedChecks = v.compliance_checks?.filter((c) => c.status === "PASSED").length || 0;
                  const isAllPass = passedChecks === 4;

                  return (
                    <tr
                      key={v.id}
                      className="hover:bg-slate-50/70 transition-colors cursor-pointer"
                    >
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <span className="font-bold font-mono px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 text-xs">
                            v{v.version_number}
                          </span>
                          <span className="font-semibold text-slate-900">{v.original_filename}</span>
                        </div>
                        {v.designer_notes && (
                          <div className="text-[11px] text-slate-400 mt-0.5 truncate max-w-xs">
                            {v.designer_notes}
                          </div>
                        )}
                      </td>

                      <td className="py-3 px-4">
                        <span className="font-mono text-slate-700 text-xs">{v.mime_type}</span>
                        <div className="text-[11px] text-slate-400">
                          {(v.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                        </div>
                      </td>

                      <td className="py-3 px-4 text-slate-800 font-medium">
                        {v.uploader_name}
                      </td>

                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${isAllPass
                              ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                              : "bg-amber-100 text-amber-800 border border-amber-300"
                            }`}
                        >
                          <ShieldCheck className="w-3.5 h-3.5 text-amber-600" />
                          {passedChecks} of 4 Checks Passed
                        </span>
                      </td>

                      <td className="py-3 px-4 text-slate-500">
                        {new Date(v.created_at).toLocaleString()}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <a
                          href={creativesApi.getAssetDownloadUrl(v.id, false)}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 px-3 py-1 rounded bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-semibold text-xs transition"
                        >
                          <span>Inspect</span>
                          <ArrowRight className="w-3.5 h-3.5 ml-1" />
                        </a>
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

