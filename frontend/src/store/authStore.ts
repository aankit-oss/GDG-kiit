import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthUser {
  user_id: number;
  email: string;
  full_name: string;
  plan: "free" | "pro" | "enterprise";
  is_admin: boolean;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  setAuth: (token: string, user: AuthUser) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: "lexaudit-auth" }
  )
);

export function getAuthHeader(): Record<string, string> {
  const token = useAuthStore.getState().token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}
