import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { PhoneCall, Calendar, X } from "lucide-react";
import { crmApi } from "../../api/crmApi";
import { HRContact } from "../../types/crm";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

const outreachSchema = z.object({
  contact_id: z.string().optional(),
  channel: z.string().min(1, "Outreach channel is required"),
  outcome: z.string().min(1, "Outreach outcome is required"),
  notes: z.string().min(3, "Notes are required (minimum 3 characters)"),
  next_action: z.string().optional(),
  follow_up_date: z.string().optional(),
});

type OutreachFormData = z.infer<typeof outreachSchema>;

interface LogOutreachModalProps {
  companyId: string;
  companyName: string;
  contacts: HRContact[];
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const LogOutreachModal: React.FC<LogOutreachModalProps> = ({
  companyId,
  companyName,
  contacts,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<OutreachFormData>({
    resolver: zodResolver(outreachSchema),
    defaultValues: {
      channel: "PHONE",
      outcome: "INTERESTED",
      notes: "",
      next_action: "",
      follow_up_date: "",
    },
  });

  const onSubmit = async (data: OutreachFormData) => {
    setServerError(null);
    try {
      await crmApi.logOutreach(companyId, {
        channel: data.channel,
        outcome: data.outcome,
        notes: data.notes,
        next_action: data.next_action || "",
        contact_id: data.contact_id || null,
        follow_up_date: data.follow_up_date ? new Date(data.follow_up_date).toISOString() : null,
      });
      reset();
      onSuccess();
      onClose();
    } catch (err: any) {
      setServerError(err.response?.data?.detail || "Failed to log outreach touchpoint.");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm" role="dialog" aria-modal="true">
      <div className="relative w-full max-w-md rounded-xl bg-white p-6 shadow-xl border border-slate-200">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2 text-brand-navy">
            <PhoneCall className="h-5 w-5 text-brand-blue" />
            <div>
              <h2 className="text-base font-bold">Log Calling / Outreach</h2>
              <p className="text-[11px] text-slate-500">{companyName}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {serverError && (
          <div className="mt-3 rounded-md bg-red-50 p-2.5 text-xs text-red-700 border border-red-200">
            {serverError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-3.5">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Contact Person (Optional)</label>
            <select
              className="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
              {...register("contact_id")}
            >
              <option value="">General Corporate Outreach (No contact selected)</option>
              {contacts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} {c.designation ? `(${c.designation})` : ""}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Outreach Channel *</label>
              <select
                className="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
                {...register("channel")}
              >
                <option value="PHONE">Phone Call</option>
                <option value="EMAIL">Email</option>
                <option value="WHATSAPP">WhatsApp</option>
                <option value="LINKEDIN">LinkedIn</option>
                <option value="IN_PERSON">In-Person Meeting</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Outcome / Disposition *</label>
              <select
                className="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
                {...register("outcome")}
              >
                <option value="INTERESTED">Interested in Hiring</option>
                <option value="FOLLOW_UP_REQUESTED">Requested Callback</option>
                <option value="MEETING_SCHEDULED">Meeting Scheduled</option>
                <option value="REQUIREMENT_SHARED">JD Received</option>
                <option value="NOT_INTERESTED">Not Hiring</option>
                <option value="CALL_NOT_ANSWERED">No Answer / Ringing</option>
                <option value="WRONG_NUMBER">Wrong Number</option>
                <option value="GATEKEEPER_BLOCKED">Gatekeeper Blocked</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Touchpoint Notes *</label>
            <textarea
              rows={3}
              placeholder="What was discussed? Number of hires, tech stacks, or eligibility expectations..."
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
              {...register("notes")}
            />
            {errors.notes && <p className="text-xs text-red-600 mt-1">{errors.notes.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Next Action"
              placeholder="e.g. Email placement deck"
              {...register("next_action")}
            />
            <Input
              label="Auto Schedule Follow-Up"
              type="datetime-local"
              leftIcon={<Calendar className="h-3.5 w-3.5" />}
              {...register("follow_up_date")}
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSubmitting}>
              Log Outreach Touchpoint
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

