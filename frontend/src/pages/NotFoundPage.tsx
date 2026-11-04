import React from "react";
import { useNavigate } from "react-router-dom";
import { FileQuestion } from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card, CardContent } from "../components/ui/Card";

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-4">
      <Card className="max-w-md w-full text-center">
        <CardContent className="py-12 px-6">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-slate-500">
            <FileQuestion className="h-8 w-8" />
          </div>
          <h2 className="text-xl font-bold text-brand-dark">Page Not Found (404)</h2>
          <p className="mt-2 text-sm text-brand-muted">
            The page or resource you requested does not exist or has been relocated.
          </p>

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
