import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { apiClient } from "../api/apiClient";
import { User, AuthState, RoleCode } from "../types";

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  hasRole: (role: RoleCode) => boolean;
  hasAnyRole: (roles: RoleCode[]) => boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const mapBackendUser = (data: any): User => ({
    id: data.id,
    email: data.email,
    firstName: data.first_name || "",
    lastName: data.last_name || "",
    fullName: `${data.first_name || ""} ${data.last_name || ""}`.trim() || data.email,
    phone: data.phone || "",
    isActive: data.is_active ?? true,
    isStaff: data.is_staff ?? false,
    isSuperuser: data.is_superuser ?? false,
    roles: (data.roles || []) as RoleCode[],
    createdAt: data.created_at,
  });

  const refreshUser = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await apiClient.get("/auth/me/");
      setUser(mapBackendUser(res.data));
    } catch (err: any) {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string): Promise<User> => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiClient.post("/auth/login/", { email, password });
      const authenticatedUser = mapBackendUser(res.data);
      setUser(authenticatedUser);
      return authenticatedUser;
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail || "Authentication failed. Please verify credentials.";
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await apiClient.post("/auth/logout/");
    } catch (err) {
      console.warn("Logout endpoint error, clearing local session", err);
    } finally {
      setUser(null);
      window.location.href = "/login";
    }
  };

  const hasRole = (role: RoleCode): boolean => {
    if (!user) return false;
    if (user.isSuperuser) return true;
    return user.roles.includes(role);
  };

  const hasAnyRole = (roles: RoleCode[]): boolean => {
    if (!user) return false;
    if (user.isSuperuser) return true;
    return roles.some((r) => user.roles.includes(r));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        logout,
        hasRole,
        hasAnyRole,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
