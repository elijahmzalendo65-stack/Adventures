import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useNavigate } from "react-router-dom";

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
  isAdmin: boolean;
  setUser: (user: User | null) => void;
  login: (identifier: string, password: string) => Promise<{ success: boolean; redirectTo?: string }>;
  signup: (username: string, email: string, password: string) => Promise<{ success: boolean; redirectTo?: string }>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<{ authenticated: boolean; isAdmin?: boolean }>;
  refreshUser: () => Promise<void>;
  fetchAdminStats: () => Promise<AdminStats | null>;
  fetchAdminUsers: () => Promise<User[]>;
  fetchAdminBookings: () => Promise<any[]>;
  fetchUserBookings: () => Promise<any[]>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Use Vite environment variable or fallback to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  
  // We'll use a function to get navigate later
  const [navigateFn, setNavigateFn] = useState<((path: string) => void) | null>(null);

  // Helper function to get user from localStorage
  const getUserFromLocalStorage = (): User | null => {
    try {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        const parsedUser = JSON.parse(storedUser);
        return parsedUser;
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
        console.log("👑 Admin status:", storedUser.is_admin);
        setUser(storedUser);
        setIsAuthenticated(true);
        setIsAdmin(storedUser.is_admin || false);
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

  // Set navigate function from outside component
  const setNavigationFunction = (navigate: (path: string) => void) => {
    setNavigateFn(() => navigate);
  };

  // Function to handle redirection after login
  const handleLoginRedirect = (userData: User): string => {
    console.log("🔄 Determining redirect for user:", userData.username);
    console.log("👑 Admin status:", userData.is_admin);
    
    // Get the current path or intended redirect from localStorage
    const storedRedirect = localStorage.getItem('redirect_after_login');
    const defaultRedirect = "/"; // Default to home page
    
    // Clear the stored redirect
    if (storedRedirect) {
      localStorage.removeItem('redirect_after_login');
    }
    
    // Check if user is admin
    if (userData.is_admin) {
      console.log("🎯 Redirecting admin to dashboard");
      return "/admin/dashboard";
    }
    
    // Regular users go to their intended destination or home
    const redirectTo = storedRedirect || defaultRedirect;
    console.log("🎯 Redirecting user to:", redirectTo);
    return redirectTo;
  };

  // ----------------------
  // LOGIN (UPDATED with auto-redirection logic)
  // ----------------------
  const login = async (identifier: string, password: string): Promise<{ success: boolean; redirectTo?: string }> => {
    try {
      console.log("🔐 Attempting login to:", `${API_BASE_URL}/api/auth/login`);
      console.log("👤 Login attempt for:", identifier);
      
      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        credentials: "include",
        mode: 'cors',
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
        return { 
          success: false
        };
      }

      const data = await res.json();
      console.log("✅ Login response data:", data);

      if (res.ok && data.user) {
        const userData = data.user;
        console.log("👤 User authenticated:", userData.username);
        console.log("👑 Admin status:", userData.is_admin);
        
        setUser(userData);
        setIsAuthenticated(true);
        setIsAdmin(userData.is_admin || false);
        
        localStorage.setItem('user', JSON.stringify(userData));
        console.log("✅ Login successful");
        
        // Determine where to redirect
        const redirectTo = handleLoginRedirect(userData);
        
        return { 
          success: true, 
          redirectTo
        };
      } else {
        console.error("❌ Login failed:", data.message);
        return { 
          success: false
        };
      }
    } catch (err) {
      console.error("❌ Login request failed:", err);
      return { 
        success: false
      };
    }
  };

  // ----------------------
  // SIGNUP (UPDATED with auto-redirection)
  // ----------------------
  const signup = async (username: string, email: string, password: string): Promise<{ success: boolean; redirectTo?: string }> => {
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
        return { success: false };
      }

      const data = await res.json();
      console.log("✅ Signup response:", data);

      if (res.ok && data.user) {
        const userData = data.user;
        setUser(userData);
        setIsAuthenticated(true);
        setIsAdmin(userData.is_admin || false);
        localStorage.setItem('user', JSON.stringify(userData));
        console.log("✅ Signup successful");
        
        // Determine where to redirect
        const redirectTo = handleLoginRedirect(userData);
        
        return { 
          success: true, 
          redirectTo
        };
      }

      console.error("❌ Signup failed:", data.message);
      return { success: false };
    } catch (err) {
      console.error("❌ Signup request failed:", err);
      return { success: false };
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
      setIsAdmin(false);
      localStorage.removeItem('user');
      console.log("✅ Local auth state cleared");
    }
  };

  // ----------------------
  // CHECK AUTH (UPDATED for admin status)
  // ----------------------
  const checkAuth = async (): Promise<{ authenticated: boolean; isAdmin?: boolean }> => {
    try {
      console.log("🔍 Checking auth at:", `${API_BASE_URL}/api/auth/check-auth`);
      
      const storedUser = getUserFromLocalStorage();
      if (storedUser) {
        setUser(storedUser);
        setIsAuthenticated(true);
        setIsAdmin(storedUser.is_admin || false);
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
          setIsAdmin(false);
        }
        return { authenticated: false };
      }

      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        console.error("❌ Non-JSON response");
        return { authenticated: false };
      }

      const data = await res.json();
      console.log("✅ Auth response:", data);

      if (data.authenticated && data.user) {
        const userData = data.user;
        setUser(userData);
        setIsAuthenticated(true);
        setIsAdmin(userData.is_admin || false);
        localStorage.setItem('user', JSON.stringify(userData));
        return { 
          authenticated: true, 
          isAdmin: userData.is_admin || false 
        };
      } else if (data.user) {
        const userData = data.user;
        setUser(userData);
        setIsAuthenticated(true);
        setIsAdmin(userData.is_admin || false);
        localStorage.setItem('user', JSON.stringify(userData));
        return { 
          authenticated: true, 
          isAdmin: userData.is_admin || false 
        };
      } else if (!storedUser) {
        setUser(null);
        setIsAuthenticated(false);
        setIsAdmin(false);
        return { authenticated: false };
      }
      
      return { 
        authenticated: true, 
        isAdmin: storedUser?.is_admin || false 
      };
    } catch (err) {
      console.error("❌ Auth check failed:", err);
      const storedUser = getUserFromLocalStorage();
      if (!storedUser) {
        setUser(null);
        setIsAuthenticated(false);
        setIsAdmin(false);
      }
      return { 
        authenticated: !!storedUser, 
        isAdmin: storedUser?.is_admin || false 
      };
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
          const userData = data.user;
          setUser(userData);
          setIsAdmin(userData.is_admin || false);
          localStorage.setItem('user', JSON.stringify(userData));
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
    if (!isAdmin) {
      console.log("❌ Access denied: User is not an admin");
      return null;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/dashboard`, {
        method: "GET",
        credentials: "include",
        mode: 'cors',
        headers: {
          "Accept": "application/json"
        },
      });

      if (res.ok) {
        const data = await res.json();
        return data;
      }
      
      console.error("❌ Failed to fetch admin stats:", res.status);
      return null;
    } catch (err) {
      console.error("❌ Failed to fetch stats:", err);
      return null;
    }
  };

  const fetchAdminUsers = async (): Promise<User[]> => {
    if (!isAdmin) {
      console.log("❌ Access denied: User is not an admin");
      return [];
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/users`, {
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
    if (!isAdmin) {
      console.log("❌ Access denied: User is not an admin");
      return [];
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/bookings`, {
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
        isAdmin,
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

// Helper function to use auth with navigation
export const useAuthWithNavigation = () => {
  const auth = useAuth();
  const navigate = useNavigate();
  
  // Create enhanced login function with automatic navigation
  const loginWithRedirect = async (identifier: string, password: string) => {
    const result = await auth.login(identifier, password);
    
    if (result.success && result.redirectTo) {
      navigate(result.redirectTo);
    }
    
    return result;
  };
  
  // Create enhanced signup function with automatic navigation
  const signupWithRedirect = async (username: string, email: string, password: string) => {
    const result = await auth.signup(username, email, password);
    
    if (result.success && result.redirectTo) {
      navigate(result.redirectTo);
    }
    
    return result;
  };
  
  return {
    ...auth,
    login: loginWithRedirect,
    signup: signupWithRedirect
  };
};