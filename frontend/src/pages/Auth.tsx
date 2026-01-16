import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const Auth: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [isRedirecting, setIsRedirecting] = useState(false);
  
  const { login, signup, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();

  // Debug: Log auth state changes
  useEffect(() => {
    console.log("🔍 Auth Component - Auth state:", {
      isAuthenticated,
      user: user ? user.username : null,
      localStorageUser: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')!).username : 'none'
    });
  }, [isAuthenticated, user]);

  // Check if user is already logged in (on mount)
  useEffect(() => {
    const checkIfLoggedIn = () => {
      try {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          const parsedUser = JSON.parse(storedUser);
          console.log("📱 Found user in localStorage:", parsedUser.username);
        }
      } catch (error) {
        console.error("Error checking localStorage:", error);
      }
    };
    
    checkIfLoggedIn();
  }, []);

  // Redirect when authenticated
  useEffect(() => {
    const redirectIfAuthenticated = () => {
      const hasAuth = isAuthenticated || localStorage.getItem('user');
      
      if (hasAuth && !isRedirecting) {
        setIsRedirecting(true);
        console.log("✅ User authenticated, redirecting to home...");
        
        setTimeout(() => {
          navigate("/");
        }, 500);
      }
    };
    
    redirectIfAuthenticated();
  }, [isAuthenticated, user, isRedirecting, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Debug info
    console.log("🌐 ========== AUTH FORM SUBMISSION ==========");
    console.log("📱 Mode:", isLogin ? "LOGIN" : "SIGNUP");
    console.log("👤 Username:", username);
    if (!isLogin) console.log("📧 Email:", email);
    console.log("🔒 Password length:", password.length);
    
    setLoading(true);
    setMessage(null);
    setIsRedirecting(false);

    try {
      let success = false;

      if (isLogin) {
        // Login flow
        console.log("🔄 Attempting login...");
        success = await login(username, password);
        
        if (success) {
          console.log("✅ Login successful via AuthContext");
          setMessage({ text: "Login successful! Redirecting...", type: 'success' });
          
          // Force immediate localStorage check
          setTimeout(() => {
            const storedUser = localStorage.getItem('user');
            if (storedUser) {
              console.log("💾 Confirmed: User saved to localStorage");
            }
          }, 100);
        } else {
          console.error("❌ Login failed via AuthContext");
          setMessage({ text: "Login failed. Please check your credentials.", type: 'error' });
        }
      } else {
        // Signup flow
        if (password !== confirmPassword) {
          setMessage({ text: "Passwords do not match!", type: 'error' });
          setLoading(false);
          return;
        }

        if (password.length < 6) {
          setMessage({ text: "Password must be at least 6 characters!", type: 'error' });
          setLoading(false);
          return;
        }

        console.log("🔄 Attempting signup...");
        success = await signup(username, email, password);
        
        if (success) {
          console.log("✅ Signup successful via AuthContext");
          setMessage({ text: "Account created successfully! You are now logged in.", type: 'success' });
          
          setTimeout(() => {
            const storedUser = localStorage.getItem('user');
            if (storedUser) {
              console.log("💾 Confirmed: User saved to localStorage after signup");
            }
          }, 100);
        } else {
          console.error("❌ Signup failed via AuthContext");
          setMessage({ text: "Signup failed. Please try again.", type: 'error' });
        }
      }
    } catch (error) {
      console.error("❌ Auth error:", error);
      setMessage({ text: "An error occurred. Please try again.", type: 'error' });
    } finally {
      setLoading(false);
      console.log("🌐 ========== FORM SUBMISSION COMPLETE ==========");
    }
  };

  const handleDemoLogin = async (demoUser: string) => {
    setLoading(true);
    setMessage(null);
    setIsRedirecting(false);
    
    // Demo credentials - UPDATED
    const credentials: Record<string, { username: string; password: string }> = {
      admin: { username: "admin", password: "admin123" },
      user: { username: "testuser", password: "test123" },
    };

    const creds = credentials[demoUser];
    if (!creds) return;

    console.log(`🔐 Attempting demo login as ${demoUser}...`);
    console.log(`👤 Using credentials: ${creds.username} / ${creds.password}`);
    
    try {
      const success = await login(creds.username, creds.password);
      
      if (success) {
        setMessage({ text: `Logged in as ${demoUser}! Redirecting...`, type: 'success' });
        console.log("✅ Demo login successful");
      } else {
        setMessage({ text: "Demo login failed. Please try manual login.", type: 'error' });
      }
    } catch (error) {
      console.error("❌ Demo login error:", error);
      setMessage({ text: "Demo login failed.", type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // NEW: Direct API test function
  const testApiConnection = async () => {
    console.log("🧪 ========== API CONNECTION TEST ==========");
    
    try {
      // Test 1: Simple GET to health endpoint
      console.log("🔧 Testing GET request to /api/health...");
      const healthRes = await fetch("http://localhost:5000/api/health");
      console.log("📡 Health endpoint status:", healthRes.status);
      console.log("📡 Health endpoint headers:", Object.fromEntries(healthRes.headers.entries()));
      
      // Test 2: CORS preflight
      console.log("🔧 Testing OPTIONS preflight...");
      const optionsRes = await fetch("http://localhost:5000/api/auth/login", {
        method: "OPTIONS",
        headers: {
          "Origin": "http://localhost:8080",
          "Access-Control-Request-Method": "POST",
          "Access-Control-Request-Headers": "Content-Type"
        }
      });
      console.log("📡 OPTIONS status:", optionsRes.status);
      
      // Test 3: Direct login attempt
      console.log("🔧 Testing direct login API call...");
      const testLogin = await fetch("http://localhost:5000/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
          "Origin": "http://localhost:8080"
        },
        credentials: "include",
        body: JSON.stringify({
          username: "admin",
          password: "admin123"
        })
      });
      console.log("📡 Direct login status:", testLogin.status);
      
      if (testLogin.ok) {
        const data = await testLogin.json();
        console.log("✅ Direct login successful:", data);
        setMessage({ text: "API connection successful! Server is responding.", type: 'success' });
      } else {
        const text = await testLogin.text();
        console.error("❌ Direct login failed:", text);
        setMessage({ text: "API connection failed. Check server logs.", type: 'error' });
      }
      
    } catch (error) {
      console.error("❌ API test failed completely:", error);
      setMessage({ text: "Cannot connect to API server. Is Flask running?", type: 'error' });
    }
    
    console.log("🧪 ========== API TEST COMPLETE ==========");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Logo/Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              MLima Adventures
            </h1>
            <p className="text-gray-600">
              {isLogin ? "Welcome back!" : "Create your account"}
            </p>
          </div>

          {/* Message Display */}
          {message && (
            <div className={`mb-6 p-3 rounded-lg ${message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              <div className="flex items-center">
                {message.type === 'success' ? (
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                )}
                <span>{message.text}</span>
                {message.type === 'success' && (
                  <div className="ml-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-700"></div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Demo Login Buttons */}
          {isLogin && (
            <div className="mb-6">
              <p className="text-sm text-gray-600 mb-3 text-center">
                Try demo accounts:
              </p>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => handleDemoLogin("admin")}
                  disabled={loading || isRedirecting}
                  className="flex-1 bg-purple-100 text-purple-700 py-2 px-4 rounded-lg font-medium hover:bg-purple-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Admin Demo
                </button>
                <button
                  onClick={() => handleDemoLogin("user")}
                  disabled={loading || isRedirecting}
                  className="flex-1 bg-blue-100 text-blue-700 py-2 px-4 rounded-lg font-medium hover:bg-blue-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  User Demo
                </button>
              </div>
            </div>
          )}

          {/* API Test Button (Debug - Remove in production) */}
          {process.env.NODE_ENV === 'development' && (
            <div className="mb-6 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800 mb-2 text-center font-medium">
                🔧 API Connection Test
              </p>
              <button
                onClick={testApiConnection}
                className="w-full bg-yellow-100 text-yellow-800 py-2 px-4 rounded-lg font-medium hover:bg-yellow-200 transition-colors"
              >
                Test Server Connection
              </button>
              <p className="text-xs text-yellow-600 mt-2 text-center">
                Checks if Flask server is reachable
              </p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                  placeholder="Enter your email"
                  required
                  disabled={loading || isRedirecting}
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {isLogin ? "Username or Email" : "Username"}
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                placeholder={isLogin ? "Enter username or email" : "Choose a username"}
                required
                disabled={loading || isRedirecting}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                placeholder="Enter password"
                required
                minLength={6}
                disabled={loading || isRedirecting}
              />
              {!isLogin && (
                <p className="mt-1 text-xs text-gray-500">
                  Must be at least 6 characters
                </p>
              )}
            </div>

            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Confirm Password
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                  placeholder="Confirm your password"
                  required
                  minLength={6}
                  disabled={loading || isRedirecting}
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading || isRedirecting}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-3 px-4 rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 focus:ring-4 focus:ring-blue-300 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isRedirecting ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 mr-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Redirecting...
                </span>
              ) : loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 mr-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {isLogin ? "Logging in..." : "Creating Account..."}
                </span>
              ) : (
                isLogin ? "Sign In" : "Create Account"
              )}
            </button>
          </form>

          {/* Toggle between login/signup */}
          <div className="mt-8 text-center">
            <p className="text-gray-600">
              {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
              <button
                onClick={() => {
                  setIsLogin(!isLogin);
                  setPassword("");
                  setConfirmPassword("");
                  setMessage(null);
                }}
                className="text-blue-600 font-medium hover:text-blue-800 transition-colors"
                disabled={loading || isRedirecting}
              >
                {isLogin ? "Sign up" : "Sign in"}
              </button>
            </p>
          </div>

          {/* Debug info (remove in production) */}
          {process.env.NODE_ENV === 'development' && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <div className="space-y-2">
                <p className="text-xs text-gray-600">
                  <span className="font-medium">Auth State:</span> {isAuthenticated ? "✅ Authenticated" : "❌ Not Authenticated"}
                  {user && ` | 👤 User: ${user.username}`}
                  {isRedirecting && " | 🔄 Redirecting..."}
                </p>
                <p className="text-xs text-gray-500">
                  <span className="font-medium">LocalStorage:</span> {localStorage.getItem('user') ? '✅ Has user' : '❌ No user'}
                </p>
                <p className="text-xs text-gray-400">
                  <span className="font-medium">API Target:</span> localhost:5000 (check AuthContext.tsx)
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Home link */}
        <div className="text-center mt-6">
          <Link
            to="/"
            className="text-gray-600 hover:text-gray-800 transition-colors inline-flex items-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Auth;