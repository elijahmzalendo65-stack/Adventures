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
  isAuthenticated: boolean;
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

// FIX: Use environment-based URL
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? "https://mlima-adventures.onrender.com"
  : "http://localhost:5000"; // Change this to your local Flask server

// OR use Vite environment variable:
// const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

// OR create a simple config:
const config = {
  apiBaseUrl: window.location.hostname === 'localhost' 
    ? "http://localhost:5000" 
    : "https://mlima-adventures.onrender.com"
};

// Use this:
// const API_BASE_URL = config.apiBaseUrl;

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Helper function to get user from localStorage
  const getUserFromLocalStorage = (): User | null => {
    try {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        return JSON.parse(storedUser);
      }
    } catch (error) {
      console.error("❌ Error parsing user from localStorage:", error);
      localStorage.removeItem('user');
    }
    return null;
  };

  // Initialize auth on mount
  useEffect(() => {
    const initializeAuth = async () => {
      console.log("🔍 Initializing authentication...");
      console.log("🌐 API Base URL:", API_BASE_URL);
      
      // Check localStorage first
      const storedUser = getUserFromLocalStorage();
      if (storedUser) {
        console.log("📱 Found stored user:", storedUser.username);
        setUser(storedUser);
        setIsAuthenticated(true);
      }
      
      // Verify with server
      try {
        await checkAuth();
      } catch (error) {
        console.error("❌ Background auth check failed:", error);
      }
      
      setLoading(false);
    };
    
    initializeAuth();
  }, []);

  // ----------------------
  // LOGIN
  // ----------------------
  const login = async (identifier: string, password: string): Promise<boolean> => {
    try {
      console.log("🔐 Attempting login to:", `${API_BASE_URL}/api/auth/login`);
      
      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        credentials: "include", // IMPORTANT: For session cookies
        mode: 'cors', // Explicitly set CORS mode
        body: JSON.stringify({
          email: identifier.includes("@") ? identifier : undefined,
          username: !identifier.includes("@") ? identifier : undefined,
          password
        }),
      });

      console.log("📡 Login response status:", res.status);
      
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        const text = await res.text();
        console.error("❌ Non-JSON response:", text.substring(0, 200));
        return false;
      }

      const data = await res.json();
      console.log("✅ Login response:", data);

      if (res.ok && data.user) {
        setUser(data.user);
        setIsAuthenticated(true);
        localStorage.setItem('user', JSON.stringify(data.user));
        console.log("✅ Login successful");
        return true;
      }

      console.error("❌ Login failed:", data.message);
      return false;
    } catch (err) {
      console.error("❌ Login request failed:", err);
      return false;
    }
  };

  // ----------------------
  // SIGNUP
  // ----------------------
  const signup = async (username: string, email: string, password: string): Promise<boolean> => {
    try {
      console.log("📝 Attempting signup to:", `${API_BASE_URL}/api/auth/register`);
      
      const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        credentials: "include",
        mode: 'cors',
        body: JSON.stringify({ 
          username, 
          email, 
          password
        }),
      });

      console.log("📡 Signup response status:", res.status);
      
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        const text = await res.text();
        console.error("❌ Non-JSON response:", text.substring(0, 200));
        return false;
      }

      const data = await res.json();
      console.log("✅ Signup response:", data);

      if (res.ok && data.user) {
        setUser(data.user);
        setIsAuthenticated(true);
        localStorage.setItem('user', JSON.stringify(data.user));
        console.log("✅ Signup successful");
        return true;
      }

      console.error("❌ Signup failed:", data.message);
      return false;
    } catch (err) {
      console.error("❌ Signup request failed:", err);
      return false;
    }
  };

  // ----------------------
  // LOGOUT
  // ----------------------
  const logout = async (): Promise<void> => {
    try {
      console.log("🚪 Attempting logout...");
      
      const res = await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: "POST",
        credentials: "include",
        mode: 'cors',
        headers: {
          "Accept": "application/json"
        },
      });

      console.log("📡 Logout response status:", res.status);
    } catch (err) {
      console.error("❌ Logout request failed:", err);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('user');
      console.log("✅ Local auth state cleared");
    }
  };

  // ----------------------
  // CHECK AUTH
  // ----------------------
  const checkAuth = async (): Promise<void> => {
    try {
      console.log("🔍 Checking auth at:", `${API_BASE_URL}/api/auth/check-auth`);
      
      const storedUser = getUserFromLocalStorage();
      if (storedUser) {
        setUser(storedUser);
        setIsAuthenticated(true);
      }
      
      const res = await fetch(`${API_BASE_URL}/api/auth/check-auth`, {
        method: "GET",
        credentials: "include",
        mode: 'cors',
        headers: {
          "Accept": "application/json"
        },
      });

      console.log("📡 Auth check status:", res.status);

      if (!res.ok) {
        console.log("❌ Server auth check failed");
        if (!storedUser) {
          setUser(null);
          setIsAuthenticated(false);
        }
        return;
      }

      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        console.error("❌ Non-JSON response");
        return;
      }

      const data = await res.json();
      console.log("✅ Auth response:", data);

      if (data.authenticated && data.user) {
        setUser(data.user);
        setIsAuthenticated(true);
        localStorage.setItem('user', JSON.stringify(data.user));
      } else if (data.user) {
        setUser(data.user);
        setIsAuthenticated(true);
        localStorage.setItem('user', JSON.stringify(data.user));
      } else if (!storedUser) {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (err) {
      console.error("❌ Auth check failed:", err);
      const storedUser = getUserFromLocalStorage();
      if (!storedUser) {
        setUser(null);
        setIsAuthenticated(false);
      }
    }
  };

  // ----------------------
  // REFRESH USER
  // ----------------------
  const refreshUser = async (): Promise<void> => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
        method: "GET",
        credentials: "include",
        mode: 'cors',
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
      });

      if (res.ok) {
        const data = await res.json();
        if (data.user) {
          setUser(data.user);
          localStorage.setItem('user', JSON.stringify(data.user));
        }
      }
    } catch (err) {
      console.error("❌ Failed to refresh user:", err);
    }
  };

  // ----------------------
  // FETCH USER BOOKINGS
  // ----------------------
  const fetchUserBookings = async (): Promise<any[]> => {
    const currentUser = user || getUserFromLocalStorage();
    
    if (!currentUser) {
      console.log("❌ User not logged in");
      return [];
    }

    try {
      const endpoints = [
        `${API_BASE_URL}/api/bookings/my-bookings`,
        `${API_BASE_URL}/api/bookings/user/${currentUser.id}`,
        `${API_BASE_URL}/api/bookings`,
      ];
      
      for (const endpoint of endpoints) {
        try {
          const res = await fetch(endpoint, {
            method: "GET",
            credentials: "include",
            mode: 'cors',
            headers: {
              "Accept": "application/json"
            },
          });

          if (res.ok) {
            const data = await res.json();
            if (Array.isArray(data)) {
              return data;
            } else if (data.bookings && Array.isArray(data.bookings)) {
              return data.bookings;
            } else if (data.data && Array.isArray(data.data)) {
              return data.data;
            }
          }
        } catch (err) {
          console.error(`❌ Error with ${endpoint}:`, err);
        }
      }
      
      return [];
    } catch (err) {
      console.error("❌ Failed to fetch bookings:", err);
      return [];
    }
  };

  // ----------------------
  // ADMIN FUNCTIONS
  // ----------------------
  const fetchAdminStats = async (): Promise<AdminStats | null> => {
    const currentUser = user || getUserFromLocalStorage();
    
    if (!currentUser?.is_admin) {
      return null;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/admin/stats`, {
        method: "GET",
        credentials: "include",
        mode: 'cors',
        headers: {
          "Accept": "application/json"
        },
      });

      if (res.ok) {
        return await res.json();
      }
      return null;
    } catch (err) {
      console.error("❌ Failed to fetch stats:", err);
      return null;
    }
  };

  const fetchAdminUsers = async (): Promise<User[]> => {
    const currentUser = user || getUserFromLocalStorage();
    
    if (!currentUser?.is_admin) {
      return [];
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/admin/users`, {
        method: "GET",
        credentials: "include",
        mode: 'cors',
        headers: {
          "Accept": "application/json"
        },
      });

      if (res.ok) {
        const data = await res.json();
        return data.users || [];
      }
      return [];
    } catch (err) {
      console.error("❌ Failed to fetch users:", err);
      return [];
    }
  };

  const fetchAdminBookings = async (): Promise<any[]> => {
    const currentUser = user || getUserFromLocalStorage();
    
    if (!currentUser?.is_admin) {
      return [];
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/admin/bookings`, {
        method: "GET",
        credentials: "include",
        mode: 'cors',
        headers: {
          "Accept": "application/json"
        },
      });

      if (res.ok) {
        const data = await res.json();
        return data.bookings || [];
      }
      return [];
    } catch (err) {
      console.error("❌ Failed to fetch admin bookings:", err);
      return [];
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
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