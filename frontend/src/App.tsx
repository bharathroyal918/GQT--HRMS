import React, { Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/queryClient";
import { AuthProvider } from "./context/AuthContext";
import { AppShell } from "./components/layout/AppShell";
import { ProtectedRoute } from "./components/layout/ProtectedRoute";

const LoginPage = React.lazy(() => import("./pages/LoginPage").then(m => ({ default: m.LoginPage })));
const DashboardPage = React.lazy(() => import("./pages/DashboardPage").then(m => ({ default: m.DashboardPage })));
const AccessDeniedPage = React.lazy(() => import("./pages/AccessDeniedPage").then(m => ({ default: m.AccessDeniedPage })));
const NotFoundPage = React.lazy(() => import("./pages/NotFoundPage").then(m => ({ default: m.NotFoundPage })));
const CompanyDirectoryPage = React.lazy(() => import("./pages/crm/CompanyDirectoryPage").then(m => ({ default: m.CompanyDirectoryPage })));
const CompanyDetailPage = React.lazy(() => import("./pages/crm/CompanyDetailPage").then(m => ({ default: m.CompanyDetailPage })));
const FollowUpDashboardPage = React.lazy(() => import("./pages/crm/FollowUpDashboardPage").then(m => ({ default: m.FollowUpDashboardPage })));
const JobDirectoryPage = React.lazy(() => import("./pages/jobs/JobDirectoryPage").then(m => ({ default: m.JobDirectoryPage })));
const JobFormPage = React.lazy(() => import("./pages/jobs/JobFormPage").then(m => ({ default: m.JobFormPage })));
const JobDetailPage = React.lazy(() => import("./pages/jobs/JobDetailPage").then(m => ({ default: m.JobDetailPage })));
const VerificationQueuePage = React.lazy(() => import("./pages/jobs/VerificationQueuePage").then(m => ({ default: m.VerificationQueuePage })));
const ApprovalQueuePage = React.lazy(() => import("./pages/jobs/ApprovalQueuePage").then(m => ({ default: m.ApprovalQueuePage })));
const CreativeStudioDashboardPage = React.lazy(() => import("./pages/creatives/CreativeStudioDashboardPage").then(m => ({ default: m.CreativeStudioDashboardPage })));
const CreativeDirectoryPage = React.lazy(() => import("./pages/creatives/CreativeDirectoryPage").then(m => ({ default: m.CreativeDirectoryPage })));
const CreativeRequestFormPage = React.lazy(() => import("./pages/creatives/CreativeRequestFormPage").then(m => ({ default: m.CreativeRequestFormPage })));
const CreativeDetailPage = React.lazy(() => import("./pages/creatives/CreativeDetailPage").then(m => ({ default: m.CreativeDetailPage })));
const CreativeReviewQueuePage = React.lazy(() => import("./pages/creatives/CreativeReviewQueuePage").then(m => ({ default: m.CreativeReviewQueuePage })));
const DesignerWorkspacePage = React.lazy(() => import("./pages/creatives/DesignerWorkspacePage").then(m => ({ default: m.DesignerWorkspacePage })));
const AuditLogViewerPage = React.lazy(() => import("./pages/audit/AuditLogViewerPage").then(m => ({ default: m.AuditLogViewerPage })));
const StudentDirectoryPage = React.lazy(() => import("./pages/students/StudentDirectoryPage").then(m => ({ default: m.StudentDirectoryPage })));
const StudentDetailPage = React.lazy(() => import("./pages/students/StudentDetailPage").then(m => ({ default: m.StudentDetailPage })));
const PlacementDrivesPage = React.lazy(() => import("./pages/interviews/PlacementDrivesPage").then(m => ({ default: m.PlacementDrivesPage })));
const DriveDetailPage = React.lazy(() => import("./pages/interviews/DriveDetailPage").then(m => ({ default: m.DriveDetailPage })));

const PageLoader: React.FC = () => (
  <div className="flex h-64 items-center justify-center">
    <div className="flex items-center space-x-2 text-slate-500 text-sm">
      <div className="h-4 w-4 animate-spin rounded-full border-2 border-brand-teal border-t-transparent" />
      <span>Loading module...</span>
    </div>
  </div>
);

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<PageLoader />}>
            <Routes>
            {/* Public Authentication Route */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected Application Routes within AppShell */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="access-denied" element={<AccessDeniedPage />} />

              {/* Recruitment CRM: Phase 2 Implemented Modules */}
              <Route
                path="companies"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CALLING_EXECUTIVE", "CRM_EXECUTIVE", "AUDITOR"]}>
                    <CompanyDirectoryPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="companies/:id"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CALLING_EXECUTIVE", "CRM_EXECUTIVE", "AUDITOR"]}>
                    <CompanyDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="outreach"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "CALLING_EXECUTIVE", "CRM_EXECUTIVE", "AUDITOR"]}>
                    <FollowUpDashboardPage />
                  </ProtectedRoute>
                }
              />
              {/* Job Requirements & Verification: Phase 3 Implemented Modules */}
              <Route
                path="jobs"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CALLING_EXECUTIVE", "CRM_EXECUTIVE", "AUDITOR"]}>
                    <JobDirectoryPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="jobs/new"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER"]}>
                    <JobFormPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="jobs/:id"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CALLING_EXECUTIVE", "CRM_EXECUTIVE", "AUDITOR"]}>
                    <JobDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="jobs/:id/edit"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER"]}>
                    <JobFormPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="jobs/verification-queue"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "AUDITOR"]}>
                    <VerificationQueuePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="jobs/approval-queue"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD"]}>
                    <ApprovalQueuePage />
                  </ProtectedRoute>
                }
              />
              {/* Creative Studio & Asset Approval: Phase 4 Implemented Modules */}
              <Route
                path="creatives"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CREATIVE_REVIEWER", "CREATIVE_DESIGNER", "AUDITOR"]}>
                    <CreativeStudioDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="creatives/dashboard"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CREATIVE_REVIEWER", "CREATIVE_DESIGNER", "AUDITOR"]}>
                    <CreativeStudioDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="creatives/directory"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CREATIVE_REVIEWER", "CREATIVE_DESIGNER", "AUDITOR"]}>
                    <CreativeDirectoryPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="creatives/new"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CREATIVE_REVIEWER"]}>
                    <CreativeRequestFormPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="creatives/:id"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CREATIVE_REVIEWER", "CREATIVE_DESIGNER", "AUDITOR"]}>
                    <CreativeDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="creatives/:id/edit"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CREATIVE_REVIEWER"]}>
                    <CreativeRequestFormPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="creatives/review-queue"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "CREATIVE_REVIEWER", "AUDITOR"]}>
                    <CreativeReviewQueuePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="creatives/triage-queue"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "CREATIVE_REVIEWER", "AUDITOR"]}>
                    <CreativeDirectoryPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="creatives/designer-workspace"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "CREATIVE_DESIGNER", "CREATIVE_REVIEWER"]}>
                    <DesignerWorkspacePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="students"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "TRAINER", "AUDITOR"]}>
                    <StudentDirectoryPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="students/:id"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "TRAINER", "AUDITOR"]}>
                    <StudentDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="interviews"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "INTERVIEW_COORDINATOR", "AUDITOR"]}>
                    <PlacementDrivesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="interviews/:id"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "INTERVIEW_COORDINATOR", "AUDITOR"]}>
                    <DriveDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="audit"
                element={
                  <ProtectedRoute requiredRoles={["ADMIN", "AUDITOR"]}>
                    <AuditLogViewerPage />
                  </ProtectedRoute>
                }
              />

              <Route path="*" element={<NotFoundPage />} />
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
