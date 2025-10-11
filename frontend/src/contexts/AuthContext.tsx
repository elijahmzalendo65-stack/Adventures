import { createContext, useContext, useState, useEffect, ReactNode } from "react";

export interface User {
  id: number;
  username: string;
  email: string;
  phone_number?: string;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminStats {
  totalUsers: number;
  totalBookings: number;
  pendingBookings: number;
  completedBookings: number;
}

interface AuthContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  login: (identifier: string, password: string) => Promise<boolean>;
  signup: (username: string, email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  refreshUser: () => Promise<void>;
  fetchAdminStats: () => Promise<AdminStats | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    checkAuth();
  }, []);

  // Login user with username or email
  const login = async (identifier: string, password: string): Promise<boolean> => {
    try {
      const res = await fetch("http://localhost:5000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username: identifier, password }),
      });

      const data = await res.json();
      if (res.ok && data.user) {
        setUser(data.user);
        return true;
      }

      console.error("Login failed:", data.message);
      return false;
    } catch (err) {
      console.error("Login request failed:", err);
      return false;
    }
  };

  // Signup new user
  const signup = async (username: string, email: string, password: string): Promise<boolean> => {
    try {
      const res = await fetch("http://localhost:5000/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, email, password, phone_number: "" }),
      });

      const data = await res.json();
      if (res.ok && data.user) {
        setUser(data.user);
        return true;
      }

      console.error("Signup failed:", data.message);
      return false;
    } catch (err) {
      console.error("Signup request failed:", err);
      return false;
    }
  };

  // Logout user
  const logout = async (): Promise<void> => {
    try {
      const res = await fetch("http://localhost:5000/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });

      if (res.ok) setUser(null);
    } catch (err) {
      console.error("Logout request failed:", err);
    }
  };

  // Check if user is already authenticated
  const checkAuth = async (): Promise<void> => {
    try {
      const res = await fetch("http://localhost:5000/api/auth/check-auth", {
        method: "GET",
        credentials: "include",
      });

      const data = await res.json();
      if (res.ok && data.authenticated && data.user) {
        setUser(data.user);
      } else {
        setUser(null);
      }
    } catch (err) {
      console.error("Check auth request failed:", err);
      setUser(null);
    }
  };

  // Refresh user data (useful after booking or payment)
  const refreshUser = async (): Promise<void> => {
    try {
      const res = await fetch("http://localhost:5000/api/auth/me", {
        method: "GET",
        credentials: "include",
      });
      const data = await res.json();
      if (res.ok && data.user) {
        setUser(data.user);
      }
    } catch (err) {
      console.error("Failed to refresh user data:", err);
    }
  };

  // Fetch admin dashboard stats
  const fetchAdminStats = async (): Promise<AdminStats | null> => {
    if (!user?.is_admin) return null;
    try {
      const res = await fetch("http://localhost:5000/api/admin/stats", {
        method: "GET",
        credentials: "include",
      });
      const data = await res.json();
      if (res.ok) return data as AdminStats;
      return null;
    } catch (err) {
      console.error("Failed to fetch admin stats:", err);
      return null;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        login,
        signup,
        logout,
        checkAuth,
        refreshUser,
        fetchAdminStats,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};
