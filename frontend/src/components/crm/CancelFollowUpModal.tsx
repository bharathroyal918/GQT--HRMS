import React, { useState } from "react";
import { XCircle, X } from "lucide-react";
import { crmApi } from "../../api/crmApi";
import { FollowUp } from "../../types/crm";
import { Button } from "../ui/Button";

interface CancelFollowUpModalProps {
  followUp: FollowUp | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const CancelFollowUpModal: React.FC<CancelFollowUpModalProps> = ({
  followUp,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !followUp) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (reason.trim().length < 3) {
      setError("Please provide a cancellation reason (minimum 3 characters).");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      await crmApi.cancelFollowUp(followUp.id, reason);
      setReason("");
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to cancel follow-up.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm" role="dialog" aria-modal="true">
      <div className="relative w-full max-w-sm rounded-xl bg-white p-6 shadow-xl border border-slate-200">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2 text-red-600">
            <XCircle className="h-5 w-5" />
            <h2 className="text-sm font-bold text-brand-navy">Cancel Follow-Up</h2>
          </div>
          <button type="button" onClick={onClose} className="rounded p-1 text-slate-400 hover:bg-slate-100">
            <X className="h-4 w-4" />
          </button>
        </div>

        {error && (
          <div className="mt-3 rounded-md bg-red-50 p-2 text-xs text-red-700 border border-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-3">
          <div>
            <p className="text-xs font-semibold text-brand-dark">{followUp.title}</p>
            <p className="text-[11px] text-slate-500">{followUp.company_name}</p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Cancellation Reason *</label>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Hiring drive postponed to next fiscal quarter by company..."
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Go Back
            </Button>
            <Button type="submit" variant="danger" size="sm" isLoading={isSubmitting}>
              Confirm Cancellation
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

