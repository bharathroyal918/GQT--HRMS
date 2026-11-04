import React, { useState } from "react";
import { X, RefreshCw, AlertTriangle, AlertCircle } from "lucide-react";
import { JobRequirementDetail } from "../../types/jobs";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

interface AmendJobModalProps {
  job: JobRequirementDetail | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (payload: { reason: string; min_ctc_lpa?: number; max_ctc_lpa?: number; title?: string }) => Promise<void>;
}

export const AmendJobModal: React.FC<AmendJobModalProps> = ({
  job,
  isOpen,
  onClose,
  onConfirm,
}) => {
  const [reason, setReason] = useState("");
  const [title, setTitle] = useState(job?.title || "");
  const [minCtc, setMinCtc] = useState(job?.min_ctc_lpa || "");
  const [maxCtc, setMaxCtc] = useState(job?.max_ctc_lpa || "");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  React.useEffect(() => {
    if (job) {
      setTitle(job.title);
      setMinCtc(job.min_ctc_lpa);
      setMaxCtc(job.max_ctc_lpa);
      setReason("");
      setError(null);
    }
  }, [job]);

  if (!isOpen || !job) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim() || reason.trim().length < 10) {
      setError("An explicit amendment justification of at least 10 characters is required.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onConfirm({
        reason: reason.trim(),
        title: title.trim(),
        min_ctc_lpa: minCtc ? Number(minCtc) : undefined,
        max_ctc_lpa: maxCtc ? Number(maxCtc) : undefined,
      });
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.reason?.[0] || err?.response?.data?.detail || "Failed to amend approved job.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-lg overflow-hidden animate-scale-up">
        <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50">
          <div className="flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-indigo-600" />
            <h3 className="font-semibold text-slate-900 text-base">Authorized Revision #{job.revision_number + 1}</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2 text-amber-800 text-xs">
            <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
            <div>
              <span className="font-bold">Important Audit Notice:</span> Authorizing an amendment will unlock this approved job, increment the revision number, and automatically invalidate the affected verification checks so they must be re-verified.
            </div>
          </div>

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Amendment Reason / Recruiter Memo <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={3}
              value={reason}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setReason(e.target.value)}
              placeholder="e.g., Recruiter updated compensation structure to 8.5 LPA fixed base..."
              className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Role Title
            </label>
            <Input value={title} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Min CTC (LPA)
              </label>
              <Input
                type="number"
                step="0.01"
                value={minCtc}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMinCtc(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Max CTC (LPA)
              </label>
              <Input
                type="number"
                step="0.01"
                value={maxCtc}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMaxCtc(e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSubmitting}>
              Create Revision #{job.revision_number + 1}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
