import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  CalendarCheck,
  Send,
  Award,
  ChevronRight,
  FileSpreadsheet,
} from "lucide-react";
import { interviewsApi } from "../../api/interviewsApi";
import { API_BASE_URL } from "../../api/apiClient";
import { Card } from "../../components/ui/Card";
import { LoadingState } from "../../components/ui/LoadingState";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorState } from "../../components/ui/ErrorState";

export const PlacementDrivesPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"drives" | "submissions" | "offers">("drives");

  const {
    data: drivesData,
    isLoading: isDrivesLoading,
    isError: isDrivesError,
  } = useQuery({
    queryKey: ["placementDrives"],
    queryFn: () => interviewsApi.getDrives(),
    enabled: activeTab === "drives",
  });

  const {
    data: submissionsData,
    isLoading: isSubmissionsLoading,
  } = useQuery({
    queryKey: ["submissionPackages"],
    queryFn: () => interviewsApi.getSubmissions(),
    enabled: activeTab === "submissions",
  });

  const {
    data: offersData,
    isLoading: isOffersLoading,
  } = useQuery({
    queryKey: ["placementOffers"],
    queryFn: () => interviewsApi.getOffers(),
    enabled: activeTab === "offers",
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <CalendarCheck className="h-7 w-7 text-brand-navy" />
            <h1 className="text-2xl font-bold text-brand-dark">Interviews, Drives & Placement Outcomes</h1>
          </div>
          <p className="text-sm text-brand-muted mt-1">
            Recruiter profile submissions, multi-stage drive scheduling, attendance logs, and corporate offer auditing.
          </p>
        </div>
      </div>

      {/* Tabs navigation */}
      <div className="flex border-b border-slate-200 gap-4 text-sm font-semibold">
        <button
          onClick={() => setActiveTab("drives")}
          className={`pb-3 flex items-center gap-2 transition-colors border-b-2 ${
            activeTab === "drives"
              ? "border-brand-blue text-brand-navy"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <CalendarCheck className="h-4 w-4" />
          Placement Drives & Rounds
        </button>

        <button
          onClick={() => setActiveTab("submissions")}
          className={`pb-3 flex items-center gap-2 transition-colors border-b-2 ${
            activeTab === "submissions"
              ? "border-brand-blue text-brand-navy"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Send className="h-4 w-4" />
          Candidate Submissions & Dispatches
        </button>

        <button
          onClick={() => setActiveTab("offers")}
          className={`pb-3 flex items-center gap-2 transition-colors border-b-2 ${
            activeTab === "offers"
              ? "border-brand-blue text-brand-navy"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Award className="h-4 w-4" />
          Offers & Joining Verification
        </button>
      </div>

      {/* TAB 1: PLACEMENT DRIVES */}
      {activeTab === "drives" && (
        <div className="space-y-4">
          <Card className="overflow-hidden bg-white shadow-sm border border-slate-200">
            {isDrivesLoading ? (
              <div className="p-8">
                <LoadingState message="Loading placement drives..." />
              </div>
            ) : isDrivesError ? (
              <div className="p-8">
                <ErrorState message="Failed to load placement drives." />
              </div>
            ) : !drivesData?.results || drivesData.results.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  title="No Placement Drives Scheduled"
                  description="No drives match the active criteria. Coordinate with corporate partners to schedule interview drives."
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                      <th className="py-3 px-4">Drive Code</th>
                      <th className="py-3 px-4">Drive Title & Company</th>
                      <th className="py-3 px-4">Scheduled Date</th>
                      <th className="py-3 px-4">Mode & Venue</th>
                      <th className="py-3 px-4">Rounds</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {drivesData.results.map((drive) => (
                      <tr key={drive.id} className="hover:bg-slate-50 transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-brand-navy whitespace-nowrap">
                          {drive.drive_code}
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold text-slate-900">{drive.title}</div>
                          <div className="text-[11px] text-slate-500">{drive.company_name} — {drive.job_title}</div>
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap text-slate-700 font-medium">
                          {new Date(drive.drive_date).toLocaleDateString()} {new Date(drive.drive_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-medium text-slate-800">{drive.drive_mode}</span>
                          <div className="text-[11px] text-slate-400 truncate max-w-[160px]" title={drive.venue_or_link}>
                            {drive.venue_or_link}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center px-2 py-0.5 rounded bg-slate-100 text-slate-800 font-semibold">
                            {drive.rounds_count} Rounds
                          </span>
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-semibold ${
                              drive.status === "COMPLETED"
                                ? "bg-emerald-100 text-emerald-800"
                                : drive.status === "IN_PROGRESS"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-blue-100 text-blue-800"
                            }`}
                          >
                            {drive.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Link
                            to={`/interviews/${drive.id}`}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-brand-blue hover:text-brand-dark"
                          >
                            Manage Rounds
                            <ChevronRight className="h-3.5 w-3.5" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* TAB 2: CANDIDATE SUBMISSIONS */}
      {activeTab === "submissions" && (
        <Card className="overflow-hidden bg-white shadow-sm border border-slate-200">
          {isSubmissionsLoading ? (
            <div className="p-8">
              <LoadingState message="Loading submission packages..." />
            </div>
          ) : !submissionsData?.results || submissionsData.results.length === 0 ? (
            <div className="p-8">
              <EmptyState
                title="No Submissions Dispatched"
                description="Assemble candidate profiles from approved cohorts to create corporate submission packages."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                    <th className="py-3 px-4">Package Code</th>
                    <th className="py-3 px-4">Title & Opportunity</th>
                    <th className="py-3 px-4">Candidates</th>
                    <th className="py-3 px-4">Roster Digest (SHA-256)</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Dispatched At</th>
                    <th className="py-3 px-4 text-right">Roster CSV</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {submissionsData.results.map((pkg) => (
                    <tr key={pkg.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-brand-navy whitespace-nowrap">
                        {pkg.package_code}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900">{pkg.title}</div>
                        <div className="text-[11px] text-slate-500">{pkg.company_name} — {pkg.job_title}</div>
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-800">
                        {pkg.candidates_count} Candidates
                      </td>
                      <td className="py-3 px-4 font-mono text-[10px] text-slate-400 truncate max-w-[140px]" title={pkg.roster_hash}>
                        {pkg.roster_hash || "—"}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-indigo-100 text-indigo-800">
                          {pkg.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap font-mono text-slate-500">
                        {pkg.dispatched_at ? new Date(pkg.dispatched_at).toLocaleDateString() : "Pending"}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <a
                          href={`${API_BASE_URL}/submissions/${pkg.id}/roster-csv/`}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-semibold text-brand-blue hover:text-brand-dark"
                        >
                          <FileSpreadsheet className="h-3.5 w-3.5" />
                          Download
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* TAB 3: PLACEMENT OFFERS */}
      {activeTab === "offers" && (
        <Card className="overflow-hidden bg-white shadow-sm border border-slate-200">
          {isOffersLoading ? (
            <div className="p-8">
              <LoadingState message="Loading offers..." />
            </div>
          ) : !offersData?.results || offersData.results.length === 0 ? (
            <div className="p-8">
              <EmptyState
                title="No Placement Offers Logged"
                description="Recorded corporate selection results and candidate offer decisions will appear here."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                    <th className="py-3 px-4">Candidate</th>
                    <th className="py-3 px-4">Company & Designation</th>
                    <th className="py-3 px-4">CTC Offered</th>
                    <th className="py-3 px-4">Offer Status</th>
                    <th className="py-3 px-4">Joining Status</th>
                    <th className="py-3 px-4">Deadline</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {offersData.results.map((offer) => (
                    <tr key={offer.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900">{offer.student_name}</div>
                        <div className="font-mono text-[11px] text-slate-500">{offer.student_roll} ({offer.branch})</div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-800">{offer.designation}</div>
                        <div className="text-[11px] text-slate-500">{offer.company_name}</div>
                      </td>
                      <td className="py-3 px-4 font-bold text-emerald-700">
                        ₹{offer.ctc_lpa} LPA
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            offer.status === "ACCEPTED"
                              ? "bg-emerald-100 text-emerald-800"
                              : offer.status === "DECLINED"
                              ? "bg-red-100 text-red-800"
                              : "bg-blue-100 text-blue-800"
                          }`}
                        >
                          {offer.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700">
                          {offer.joining_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-500 whitespace-nowrap">
                        {offer.response_deadline}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};
