import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Mail, Lock, AlertCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { GQTLogo } from "../components/layout/GQTLogo";
import { Input } from "../components/ui/Input";
import { Button } from "../components/ui/Button";
import { Card, CardContent } from "../components/ui/Card";

const loginSchema = z.object({
  email: z.string().min(1, "Email is required").email("Please enter a valid corporate email"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const queryParams = new URLSearchParams(location.search);
  const sessionExpired = queryParams.get("session_expired") === "true";

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (values: LoginFormValues) => {
    setErrorMessage(null);
    try {
      await login(values.email, values.password);
      const from = (location.state as any)?.from?.pathname || "/dashboard";
      navigate(from, { replace: true });
    } catch (err: any) {
      setErrorMessage(err.message || "Invalid email or password.");
    }
  };

  return (
    <div className="flex min-h-screen flex-col justify-center bg-gradient-to-b from-brand-surface to-slate-200 py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="flex justify-center mb-4">
          <GQTLogo size="lg" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-brand-navy">
          GQT Recruitment CRM
        </h2>
        <p className="mt-1 text-sm text-brand-muted">
          Staff Authentication & Placement Operations Portal
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card className="shadow-lg border-slate-200">
          <CardContent className="py-8 px-6 sm:px-10">
            {sessionExpired && (
              <div className="mb-4 rounded-md bg-amber-50 p-3 border border-amber-200 flex items-start gap-2 text-xs text-amber-800">
                <AlertCircle className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
                <span>Your session has expired. Please sign in again to continue.</span>
              </div>
            )}

            {errorMessage && (
              <div
                role="alert"
                className="mb-4 rounded-md bg-red-50 p-3 border border-red-200 flex items-start gap-2 text-xs text-red-800"
              >
                <AlertCircle className="h-4 w-4 shrink-0 text-red-600 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
              <Input
                label="Corporate Email Address"
                type="email"
                placeholder="staff@gqt.local"
                autoComplete="email"
                leftIcon={<Mail className="h-4 w-4" />}
                error={errors.email?.message}
                {...register("email")}
              />

              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                autoComplete="current-password"
                leftIcon={<Lock className="h-4 w-4" />}
                error={errors.password?.message}
                {...register("password")}
              />

              <div className="pt-2">
                <Button
                  type="submit"
                  className="w-full"
                  isLoading={isSubmitting}
                  variant="primary"
                  size="md"
                >
                  Sign In to HRMS
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <p className="mt-6 text-center text-xs text-slate-500">
          Authorized personnel only • Protected by Argon2id & Audit Trail
        </p>
      </div>
    </div>
  );
};
