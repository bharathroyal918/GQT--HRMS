import React from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  MapPin,
  Clock,
  UserCheck,
} from "lucide-react";
import { interviewsApi } from "../../api/interviewsApi";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

export const DriveDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const {
    data: drive,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["driveDetail", id],
    queryFn: () => interviewsApi.getDriveDetail(id!),
    enabled: !!id,
  });

  const handleUpdateOutcome = async (slotId: string, outcome: string) => {
    try {
      await interviewsApi.updateSlotOutcome(slotId, {
        attendance_status: "PRESENT",
        outcome: outcome,
      });
      refetch();
    } catch (err: any) {
      alert("Failed to update outcome: " + (err.response?.data?.detail || err.message));
    }
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <LoadingState message="Loading placement drive..." />
      </div>
    );
  }

  if (isError || !drive) {
    return (
      <div className="p-8">
        <ErrorState message="Could not find drive details. Please return to drive directory." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button and Header */}
      <div>
        <Link
          to="/interviews"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-brand-navy mb-2 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Drives & Interviews
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-brand-blue bg-blue-50 px-2 py-0.5 rounded">
                {drive.drive_code}
              </span>
              <h1 className="text-2xl font-bold text-brand-dark">{drive.title}</h1>
            </div>
            <p className="text-xs text-brand-muted mt-1">
              {drive.company_name} — {drive.job_title} • Mode: {drive.drive_mode}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800">
              {drive.status}
            </span>
          </div>
        </div>
      </div>

      {/* Drive Metadata Card */}
      <Card className="p-5 bg-white">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-slate-400" />
            <div>
              <span className="text-slate-500 block">Scheduled Date & Time</span>
              <span className="font-semibold text-slate-800">
                {new Date(drive.drive_date).toLocaleDateString()} at {new Date(drive.drive_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-slate-400" />
            <div>
              <span className="text-slate-500 block">Venue / Virtual Link</span>
              <span className="font-semibold text-slate-800">{drive.venue_or_link}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <UserCheck className="h-4 w-4 text-slate-400" />
            <div>
              <span className="text-slate-500 block">Lead Coordinator</span>
              <span className="font-semibold text-slate-800">{drive.coordinator_name || "Unassigned"}</span>
            </div>
          </div>
        </div>

        {drive.instructions && (
          <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-600">
            <strong>Candidate Instructions:</strong> {drive.instructions}
          </div>
        )}
      </Card>

      {/* Multi-Round Stages */}
      <div className="space-y-6">
        <h2 className="text-lg font-bold text-brand-dark">Interview Rounds & Evaluation Stages</h2>

        {!drive.rounds || drive.rounds.length === 0 ? (
          <Card className="p-8 bg-white text-center">
            <p className="text-xs text-slate-500 italic">No interview rounds defined yet for this drive.</p>
          </Card>
        ) : (
          drive.rounds.map((round) => (
            <Card key={round.id} className="overflow-hidden bg-white shadow-sm border border-slate-200">
              <div className="flex items-center justify-between px-5 py-3 border-b border-slate-200 bg-slate-50">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-xs text-brand-navy">
                    Round {round.round_number}: {round.round_name}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-100 text-indigo-800">
                    {round.round_type}
                  </span>
                </div>
                <span className="text-xs text-slate-500">{round.slots_count} Candidates Scheduled</span>
              </div>

              {!round.slots || round.slots.length === 0 ? (
                <div className="p-4 text-xs text-slate-500 italic">No candidates scheduled in this round yet.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-slate-100 text-slate-500 font-semibold uppercase">
                        <th className="py-2.5 px-4">Candidate</th>
                        <th className="py-2.5 px-4">Discipline</th>
                        <th className="py-2.5 px-4">Scheduled Slot</th>
                        <th className="py-2.5 px-4">Attendance</th>
                        <th className="py-2.5 px-4">Stage Outcome</th>
                        <th className="py-2.5 px-4 text-right">Quick Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {round.slots.map((slot) => (
                        <tr key={slot.id} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2.5 px-4 font-semibold text-slate-900">
                            {slot.student_name}
                            <div className="font-mono text-[10px] text-slate-500">{slot.student_roll}</div>
                          </td>
                          <td className="py-2.5 px-4 text-slate-700">{slot.branch}</td>
                          <td className="py-2.5 px-4 font-mono text-slate-600">
                            {new Date(slot.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </td>
                          <td className="py-2.5 px-4">
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700">
                              {slot.attendance_status}
                            </span>
                          </td>
                          <td className="py-2.5 px-4">
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                                slot.outcome === "SELECTED"
                                  ? "bg-emerald-100 text-emerald-800"
                                  : slot.outcome === "NOT_SELECTED"
                                  ? "bg-red-100 text-red-800"
                                  : slot.outcome === "NEXT_ROUND"
                                  ? "bg-indigo-100 text-indigo-800"
                                  : "bg-amber-100 text-amber-800"
                              }`}
                            >
                              {slot.outcome}
                            </span>
                          </td>
                          <td className="py-2.5 px-4 text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleUpdateOutcome(slot.id, "SELECTED")}
                                className="text-[11px] py-0.5 px-2 text-emerald-700 hover:bg-emerald-50"
                              >
                                Select
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleUpdateOutcome(slot.id, "NOT_SELECTED")}
                                className="text-[11px] py-0.5 px-2 text-red-700 hover:bg-red-50"
                              >
                                Reject
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          ))
        )}
      </div>
    </div>
  );
};
