/**
 * API Client
 * 
 * Axios-based API client with interceptors for authentication
 * and error handling.
 */

import axios, { AxiosError, AxiosInstance } from "axios";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Create axios instance
export const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = Cookies.get("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    // Handle 401 - try to refresh token
    if (error.response?.status === 401 && originalRequest) {
      const refreshToken = Cookies.get("refresh_token");
      
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data;
          
          Cookies.set("access_token", access_token);
          Cookies.set("refresh_token", refresh_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed - clear tokens and redirect to login
          Cookies.remove("access_token");
          Cookies.remove("refresh_token");
          window.location.href = "/auth/login";
          return Promise.reject(refreshError);
        }
      }
    }

    return Promise.reject(error);
  }
);

// API endpoints
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password, remember_me: false }),
  register: (email: string, password: string, confirmPassword: string, fullName: string) =>
    api.post("/auth/register", {
      email,
      password,
      confirm_password: confirmPassword,
      full_name: fullName,
    }),
  logout: () => api.post("/auth/logout"),
  me: () => api.get("/users/me"),
};

export const transactionsApi = {
  list: (params?: {
    page?: number;
    page_size?: number;
    category_id?: string;
    start_date?: string;
    end_date?: string;
    search?: string;
  }) => api.get("/transactions", { params }),
  get: (id: string) => api.get(`/transactions/${id}`),
  create: (data: {
    amount: number;
    transaction_date: string;
    description: string;
    merchant_name?: string;
    category_id?: string;
    transaction_type?: string;
  }) => api.post("/transactions", data),
  update: (id: string, data: Partial<{
    amount: number;
    description: string;
    category_id: string;
  }>) => api.put(`/transactions/${id}`, data),
  delete: (id: string) => api.delete(`/transactions/${id}`),
};

export const analyticsApi = {
  summary: (startDate?: string, endDate?: string) =>
    api.get("/analytics/summary", { params: { start_date: startDate, end_date: endDate } }),
  categories: (startDate?: string, endDate?: string) =>
    api.get("/analytics/category-breakdown", { params: { start_date: startDate, end_date: endDate } }),
  trends: (startDate?: string, endDate?: string, period?: string) =>
    api.get("/analytics/trends", { params: { start_date: startDate, end_date: endDate, period } }),
  focusCategories: (names: string[], startDate?: string, endDate?: string) =>
    api.get("/analytics/focus-categories", {
      params: {
        names: names.join(","),
        start_date: startDate,
        end_date: endDate,
      },
    }),
  insights: () => api.get("/analytics/insights"),
  budgetStatus: () => api.get("/analytics/budget-status"),
};

export const uploadApi = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  listJobs: () => api.get("/upload/jobs"),
  getJobStatus: (jobId: string) => api.get(`/upload/jobs/${jobId}`),
};
