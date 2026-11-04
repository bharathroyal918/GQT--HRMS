import React, { useState } from "react";
import { X, ShieldCheck, AlertCircle } from "lucide-react";
import { JobVerificationCheck, CheckStatus } from "../../types/jobs";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

interface UpdateCheckModalProps {
  check: JobVerificationCheck | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (checkType: string, payload: { status: CheckStatus; notes?: string; evidence_reference?: string }) => Promise<void>;
}

export const UpdateCheckModal: React.FC<UpdateCheckModalProps> = ({
  check,
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [selectedStatus, setSelectedStatus] = useState<CheckStatus>(check?.status || "VERIFIED");
  const [notes, setNotes] = useState(check?.notes || "");
  const [evidence, setEvidence] = useState(check?.evidence_reference || "");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Sync state when check changes
  React.useEffect(() => {
    if (check) {
      setSelectedStatus(check.status === "PENDING" ? "VERIFIED" : check.status);
      setNotes(check.notes || "");
      setEvidence(check.evidence_reference || "");
      setError(null);
    }
  }, [check]);

  if (!isOpen || !check) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((selectedStatus === "FLAGGED" || selectedStatus === "REJECTED") && !notes.trim()) {
      setError("Documented reviewer notes are required when flagging or rejecting a check.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onSubmit(check.check_type, {
        status: selectedStatus,
        notes: notes.trim(),
        evidence_reference: evidence.trim(),
      });
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.notes?.[0] || err?.response?.data?.detail || "Failed to update check.");
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
            <h3 className="font-semibold text-slate-900 text-base">Evaluate Verification Check</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="p-3 bg-indigo-50/50 rounded-lg border border-indigo-100 text-xs text-indigo-900">
            <span className="font-semibold">Check Type: </span>
            <span className="font-mono">{check.check_type}</span>
          </div>

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Verification Evaluation <span className="text-rose-500">*</span>
            </label>
            <div className="grid grid-cols-2 gap-2.5">
              {(["VERIFIED", "FLAGGED", "REJECTED", "PENDING"] as CheckStatus[]).map((st) => (
                <button
                  type="button"
                  key={st}
                  onClick={() => setSelectedStatus(st)}
                  className={`p-2.5 rounded-lg text-xs font-semibold border text-center transition-all ${
                    selectedStatus === st
                      ? st === "VERIFIED"
                        ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                        : st === "FLAGGED"
                        ? "bg-amber-500 text-white border-amber-500 shadow-sm"
                        : st === "REJECTED"
                        ? "bg-rose-600 text-white border-rose-600 shadow-sm"
                        : "bg-slate-700 text-white border-slate-700 shadow-sm"
                      : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Evidence Reference / Link
            </label>
            <Input
              value={evidence}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEvidence(e.target.value)}
              placeholder="e.g., CIN/GST registry link, prior offer letter doc, salary benchmark URL"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Reviewer Notes / Findings {selectedStatus !== "VERIFIED" && <span className="text-rose-500">*</span>}
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNotes(e.target.value)}
              placeholder="Record observations, institutional policy verification notes, or discrepancy reasons..."
              className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSubmitting}>
              Save Evaluation
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

