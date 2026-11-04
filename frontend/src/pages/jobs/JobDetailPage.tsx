import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Send,
  Edit3,
  RefreshCw,
  Building2,
  MapPin,
  Calendar,
  History,
  ShieldCheck,
  AlertTriangle,
} from "lucide-react";
import { jobsApi } from "../../api/jobsApi";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { JobStatusBadge } from "../../components/jobs/JobStatusBadge";
import { VerificationChecklistCard } from "../../components/jobs/VerificationChecklistCard";
import { UpdateCheckModal } from "../../components/jobs/UpdateCheckModal";
import { ApprovalModal } from "../../components/jobs/ApprovalModal";
import { RejectModal } from "../../components/jobs/RejectModal";
import { RequestChangesModal } from "../../components/jobs/RequestChangesModal";
import { AmendJobModal } from "../../components/jobs/AmendJobModal";
import { JobVerificationCheck, CheckStatus } from "../../types/jobs";

export const JobDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  // Modals state
  const [activeCheck, setActiveCheck] = useState<JobVerificationCheck | null>(null);
  const [isApprovalOpen, setIsApprovalOpen] = useState(false);
  const [isRejectOpen, setIsRejectOpen] = useState(false);
  const [isChangesOpen, setIsChangesOpen] = useState(false);
  const [isAmendOpen, setIsAmendOpen] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const {
    data: job,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["jobDetail", id],
    queryFn: () => jobsApi.getJobDetail(id!),
    enabled: Boolean(id),
  });

  if (isLoading) {
    return <LoadingState message="Loading job requirement specifications..." />;
  }

  if (isError || !job) {
    return (
      <ErrorState
        title="Job requirement not found"
        message={(error as any)?.message || "Could not retrieve the requested job specification."}
        onRetry={refetch}
      />
    );
  }

  // Role evaluations
  const userRoles = user?.roles || [];
  const isAdminOrHead = userRoles.includes("ADMIN") || userRoles.includes("PLACEMENT_HEAD");
  const isOfficer = userRoles.includes("PLACEMENT_OFFICER");
  const canVerify = isAdminOrHead || isOfficer;
  const isJobLocked = job.status === "APPROVED" || job.status === "REJECTED";
  const isSubmitter = Boolean(user?.id && job.submitted_by === user.id);

  // Workflow Handlers
  const handleSubmitForVerification = async () => {
    try {
      setActionError(null);
      await jobsApi.submitForVerification(job.id);
      queryClient.invalidateQueries({ queryKey: ["jobDetail", job.id] });
      queryClient.invalidateQueries({ queryKey: ["jobsList"] });
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || "Failed to submit for verification.");
    }
  };

  const handleUpdateCheck = async (
    checkType: string,
    payload: { status: CheckStatus; notes?: string; evidence_reference?: string }
  ) => {
    await jobsApi.updateCheck(job.id, checkType, payload);
    queryClient.invalidateQueries({ queryKey: ["jobDetail", job.id] });
    queryClient.invalidateQueries({ queryKey: ["jobsList"] });
  };

  const handleApprove = async (notes: string) => {
    await jobsApi.approveJob(job.id, notes);
    queryClient.invalidateQueries({ queryKey: ["jobDetail", job.id] });
    queryClient.invalidateQueries({ queryKey: ["jobsList"] });
    queryClient.invalidateQueries({ queryKey: ["jobWorkflowMetrics"] });
  };

  const handleReject = async (reason: string) => {
    await jobsApi.rejectJob(job.id, reason);
    queryClient.invalidateQueries({ queryKey: ["jobDetail", job.id] });
    queryClient.invalidateQueries({ queryKey: ["jobsList"] });
    queryClient.invalidateQueries({ queryKey: ["jobWorkflowMetrics"] });
  };

  const handleRequestChanges = async (reason: string) => {
    await jobsApi.requestChanges(job.id, reason);
    queryClient.invalidateQueries({ queryKey: ["jobDetail", job.id] });
    queryClient.invalidateQueries({ queryKey: ["jobsList"] });
  };

  const handleAmend = async (payload: { reason: string; min_ctc_lpa?: number; max_ctc_lpa?: number; title?: string }) => {
    await jobsApi.amendApprovedJob(job.id, payload);
    queryClient.invalidateQueries({ queryKey: ["jobDetail", job.id] });
    queryClient.invalidateQueries({ queryKey: ["jobsList"] });
  };

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate("/jobs")}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Job Directory</span>
        </button>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
          <span>Job ID: {job.id.slice(0, 8)}</span>
          <span>•</span>
          <span className="font-semibold text-slate-700">Revision #{job.revision_number}</span>
        </div>
      </div>

      {actionError && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-500" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Main Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-slate-900">{job.title}</h1>
              <JobStatusBadge status={job.status} />
              {job.revision_number > 1 && (
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-purple-100 text-purple-800 font-semibold">
                  v{job.revision_number}
                </span>
              )}
            </div>

            <div className="flex items-center gap-4 text-xs text-slate-500 flex-wrap">
              <span className="flex items-center gap-1.5 font-medium text-slate-700">
                <Building2 className="w-4 h-4 text-slate-400" />
                {job.company_name}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-slate-400" />
                {job.job_location || "Location not specified"} ({job.work_arrangement})
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5">
                <Calendar className="w-4 h-4 text-slate-400" />
                Deadline: {new Date(job.registration_deadline).toLocaleDateString()}
              </span>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center gap-2.5 flex-wrap self-start lg:self-center">
            {/* Draft / Changes Requested Actions */}
            {(job.status === "DRAFT" || job.status === "CHANGES_REQUESTED") && canVerify && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/jobs/${job.id}/edit`)}
                  className="flex items-center gap-1.5"
                >
                  <Edit3 className="w-4 h-4" />
                  <span>Edit Draft</span>
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleSubmitForVerification}
                  className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700"
                >
                  <Send className="w-4 h-4" />
                  <span>Submit for Verification</span>
                </Button>
              </>
            )}

            {/* Verification Phase Actions */}
            {(job.status === "PENDING_VERIFICATION" || job.status === "UNDER_VERIFICATION") && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsChangesOpen(true)}
                  className="flex items-center gap-1.5 text-amber-700 hover:bg-amber-50"
                >
                  <HelpCircle className="w-4 h-4 text-amber-600" />
                  <span>Request Changes</span>
                </Button>
                {isAdminOrHead && (
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => setIsRejectOpen(true)}
                    className="flex items-center gap-1.5"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject</span>
                  </Button>
                )}
              </>
            )}

            {/* Approval Phase Actions */}
            {job.status === "PENDING_APPROVAL" && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsChangesOpen(true)}
                  className="flex items-center gap-1.5 text-amber-700 hover:bg-amber-50"
                >
                  <HelpCircle className="w-4 h-4 text-amber-600" />
                  <span>Request Changes</span>
                </Button>

                {isAdminOrHead && (
                  <>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => setIsRejectOpen(true)}
                      className="flex items-center gap-1.5"
                    >
                      <XCircle className="w-4 h-4" />
                      <span>Reject</span>
                    </Button>

                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setIsApprovalOpen(true)}
                      disabled={isSubmitter}
                      className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700"
                      title={isSubmitter ? "Cannot approve self-submitted job (SoD rule)" : "Authorize and approve"}
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Approve Job</span>
                    </Button>
                  </>
                )}
              </>
            )}

            {/* Approved Job Revision */}
            {job.status === "APPROVED" && isAdminOrHead && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsAmendOpen(true)}
                className="flex items-center gap-1.5 text-indigo-700 hover:bg-indigo-50"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Amend Approved Job</span>
              </Button>
            )}
          </div>
        </div>

        {/* Changes requested banner */}
        {job.status === "CHANGES_REQUESTED" && job.changes_requested_reason && (
          <div className="mt-4 p-4 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900">
            <div className="font-bold flex items-center gap-1.5 text-amber-900 mb-1">
              <HelpCircle className="w-4 h-4 text-amber-600" />
              Revisions Requested by Reviewer
            </div>
            <p>{job.changes_requested_reason}</p>
          </div>
        )}

        {/* Rejection banner */}
        {job.status === "REJECTED" && job.rejection_reason && (
          <div className="mt-4 p-4 bg-rose-50 rounded-xl border border-rose-200 text-xs text-rose-900">
            <div className="font-bold flex items-center gap-1.5 text-rose-900 mb-1">
              <XCircle className="w-4 h-4 text-rose-600" />
              Job Rejected by Placement Head
            </div>
            <p>{job.rejection_reason}</p>
          </div>
        )}

        {/* Submitter SoD Warning Banner */}
        {job.status === "PENDING_APPROVAL" && isSubmitter && (
          <div className="mt-4 p-3 bg-indigo-50 border border-indigo-200 rounded-lg text-xs text-indigo-900 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-indigo-600 shrink-0" />
            <span>
              <strong>Segregation of Duties Enforced:</strong> You submitted this job requirement. Another Placement Head or Administrator must conduct the final approval.
            </span>
          </div>
        )}
      </div>

      {/* Grid: 5-Point Verification & Specifications */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: 5-Point Verification Card */}
        <div className="lg:col-span-2 space-y-6">
          <VerificationChecklistCard
            checks={job.verification_checks || []}
            canVerify={canVerify}
            isJobLocked={isJobLocked}
            onUpdateCheck={(check) => setActiveCheck(check)}
          />

          {/* Job Description & Responsibilities */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-3">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Role Description & Expectations
            </h3>
            <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">
              {job.description || "No description provided."}
            </p>

            {job.required_skills && job.required_skills.length > 0 && (
              <div className="pt-3 border-t border-slate-100">
                <div className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Required Competencies
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {job.required_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-lg text-xs font-medium border border-indigo-100"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Specification Highlights & Workflow Timeline */}
        <div className="space-y-6">
          {/* Key Specifications Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4 text-xs">
            <h3 className="font-bold text-slate-900 uppercase tracking-wider border-b pb-2 border-slate-100">
              Recruitment Parameters
            </h3>

            <div>
              <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                Compensation Package
              </div>
              <div className="text-sm font-bold text-slate-900 mt-0.5">
                ₹{job.min_ctc_lpa} - ₹{job.max_ctc_lpa} LPA
              </div>
              {job.stipend_amount && (
                <div className="text-slate-600 mt-0.5">Stipend: ₹{job.stipend_amount}/mo</div>
              )}
              {job.salary_details && (
                <div className="text-slate-500 text-[11px] mt-1">{job.salary_details}</div>
              )}
            </div>

            <div className="pt-2 border-t border-slate-100">
              <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                Academic Eligibility
              </div>
              <div className="mt-1 space-y-1 text-slate-700">
                <div>Min CGPA: <span className="font-semibold">{job.min_cgpa || "None"}</span></div>
                <div>Min Aggregate: <span className="font-semibold">{job.min_percentage ? `${job.min_percentage}%` : "None"}</span></div>
                <div>Permissible Backlogs: <span className="font-semibold">{job.max_backlogs_allowed}</span></div>
                <div>Batches: <span className="font-semibold">{job.eligible_batches?.join(", ") || "All"}</span></div>
                <div>Branches: <span className="font-semibold">{job.eligible_branches?.join(", ") || "All"}</span></div>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100">
              <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                Service Agreement
              </div>
              <div className="mt-1 text-slate-700">
                {job.has_bond ? (
                  <span className="font-semibold text-amber-700">
                    Bond required: {job.bond_duration_months} months
                  </span>
                ) : (
                  <span className="text-emerald-700 font-semibold">No service agreement / bond</span>
                )}
                {job.bond_details && <div className="text-slate-500 text-[11px] mt-0.5">{job.bond_details}</div>}
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100">
              <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                Attribution & Submission
              </div>
              <div className="mt-1 text-slate-600 space-y-0.5">
                <div>Submitted by: <span className="font-semibold text-slate-800">{job.submitted_by_name || "Unknown"}</span></div>
                {job.assigned_verifier_name && (
                  <div>Assigned Verifier: <span className="font-semibold text-slate-800">{job.assigned_verifier_name}</span></div>
                )}
                {job.approved_by_name && (
                  <div>Approved by: <span className="font-semibold text-emerald-800">{job.approved_by_name}</span></div>
                )}
              </div>
            </div>
          </div>

          {/* Workflow History Timeline Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
            <div className="flex items-center gap-2 border-b pb-2 border-slate-100">
              <History className="w-4 h-4 text-slate-500" />
              <h3 className="font-bold text-slate-900 text-xs uppercase tracking-wider">
                Audit & Workflow History
              </h3>
            </div>

            <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
              {job.workflow_history && job.workflow_history.length > 0 ? (
                job.workflow_history.map((item) => (
                  <div key={item.id} className="relative pl-4 border-l-2 border-slate-200 text-xs space-y-0.5">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-slate-800">{item.action}</span>
                      <span className="text-slate-400 text-[10px]">
                        {new Date(item.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <div className="text-slate-500 text-[11px]">
                      {item.from_status ? `${item.from_status} → ` : ""}
                      <span className="font-semibold text-slate-700">{item.to_status}</span> by {item.actor_name}
                    </div>
                    {item.notes && <div className="text-slate-600 text-[11px] italic bg-slate-50 p-1.5 rounded">{item.notes}</div>}
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-400 py-3 text-center">No history recorded yet.</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Modals */}
      <UpdateCheckModal
        check={activeCheck}
        isOpen={Boolean(activeCheck)}
        onClose={() => setActiveCheck(null)}
        onSubmit={handleUpdateCheck}
      />

      <ApprovalModal
        job={job}
        isOpen={isApprovalOpen}
        onClose={() => setIsApprovalOpen(false)}
        onConfirm={handleApprove}
        currentUserId={user?.id}
      />

      <RejectModal
        job={job}
        isOpen={isRejectOpen}
        onClose={() => setIsRejectOpen(false)}
        onConfirm={handleReject}
      />

      <RequestChangesModal
        job={job}
        isOpen={isChangesOpen}
        onClose={() => setIsChangesOpen(false)}
        onConfirm={handleRequestChanges}
      />

      <AmendJobModal
        job={job}
        isOpen={isAmendOpen}
        onClose={() => setIsAmendOpen(false)}
        onConfirm={handleAmend}
      />
    </div>
  );
};

