import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertCircle, Eye, EyeOff, LogIn, UserPlus, Shield } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";

const Auth = () => {
  const [activeTab, setActiveTab] = useState<"login" | "signup">("login");
  const [formData, setFormData] = useState({
    identifier: "",
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const { login, signup } = useAuth();
  const navigate = useNavigate();

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // Call login which now returns { success: boolean; redirectTo?: string }
      const result = await login(formData.identifier, formData.password);
      
      console.log("✅ Login result:", result);
      
      if (result.success) {
        toast({
          title: "Login Successful",
          description: result.redirectTo?.includes("admin") 
            ? "Redirecting to admin dashboard..." 
            : "Welcome back!",
          variant: "default",
        });

        // If redirectTo is provided, navigate to it
        if (result.redirectTo) {
          navigate(result.redirectTo);
        } else {
          // Fallback: navigate to home
          navigate("/");
        }
      } else {
        setError("Invalid credentials. Please try again.");
        toast({
          title: "Login Failed",
          description: "Invalid email/username or password",
          variant: "destructive",
        });
      }
    } catch (err: any) {
      console.error("❌ Login error:", err);
      setError(err.message || "An error occurred during login");
      toast({
        title: "Login Error",
        description: err.message || "Something went wrong",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoading(true);

    try {
      // Call signup which now returns { success: boolean; redirectTo?: string }
      const result = await signup(formData.username, formData.email, formData.password);
      
      console.log("✅ Signup result:", result);
      
      if (result.success) {
        toast({
          title: "Registration Successful",
          description: result.redirectTo?.includes("admin")
            ? "Account created! Redirecting to admin dashboard..."
            : "Account created successfully!",
          variant: "default",
        });

        // If redirectTo is provided, navigate to it
        if (result.redirectTo) {
          navigate(result.redirectTo);
        } else {
          // Fallback: navigate to home
          navigate("/");
        }
      } else {
        setError("Registration failed. Please try again.");
        toast({
          title: "Registration Failed",
          description: "Could not create account",
          variant: "destructive",
        });
      }
    } catch (err: any) {
      console.error("❌ Signup error:", err);
      setError(err.message || "An error occurred during registration");
      toast({
        title: "Registration Error",
        description: err.message || "Something went wrong",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (type: "admin" | "test") => {
    if (type === "admin") {
      handleInputChange("identifier", "admin456@gmail.com");
      handleInputChange("password", "admin456");
      toast({
        title: "Admin Credentials Loaded",
        description: "Click Login to access admin dashboard",
        variant: "default",
      });
    } else {
      handleInputChange("identifier", "test@example.com");
      handleInputChange("password", "password123");
      toast({
        title: "Test Credentials Loaded",
        description: "Click Login to continue",
        variant: "default",
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 p-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">
            Mlima Adventures
          </CardTitle>
          <CardDescription className="text-center">
            {activeTab === "login" 
              ? "Login to your account" 
              : "Create a new account"}
          </CardDescription>
        </CardHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "login" | "signup")}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="login" className="flex items-center gap-2">
              <LogIn className="h-4 w-4" />
              Login
            </TabsTrigger>
            <TabsTrigger value="signup" className="flex items-center gap-2">
              <UserPlus className="h-4 w-4" />
              Sign Up
            </TabsTrigger>
          </TabsList>

          {/* LOGIN TAB */}
          <TabsContent value="login">
            <form onSubmit={handleLogin}>
              <CardContent className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="login-identifier">Email or Username</Label>
                  <Input
                    id="login-identifier"
                    type="text"
                    placeholder="admin456@gmail.com or admin456"
                    value={formData.identifier}
                    onChange={(e) => handleInputChange("identifier", e.target.value)}
                    required
                    disabled={loading}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="login-password">Password</Label>
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1"
                    >
                      {showPassword ? (
                        <>
                          <EyeOff className="h-3 w-3" />
                          Hide
                        </>
                      ) : (
                        <>
                          <Eye className="h-3 w-3" />
                          Show
                        </>
                      )}
                    </button>
                  </div>
                  <Input
                    id="login-password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => handleInputChange("password", e.target.value)}
                    required
                    disabled={loading}
                  />
                </div>

                <div className="space-y-3">
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Logging in...
                      </>
                    ) : (
                      <>
                        <LogIn className="h-4 w-4 mr-2" />
                        Login
                      </>
                    )}
                  </Button>

                  <div className="grid grid-cols-2 gap-2">
                    {/* <Button
                      type="button"
                      variant="outline"
                      onClick={() => handleQuickLogin("admin")}
                      disabled={loading}
                      className="flex items-center gap-2"
                    >
                      <Shield className="h-4 w-4" />
                      Admin
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => handleQuickLogin("test")}
                      disabled={loading}
                    >
                      Test User
                    </Button> */}
                  </div>
                </div>

                <div className="text-center text-sm text-muted-foreground">
                  <p>
                    Don't have an account?{" "}
                    <button
                      type="button"
                      onClick={() => setActiveTab("signup")}
                      className="text-primary hover:underline font-medium"
                    >
                      Sign up
                    </button>
                  </p>
                </div>
              </CardContent>
            </form>
          </TabsContent>

          {/* SIGNUP TAB */}
          <TabsContent value="signup">
            <form onSubmit={handleSignup}>
              <CardContent className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="signup-username">Username</Label>
                  <Input
                    id="signup-username"
                    type="text"
                    placeholder="john_doe"
                    value={formData.username}
                    onChange={(e) => handleInputChange("username", e.target.value)}
                    required
                    disabled={loading}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="signup-email">Email</Label>
                  <Input
                    id="signup-email"
                    type="email"
                    placeholder="john@example.com"
                    value={formData.email}
                    onChange={(e) => handleInputChange("email", e.target.value)}
                    required
                    disabled={loading}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="signup-password">Password</Label>
                  <Input
                    id="signup-password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => handleInputChange("password", e.target.value)}
                    required
                    disabled={loading}
                  />
                  <p className="text-xs text-muted-foreground">
                    Must be at least 6 characters
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm-password">Confirm Password</Label>
                  <Input
                    id="confirm-password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={(e) => handleInputChange("confirmPassword", e.target.value)}
                    required
                    disabled={loading}
                  />
                </div>

                <div className="space-y-3">
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Creating account...
                      </>
                    ) : (
                      <>
                        <UserPlus className="h-4 w-4 mr-2" />
                        Sign Up
                      </>
                    )}
                  </Button>

                  <div className="text-center text-sm text-muted-foreground">
                    <p>
                      Already have an account?{" "}
                      <button
                        type="button"
                        onClick={() => setActiveTab("login")}
                        className="text-primary hover:underline font-medium"
                      >
                        Login
                      </button>
                    </p>
                  </div>
                </div>
              </CardContent>
            </form>
          </TabsContent>
        </Tabs>

        {/* <CardFooter className="border-t pt-4">
          <div className="w-full">
            <p className="text-xs text-center text-muted-foreground">
              <strong>Demo Credentials:</strong>
            </p>
            <div className="grid grid-cols-2 gap-2 mt-2 text-xs text-center">
              <div className="p-2 bg-blue-50 rounded">
                <p className="font-medium">Admin</p>
                <p>admin456@gmail.com</p>
                <p>password: admin456</p>
              </div>
              <div className="p-2 bg-green-50 rounded">
                <p className="font-medium">Test User</p>
                <p>test@example.com</p>
                <p>password: password123</p>
              </div>
            </div>
          </div>
        </CardFooter> */}
      </Card>
    </div>
  );
};

export default Auth;