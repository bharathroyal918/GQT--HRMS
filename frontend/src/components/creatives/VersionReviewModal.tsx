import React, { useState } from "react";
import { X, ShieldCheck, AlertTriangle, CheckCircle2 } from "lucide-react";
import { CreativeAssetVersion } from "../../types/creatives";
import { Button } from "../ui/Button";

interface VersionReviewModalProps {
  version: CreativeAssetVersion | null;
  isOpen: boolean;
  onClose: () => void;
  onApprove: (feedback?: string) => Promise<void>;
  onRequestChanges: (feedback: string) => Promise<void>;
  currentUserId?: string;
}

export const VersionReviewModal: React.FC<VersionReviewModalProps> = ({
  version,
  isOpen,
  onClose,
  onApprove,
  onRequestChanges,
  currentUserId,
}) => {
  const [activeTab, setActiveTab] = useState<"APPROVE" | "CHANGES">("APPROVE");
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen || !version) return null;

  const isSelfUpload = Boolean(currentUserId && version.uploader === currentUserId);
  const passedChecksCount = version.compliance_checks.filter((c) => c.status === "PASSED").length;
  const isAllChecksPassed = version.compliance_checks.length === 4 && passedChecksCount === 4;

  const handleApproveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSelfUpload) {
      setError("Segregation of duties violation: Designers cannot self-approve their own submissions.");
      return;
    }
    if (!isAllChecksPassed) {
      setError("All 4 design compliance checks must be marked PASSED before approval can be granted.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onApprove(feedback.trim() || undefined);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to approve version.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChangesSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedback.trim()) {
      setError("Detailed reviewer feedback is mandatory when requesting revisions.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onRequestChanges(feedback.trim());
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to request revisions.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-lg overflow-hidden animate-scale-up">
        <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-600" />
            <div>
              <h3 className="font-semibold text-slate-900 text-base">
                Review Asset Deliverable (v{version.version_number})
              </h3>
              <p className="text-xs text-slate-500">
                Uploaded by {version.uploader_name} • {version.original_filename}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-slate-200 bg-slate-50/50">
          <button
            type="button"
            onClick={() => {
              setActiveTab("APPROVE");
              setError(null);
            }}
            className={`flex-1 py-3 text-xs font-semibold text-center border-b-2 transition-colors ${
              activeTab === "APPROVE"
                ? "border-emerald-600 text-emerald-700 bg-white"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Authorize Approval
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab("CHANGES");
              setError(null);
            }}
            className={`flex-1 py-3 text-xs font-semibold text-center border-b-2 transition-colors ${
              activeTab === "CHANGES"
                ? "border-amber-600 text-amber-700 bg-white"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Request Revisions
          </button>
        </div>

        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          {/* SoD Warning */}
          {isSelfUpload && (
            <div className="p-3 bg-amber-50 border border-amber-300 rounded-lg text-amber-900 text-xs space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-amber-800">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Segregation of Duties Warning:</span>
              </div>
              <p>
                You uploaded this asset version. Under GQT compliance policies, creators cannot self-approve their own submissions. An independent Reviewer or Placement Head must authorize this asset.
              </p>
            </div>
          )}

          {/* 4-Point Checklist Compliance Alert */}
          <div
            className={`p-3 rounded-lg border text-xs flex items-center justify-between ${
              isAllChecksPassed
                ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                : "bg-slate-50 border-slate-200 text-slate-700"
            }`}
          >
            <div className="flex items-center gap-2">
              <CheckCircle2
                className={`w-4 h-4 ${isAllChecksPassed ? "text-emerald-600" : "text-slate-400"}`}
              />
              <span className="font-medium">4-Point Compliance Checks:</span>
            </div>
            <span className="font-bold">
              {passedChecksCount} / 4 Passed
            </span>
          </div>

          {activeTab === "APPROVE" ? (
            <form onSubmit={handleApproveSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Approval Notes / Authorization Remarks
                </label>
                <textarea
                  rows={3}
                  value={feedback}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFeedback(e.target.value)}
                  placeholder="Record formal authorization remarks, placement drive readiness notes..."
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isSubmitting}
                  disabled={isSelfUpload || !isAllChecksPassed}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  Confirm Asset Approval
                </Button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleChangesSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Required Adjustments / Rejection Reason <span className="text-rose-500">*</span>
                </label>
                <textarea
                  rows={4}
                  value={feedback}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFeedback(e.target.value)}
                  placeholder="Explain exactly what the Graphic Designer needs to correct (e.g. CTC range typo, official logo aspect ratio, registration URL)..."
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isSubmitting}
                  className="bg-amber-600 hover:bg-amber-700"
                >
                  Send Revision Request
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

