import React from "react";
import { CheckCircle2, AlertTriangle, Clock, ShieldCheck, Edit3 } from "lucide-react";
import { DesignComplianceCheck, ComplianceCheckType, ComplianceCheckStatus } from "../../types/creatives";
import { Button } from "../ui/Button";

interface DesignChecklistCardProps {
  checks: DesignComplianceCheck[];
  canReview: boolean;
  onEvaluateCheck: (check: DesignComplianceCheck) => void;
}

const CHECK_TITLES: Record<ComplianceCheckType, { title: string; desc: string }> = {
  FLYER_TEXT_ACCURACY: {
    title: "1. Job Title, CTC & Eligibility Accuracy",
    desc: "Verify that job title, salary packages, eligibility, and dates strictly match the approved Job Requirement.",
  },
  BRAND_ASSETS_COMPLIANCE: {
    title: "2. Official GQT & Corporate Brand Assets",
    desc: "Ensure official GQT logo and corporate partner logo adhere to official aspect ratio, resolution, and clear-space.",
  },
  QR_CODE_INTEGRITY: {
    title: "3. QR Code Routing & Link Validation",
    desc: "Confirm embedded QR codes and URLs route strictly to official GQT portal destinations without unverified redirects.",
  },
  CONTACT_DISCLOSURE: {
    title: "4. Recruiter Contact & Zero-Fee Disclaimer",
    desc: "Verify authorized placement contact channels and mandatory GQT zero student-placement fee transparency notice.",
  },
};

export const DesignChecklistCard: React.FC<DesignChecklistCardProps> = ({
  checks,
  canReview,
  onEvaluateCheck,
}) => {
  const passedCount = checks.filter((c) => c.status === "PASSED").length;
  const isAllPassed = checks.length === 4 && passedCount === 4;

  const getStatusBadge = (status: ComplianceCheckStatus) => {
    switch (status) {
      case "PASSED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Passed
          </span>
        );
      case "FLAGGED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-300">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
            Flagged for Revision
          </span>
        );
      case "PENDING":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            Pending Review
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-indigo-50 text-indigo-700 rounded-lg">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-base">4-Point Design Compliance Gate</h3>
            <p className="text-xs text-slate-500">
              Mandatory verification checks required before asset approval and placement drive handoff.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-bold px-3 py-1 rounded-full border ${
              isAllPassed
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : "bg-amber-50 text-amber-700 border-amber-200"
            }`}
          >
            {passedCount} / 4 Passed
          </span>
        </div>
      </div>

      <div className="space-y-3">
        {checks.map((check) => {
          const info = CHECK_TITLES[check.check_type] || {
            title: check.check_type_display || check.check_type,
            desc: "",
          };

          return (
            <div
              key={check.id}
              className={`p-4 rounded-xl border transition-all ${
                check.status === "PASSED"
                  ? "bg-emerald-50/20 border-emerald-200"
                  : check.status === "FLAGGED"
                  ? "bg-rose-50/30 border-rose-200"
                  : "bg-slate-50/60 border-slate-200"
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div className="space-y-1 max-w-xl">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-slate-900 text-xs sm:text-sm">
                      {info.title}
                    </span>
                    {getStatusBadge(check.status)}
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed">{info.desc}</p>

                  {check.notes && (
                    <div className="mt-2 text-xs p-2.5 rounded-lg bg-white border border-slate-200 text-slate-700">
                      <span className="font-semibold text-slate-900">Reviewer Note: </span>
                      <span>{check.notes}</span>
                    </div>
                  )}

                  {check.verified_by_name && (
                    <div className="text-[11px] text-slate-400 mt-1">
                      Evaluated by {check.verified_by_name}
                      {check.verified_at && ` on ${new Date(check.verified_at).toLocaleString()}`}
                    </div>
                  )}
                </div>

                {canReview && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onEvaluateCheck(check)}
                    className="shrink-0 text-xs flex items-center gap-1.5"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span>Evaluate</span>
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

