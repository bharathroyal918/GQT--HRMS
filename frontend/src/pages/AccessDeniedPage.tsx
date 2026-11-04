import React from "react";
import { useNavigate } from "react-router-dom";
import { ShieldX } from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card, CardContent } from "../components/ui/Card";
import { useAuth } from "../context/AuthContext";

export const AccessDeniedPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-4">
      <Card className="max-w-md w-full text-center">
        <CardContent className="py-12 px-6">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600">
            <ShieldX className="h-8 w-8" />
          </div>
          <h2 className="text-xl font-bold text-brand-dark">Access Denied (403)</h2>
          <p className="mt-2 text-sm text-brand-muted">
            You do not have the required institutional role to view this operational module.
          </p>

          {user && (
            <div className="mt-4 rounded-md bg-slate-50 p-3 text-xs text-slate-600 border border-slate-200">
              <span className="font-semibold text-brand-dark">Your Assigned Roles: </span>
              {user.roles.length > 0 ? user.roles.join(", ") : "None assigned"}
            </div>
          )}

          <div className="mt-6 flex justify-center gap-3">
            <Button variant="primary" onClick={() => navigate("/dashboard")}>
              Return to Dashboard
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
