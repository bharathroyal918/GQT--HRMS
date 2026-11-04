import React, { useState } from "react";
import { X, CheckCircle2, AlertTriangle, AlertCircle } from "lucide-react";
import { JobRequirementDetail } from "../../types/jobs";
import { Button } from "../ui/Button";

interface ApprovalModalProps {
  job: JobRequirementDetail | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (notes: string) => Promise<void>;
  currentUserId?: string;
}

export const ApprovalModal: React.FC<ApprovalModalProps> = ({
  job,
  isOpen,
  onClose,
  onConfirm,
  currentUserId,
}) => {
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen || !job) return null;

  const isSubmitter = Boolean(currentUserId && job.submitted_by === currentUserId);
  const isAllChecksVerified = job.is_all_checks_verified;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitter) {
      setError("Segregation of Duties Violation: You cannot approve a job that you submitted.");
      return;
    }
    if (!isAllChecksVerified) {
      setError("Approval Denied: All 5 mandatory verification checks must be VERIFIED first.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onConfirm(notes.trim());
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to approve job requirement.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden animate-scale-up">
        <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <h3 className="font-semibold text-slate-900 text-base">Authorize & Approve Job</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <p className="text-xs text-slate-600 leading-relaxed">
            You are about to formally authorize <strong className="text-slate-900">{job.title}</strong> at{" "}
            <strong className="text-slate-900">{job.company_name}</strong>. Once approved, the requirement will be locked against ordinary edits.
          </p>

          {isSubmitter && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-2 text-rose-800 text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
              <div>
                <span className="font-bold">Segregation of Duties Warning:</span> You submitted this requirement. An independent Placement Head must conduct the final sign-off.
              </div>
            </div>
          )}

          {!isAllChecksVerified && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2 text-amber-800 text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
              <div>
                <span className="font-bold">Incomplete Verification:</span> Only {job.verification_summary?.verified_count || 0} / 5 checks are verified. All checks must pass before approval.
              </div>
            </div>
          )}

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Approval Sign-Off Notes (Optional)
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNotes(e.target.value)}
              placeholder="e.g., Reviewed against company quota and verified with corporate recruiter..."
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
              disabled={isSubmitter || !isAllChecksVerified}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              Confirm Approval
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
