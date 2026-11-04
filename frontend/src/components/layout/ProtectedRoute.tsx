import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { RoleCode } from "../../types";
import { LoadingState } from "../ui/LoadingState";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: RoleCode[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles,
}) => {
  const { isAuthenticated, isLoading, hasAnyRole, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-brand-surface">
        <LoadingState message="Verifying session and security permissions..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRoles && requiredRoles.length > 0) {
    const isSuper = user?.isSuperuser;
    if (!isSuper && !hasAnyRole(requiredRoles)) {
      return <Navigate to="/access-denied" replace />;
    }
  }

  return <>{children}</>;
};
