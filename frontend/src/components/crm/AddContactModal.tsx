import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { UserCheck, Mail, Phone, X } from "lucide-react";
import { crmApi } from "../../api/crmApi";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

const contactSchema = z.object({
  name: z.string().min(2, "Contact name is required"),
  designation: z.string().optional(),
  department: z.string().optional(),
  email: z.string().email("Invalid email address").or(z.literal("")),
  phone: z.string().optional(),
  preferred_channel: z.string().default("EMAIL"),
  status: z.string().default("ACTIVE"),
  is_primary: z.boolean().default(false),
  notes: z.string().optional(),
});

type ContactFormData = z.infer<typeof contactSchema>;

interface AddContactModalProps {
  companyId: string;
  companyName: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const AddContactModal: React.FC<AddContactModalProps> = ({
  companyId,
  companyName,
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
  } = useForm<ContactFormData>({
    resolver: zodResolver(contactSchema),
    defaultValues: {
      name: "",
      designation: "",
      department: "Human Resources",
      email: "",
      phone: "",
      preferred_channel: "EMAIL",
      status: "ACTIVE",
      is_primary: false,
      notes: "",
    },
  });

  const onSubmit = async (data: ContactFormData) => {
    setServerError(null);
    try {
      await crmApi.createHRContact(companyId, data);
      reset();
      onSuccess();
      onClose();
    } catch (err: any) {
      setServerError(err.response?.data?.detail || "Failed to add HR contact.");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm" role="dialog" aria-modal="true">
      <div className="relative w-full max-w-md rounded-xl bg-white p-6 shadow-xl border border-slate-200">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2 text-brand-navy">
            <UserCheck className="h-5 w-5 text-brand-blue" />
            <div>
              <h2 className="text-base font-bold">Add HR Recruiter Contact</h2>
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
          <Input
            label="Recruiter Name *"
            placeholder="e.g. Priya Sharma"
            error={errors.name?.message}
            {...register("name")}
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Designation"
              placeholder="e.g. Campus Talent Lead"
              {...register("designation")}
            />
            <Input
              label="Department"
              placeholder="e.g. University Relations"
              {...register("department")}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Work Email"
              type="email"
              placeholder="name@company.com"
              leftIcon={<Mail className="h-3.5 w-3.5" />}
              error={errors.email?.message}
              {...register("email")}
            />
            <Input
              label="Work Phone"
              placeholder="+91 98765 43210"
              leftIcon={<Phone className="h-3.5 w-3.5" />}
              {...register("phone")}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Preferred Channel</label>
              <select
                className="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
                {...register("preferred_channel")}
              >
                <option value="EMAIL">Corporate Email</option>
                <option value="PHONE">Direct Phone Call</option>
                <option value="WHATSAPP">WhatsApp</option>
                <option value="LINKEDIN">LinkedIn InMail</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Status</label>
              <select
                className="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
                {...register("status")}
              >
                <option value="ACTIVE">Active Recruiter</option>
                <option value="INACTIVE">Inactive</option>
                <option value="FORMER_EMPLOYEE">Left Company</option>
              </select>
            </div>
          </div>

          <label className="flex items-center gap-2 pt-1 font-medium text-xs text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              className="rounded border-slate-300 text-brand-blue focus:ring-brand-blue"
              {...register("is_primary")}
            />
            <span>Mark as primary institutional placement contact</span>
          </label>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSubmitting}>
              Save Contact
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

