import React, { useState } from "react";
import { X, UserCheck, AlertCircle } from "lucide-react";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { CreativePriority } from "../../types/creatives";

interface AssignDesignerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAssign: (payload: { assigned_designer_id: string; priority?: string; notes?: string }) => Promise<void>;
  requestCode: string;
  currentPriority: CreativePriority;
}

export const AssignDesignerModal: React.FC<AssignDesignerModalProps> = ({
  isOpen,
  onClose,
  onAssign,
  requestCode,
  currentPriority,
}) => {
  const [designerId, setDesignerId] = useState("");
  const [priority, setPriority] = useState<CreativePriority>(currentPriority);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!designerId.trim()) {
      setError("Please specify the designer user UUID.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onAssign({
        assigned_designer_id: designerId.trim(),
        priority,
        notes: notes.trim() || undefined,
      });
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.assigned_designer_id?.[0] || err?.response?.data?.detail || "Assignment failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden animate-scale-up">
        <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50">
          <div className="flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-indigo-600" />
            <h3 className="font-semibold text-slate-900 text-base">Assign Graphic Designer</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="p-3 bg-indigo-50/50 rounded-lg border border-indigo-100 text-xs text-indigo-900">
            <span className="font-semibold">Requisition: </span>
            <span className="font-mono">{requestCode}</span>
          </div>

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Designer User UUID <span className="text-rose-500">*</span>
            </label>
            <Input
              value={designerId}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDesignerId(e.target.value)}
              placeholder="e.g. 22222222-2222-2222-2222-222222222222"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Requisition Priority
            </label>
            <select
              value={priority}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setPriority(e.target.value as CreativePriority)}
              className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-700 outline-none focus:border-indigo-500"
            >
              <option value="LOW">Low Priority</option>
              <option value="MEDIUM">Medium Priority</option>
              <option value="HIGH">High Priority</option>
              <option value="URGENT">Urgent / Fast-Track</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Triage Instructions / Notes
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNotes(e.target.value)}
              placeholder="Provide turnaround instructions or campus drive timeline..."
              className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSubmitting}>
              Confirm Assignment
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

