import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Building2,
  Globe,
  Users,
  PhoneCall,
  Calendar,
  Plus,
  ArrowLeft,
  Mail,
  Phone,
  CheckCircle2,
  XCircle,
  ExternalLink,
} from "lucide-react";
import { crmApi } from "../../api/crmApi";
import { FollowUp, HRContact } from "../../types/crm";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { AddContactModal } from "../../components/crm/AddContactModal";
import { LogOutreachModal } from "../../components/crm/LogOutreachModal";
import { CompleteFollowUpModal } from "../../components/crm/CompleteFollowUpModal";
import { CancelFollowUpModal } from "../../components/crm/CancelFollowUpModal";

export const CompanyDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { hasAnyRole } = useAuth();
  const [activeTab, setActiveTab] = useState<"contacts" | "outreach" | "followups">("contacts");

  const [isAddContactOpen, setIsAddContactOpen] = useState(false);
  const [isLogOutreachOpen, setIsLogOutreachOpen] = useState(false);
  const [completeFollowUpTarget, setCompleteFollowUpTarget] = useState<FollowUp | null>(null);
  const [cancelFollowUpTarget, setCancelFollowUpTarget] = useState<FollowUp | null>(null);

  const canEdit = hasAnyRole(["ADMIN", "PLACEMENT_HEAD", "CALLING_EXECUTIVE", "CRM_EXECUTIVE"]);

  const {
    data: company,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["company", id],
    queryFn: () => crmApi.getCompanyDetail(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return <LoadingState message="Loading company profile & relationship history..." />;
  }

  if (isError || !company) {
    return (
      <ErrorState
        title="Company not found"
        message="Could not load the requested hiring partner profile."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb Back Link */}
      <div>
        <Link
          to="/companies"
          className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-brand-blue"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to Company Directory
        </Link>
      </div>

      {/* Company Header Card */}
      <Card className="border-t-4 border-t-brand-navy">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-brand-navy">
                <Building2 className="h-7 w-7" />
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <h1 className="text-xl font-bold text-brand-dark">{company.name}</h1>
                  <StatusBadge variant="info" dot>
                    {company.status.replace(/_/g, " ")}
                  </StatusBadge>
                  {company.tier !== "UNRATED" && (
                    <StatusBadge variant="neutral">{company.tier}</StatusBadge>
                  )}
                </div>

                <div className="mt-1.5 flex flex-wrap items-center gap-4 text-xs text-slate-500">
                  {company.canonical_domain && (
                    <span className="flex items-center gap-1">
                      <Globe className="h-3.5 w-3.5 text-slate-400" />
                      {company.canonical_domain}
                      {company.website && (
                        <a
                          href={company.website}
                          target="_blank"
                          rel="noreferrer"
                          className="text-brand-blue hover:underline"
                        >
                          <ExternalLink className="h-3 w-3 inline ml-0.5" />
                        </a>
                      )}
                    </span>
                  )}
                  <span>Industry: <strong className="text-slate-700">{company.industry.replace("_", " ")}</strong></span>
                  <span>
                    Assigned:{" "}
                    <strong className="text-slate-700">
                      {company.assigned_to_name || "Unassigned"}
                    </strong>
                  </span>
                </div>
              </div>
            </div>

            {canEdit && (
              <div className="flex items-center gap-2 shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  leftIcon={<Users className="h-4 w-4" />}
                  onClick={() => setIsAddContactOpen(true)}
                >
                  Add Recruiter
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  leftIcon={<PhoneCall className="h-4 w-4" />}
                  onClick={() => setIsLogOutreachOpen(true)}
                >
                  Log Outreach
                </Button>
              </div>
            )}
          </div>

          {company.notes && (
            <div className="mt-4 rounded-md bg-slate-50 p-3 text-xs text-slate-600 border border-slate-200">
              <span className="font-semibold text-brand-dark">Account Notes: </span>
              {company.notes}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tabs Row */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-8">
          <button
            type="button"
            onClick={() => setActiveTab("contacts")}
            className={`py-3 px-1 border-b-2 font-medium text-xs inline-flex items-center gap-1.5 ${
              activeTab === "contacts"
                ? "border-brand-navy text-brand-navy font-bold"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <Users className="h-4 w-4" />
            HR Contacts ({company.contacts?.length || 0})
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("outreach")}
            className={`py-3 px-1 border-b-2 font-medium text-xs inline-flex items-center gap-1.5 ${
              activeTab === "outreach"
                ? "border-brand-navy text-brand-navy font-bold"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <PhoneCall className="h-4 w-4" />
            Touchpoints ({company.recent_outreach?.length || 0})
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("followups")}
            className={`py-3 px-1 border-b-2 font-medium text-xs inline-flex items-center gap-1.5 ${
              activeTab === "followups"
                ? "border-brand-navy text-brand-navy font-bold"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <Calendar className="h-4 w-4" />
            Active Follow-Ups ({company.active_follow_ups?.length || 0})
          </button>
        </nav>
      </div>

      {/* Tab 1: HR Contacts */}
      {activeTab === "contacts" && (
        <Card>
          <CardHeader className="flex items-center justify-between py-3">
            <h2 className="text-xs font-bold text-brand-dark">Recruiter & TA Contacts</h2>
            {canEdit && (
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-brand-blue"
                leftIcon={<Plus className="h-3.5 w-3.5" />}
                onClick={() => setIsAddContactOpen(true)}
              >
                Add Recruiter
              </Button>
            )}
          </CardHeader>
          <CardContent className="p-0">
            {company.contacts?.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                No HR recruiter contacts recorded yet for this organization.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 border-b border-slate-100">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Name & Role</th>
                      <th className="px-4 py-3 font-semibold">Department</th>
                      <th className="px-4 py-3 font-semibold">Email</th>
                      <th className="px-4 py-3 font-semibold">Phone</th>
                      <th className="px-4 py-3 font-semibold">Preferred Channel</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {company.contacts.map((c: HRContact) => (
                      <tr key={c.id} className="hover:bg-slate-50">
                        <td className="px-4 py-3 font-medium text-brand-dark">
                          <div className="flex items-center gap-1.5">
                            <span>{c.name}</span>
                            {c.is_primary && (
                              <StatusBadge variant="info" className="text-[10px]">
                                Primary
                              </StatusBadge>
                            )}
                          </div>
                          {c.designation && (
                            <p className="text-[11px] text-slate-500">{c.designation}</p>
                          )}
                        </td>
                        <td className="px-4 py-3 text-slate-600">{c.department || "—"}</td>
                        <td className="px-4 py-3 text-slate-600">
                          {c.email ? (
                            <a
                              href={`mailto:${c.email}`}
                              className="text-brand-blue hover:underline inline-flex items-center gap-1"
                            >
                              <Mail className="h-3 w-3" />
                              {c.email}
                            </a>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {c.phone ? (
                            <span className="inline-flex items-center gap-1">
                              <Phone className="h-3 w-3" />
                              {c.phone}
                            </span>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="px-4 py-3 text-slate-600">{c.preferred_channel}</td>
                        <td className="px-4 py-3">
                          <StatusBadge
                            variant={c.status === "ACTIVE" ? "success" : "neutral"}
                            dot
                          >
                            {c.status}
                          </StatusBadge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 2: Outreach Activities */}
      {activeTab === "outreach" && (
        <Card>
          <CardHeader className="py-3">
            <h2 className="text-xs font-bold text-brand-dark">Outreach History & Interaction Logs</h2>
          </CardHeader>
          <CardContent className="p-6">
            {company.recent_outreach?.length === 0 ? (
              <div className="text-center text-xs text-slate-500">
                No outreach calls or touchpoints recorded yet.
              </div>
            ) : (
              <div className="space-y-4">
                {company.recent_outreach.map((act) => (
                  <div
                    key={act.id}
                    className="flex items-start gap-3 rounded-lg border border-slate-200 p-3.5 hover:bg-slate-50 transition-colors"
                  >
                    <div className="rounded-full bg-slate-100 p-2 text-brand-blue shrink-0">
                      <PhoneCall className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-xs text-brand-dark">
                            {act.channel} Outreach
                          </span>
                          <StatusBadge variant="info" className="text-[10px]">
                            {act.outcome.replace(/_/g, " ")}
                          </StatusBadge>
                        </div>
                        <span className="text-[10px] text-slate-400">
                          {new Date(act.attempted_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-slate-700 leading-relaxed">{act.notes}</p>
                      <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
                        <span>Conducted by: <strong className="text-slate-600">{act.executive_name}</strong></span>
                        {act.next_action && (
                          <span>Next action: <strong className="text-brand-dark">{act.next_action}</strong></span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 3: Active Follow-Up Tasks */}
      {activeTab === "followups" && (
        <Card>
          <CardHeader className="py-3">
            <h2 className="text-xs font-bold text-brand-dark">Pending Follow-Up Tasks</h2>
          </CardHeader>
          <CardContent className="p-6">
            {company.active_follow_ups?.length === 0 ? (
              <div className="text-center text-xs text-slate-500">
                No active follow-up tasks scheduled for this employer.
              </div>
            ) : (
              <div className="space-y-3">
                {company.active_follow_ups.map((f: FollowUp) => (
                  <div
                    key={f.id}
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-lg border border-slate-200 p-3.5 hover:bg-slate-50"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-brand-dark">{f.title}</span>
                        {f.is_overdue && (
                          <StatusBadge variant="danger" dot className="text-[10px]">
                            OVERDUE
                          </StatusBadge>
                        )}
                        <StatusBadge variant="neutral" className="text-[10px]">
                          {f.priority}
                        </StatusBadge>
                      </div>
                      {f.description && (
                        <p className="mt-1 text-xs text-slate-600">{f.description}</p>
                      )}
                      <p className="mt-1 text-[11px] text-slate-400">
                        Due: {new Date(f.due_date).toLocaleString()} • Assigned to: {f.assigned_to_name}
                      </p>
                    </div>

                    {canEdit && (
                      <div className="flex items-center gap-2 shrink-0">
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-emerald-700 hover:bg-emerald-50 border-emerald-200"
                          leftIcon={<CheckCircle2 className="h-3.5 w-3.5" />}
                          onClick={() => setCompleteFollowUpTarget(f)}
                        >
                          Complete
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-600 hover:bg-red-50"
                          leftIcon={<XCircle className="h-3.5 w-3.5" />}
                          onClick={() => setCancelFollowUpTarget(f)}
                        >
                          Cancel
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Modals */}
      <AddContactModal
        companyId={company.id}
        companyName={company.name}
        isOpen={isAddContactOpen}
        onClose={() => setIsAddContactOpen(false)}
        onSuccess={() => refetch()}
      />

      <LogOutreachModal
        companyId={company.id}
        companyName={company.name}
        contacts={company.contacts || []}
        isOpen={isLogOutreachOpen}
        onClose={() => setIsLogOutreachOpen(false)}
        onSuccess={() => refetch()}
      />

      <CompleteFollowUpModal
        followUp={completeFollowUpTarget}
        isOpen={!!completeFollowUpTarget}
        onClose={() => setCompleteFollowUpTarget(null)}
        onSuccess={() => refetch()}
      />

      <CancelFollowUpModal
        followUp={cancelFollowUpTarget}
        isOpen={!!cancelFollowUpTarget}
        onClose={() => setCancelFollowUpTarget(null)}
        onSuccess={() => refetch()}
      />
    </div>
  );
};
