import React, { useState } from "react";
import { X, HelpCircle, AlertCircle } from "lucide-react";
import { JobRequirementDetail } from "../../types/jobs";
import { Button } from "../ui/Button";

interface RequestChangesModalProps {
  job: JobRequirementDetail | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason: string) => Promise<void>;
}

export const RequestChangesModal: React.FC<RequestChangesModalProps> = ({
  job,
  isOpen,
  onClose,
  onConfirm,
}) => {
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen || !job) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) {
      setError("Please explain the required adjustments so the Placement Officer can revise the requirement.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onConfirm(reason.trim());
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.reason?.[0] || err?.response?.data?.detail || "Failed to request changes.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden animate-scale-up">
        <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-amber-600" />
            <h3 className="font-semibold text-slate-900 text-base">Request Revisions & Changes</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <p className="text-xs text-slate-600 leading-relaxed">
            This will transition <strong className="text-slate-900">{job.title}</strong> to{" "}
            <span className="font-semibold text-amber-700">CHANGES_REQUESTED</span> and return it to the submitting Placement Officer.
          </p>

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Required Modifications Feedback <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={4}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Detail specific criteria that must be corrected (e.g., minimum CGPA mismatch, unconfirmed CTC breakdown, extend registration deadline)..."
              className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 outline-none"
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
              className="bg-amber-600 hover:bg-amber-700 text-white"
            >
              Send Feedback
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

