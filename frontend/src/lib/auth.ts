/**
 * Authentication utilities
 */

import Cookies from "js-cookie";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export function getAccessToken(): string | undefined {
  return Cookies.get("access_token");
}

export function setAccessToken(token: string): void {
  Cookies.set("access_token", token, { expires: 1 / 48 }); // 30 minutes
}

export function getRefreshToken(): string | undefined {
  return Cookies.get("refresh_token");
}

export function setRefreshToken(token: string): void {
  Cookies.set("refresh_token", token, { expires: 7 }); // 7 days
}

export function clearTokens(): void {
  Cookies.remove("access_token");
  Cookies.remove("refresh_token");
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}
