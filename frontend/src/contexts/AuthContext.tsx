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
  dashboard: {
    total_users: number;
    total_adventures: number;
    total_bookings: number;
    total_revenue: number;
    recent_users: number;
    recent_bookings: number;
    recent_revenue: number;
  };
  analytics: {
    booking_status: { status: string; count: number }[];
    payment_status: { status: string; count: number }[];
    monthly_revenue: { year: number; month: number; revenue: number }[];
  };
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
  fetchAdminUsers: () => Promise<User[]>;
  fetchAdminBookings: () => Promise<any[]>;
  fetchUserBookings: () => Promise<any[]>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Base URL for all API calls
const API_BASE_URL = "https://mlima-adventures.onrender.com";

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // ----------------------
  // Initialize auth on mount
  // ----------------------
  useEffect(() => {
    checkAuth().finally(() => setLoading(false));
  }, []);

  // ----------------------
  // LOGIN (Session-based)
  // ----------------------
  const login = async (identifier: string, password: string): Promise<boolean> => {
    try {
      console.log("🔐 Attempting login with:", identifier);
      
      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        credentials: "include", // CRITICAL for session cookies
        body: JSON.stringify({
          email: identifier.includes("@") ? identifier : undefined,
          username: !identifier.includes("@") ? identifier : undefined,
          password
        }),
      });

      console.log("📡 Login response status:", res.status, res.statusText);
      
      // Check if response is JSON
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        console.error("❌ Server returned non-JSON response during login");
        const text = await res.text();
        console.error("📝 Response text:", text.substring(0, 200));
        return false;
      }

      const data = await res.json();
      console.log("✅ Login response data:", data);

      if (res.ok && data.user) {
        setUser(data.user);
        return true;
      }

      console.error("❌ Login failed:", data.message || "Unknown error");
      return false;
    } catch (err) {
      console.error("❌ Login request failed:", err);
      return false;
    }
  };

  // ----------------------
  // SIGNUP (Session-based) - FIXED ENDPOINT
  // ----------------------
  const signup = async (username: string, email: string, password: string): Promise<boolean> => {
    try {
      console.log("📝 Attempting signup with:", { username, email });
      
      // ✅ FIXED: Changed from /signup to /register
      const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        credentials: "include",
        body: JSON.stringify({ 
          username, 
          email, 
          password
          // Note: phone_number is optional in your backend, so we don't need to send it if not provided
        }),
      });

      console.log("📡 Signup response status:", res.status, res.statusText);
      
      // Check if response is JSON
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        console.error("❌ Server returned non-JSON response during signup");
        const text = await res.text();
        console.error("📝 Response text:", text.substring(0, 200));
        return false;
      }

      const data = await res.json();
      console.log("✅ Signup response data:", data);

      if (res.ok && data.user) {
        setUser(data.user);
        return true;
      }

      console.error("❌ Signup failed:", data.message || "Unknown error");
      return false;
    } catch (err) {
      console.error("❌ Signup request failed:", err);
      return false;
    }
  };

  // ----------------------
  // LOGOUT (Session-based)
  // ----------------------
  const logout = async (): Promise<void> => {
    try {
      console.log("🚪 Attempting logout...");
      
      const res = await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: "POST",
        credentials: "include",
      });

      console.log("📡 Logout response status:", res.status, res.statusText);

      if (res.ok) {
        setUser(null);
        console.log("✅ Logout successful");
      } else {
        console.error("❌ Logout failed with status:", res.status);
      }
    } catch (err) {
      console.error("❌ Logout request failed:", err);
    }
  };

  // ----------------------
  // CHECK AUTH (Session-based) - FIXED ENDPOINT
  // ----------------------
  const checkAuth = async (): Promise<void> => {
    try {
      console.log("🔍 Checking authentication status...");
      
      // ✅ FIXED: Changed from /api/auth/check to /api/auth/check-auth
      const res = await fetch(`${API_BASE_URL}/api/auth/check-auth`, {
        method: "GET",
        credentials: "include",
      });

      console.log("📡 Check auth response status:", res.status, res.statusText);

      if (!res.ok) {
        console.log("❌ Check auth failed, user not authenticated");
        setUser(null);
        return;
      }

      // Check if response is JSON
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        console.error("❌ Server returned non-JSON response during auth check");
        setUser(null);
        return;
      }

      const data = await res.json();
      console.log("✅ Check auth response data:", data);

      if (data.authenticated && data.user) {
        setUser(data.user);
        console.log("✅ User is authenticated:", data.user.username);
      } else {
        setUser(null);
        console.log("❌ User is not authenticated");
      }
    } catch (err) {
      console.error("❌ Check auth request failed:", err);
      setUser(null);
    }
  };

  // ----------------------
  // REFRESH USER (Session-based)
  // ----------------------
  const refreshUser = async (): Promise<void> => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
        method: "GET",
        credentials: "include",
      });

      if (res.ok) {
        const data = await res.json();
        if (data.user) {
          setUser(data.user);
          console.log("✅ User data refreshed");
        }
      }
    } catch (err) {
      console.error("❌ Failed to refresh user data:", err);
    }
  };

  // ----------------------
  // FETCH ADMIN DASHBOARD STATS - NOTE: This endpoint may not exist
  // ----------------------
  const fetchAdminStats = async (): Promise<AdminStats | null> => {
    if (!user?.is_admin) {
      console.log("❌ User is not admin, cannot fetch stats");
      return null;
    }

    try {
      console.log("📊 Fetching admin stats...");
      
      // ⚠️ NOTE: This endpoint (/api/auth/admin/stats) might not exist in your backend
      const res = await fetch(`${API_BASE_URL}/api/auth/admin/stats`, {
        method: "GET",
        credentials: "include",
      });

      if (res.ok) {
        const data = await res.json();
        console.log("✅ Admin stats fetched successfully");
        return data as AdminStats;
      }
      
      console.error("❌ Failed to fetch admin stats, status:", res.status);
      return null;
    } catch (err) {
      console.error("❌ Failed to fetch admin stats:", err);
      return null;
    }
  };

  // ----------------------
  // FETCH ALL USERS (ADMIN)
  // ----------------------
  const fetchAdminUsers = async (): Promise<User[]> => {
    if (!user?.is_admin) {
      console.log("❌ User is not admin, cannot fetch users");
      return [];
    }

    try {
      console.log("👥 Fetching admin users...");
      
      const res = await fetch(`${API_BASE_URL}/api/auth/admin/users`, {
        method: "GET",
        credentials: "include",
      });

      if (res.ok) {
        const data = await res.json();
        console.log("✅ Admin users fetched:", data.users?.length || 0, "users");
        return data.users || [];
      }
      
      console.error("❌ Failed to fetch admin users, status:", res.status);
      return [];
    } catch (err) {
      console.error("❌ Failed to fetch admin users:", err);
      return [];
    }
  };

  // ----------------------
  // FETCH ALL BOOKINGS (ADMIN) - NOTE: This endpoint may not exist
  // ----------------------
  const fetchAdminBookings = async (): Promise<any[]> => {
    if (!user?.is_admin) {
      console.log("❌ User is not admin, cannot fetch bookings");
      return [];
    }

    try {
      console.log("📋 Fetching admin bookings...");
      
      // ⚠️ NOTE: This endpoint (/api/auth/admin/bookings) might not exist in your backend
      const res = await fetch(`${API_BASE_URL}/api/auth/admin/bookings`, {
        method: "GET",
        credentials: "include",
      });

      if (res.ok) {
        const data = await res.json();
        console.log("✅ Admin bookings fetched:", data.bookings?.length || 0, "bookings");
        return data.bookings || [];
      }
      
      console.error("❌ Failed to fetch admin bookings, status:", res.status);
      return [];
    } catch (err) {
      console.error("❌ Failed to fetch admin bookings:", err);
      return [];
    }
  };

  // ----------------------
  // FETCH USER BOOKINGS (for Pricing page) - NOTE: This endpoint may not exist
  // ----------------------
  const fetchUserBookings = async (): Promise<any[]> => {
    if (!user) {
      console.log("❌ User not logged in, cannot fetch bookings");
      return [];
    }

    try {
      console.log("📋 Fetching user bookings...");
      
      // ⚠️ NOTE: This endpoint (/api/auth/bookings) might not exist in your backend
      const res = await fetch(`${API_BASE_URL}/api/auth/bookings`, {
        method: "GET",
        credentials: "include",
      });

      if (res.ok) {
        const data = await res.json();
        console.log("✅ User bookings fetched:", data.bookings?.length || 0, "bookings");
        return data.bookings || [];
      }
      
      console.error("❌ Failed to fetch user bookings, status:", res.status);
      return [];
    } catch (err) {
      console.error("❌ Failed to fetch user bookings:", err);
      return [];
    }
  };

  // Optional: Show loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading authentication...</p>
        </div>
      </div>
    );
  }

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
        fetchAdminUsers,
        fetchAdminBookings,
        fetchUserBookings,
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