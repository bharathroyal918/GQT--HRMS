import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { AlertCircle, Building2, Globe, X } from "lucide-react";
import { crmApi } from "../../api/crmApi";
import { DuplicateCheckResult } from "../../types/crm";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

const companySchema = z.object({
  name: z.string().min(2, "Company name is required (minimum 2 characters)"),
  website: z.string().url("Must be a valid website URL (e.g. https://example.com)").or(z.literal("")),
  industry: z.string().min(1, "Please select an industry category"),
  source: z.string().min(1, "Please select an acquisition source"),
  status: z.string().min(1, "Please select an acquisition status"),
  tier: z.string().default("UNRATED"),
  notes: z.string().optional(),
});

type CompanyFormData = z.infer<typeof companySchema>;

interface CreateCompanyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateCompanyModal: React.FC<CreateCompanyModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [duplicateCheck, setDuplicateCheck] = useState<DuplicateCheckResult | null>(null);
  const [isCheckingDuplicate, setIsCheckingDuplicate] = useState(false);
  const [allowDuplicate, setAllowDuplicate] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CompanyFormData>({
    resolver: zodResolver(companySchema),
    defaultValues: {
      name: "",
      website: "",
      industry: "IT_SERVICES",
      source: "OUTBOUND_CALLING",
      status: "LEAD",
      tier: "UNRATED",
      notes: "",
    },
  });

  const companyName = watch("name");
  const companyWebsite = watch("website");

  const runDuplicateCheck = async () => {
    if (!companyName || companyName.trim().length < 2) return;
    setIsCheckingDuplicate(true);
    try {
      const res = await crmApi.checkDuplicateCompany(companyName, companyWebsite);
      setDuplicateCheck(res);
    } catch (err) {
      console.warn("Duplicate check error", err);
    } finally {
      setIsCheckingDuplicate(false);
    }
  };

  const onSubmit = async (data: CompanyFormData) => {
    setServerError(null);
    try {
      await crmApi.createCompany({
        ...data,
        allow_duplicate: allowDuplicate,
      });
      reset();
      setDuplicateCheck(null);
      setAllowDuplicate(false);
      onSuccess();
      onClose();
    } catch (err: any) {
      setServerError(err.response?.data?.detail || "Failed to create company. Please check fields.");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm" role="dialog" aria-modal="true">
      <div className="relative w-full max-w-lg rounded-xl bg-white p-6 shadow-xl border border-slate-200 overflow-y-auto max-h-[90vh]">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2 text-brand-navy">
            <Building2 className="h-5 w-5 text-brand-blue" />
            <h2 className="text-base font-bold">Add Target Company</h2>
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
          <div className="mt-4 rounded-md bg-red-50 p-3 text-xs text-red-700 border border-red-200">
            {serverError}
          </div>
        )}

        {duplicateCheck && duplicateCheck.is_duplicate && (
          <div className="mt-4 rounded-md bg-amber-50 p-3.5 border border-amber-200 text-xs text-amber-900 space-y-2">
            <div className="flex items-start gap-2 font-semibold">
              <AlertCircle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
              <span>Potential Duplicate Detected ({duplicateCheck.match_count} existing matches)</span>
            </div>
            <ul className="list-disc pl-5 space-y-1 text-slate-700">
              {duplicateCheck.matches.map((m) => (
                <li key={m.id}>
                  <span className="font-medium text-brand-dark">{m.name}</span> — {m.canonical_domain || "No domain"} ({m.status})
                </li>
              ))}
            </ul>
            <label className="flex items-center gap-2 pt-1 font-medium text-amber-950 cursor-pointer">
              <input
                type="checkbox"
                checked={allowDuplicate}
                onChange={(e) => setAllowDuplicate(e.target.checked)}
                className="rounded border-amber-300 text-brand-blue focus:ring-brand-blue"
              />
              <span>I confirm this is a separate company / subsidiary. Proceed anyway.</span>
            </label>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-4">
          <Input
            label="Company Name *"
            placeholder="e.g. Infosys Technologies"
            error={errors.name?.message}
            {...register("name")}
            onBlur={runDuplicateCheck}
          />

          <Input
            label="Corporate Website"
            placeholder="https://www.company.com"
            leftIcon={<Globe className="h-4 w-4" />}
            error={errors.website?.message}
            {...register("website")}
            onBlur={runDuplicateCheck}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Industry Category *</label>
              <select
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
                {...register("industry")}
              >
                <option value="IT_SERVICES">IT Services & Consulting</option>
                <option value="PRODUCT_TECH">Product / Software Tech</option>
                <option value="FINTECH">FinTech & Banking</option>
                <option value="EDTECH">EdTech & Learning</option>
                <option value="HEALTHCARE">Healthcare & Pharma</option>
                <option value="MANUFACTURING">Manufacturing & Engineering</option>
                <option value="ECOMMERCE">E-Commerce & Retail</option>
                <option value="CONSULTING">Management Consulting</option>
                <option value="TELECOM">Telecommunications</option>
                <option value="OTHER">Other Industry</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Acquisition Source *</label>
              <select
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
                {...register("source")}
              >
                <option value="OUTBOUND_CALLING">Outbound Cold Calling</option>
                <option value="INBOUND_INQUIRY">Inbound Inquiry</option>
                <option value="JOB_PORTAL">Job Portal Lead</option>
                <option value="CAMPUS_ALUMNI">Campus Alumni Referral</option>
                <option value="LINKEDIN">LinkedIn Outreach</option>
                <option value="EXECUTIVE_REFERRAL">Leadership Referral</option>
                <option value="OTHER">Other Source</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Pipeline Status *</label>
              <select
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
                {...register("status")}
              >
                <option value="LEAD">Lead / Prospect</option>
                <option value="CONTACTED">Contacted / In Outreach</option>
                <option value="ENGAGED">Engaged / In Discussion</option>
                <option value="ACTIVE_HIRING_PARTNER">Active Hiring Partner</option>
                <option value="DORMANT">Dormant</option>
                <option value="BLACKLISTED">Blacklisted</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Company Tier</label>
              <select
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
                {...register("tier")}
              >
                <option value="UNRATED">Unrated</option>
                <option value="TIER_1">Tier 1 (Enterprise / MNC)</option>
                <option value="TIER_2">Tier 2 (Mid-Market)</option>
                <option value="TIER_3">Tier 3 (Startup)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Account Notes</label>
            <textarea
              rows={3}
              placeholder="Key hiring background, tech stacks, or corporate campus requirements..."
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
              {...register("notes")}
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isSubmitting || isCheckingDuplicate}
            >
              Save Company
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

