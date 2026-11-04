import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, Clock, ShieldCheck, ExternalLink } from "lucide-react";
import { JobVerificationCheck, VerificationCheckType, CheckStatus } from "../../types/jobs";
import { Button } from "../ui/Button";

interface VerificationChecklistCardProps {
  checks: JobVerificationCheck[];
  canVerify: boolean;
  isJobLocked: boolean;
  onUpdateCheck: (check: JobVerificationCheck) => void;
}

const CHECK_TITLES: Record<VerificationCheckType, { title: string; desc: string }> = {
  ELIGIBILITY: {
    title: "1. Candidate Eligibility Compliance",
    desc: "Branch suitability, CGPA/percentage floor, passing batch, and active backlogs.",
  },
  SALARY_AUTHENTICITY: {
    title: "2. Salary Authenticity & Plausibility",
    desc: "Fixed/variable CTC plausibility, market benchmark, and prior offer consistency.",
  },
  COMPANY_AUTHENTICITY: {
    title: "3. Corporate Legitimacy & Recruiter Identity",
    desc: "GST/CIN entity registration, company domain, and recruiter work email domain match.",
  },
  INTERVIEW_PROCESS: {
    title: "4. Interview Process & Fee Disclosure",
    desc: "Explicit round definitions, test modes, and strict zero candidate-fee confirmation.",
  },
  REGISTRATION_DEADLINE: {
    title: "5. Application Deadline Validity",
    desc: "Future deadline with sufficient lead time; non-conflicting with exam schedules.",
  },
};

export const VerificationChecklistCard: React.FC<VerificationChecklistCardProps> = ({
  checks,
  canVerify,
  isJobLocked,
  onUpdateCheck,
}) => {
  const getStatusBadge = (status: CheckStatus, requiresReverification: boolean) => {
    if (requiresReverification) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
          Re-verification Required
        </span>
      );
    }
    switch (status) {
      case "VERIFIED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            VERIFIED
          </span>
        );
      case "FLAGGED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800 border border-yellow-300">
            <AlertTriangle className="w-3.5 h-3.5 text-yellow-600" />
            FLAGGED
          </span>
        );
      case "REJECTED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-300">
            <XCircle className="w-3.5 h-3.5 text-rose-600" />
            REJECTED
          </span>
        );
      case "PENDING":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            PENDING
          </span>
        );
    }
  };

  const verifiedCount = checks.filter((c) => c.status === "VERIFIED" && !c.requires_reverification).length;
  const isFullyVerified = verifiedCount === 5;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="p-5 border-b border-slate-100 flex flex-wrap items-center justify-between gap-4 bg-slate-50">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-600" />
            <h3 className="font-semibold text-slate-900 text-base">5-Point Verification Checklist</h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            All five mandatory checks must reach <span className="font-semibold text-emerald-700">VERIFIED</span> before this job can enter the approval queue.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Progress</div>
            <div className={`text-base font-bold ${isFullyVerified ? "text-emerald-600" : "text-amber-600"}`}>
              {verifiedCount} / 5 Verified
            </div>
          </div>
          <div className="w-24 bg-slate-200 h-2.5 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${isFullyVerified ? "bg-emerald-500" : "bg-amber-500"}`}
              style={{ width: `${(verifiedCount / 5) * 100}%` }}
            />
          </div>
        </div>
      </div>

      <div className="divide-y divide-slate-100">
        {checks.map((check) => {
          const meta = CHECK_TITLES[check.check_type] || { title: check.check_type, desc: "" };
          return (
            <div key={check.id} className="p-4 hover:bg-slate-50/70 transition-colors">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="font-medium text-slate-900 text-sm">{meta.title}</span>
                    {getStatusBadge(check.status, check.requires_reverification)}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{meta.desc}</p>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-center">
                  {canVerify && !isJobLocked && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onUpdateCheck(check)}
                      className="text-xs py-1 px-3"
                    >
                      Evaluate Check
                    </Button>
                  )}
                </div>
              </div>

              {/* Review notes and evidence display */}
              {(check.notes || check.evidence_reference || check.invalidation_reason || check.verified_by_name) && (
                <div className="mt-3 p-3 bg-slate-50 rounded-lg text-xs border border-slate-100 space-y-1">
                  {check.invalidation_reason && (
                    <div className="text-rose-700 font-medium flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                      <span>{check.invalidation_reason}</span>
                    </div>
                  )}
                  {check.notes && (
                    <div className="text-slate-700">
                      <span className="font-semibold text-slate-800">Reviewer Notes: </span>
                      {check.notes}
                    </div>
                  )}
                  {check.evidence_reference && (
                    <div className="text-slate-600 flex items-center gap-1">
                      <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                      <span className="font-semibold text-slate-700">Evidence: </span>
                      <span className="font-mono text-slate-800">{check.evidence_reference}</span>
                    </div>
                  )}
                  {check.verified_by_name && (
                    <div className="text-slate-400 text-[11px] pt-0.5">
                      Last evaluated by {check.verified_by_name} ({check.verified_by_email})
                      {check.verified_at && ` on ${new Date(check.verified_at).toLocaleString()}`}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

