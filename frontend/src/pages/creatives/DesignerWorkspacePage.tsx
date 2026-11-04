import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Layers, ArrowLeft, UploadCloud } from "lucide-react";
import { creativesApi } from "../../api/creativesApi";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { CreativeStatusBadge } from "../../components/creatives/CreativeStatusBadge";
import { AssetVersionUploadModal } from "../../components/creatives/AssetVersionUploadModal";
import { CreativeRequestDetail } from "../../types/creatives";

export const DesignerWorkspacePage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeUploadReq, setActiveUploadReq] = useState<CreativeRequestDetail | null>(null);

  const {
    data: queueData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["designerQueue"],
    queryFn: creativesApi.getDesignerQueue,
  });

  const handleUploadSuccess = async (formData: FormData) => {
    if (!activeUploadReq) return;
    await creativesApi.uploadVersion(activeUploadReq.id, formData);
    queryClient.invalidateQueries({ queryKey: ["designerQueue"] });
    queryClient.invalidateQueries({ queryKey: ["creativeStudioMetrics"] });
    setActiveUploadReq(null);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back button */}
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
            <div className="p-2 bg-blue-50 text-blue-700 rounded-lg">
              <Layers className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold text-slate-900">Graphic Designer Active Workspace</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Recruitment requisitions assigned to you awaiting design drafting, deliverable upload, or feedback revision.
          </p>
        </div>

        <div className="text-right">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Tasks</div>
          <div className="text-2xl font-bold text-blue-700">{queueData?.length ?? 0} In Progress</div>
        </div>
      </div>

      {isLoading ? (
        <LoadingState message="Loading assigned design tasks..." />
      ) : isError ? (
        <ErrorState
          title="Error loading workspace"
          message={(error as any)?.message || "Failed to load assigned tasks."}
          onRetry={refetch}
        />
      ) : !queueData || queueData.length === 0 ? (
        <EmptyState
          title="Workspace is clear"
          description="You currently have no design tasks assigned in ASSIGNED, IN_DESIGN, or CHANGES_REQUESTED status."
          actionText="View Requisition Directory"
          onAction={() => navigate("/creatives/directory")}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Code & Title</th>
                  <th className="py-3 px-4">Format / Type</th>
                  <th className="py-3 px-4">Target Company</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Target Date</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                {queueData.map((req) => (
                  <tr
                    key={req.id}
                    onClick={() => navigate(`/creatives/${req.id}`)}
                    className="hover:bg-slate-50/70 transition-colors cursor-pointer"
                  >
                    <td className="py-3 px-4">
                      <div className="font-mono text-[11px] text-indigo-600 font-semibold">
                        {req.request_code}
                      </div>
                      <div className="font-semibold text-slate-900">{req.title}</div>
                    </td>

                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-800">
                        {req.creative_type.replace(/_/g, " ")}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {req.deliverable_format} • {req.aspect_ratio}
                      </div>
                    </td>

                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">{req.company_name || "—"}</div>
                      <div className="text-[11px] text-slate-500 truncate max-w-[150px]">
                        {req.job_title || "General Campaign"}
                      </div>
                    </td>

                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold ${req.priority === "URGENT"
                            ? "bg-rose-100 text-rose-800"
                            : req.priority === "HIGH"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-slate-100 text-slate-700"
                          }`}
                      >
                        {req.priority}
                      </span>
                    </td>

                    <td className="py-3 px-4">
                      <CreativeStatusBadge status={req.status} />
                    </td>

                    <td className="py-3 px-4 text-slate-600">
                      {req.target_completion_date
                        ? new Date(req.target_completion_date).toLocaleDateString()
                        : "—"}
                    </td>

                    <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => setActiveUploadReq(req)}
                        className="text-xs py-1 px-3 bg-indigo-600 hover:bg-indigo-700"
                      >
                        <UploadCloud className="w-3.5 h-3.5 mr-1" />
                        <span>Upload Deliverable</span>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeUploadReq && (
        <AssetVersionUploadModal
          isOpen={Boolean(activeUploadReq)}
          onClose={() => setActiveUploadReq(null)}
          onUpload={handleUploadSuccess}
          requestCode={activeUploadReq.request_code}
          nextVersionNumber={(activeUploadReq.versions?.length || 0) + 1}
        />
      )}
    </div>
  );
};

