"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Cookies from "js-cookie";
import { authApi } from "@/lib/api";

interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
}

export function useAuth() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await authApi.login(email, password);
      const { access_token, refresh_token } = response.data.tokens;

      Cookies.set("access_token", access_token, { expires: 1 / 48 });
      Cookies.set("refresh_token", refresh_token, { expires: 7 });

      const userResponse = await authApi.me();
      setUser(userResponse.data);

      return userResponse.data;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(
    async (email: string, password: string, confirmPassword: string, fullName: string) => {
      setIsLoading(true);
      try {
        await authApi.register(email, password, confirmPassword, fullName);
        return await login(email, password);
      } finally {
        setIsLoading(false);
      }
    },
    [login]
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (error) {
      // Ignore errors
    } finally {
      Cookies.remove("access_token");
      Cookies.remove("refresh_token");
      setUser(null);
      router.push("/auth/login");
    }
  }, [router]);

  const fetchUser = useCallback(async () => {
    const token = Cookies.get("access_token");
    if (!token) return null;

    try {
      const response = await authApi.me();
      setUser(response.data);
      return response.data;
    } catch (error) {
      Cookies.remove("access_token");
      Cookies.remove("refresh_token");
      return null;
    }
  }, []);

  return {
    user,
    isLoading,
    login,
    register,
    logout,
    fetchUser,
  };
}
