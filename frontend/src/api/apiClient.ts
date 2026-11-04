import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { generateCorrelationId } from "../lib/utils";

export const apiClient = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
  timeout: 15000,
});

// Request Interceptor: Attach X-Correlation-ID and CSRF Token if present
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (!config.headers["X-Correlation-ID"]) {
      config.headers["X-Correlation-ID"] = generateCorrelationId();
    }
    // Extract Django CSRF cookie if present
    const csrfMatch = document.cookie.match(/(^|;)\s*csrftoken\s*=\s*([^;]+)/);
    if (csrfMatch && csrfMatch[2]) {
      config.headers["X-CSRFToken"] = csrfMatch[2];
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Silent refresh on 401 once
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve();
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Don't loop refresh for login, refresh or logout endpoints
    const requestUrl = originalRequest?.url || "";
    const isAuthEndpoint =
      requestUrl.includes("auth/login") ||
      requestUrl.includes("auth/token/refresh") ||
      requestUrl.includes("auth/logout");

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => apiClient(originalRequest))
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await apiClient.post("/auth/token/refresh/");
        processQueue();
        return apiClient(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr);
        // Force redirect to login page if refresh fails
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
          window.location.href = `/login?session_expired=true`;
        }
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
