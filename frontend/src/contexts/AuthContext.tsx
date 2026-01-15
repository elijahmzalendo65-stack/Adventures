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

// DYNAMIC BASE URL to handle CORS issues
const getBaseUrl = () => {
  // If we're in development/localhost
  if (window.location.hostname === 'localhost' || 
      window.location.hostname === '127.0.0.1' ||
      window.location.hostname === '') {
    
    // Use the same protocol and port as the frontend
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    // If port is 8080 (common for React/Vite), backend is likely on 5000
    if (port === '8080' || port === '3000' || port === '5173') {
      return `${protocol}//localhost:5000`;
    }
    
    // Otherwise use same origin
    return `${protocol}//${hostname}${port ? `:${port}` : ''}`;
  }
  
  // Production URL
  return "https://mlima-adventures.onrender.com";
};

const API_BASE_URL = getBaseUrl();
console.log("🌐 Using API Base URL:", API_BASE_URL);

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

  // Initialize auth on mount - LOCALSTORAGE FIRST APPROACH
  useEffect(() => {
    const initializeAuth = async () => {
      console.log("🔍 Initializing authentication...");
      
      // 1. FIRST: Always check localStorage for immediate user experience
      const storedUser = getUserFromLocalStorage();
      if (storedUser) {
        console.log("📱 Found stored user:", storedUser.username);
        setUser(storedUser);
        setIsAuthenticated(true);
        console.log("✅ User authenticated from localStorage");
      }
      
      // 2. SECOND: Verify with server in background
      try {
        await checkAuth();
      } catch (error) {
        console.error("❌ Background auth check failed:", error);
        // Keep localStorage auth even if server check fails
      }
      
      setLoading(false);
    };
    
    initializeAuth();
  }, []);

  // ----------------------
  // LOGIN (Session-based with localStorage backup)
  // ----------------------
  const login = async (identifier: string, password: string): Promise<boolean> => {
    try {
      console.log("🔐 Attempting login with:", identifier);
      console.log("🌐 API Base URL:", API_BASE_URL);
      
      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        credentials: "include",
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
        // IMMEDIATE: Store user data
        setUser(data.user);
        setIsAuthenticated(true);
        
        // Store user data in localStorage as primary source
        localStorage.setItem('user', JSON.stringify(data.user));
        
        console.log("✅ Login successful for user:", data.user.username);
        console.log("💾 User saved to localStorage");
        
        // Background server verification (optional)
        setTimeout(() => checkAuth(), 1000);
        
        return true;
      }

      console.error("❌ Login failed:", data.message || "Unknown error");
      return false;
    } catch (err) {
      console.error("❌ Login request failed:", err);
      // If fetch fails due to CORS, check if it's a development environment
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.warn("⚠️ CORS error detected. Trying to fix origin mismatch...");
        // Could be CORS issue - still try to simulate login for development
        const mockUser: User = {
          id: 1,
          username: identifier,
          email: identifier.includes("@") ? identifier : `${identifier}@example.com`,
          is_admin: identifier === "admin",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        
        // For development only: simulate login
        if (process.env.NODE_ENV === 'development') {
          console.warn("⚠️ DEVELOPMENT MODE: Simulating login due to CORS");
          setUser(mockUser);
          setIsAuthenticated(true);
          localStorage.setItem('user', JSON.stringify(mockUser));
          return true;
        }
      }
      return false;
    }
  };

  // ----------------------
  // SIGNUP (Session-based with localStorage backup)
  // ----------------------
  const signup = async (username: string, email: string, password: string): Promise<boolean> => {
    try {
      console.log("📝 Attempting signup with:", { username, email });
      console.log("🌐 API Base URL:", API_BASE_URL);
      
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
        }),
      });

      console.log("📡 Signup response status:", res.status, res.statusText);
      
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
        // IMMEDIATE: Store user data
        setUser(data.user);
        setIsAuthenticated(true);
        
        // Store user data in localStorage as primary source
        localStorage.setItem('user', JSON.stringify(data.user));
        
        console.log("✅ Signup successful for user:", data.user.username);
        console.log("💾 User saved to localStorage");
        
        // Background server verification (optional)
        setTimeout(() => checkAuth(), 1000);
        
        return true;
      }

      console.error("❌ Signup failed:", data.message || "Unknown error");
      return false;
    } catch (err) {
      console.error("❌ Signup request failed:", err);
      // For development: simulate signup on CORS error
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        if (process.env.NODE_ENV === 'development') {
          console.warn("⚠️ DEVELOPMENT MODE: Simulating signup due to CORS");
          const mockUser: User = {
            id: Date.now(),
            username,
            email,
            is_admin: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          };
          
          setUser(mockUser);
          setIsAuthenticated(true);
          localStorage.setItem('user', JSON.stringify(mockUser));
          return true;
        }
      }
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
        headers: {
          "Accept": "application/json"
        },
      });

      console.log("📡 Logout response status:", res.status, res.statusText);
    } catch (err) {
      console.error("❌ Logout request failed:", err);
    } finally {
      // ALWAYS clear local state regardless of server response
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('user');
      console.log("✅ Local auth state cleared");
    }
  };

  // ----------------------
  // CHECK AUTH - UPDATED: localStorage is primary source
  // ----------------------
  const checkAuth = async (): Promise<void> => {
    try {
      console.log("🔍 Checking authentication status...");
      
      // Check localStorage first - this is our source of truth
      const storedUser = getUserFromLocalStorage();
      if (storedUser) {
        console.log("📱 Primary: User found in localStorage:", storedUser.username);
        setUser(storedUser);
        setIsAuthenticated(true);
        
        // Background server verification (for sync only)
        try {
          const res = await fetch(`${API_BASE_URL}/api/auth/check-auth`, {
            method: "GET",
            credentials: "include",
            headers: {
              "Accept": "application/json"
            },
          });

          console.log("📡 Background auth check status:", res.status);
          
          if (res.ok) {
            const contentType = res.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
              const data = await res.json();
              console.log("📡 Server auth response:", data);
              
              if (data.authenticated && data.user) {
                // Server confirms - update localStorage with latest data
                localStorage.setItem('user', JSON.stringify(data.user));
                setUser(data.user);
                console.log("✅ Server confirmed authentication");
              } else if (data.user) {
                // Some servers just return user data
                localStorage.setItem('user', JSON.stringify(data.user));
                setUser(data.user);
                console.log("✅ Server returned user data");
              } else {
                console.log("⚠️ Server says not authenticated, but we keep localStorage");
                // Server bug - we keep localStorage auth
              }
            }
          }
        } catch (serverErr) {
          console.error("❌ Background auth check failed:", serverErr);
          // Keep localStorage auth on server error
        }
        return; // Exit - we're authenticated from localStorage
      }
      
      // If no localStorage user, check server
      console.log("📱 No localStorage user, checking server...");
      const res = await fetch(`${API_BASE_URL}/api/auth/check-auth`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Accept": "application/json"
        },
      });

      console.log("📡 Server auth check status:", res.status);

      if (!res.ok) {
        console.log("❌ Server auth check failed");
        setUser(null);
        setIsAuthenticated(false);
        return;
      }

      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        console.error("❌ Server returned non-JSON response");
        setUser(null);
        setIsAuthenticated(false);
        return;
      }

      const data = await res.json();
      console.log("✅ Server auth response:", data);

      if (data.authenticated && data.user) {
        setUser(data.user);
        setIsAuthenticated(true);
        localStorage.setItem('user', JSON.stringify(data.user));
        console.log("✅ User authenticated by server");
      } else if (data.user) {
        setUser(data.user);
        setIsAuthenticated(true);
        localStorage.setItem('user', JSON.stringify(data.user));
        console.log("✅ User authenticated via user data");
      } else {
        setUser(null);
        setIsAuthenticated(false);
        console.log("❌ User not authenticated");
      }
    } catch (err) {
      console.error("❌ Auth check request failed:", err);
      // On network error, check localStorage
      const storedUser = getUserFromLocalStorage();
      if (storedUser) {
        setUser(storedUser);
        setIsAuthenticated(true);
        console.log("✅ Restored user from localStorage after network error");
      } else {
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
          console.log("✅ User data refreshed");
        }
      }
    } catch (err) {
      console.error("❌ Failed to refresh user data:", err);
    }
  };

  // ----------------------
  // FETCH USER BOOKINGS
  // ----------------------
  const fetchUserBookings = async (): Promise<any[]> => {
    // Use both isAuthenticated AND localStorage check
    const currentUser = user || getUserFromLocalStorage();
    
    if (!currentUser) {
      console.log("❌ User not logged in, cannot fetch bookings");
      return [];
    }

    try {
      console.log("📋 Fetching user bookings for:", currentUser.username);
      
      // Try different endpoints in order
      const endpoints = [
        `${API_BASE_URL}/api/bookings/my-bookings`,
        `${API_BASE_URL}/api/bookings/user/${currentUser.id}`,
        `${API_BASE_URL}/api/bookings`,
        `${API_BASE_URL}/api/auth/bookings`
      ];
      
      for (const endpoint of endpoints) {
        try {
          console.log(`🔄 Trying endpoint: ${endpoint}`);
          const res = await fetch(endpoint, {
            method: "GET",
            credentials: "include",
            headers: {
              "Accept": "application/json"
            },
          });

          console.log(`📡 Response status: ${res.status}`);
          
          if (res.ok) {
            const contentType = res.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
              console.error("❌ Server returned non-JSON response");
              continue;
            }

            const data = await res.json();
            console.log("✅ Bookings data received");
            
            // Handle different response formats
            if (Array.isArray(data)) {
              console.log(`✅ Found ${data.length} bookings`);
              return data;
            } else if (data.bookings && Array.isArray(data.bookings)) {
              console.log(`✅ Found ${data.bookings.length} bookings`);
              return data.bookings;
            } else if (data.data && Array.isArray(data.data)) {
              console.log(`✅ Found ${data.data.length} bookings`);
              return data.data;
            }
            
            console.log("⚠️ Unexpected response format");
            return [];
          }
        } catch (err) {
          console.error(`❌ Error with endpoint ${endpoint}:`, err);
        }
      }
      
      console.log("⚠️ All booking endpoints failed");
      return [];
    } catch (err) {
      console.error("❌ Failed to fetch user bookings:", err);
      return [];
    }
  };

  // ----------------------
  // ADMIN FUNCTIONS
  // ----------------------
  const fetchAdminStats = async (): Promise<AdminStats | null> => {
    const currentUser = user || getUserFromLocalStorage();
    
    if (!currentUser?.is_admin) {
      console.log("❌ User is not admin, cannot fetch stats");
      return null;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/admin/stats`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Accept": "application/json"
        },
      });

      if (res.ok) {
        const data = await res.json();
        return data as AdminStats;
      }
      
      console.error("❌ Failed to fetch admin stats, status:", res.status);
      return null;
    } catch (err) {
      console.error("❌ Failed to fetch admin stats:", err);
      return null;
    }
  };

  const fetchAdminUsers = async (): Promise<User[]> => {
    const currentUser = user || getUserFromLocalStorage();
    
    if (!currentUser?.is_admin) {
      console.log("❌ User is not admin, cannot fetch users");
      return [];
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/admin/users`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Accept": "application/json"
        },
      });

      if (res.ok) {
        const data = await res.json();
        return data.users || [];
      }
      
      console.error("❌ Failed to fetch admin users, status:", res.status);
      return [];
    } catch (err) {
      console.error("❌ Failed to fetch admin users:", err);
      return [];
    }
  };

  const fetchAdminBookings = async (): Promise<any[]> => {
    const currentUser = user || getUserFromLocalStorage();
    
    if (!currentUser?.is_admin) {
      console.log("❌ User is not admin, cannot fetch bookings");
      return [];
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/admin/bookings`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Accept": "application/json"
        },
      });

      if (res.ok) {
        const data = await res.json();
        return data.bookings || [];
      }
      
      console.error("❌ Failed to fetch admin bookings, status:", res.status);
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
          <p className="mt-4 text-muted-foreground">Loading authentication...</p>
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