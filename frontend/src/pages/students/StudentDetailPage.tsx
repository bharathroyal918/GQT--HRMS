import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Mail,
  Phone,
  FileText,
  CheckCircle,
  AlertTriangle,
  XCircle,
  ShieldCheck,
} from "lucide-react";
import { studentsApi } from "../../api/studentsApi";
import { jobsApi } from "../../api/jobsApi";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

export const StudentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  // State for eligibility check modal
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [evalResult, setEvalResult] = useState<any | null>(null);
  const [evalLoading, setEvalLoading] = useState<boolean>(false);
  const [certResult, setCertResult] = useState<any | null>(null);
  const [certLoading, setCertLoading] = useState<boolean>(false);

  const {
    data: student,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["studentDetail", id],
    queryFn: () => studentsApi.getStudentDetail(id!),
    enabled: !!id,
  });

  const { data: jobsData } = useQuery({
    queryKey: ["activeJobsForEligibility"],
    queryFn: () => jobsApi.getJobs({ page_size: 50 }),
  });

  const handleRunEligibilityCheck = async () => {
    if (!id || !selectedJobId) return;
    setEvalLoading(true);
    setEvalResult(null);
    try {
      const res = await studentsApi.evaluateEligibility(id, selectedJobId);
      setEvalResult(res);
    } catch (err: any) {
      alert("Eligibility evaluation failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setEvalLoading(false);
    }
  };

  const handleCheckAndCertifyReadiness = async () => {
    if (!id || !selectedJobId) return;
    setCertLoading(true);
    setCertResult(null);
    try {
      const statusRes = await studentsApi.checkReadinessStatus(id, selectedJobId);
      if (!statusRes.can_certify) {
        setCertResult({
          success: false,
          missing: statusRes.missing_criteria,
        });
      } else {
        const certRes = await studentsApi.certifyReadiness(id, selectedJobId, "Certified for placement drive.");
        setCertResult({
          success: true,
          cert: certRes,
        });
        refetch();
      }
    } catch (err: any) {
      alert("Readiness check failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setCertLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <LoadingState message="Loading candidate profile..." />
      </div>
    );
  }

  if (isError || !student) {
    return (
      <div className="p-8">
        <ErrorState message="Could not find student profile. Please return to directory." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button and Header */}
      <div>
        <Link
          to="/students"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-brand-navy mb-2 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Student Directory
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-brand-navy/10 flex items-center justify-center text-brand-navy font-bold text-lg">
              {student.full_name.charAt(0)}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-brand-dark">{student.full_name}</h1>
              <p className="text-xs text-brand-muted font-mono">{student.roll_number} • {student.degree} {student.branch} ({student.graduation_year})</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800">
              {student.placement_status}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Academic & Personal Profile */}
        <div className="space-y-6">
          <Card className="p-5 bg-white">
            <h3 className="font-bold text-brand-dark text-sm border-b border-slate-100 pb-2 mb-4">
              Academic Information
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Degree & Discipline:</span>
                <span className="font-semibold text-slate-800">{student.degree} in {student.branch}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Graduation Year:</span>
                <span className="font-semibold text-slate-800">{student.graduation_year}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Current CGPA:</span>
                <span className="font-bold text-emerald-700">{student.cgpa} / 10.00</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Active Backlogs:</span>
                <span className={`font-semibold ${student.backlogs_count > 0 ? "text-red-600" : "text-slate-800"}`}>
                  {student.backlogs_count}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Class 10 Percentage:</span>
                <span className="font-semibold text-slate-800">{student.tenth_percentage ? `${student.tenth_percentage}%` : "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Class 12 / Diploma:</span>
                <span className="font-semibold text-slate-800">{student.twelfth_percentage ? `${student.twelfth_percentage}%` : "—"}</span>
              </div>
            </div>
          </Card>

          <Card className="p-5 bg-white">
            <h3 className="font-bold text-brand-dark text-sm border-b border-slate-100 pb-2 mb-4">
              Contact & Skills
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex items-center gap-2 text-slate-700">
                <Mail className="h-4 w-4 text-slate-400" />
                <span>{student.email}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700">
                <Phone className="h-4 w-4 text-slate-400" />
                <span>{student.phone}</span>
              </div>
              <div className="pt-2">
                <label className="text-slate-500 block mb-1">Technical Skills:</label>
                <div className="flex flex-wrap gap-1">
                  {student.skills && student.skills.length > 0 ? (
                    student.skills.map((skill, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-400 italic">No skills tagged</span>
                  )}
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column: Resumes Vault & Deterministic Eligibility Engine */}
        <div className="lg:col-span-2 space-y-6">
          {/* Resume Vault */}
          <Card className="p-5 bg-white">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-4">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-brand-navy" />
                <h3 className="font-bold text-brand-dark text-sm">Resume Vault & Verification History</h3>
              </div>
              <span className="text-xs text-slate-500">{student.resumes?.length || 0} versions archived</span>
            </div>

            {!student.resumes || student.resumes.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-4">No resumes uploaded yet.</p>
            ) : (
              <div className="space-y-3">
                {student.resumes.map((resume) => (
                  <div
                    key={resume.id}
                    className="flex items-center justify-between p-3 rounded border border-slate-200 bg-slate-50"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-slate-800">Version {resume.version}: {resume.file_name}</span>
                        {resume.is_verified ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                            <CheckCircle className="h-3 w-3" /> ATS Verified
                          </span>
                        ) : (
                          <span className="text-[11px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded font-semibold">
                            Pending Verification
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] font-mono text-slate-400 mt-1">
                        SHA-256: {resume.file_hash}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Real-time Deterministic Eligibility & Step 23 Gate Section */}
          <Card className="p-5 bg-white border-2 border-brand-blue/20">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-2 mb-4">
              <ShieldCheck className="h-5 w-5 text-brand-blue" />
              <h3 className="font-bold text-brand-dark text-sm">
                Deterministic Eligibility Evaluation & Step 23 Certification Gate
              </h3>
            </div>

            <div className="space-y-4">
              <p className="text-xs text-slate-600">
                Select an active approved job requirement to test this candidate's academic eligibility or execute the Step 23 Placement Readiness Certification gate.
              </p>

              <div className="flex flex-col sm:flex-row items-center gap-3">
                <select
                  value={selectedJobId}
                  onChange={(e) => {
                    setSelectedJobId(e.target.value);
                    setEvalResult(null);
                    setCertResult(null);
                  }}
                  className="w-full sm:flex-1 px-3 py-2 border border-slate-300 rounded-md text-xs bg-white focus:outline-none focus:ring-2 focus:ring-brand-blue"
                >
                  <option value="">-- Choose Job Requirement --</option>
                  {(jobsData?.results || []).map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.company_name} — {j.title}
                    </option>
                  ))}
                </select>

                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!selectedJobId || evalLoading}
                    onClick={handleRunEligibilityCheck}
                    className="text-xs"
                  >
                    {evalLoading ? "Checking..." : "Check Eligibility"}
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    disabled={!selectedJobId || certLoading}
                    onClick={handleCheckAndCertifyReadiness}
                    className="text-xs"
                  >
                    {certLoading ? "Evaluating..." : "Step 23 Certification"}
                  </Button>
                </div>
              </div>

              {/* Eligibility Result Banner */}
              {evalResult && (
                <div
                  className={`p-4 rounded-md border text-xs space-y-2 ${
                    evalResult.is_eligible || evalResult.manually_overridden
                      ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                      : "bg-red-50 border-red-200 text-red-900"
                  }`}
                >
                  <div className="flex items-center gap-2 font-bold">
                    {evalResult.is_eligible || evalResult.manually_overridden ? (
                      <>
                        <CheckCircle className="h-4 w-4 text-emerald-600" />
                        <span>ELIGIBLE FOR DRIVE: {evalResult.company_name} ({evalResult.job_title})</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="h-4 w-4 text-red-600" />
                        <span>INELIGIBLE FOR DRIVE: {evalResult.company_name} ({evalResult.job_title})</span>
                      </>
                    )}
                  </div>

                  {evalResult.failed_criteria && evalResult.failed_criteria.length > 0 && (
                    <div className="pt-1">
                      <span className="font-semibold block mb-1">Failed Criteria:</span>
                      <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                        {evalResult.failed_criteria.map((reason: string, idx: number) => (
                          <li key={idx}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {evalResult.manually_overridden && (
                    <div className="text-[11px] text-amber-800 bg-amber-100/60 p-2 rounded">
                      <strong>Manually Overridden by {evalResult.overridden_by_name}:</strong> {evalResult.override_reason}
                    </div>
                  )}
                </div>
              )}

              {/* Step 23 Certification Result */}
              {certResult && (
                <div
                  className={`p-4 rounded-md border text-xs space-y-2 ${
                    certResult.success
                      ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                      : "bg-amber-50 border-amber-200 text-amber-900"
                  }`}
                >
                  <div className="flex items-center gap-2 font-bold">
                    {certResult.success ? (
                      <>
                        <CheckCircle className="h-4 w-4 text-emerald-600" />
                        <span>STEP 23 HARD GATE: CERTIFICATION GRANTED</span>
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                        <span>STEP 23 HARD GATE: PREREQUISITES UNFULFILLED</span>
                      </>
                    )}
                  </div>

                  {!certResult.success && certResult.missing && (
                    <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                      {certResult.missing.map((m: string, idx: number) => (
                        <li key={idx}>{m}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
