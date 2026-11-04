import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Palette,
  ArrowLeft,
  CheckCircle2,
  ShieldCheck,
  UploadCloud,
  UserCheck,
  Send,
  Download,
  AlertTriangle,
  History,
  FileText,
  Briefcase,
  Building2,
  Calendar,
  X,
} from "lucide-react";
import { creativesApi } from "../../api/creativesApi";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { CreativeStatusBadge } from "../../components/creatives/CreativeStatusBadge";
import { DesignChecklistCard } from "../../components/creatives/DesignChecklistCard";
import { AssetVersionUploadModal } from "../../components/creatives/AssetVersionUploadModal";
import { VersionReviewModal } from "../../components/creatives/VersionReviewModal";
import { AssignDesignerModal } from "../../components/creatives/AssignDesignerModal";
import {
  CreativeAssetVersion,
  DesignComplianceCheck,
  ComplianceCheckStatus,
} from "../../types/creatives";

export const CreativeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  // Modals state
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [isAssignOpen, setIsAssignOpen] = useState(false);
  const [evaluatingCheck, setEvaluatingCheck] = useState<DesignComplianceCheck | null>(null);
  const [checkStatus, setCheckStatus] = useState<ComplianceCheckStatus>("PASSED");
  const [checkNotes, setCheckNotes] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  const {
    data: req,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["creativeRequestDetail", id],
    queryFn: () => creativesApi.getRequestDetail(id!),
    enabled: Boolean(id),
  });

  if (isLoading) {
    return <LoadingState message="Loading creative requisition details..." />;
  }

  if (isError || !req) {
    return (
      <ErrorState
        title="Requisition not found"
        message={(error as any)?.message || "Failed to load requisition."}
        onRetry={() => queryClient.invalidateQueries({ queryKey: ["creativeRequestDetail", id] })}
      />
    );
  }

  const userRoles = user?.roles || [];
  const isPrivileged = userRoles.some((r) =>
    ["ADMIN", "PLACEMENT_HEAD", "CREATIVE_REVIEWER"].includes(r)
  );
  const isAssignedDesigner = Boolean(user && req.assigned_designer === user.id);
  const canUpload = isAssignedDesigner || isPrivileged;
  const canAssign = isPrivileged;
  const canReview = isPrivileged;
  const canHandoff = userRoles.some((r) => ["ADMIN", "PLACEMENT_HEAD", "CREATIVE_REVIEWER"].includes(r));

  // Active or latest candidate version
  const latestVersion: CreativeAssetVersion | null =
    req.active_version || (req.versions && req.versions[0]) || null;

  const handleUpload = async (formData: FormData) => {
    await creativesApi.uploadVersion(req.id, formData);
    queryClient.invalidateQueries({ queryKey: ["creativeRequestDetail", id] });
    queryClient.invalidateQueries({ queryKey: ["creativeStudioMetrics"] });
  };

  const handleApprove = async (reviewFeedback?: string) => {
    if (!latestVersion) return;
    await creativesApi.approveVersion(latestVersion.id, { review_feedback: reviewFeedback });
    queryClient.invalidateQueries({ queryKey: ["creativeRequestDetail", id] });
    queryClient.invalidateQueries({ queryKey: ["creativeStudioMetrics"] });
  };

  const handleRequestChanges = async (reviewFeedback: string) => {
    if (!latestVersion) return;
    await creativesApi.requestChanges(latestVersion.id, { review_feedback: reviewFeedback });
    queryClient.invalidateQueries({ queryKey: ["creativeRequestDetail", id] });
    queryClient.invalidateQueries({ queryKey: ["creativeStudioMetrics"] });
  };

  const handleAssign = async (payload: { assigned_designer_id: string; priority?: string; notes?: string }) => {
    await creativesApi.assignDesigner(req.id, payload);
    queryClient.invalidateQueries({ queryKey: ["creativeRequestDetail", id] });
    queryClient.invalidateQueries({ queryKey: ["creativeStudioMetrics"] });
  };

  const handleSubmitRequisition = async () => {
    try {
      setActionError(null);
      await creativesApi.submitRequest(req.id);
      queryClient.invalidateQueries({ queryKey: ["creativeRequestDetail", id] });
      queryClient.invalidateQueries({ queryKey: ["creativeStudioMetrics"] });
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || "Failed to submit requisition.");
    }
  };

  const handleHandoff = async () => {
    try {
      setActionError(null);
      await creativesApi.markReadyForHandoff(req.id);
      queryClient.invalidateQueries({ queryKey: ["creativeRequestDetail", id] });
      queryClient.invalidateQueries({ queryKey: ["creativeStudioMetrics"] });
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || "Failed to mark ready for handoff.");
    }
  };

  const handleSaveCheckEvaluation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!evaluatingCheck || !latestVersion) return;
    if (checkStatus === "FLAGGED" && !checkNotes.trim()) {
      setActionError("Notes are required when flagging a check.");
      return;
    }

    try {
      setActionError(null);
      await creativesApi.evaluateCheck(latestVersion.id, evaluatingCheck.check_type, {
        status: checkStatus,
        notes: checkNotes.trim() || undefined,
      });
      setEvaluatingCheck(null);
      queryClient.invalidateQueries({ queryKey: ["creativeRequestDetail", id] });
    } catch (err: any) {
      setActionError(err?.response?.data?.notes?.[0] || err?.response?.data?.detail || "Check evaluation failed.");
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back button */}
      <div>
        <button
          type="button"
          onClick={() => navigate("/creatives/directory")}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Requisition Directory</span>
        </button>
      </div>

      {actionError && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-500" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Main Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="font-mono text-xs font-bold px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded border border-indigo-200">
                {req.request_code}
              </span>
              <h1 className="text-2xl font-bold text-slate-900">{req.title}</h1>
              <CreativeStatusBadge status={req.status} />
              <span
                className={`text-[11px] font-bold px-2 py-0.5 rounded ${req.priority === "URGENT"
                    ? "bg-rose-100 text-rose-800"
                    : req.priority === "HIGH"
                      ? "bg-amber-100 text-amber-800"
                      : "bg-slate-100 text-slate-700"
                  }`}
              >
                {req.priority} Priority
              </span>
            </div>

            <div className="flex items-center gap-4 text-xs text-slate-500 flex-wrap">
              <span className="flex items-center gap-1">
                <Palette className="w-3.5 h-3.5 text-indigo-500" />
                {req.creative_type.replace(/_/g, " ")} ({req.deliverable_format} • {req.aspect_ratio})
              </span>
              {req.company_name && (
                <span className="flex items-center gap-1">
                  <Building2 className="w-3.5 h-3.5 text-slate-400" />
                  {req.company_name}
                </span>
              )}
              {req.job_title && (
                <span className="flex items-center gap-1">
                  <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                  {req.job_title}
                </span>
              )}
              {req.target_completion_date && (
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  Target: {new Date(req.target_completion_date).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>

          {/* Action CTAs */}
          <div className="flex items-center gap-3 flex-wrap">
            {req.status === "DRAFT" && (
              <Button
                variant="primary"
                size="sm"
                onClick={handleSubmitRequisition}
                className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700"
              >
                <Send className="w-4 h-4" />
                <span>Submit for Triage</span>
              </Button>
            )}

            {canAssign && (req.status === "SUBMITTED" || req.status === "ASSIGNED") && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsAssignOpen(true)}
                className="flex items-center gap-1.5"
              >
                <UserCheck className="w-4 h-4 text-indigo-600" />
                <span>{req.assigned_designer ? "Reassign Designer" : "Assign Designer"}</span>
              </Button>
            )}

            {canUpload &&
              ["ASSIGNED", "IN_DESIGN", "CHANGES_REQUESTED", "IN_REVIEW"].includes(req.status) && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsUploadOpen(true)}
                  className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700"
                >
                  <UploadCloud className="w-4 h-4" />
                  <span>Upload Deliverable</span>
                </Button>
              )}

            {canReview && latestVersion && req.status === "IN_REVIEW" && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsReviewOpen(true)}
                className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Review Asset</span>
              </Button>
            )}

            {canHandoff && req.status === "APPROVED" && (
              <Button
                variant="primary"
                size="sm"
                onClick={handleHandoff}
                className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Handoff for Drives</span>
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Brief and Asset Preview (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Deliverable Preview Card */}
          {latestVersion ? (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-indigo-600" />
                  <h3 className="font-bold text-slate-900 text-sm">
                    Deliverable Asset (v{latestVersion.version_number})
                  </h3>
                  <span className="text-[11px] text-slate-400">
                    Uploaded by {latestVersion.uploader_name}
                  </span>
                </div>

                <a
                  href={creativesApi.getAssetDownloadUrl(latestVersion.id, false)}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download / Preview</span>
                </a>
              </div>

              {/* Secure Inline Image Rendering */}
              {latestVersion.mime_type.startsWith("image/") ? (
                <div className="flex justify-center bg-slate-900/5 rounded-xl p-4 overflow-hidden border border-slate-100">
                  <img
                    src={creativesApi.getAssetDownloadUrl(latestVersion.id, false)}
                    alt={latestVersion.original_filename}
                    className="max-h-96 rounded-lg object-contain shadow-sm"
                  />
                </div>
              ) : (
                <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
                  <FileText className="w-10 h-10 text-indigo-500 mx-auto mb-2" />
                  <div className="text-xs font-semibold text-slate-800">
                    {latestVersion.original_filename} ({latestVersion.mime_type})
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Print-ready PDF deliverable. Download to view high-resolution vector artwork.
                  </p>
                </div>
              )}

              {/* Version metadata footer */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] pt-3 border-t border-slate-100 text-slate-600">
                <div>
                  <span className="text-slate-400 block">File Size</span>
                  <span className="font-semibold text-slate-800">
                    {(latestVersion.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">MIME Type</span>
                  <span className="font-semibold text-slate-800">{latestVersion.mime_type}</span>
                </div>
                <div className="sm:col-span-2">
                  <span className="text-slate-400 block">SHA-256 Checksum</span>
                  <span className="font-mono text-[10px] text-slate-800 truncate block">
                    {latestVersion.sha256_hash}
                  </span>
                </div>
              </div>

              {latestVersion.designer_notes && (
                <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-700 border border-slate-100">
                  <span className="font-semibold text-slate-900">Designer Notes: </span>
                  <span>{latestVersion.designer_notes}</span>
                </div>
              )}

              {latestVersion.review_feedback && (
                <div className="p-3 bg-indigo-50/50 rounded-lg text-xs text-indigo-900 border border-indigo-100">
                  <span className="font-semibold text-indigo-950">Reviewer Feedback: </span>
                  <span>{latestVersion.review_feedback}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 text-center">
              <UploadCloud className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-slate-800">No Deliverable Asset Uploaded Yet</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                The assigned graphic designer will upload the initial draft deliverable for review.
              </p>
              {canUpload && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsUploadOpen(true)}
                  className="mt-4 bg-indigo-600 hover:bg-indigo-700"
                >
                  Upload Initial Deliverable
                </Button>
              )}
            </div>
          )}

          {/* 4-Point Compliance Gate Card */}
          {latestVersion ? (
            <DesignChecklistCard
              checks={latestVersion.compliance_checks || []}
              canReview={canReview}
              onEvaluateCheck={(check) => {
                setEvaluatingCheck(check);
                setCheckStatus(check.status === "PENDING" ? "PASSED" : check.status);
                setCheckNotes(check.notes || "");
              }}
            />
          ) : null}

          {/* Creative Brief */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-3">
            <h3 className="font-bold text-slate-900 text-sm">Creative Brief & Instructions</h3>
            <div className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap bg-slate-50 p-4 rounded-xl border border-slate-100 font-sans">
              {req.brief}
            </div>
          </div>
        </div>

        {/* Right Column: Versions History & Timeline (1 col) */}
        <div className="space-y-6">
          {/* Assignment & Operational Details */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
            <h3 className="font-bold text-slate-900 text-xs uppercase tracking-wider text-slate-400">
              Operational Assignment
            </h3>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Requester:</span>
                <span className="font-semibold text-slate-800">{req.created_by_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Assigned Designer:</span>
                <span className="font-semibold text-indigo-700">
                  {req.assigned_designer_name || "Unassigned"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Format & Ratio:</span>
                <span className="font-semibold text-slate-800">
                  {req.deliverable_format} • {req.aspect_ratio}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Target Deadline:</span>
                <span className="font-semibold text-slate-800">
                  {req.target_completion_date
                    ? new Date(req.target_completion_date).toLocaleDateString()
                    : "Not specified"}
                </span>
              </div>
            </div>
          </div>

          {/* Version Iterations List */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-900 text-xs uppercase tracking-wider text-slate-400">
                Version Iterations ({req.versions?.length ?? 0})
              </h3>
            </div>

            <div className="space-y-2">
              {req.versions?.map((v) => (
                <div
                  key={v.id}
                  className={`p-3 rounded-lg border text-xs flex items-center justify-between ${req.active_version?.id === v.id
                      ? "bg-indigo-50/50 border-indigo-200"
                      : "bg-slate-50/50 border-slate-200"
                    }`}
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold font-mono text-indigo-700">v{v.version_number}</span>
                      <span className="text-[10px] font-semibold px-2 py-0.2 rounded bg-white border border-slate-200 text-slate-700">
                        {v.status}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5 truncate max-w-[160px]">
                      {v.original_filename}
                    </div>
                  </div>

                  <a
                    href={creativesApi.getAssetDownloadUrl(v.id, false)}
                    target="_blank"
                    rel="noreferrer"
                    className="p-1.5 text-slate-400 hover:text-indigo-600 transition"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </a>
                </div>
              ))}
            </div>
          </div>

          {/* Workflow Transition History */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
            <div className="flex items-center gap-1.5 font-bold text-slate-900 text-xs uppercase tracking-wider text-slate-400">
              <History className="w-3.5 h-3.5" />
              <span>Workflow Audit Timeline</span>
            </div>

            <div className="space-y-3 text-xs">
              {req.history?.map((h) => (
                <div key={h.id} className="relative pl-4 border-l border-slate-200 space-y-0.5">
                  <div className="font-semibold text-slate-800 text-[11px]">{h.action}</div>
                  <div className="text-slate-500 text-[11px]">{h.notes}</div>
                  <div className="text-[10px] text-slate-400">
                    {new Date(h.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      <AssetVersionUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUpload={handleUpload}
        requestCode={req.request_code}
        nextVersionNumber={(req.versions?.length || 0) + 1}
      />

      <VersionReviewModal
        isOpen={isReviewOpen}
        onClose={() => setIsReviewOpen(false)}
        version={latestVersion}
        onApprove={handleApprove}
        onRequestChanges={handleRequestChanges}
        currentUserId={user?.id}
      />

      <AssignDesignerModal
        isOpen={isAssignOpen}
        onClose={() => setIsAssignOpen(false)}
        onAssign={handleAssign}
        requestCode={req.request_code}
        currentPriority={req.priority}
      />

      {/* Evaluate Check Modal */}
      {evaluatingCheck && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden animate-scale-up">
            <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-indigo-600" />
                <h3 className="font-semibold text-slate-900 text-base">Evaluate Compliance Check</h3>
              </div>
              <button
                onClick={() => setEvaluatingCheck(null)}
                className="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveCheckEvaluation} className="p-6 space-y-4">
              <div className="p-3 bg-indigo-50/50 rounded-lg border border-indigo-100 text-xs text-indigo-900">
                <span className="font-semibold">Check Type: </span>
                <span>{evaluatingCheck.check_type_display || evaluatingCheck.check_type}</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Evaluation Verdict
                </label>
                <div className="grid grid-cols-2 gap-2.5">
                  <button
                    type="button"
                    onClick={() => setCheckStatus("PASSED")}
                    className={`p-2.5 rounded-lg text-xs font-semibold border text-center transition-all ${checkStatus === "PASSED"
                        ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                        : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                      }`}
                  >
                    PASSED
                  </button>
                  <button
                    type="button"
                    onClick={() => setCheckStatus("FLAGGED")}
                    className={`p-2.5 rounded-lg text-xs font-semibold border text-center transition-all ${checkStatus === "FLAGGED"
                        ? "bg-rose-600 text-white border-rose-600 shadow-sm"
                        : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                      }`}
                  >
                    FLAGGED
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Evaluation Remarks / Flag Justification {checkStatus === "FLAGGED" && <span className="text-rose-500">*</span>}
                </label>
                <textarea
                  rows={3}
                  value={checkNotes}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setCheckNotes(e.target.value)}
                  placeholder="Record verification observations or flag reasons..."
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setEvaluatingCheck(null)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm">
                  Save Evaluation
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

