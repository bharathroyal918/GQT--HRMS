import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Palette, ArrowLeft, Save, AlertCircle } from "lucide-react";
import { creativesApi } from "../../api/creativesApi";
import { crmApi } from "../../api/crmApi";
import { jobsApi } from "../../api/jobsApi";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { LoadingState } from "../../components/ui/LoadingState";
import {
  CreativeType,
  AspectRatio,
  DeliverableFormat,
  CreativePriority,
} from "../../types/creatives";

export const CreativeRequestFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditMode = Boolean(id);

  const [title, setTitle] = useState("");
  const [brief, setBrief] = useState("");
  const [creativeType, setCreativeType] = useState<CreativeType>("JOB_FLYER");
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>("4:5");
  const [deliverableFormat, setDeliverableFormat] = useState<DeliverableFormat>("PNG");
  const [priority, setPriority] = useState<CreativePriority>("MEDIUM");
  const [targetDate, setTargetDate] = useState("");
  const [companyId, setCompanyId] = useState("");
  const [jobId, setJobId] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch companies for dropdown
  const { data: companiesData } = useQuery({
    queryKey: ["companiesDropdownList"],
    queryFn: () => crmApi.getCompanies({ page_size: 100 }),
  });

  // Fetch approved jobs for dropdown
  const { data: jobsData } = useQuery({
    queryKey: ["approvedJobsDropdownList"],
    queryFn: () => jobsApi.getJobs({ page_size: 100 }),
  });

  // Fetch requisition if editing
  const { data: existingReq, isLoading: isLoadingReq } = useQuery({
    queryKey: ["creativeRequestDetail", id],
    queryFn: () => creativesApi.getRequestDetail(id!),
    enabled: isEditMode,
  });

  useEffect(() => {
    if (existingReq) {
      setTitle(existingReq.title);
      setBrief(existingReq.brief);
      setCreativeType(existingReq.creative_type);
      setAspectRatio(existingReq.aspect_ratio);
      setDeliverableFormat(existingReq.deliverable_format);
      setPriority(existingReq.priority);
      setTargetDate(existingReq.target_completion_date || "");
      setCompanyId(existingReq.company || "");
      setJobId(existingReq.job_requirement || "");
    }
  }, [existingReq]);

  if (isEditMode && isLoadingReq) {
    return <LoadingState message="Loading requisition details..." />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !brief.trim()) {
      setError("Please fill out both the title and detailed creative brief.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const payload = {
        title: title.trim(),
        brief: brief.trim(),
        creative_type: creativeType,
        aspect_ratio: aspectRatio,
        deliverable_format: deliverableFormat,
        priority,
        target_completion_date: targetDate || null,
        company_id: companyId || null,
        job_requirement_id: jobId || null,
      };

      if (isEditMode && id) {
        await creativesApi.updateRequest(id, payload);
        navigate(`/creatives/${id}`);
      } else {
        const created = await creativesApi.createRequest(payload);
        navigate(`/creatives/${created.id}`);
      }
    } catch (err: any) {
      setError(
        err?.response?.data?.title?.[0] ||
          err?.response?.data?.brief?.[0] ||
          err?.response?.data?.detail ||
          "Failed to save creative requisition."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Back button */}
      <div>
        <button
          type="button"
          onClick={() => navigate("/creatives/directory")}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Requisition Directory</span>
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-50 text-indigo-700 rounded-lg">
              <Palette className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">
                {isEditMode ? `Edit Requisition (${existingReq?.request_code})` : "New Creative Marketing Requisition"}
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Define the deliverable format, brief instructions, and corporate branding references.
              </p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          {/* Title & Type */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Campaign / Flyer Title <span className="text-rose-500">*</span>
              </label>
              <Input
                value={title}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)}
                placeholder="e.g. Infosys Campus Drive 2026 Announcement"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Asset Type
              </label>
              <select
                value={creativeType}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setCreativeType(e.target.value as CreativeType)}
                className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-700 outline-none focus:border-indigo-500"
              >
                <option value="JOB_FLYER">Job Opening Flyer</option>
                <option value="WHATSAPP_BANNER">WhatsApp Banner</option>
                <option value="INSTAGRAM_POST">Instagram Post (1:1)</option>
                <option value="LINKEDIN_BANNER">LinkedIn Post (16:9)</option>
                <option value="EMAIL_HEADER">Email Header Graphic</option>
                <option value="CAMPUS_POSTER">Campus Noticeboard Poster (A4)</option>
                <option value="CUSTOM">Custom Marketing Asset</option>
              </select>
            </div>
          </div>

          {/* Aspect Ratio, Format, Priority */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Aspect Ratio
              </label>
              <select
                value={aspectRatio}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setAspectRatio(e.target.value as AspectRatio)}
                className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-700 outline-none focus:border-indigo-500"
              >
                <option value="4:5">4:5 Social Banner</option>
                <option value="1:1">1:1 Square</option>
                <option value="16:9">16:9 Landscape</option>
                <option value="9:16">9:16 Story / Reel</option>
                <option value="A4_PORTRAIT">A4 Print Format</option>
                <option value="CUSTOM">Custom Dimensions</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Deliverable Format
              </label>
              <select
                value={deliverableFormat}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setDeliverableFormat(e.target.value as DeliverableFormat)}
                className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-700 outline-none focus:border-indigo-500"
              >
                <option value="PNG">PNG Image</option>
                <option value="JPEG">JPEG Image</option>
                <option value="WEBP">WebP Image</option>
                <option value="PDF">Print-Ready PDF</option>
                <option value="MULTI_FORMAT">Multi-Format Package</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Turnaround Priority
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
          </div>

          {/* Associated Job & Target Date */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Target Corporate Partner
              </label>
              <select
                value={companyId}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setCompanyId(e.target.value)}
                className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-700 outline-none focus:border-indigo-500"
              >
                <option value="">None / Internal Brand Campaign</option>
                {companiesData?.results?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Linked Job Requirement
              </label>
              <select
                value={jobId}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setJobId(e.target.value)}
                className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-700 outline-none focus:border-indigo-500"
              >
                <option value="">None / Standalone Requisition</option>
                {jobsData?.results?.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title} ({j.company_name})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Target Completion Deadline
              </label>
              <Input
                type="date"
                value={targetDate}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTargetDate(e.target.value)}
              />
            </div>
          </div>

          {/* Creative Brief */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Creative Brief & Visual Specifications <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={6}
              value={brief}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setBrief(e.target.value)}
              placeholder="Detail copy instructions, eligibility criteria bullets, fixed/variable package highlights, QR code links, color palette suggestions, and official logo placement..."
              className="w-full text-xs rounded-lg border border-slate-300 p-3 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
              required
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => navigate("/creatives/directory")}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isSubmitting}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              <Save className="w-4 h-4 mr-1.5" />
              <span>{isEditMode ? "Save Changes" : "Create Requisition"}</span>
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

