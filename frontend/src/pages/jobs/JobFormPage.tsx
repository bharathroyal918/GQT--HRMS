import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Briefcase, ArrowLeft, Save, AlertCircle } from "lucide-react";
import { jobsApi } from "../../api/jobsApi";
import { crmApi } from "../../api/crmApi";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { LoadingState } from "../../components/ui/LoadingState";
import { RoleCategory, WorkArrangement } from "../../types/jobs";

export const JobFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditMode = Boolean(id);

  const [companyId, setCompanyId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [roleCategory, setRoleCategory] = useState<RoleCategory>("SOFTWARE_ENGINEERING");
  const [skills, setSkills] = useState("");
  const [minCgpa, setMinCgpa] = useState("");
  const [minPercentage, setMinPercentage] = useState("");
  const [batches, setBatches] = useState("2024, 2025");
  const [branches, setBranches] = useState("CSE, ISE, ECE, MCA");
  const [maxBacklogs, setMaxBacklogs] = useState(0);
  const [minCtc, setMinCtc] = useState("");
  const [maxCtc, setMaxCtc] = useState("");
  const [stipend, setStipend] = useState("");
  const [salaryDetails, setSalaryDetails] = useState("");
  const [location, setLocation] = useState("");
  const [workArrangement, setWorkArrangement] = useState<WorkArrangement>("ONSITE");
  const [hasBond, setHasBond] = useState(false);
  const [bondDuration, setBondDuration] = useState("");
  const [bondDetails, setBondDetails] = useState("");
  const [interviewProcessNotes, setInterviewProcessNotes] = useState("");
  const [interviewDate, setInterviewDate] = useState("");
  const [registrationDeadline, setRegistrationDeadline] = useState("");
  const [vacancies, setVacancies] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch companies for dropdown
  const { data: companiesData } = useQuery({
    queryKey: ["companiesListAll"],
    queryFn: () => crmApi.getCompanies({ page_size: 100 }),
  });

  // Fetch job if editing
  const { data: existingJob, isLoading: isLoadingJob } = useQuery({
    queryKey: ["jobDetail", id],
    queryFn: () => jobsApi.getJobDetail(id!),
    enabled: isEditMode,
  });

  useEffect(() => {
    if (existingJob) {
      setCompanyId(existingJob.company);
      setTitle(existingJob.title);
      setDescription(existingJob.description);
      setRoleCategory(existingJob.role_category);
      setSkills(existingJob.required_skills?.join(", ") || "");
      setMinCgpa(existingJob.min_cgpa || "");
      setMinPercentage(existingJob.min_percentage || "");
      setBatches(existingJob.eligible_batches?.join(", ") || "");
      setBranches(existingJob.eligible_branches?.join(", ") || "");
      setMaxBacklogs(existingJob.max_backlogs_allowed || 0);
      setMinCtc(existingJob.min_ctc_lpa);
      setMaxCtc(existingJob.max_ctc_lpa);
      setStipend(existingJob.stipend_amount || "");
      setSalaryDetails(existingJob.salary_details || "");
      setLocation(existingJob.job_location || "");
      setWorkArrangement(existingJob.work_arrangement);
      setHasBond(existingJob.has_bond);
      setBondDuration(existingJob.bond_duration_months ? String(existingJob.bond_duration_months) : "");
      setBondDetails(existingJob.bond_details || "");
      setInterviewProcessNotes(existingJob.interview_process_notes || "");
      setInterviewDate(existingJob.interview_date || "");
      setRegistrationDeadline(
        existingJob.registration_deadline
          ? new Date(existingJob.registration_deadline).toISOString().slice(0, 16)
          : ""
      );
      setVacancies(existingJob.vacancies_count ? String(existingJob.vacancies_count) : "");
    }
  }, [existingJob]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyId) {
      setError("Please select a hiring partner company.");
      return;
    }
    if (!title.trim()) {
      setError("Role title is required.");
      return;
    }
    if (!minCtc || !maxCtc) {
      setError("Minimum and maximum CTC packages are required.");
      return;
    }
    if (Number(minCtc) > Number(maxCtc)) {
      setError("Maximum CTC must be greater than or equal to minimum CTC.");
      return;
    }
    if (!registrationDeadline) {
      setError("Registration cutoff deadline is required.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const payload = {
        company: companyId,
        title: title.trim(),
        description: description.trim(),
        role_category: roleCategory,
        required_skills: skills
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        min_cgpa: minCgpa ? Number(minCgpa) : null,
        min_percentage: minPercentage ? Number(minPercentage) : null,
        eligible_batches: batches
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        eligible_branches: branches
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        max_backlogs_allowed: Number(maxBacklogs) || 0,
        min_ctc_lpa: Number(minCtc),
        max_ctc_lpa: Number(maxCtc),
        stipend_amount: stipend ? Number(stipend) : null,
        salary_details: salaryDetails.trim(),
        job_location: location.trim(),
        work_arrangement: workArrangement,
        has_bond: hasBond,
        bond_duration_months: hasBond && bondDuration ? Number(bondDuration) : null,
        bond_details: hasBond ? bondDetails.trim() : "",
        interview_process_notes: interviewProcessNotes.trim(),
        interview_date: interviewDate || null,
        registration_deadline: new Date(registrationDeadline).toISOString(),
        vacancies_count: vacancies ? Number(vacancies) : null,
      };

      if (isEditMode) {
        await jobsApi.updateJob(id!, payload);
        navigate(`/jobs/${id}`);
      } else {
        const created = await jobsApi.createJob(payload);
        navigate(`/jobs/${created.id}`);
      }
    } catch (err: any) {
      const resp = err?.response?.data;
      if (typeof resp === "object") {
        const msg = Object.entries(resp)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
          .join(" | ");
        setError(msg || "Failed to save job requirement.");
      } else {
        setError("An unexpected server error occurred.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isEditMode && isLoadingJob) {
    return <LoadingState message="Loading job requirement specifications..." />;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in pb-12">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>
        <div className="text-xs font-mono text-slate-400">
          {isEditMode ? `Editing Draft: ${existingJob?.title}` : "New Job Specification Draft"}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 bg-slate-50">
          <div className="flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900">
              {isEditMode ? "Edit Job Requirement Draft" : "Create New Job Requirement"}
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Specify recruitment parameters, eligibility criteria, and process schedule for 5-point verification.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          {/* Section 1: Core Company and Role */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b pb-1.5 border-slate-100">
              1. Corporate Entity & Role Specification
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Hiring Partner Company <span className="text-rose-500">*</span>
                </label>
                <select
                  value={companyId}
                  onChange={(e) => setCompanyId(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-700 outline-none focus:border-indigo-500"
                  required
                >
                  <option value="">Select Company</option>
                  {companiesData?.results?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.canonical_domain || "No domain"})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Role Title / Designation <span className="text-rose-500">*</span>
                </label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Graduate Software Engineer - Backend"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Domain Role Category <span className="text-rose-500">*</span>
                </label>
                <select
                  value={roleCategory}
                  onChange={(e) => setRoleCategory(e.target.value as RoleCategory)}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-700 outline-none focus:border-indigo-500"
                >
                  <option value="SOFTWARE_ENGINEERING">Software Engineering</option>
                  <option value="DATA_ANALYTICS">Data Analytics / Science</option>
                  <option value="CLOUD_DEVOPS">Cloud Computing & DevOps</option>
                  <option value="QA_TESTING">QA Automation & Testing</option>
                  <option value="PRODUCT_SUPPORT">Product Support & Operations</option>
                  <option value="CYBERSECURITY">Cybersecurity</option>
                  <option value="BUSINESS_ANALYST">Business Analyst</option>
                  <option value="OTHER">Other Domain</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Work Arrangement
                </label>
                <select
                  value={workArrangement}
                  onChange={(e) => setWorkArrangement(e.target.value as WorkArrangement)}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-700 outline-none focus:border-indigo-500"
                >
                  <option value="ONSITE">On-Site (In-Office)</option>
                  <option value="HYBRID">Hybrid</option>
                  <option value="REMOTE">Full Remote</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Primary Job Location
                </label>
                <Input
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g., Bengaluru, Hyderabad, Pune"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Detailed Job Description
                </label>
                <textarea
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Key responsibilities, project domain, day-to-day deliverables..."
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Required Technical & Soft Skills (Comma-Separated)
                </label>
                <Input
                  value={skills}
                  onChange={(e) => setSkills(e.target.value)}
                  placeholder="Python, Django, PostgreSQL, Docker, Problem Solving"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Academic & Eligibility Criteria */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b pb-1.5 border-slate-100">
              2. Candidate Eligibility Criteria (Check 1: ELIGIBILITY)
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Min. CGPA (0.00 - 10.00)
                </label>
                <Input
                  type="number"
                  step="0.01"
                  value={minCgpa}
                  onChange={(e) => setMinCgpa(e.target.value)}
                  placeholder="e.g., 6.50"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Min. Percentage (%)
                </label>
                <Input
                  type="number"
                  step="0.01"
                  value={minPercentage}
                  onChange={(e) => setMinPercentage(e.target.value)}
                  placeholder="e.g., 60.00"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Max Active Backlogs
                </label>
                <Input
                  type="number"
                  value={maxBacklogs}
                  onChange={(e) => setMaxBacklogs(Number(e.target.value))}
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Eligible Branches (Comma-Separated)
                </label>
                <Input
                  value={branches}
                  onChange={(e) => setBranches(e.target.value)}
                  placeholder="CSE, ISE, ECE, EEE, MCA"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Eligible Batches (Years)
                </label>
                <Input
                  value={batches}
                  onChange={(e) => setBatches(e.target.value)}
                  placeholder="2024, 2025"
                />
              </div>
            </div>
          </div>

          {/* Section 3: Compensation Package */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b pb-1.5 border-slate-100">
              3. Compensation Package (Check 2: SALARY_AUTHENTICITY)
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Min CTC (LPA) <span className="text-rose-500">*</span>
                </label>
                <Input
                  type="number"
                  step="0.01"
                  value={minCtc}
                  onChange={(e) => setMinCtc(e.target.value)}
                  placeholder="e.g., 6.00"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Max CTC (LPA) <span className="text-rose-500">*</span>
                </label>
                <Input
                  type="number"
                  step="0.01"
                  value={maxCtc}
                  onChange={(e) => setMaxCtc(e.target.value)}
                  placeholder="e.g., 9.50"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Internship Stipend (INR/mo)
                </label>
                <Input
                  type="number"
                  step="1000"
                  value={stipend}
                  onChange={(e) => setStipend(e.target.value)}
                  placeholder="e.g., 25000"
                />
              </div>

              <div className="sm:col-span-3">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Compensation Breakdown & Perks
                </label>
                <Input
                  value={salaryDetails}
                  onChange={(e) => setSalaryDetails(e.target.value)}
                  placeholder="Fixed base: 5.5 LPA, Performance bonus: 1.0 LPA, Medical insurance included"
                />
              </div>
            </div>
          </div>

          {/* Section 4: Service Agreement & Schedule */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b pb-1.5 border-slate-100">
              4. Service Agreement & Schedule (Checks 4 & 5)
            </h3>

            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="hasBondCheck"
                  checked={hasBond}
                  onChange={(e) => setHasBond(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="hasBondCheck" className="text-xs font-semibold text-slate-800">
                  Employment Service Agreement / Bond Required
                </label>
              </div>

              {hasBond && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pl-6 border-l-2 border-indigo-200">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Bond Duration (Months) <span className="text-rose-500">*</span>
                    </label>
                    <Input
                      type="number"
                      value={bondDuration}
                      onChange={(e) => setBondDuration(e.target.value)}
                      placeholder="e.g., 18 or 24"
                      required={hasBond}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Bond Terms & Penalties
                    </label>
                    <Input
                      value={bondDetails}
                      onChange={(e) => setBondDetails(e.target.value)}
                      placeholder="e.g., Training reimbursement penalty of ₹50,000"
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Registration Cutoff <span className="text-rose-500">*</span>
                </label>
                <input
                  type="datetime-local"
                  value={registrationDeadline}
                  onChange={(e) => setRegistrationDeadline(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-700 outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Campus Drive / Interview Date
                </label>
                <input
                  type="date"
                  value={interviewDate}
                  onChange={(e) => setInterviewDate(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-700 outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Open Vacancies Count
                </label>
                <Input
                  type="number"
                  value={vacancies}
                  onChange={(e) => setVacancies(e.target.value)}
                  placeholder="e.g., 15"
                />
              </div>

              <div className="sm:col-span-3">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Interview Stages & Round Notes
                </label>
                <textarea
                  rows={2}
                  value={interviewProcessNotes}
                  onChange={(e) => setInterviewProcessNotes(e.target.value)}
                  placeholder="Round 1: Online Aptitude (60 mins), Round 2: Technical Coding (HackerEarth), Round 3: Tech Interview, Round 4: HR Discussion"
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
                />
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => navigate(-1)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isSubmitting}
              className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700"
            >
              <Save className="w-4 h-4" />
              <span>{isEditMode ? "Save Changes" : "Save as Draft"}</span>
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

