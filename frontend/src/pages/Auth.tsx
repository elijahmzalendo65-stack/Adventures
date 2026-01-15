import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "@/hooks/use-toast";
import { ArrowLeft } from "lucide-react";

const Auth = () => {
  const navigate = useNavigate();
  const { user, login, signup, checkAuth } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  // Redirect already logged-in users
  useEffect(() => {
    if (user) {
      navigate(user.is_admin ? "/admin" : "/");
    }
  }, [user, navigate]);

  // ----------------------
  // Handle Login
  // ----------------------
  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    const formData = new FormData(e.currentTarget);
    const identifier = (formData.get("username") as string)?.trim();
    const password = formData.get("password") as string;

    if (!identifier || !password) {
      toast({
        title: "Login failed",
        description: "All fields are required",
        variant: "destructive",
      });
      setIsLoading(false);
      return;
    }

    try {
      console.log("🔐 Attempting login...");
      
      // Perform login using AuthContext
      const success = await login(identifier, password);

      if (success) {
        console.log("✅ Login successful, checking auth status...");
        
        // Refresh auth status to get updated user data
        await checkAuth();
        
        // Wait a moment for the auth context to update
        setTimeout(() => {
          console.log("✅ Redirecting user...");
          
          toast({
            title: "Login successful!",
            description: "Welcome back!",
          });

          // Navigate based on user role
          if (user?.is_admin) {
            navigate("/admin");
          } else {
            navigate("/");
          }
        }, 500);
      } else {
        toast({
          title: "Login failed",
          description: "Invalid username/email or password",
          variant: "destructive",
        });
      }
    } catch (error: any) {
      console.error("❌ Login error:", error);
      toast({
        title: "Login failed",
        description: error.message || "An error occurred during login",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // ----------------------
  // Handle Signup
  // ----------------------
  const handleSignup = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    const formData = new FormData(e.currentTarget);
    const username = (formData.get("username") as string)?.trim();
    const email = (formData.get("email") as string)?.trim();
    const password = formData.get("password") as string;

    if (!username || !email || !password) {
      toast({
        title: "Signup failed",
        description: "All fields are required",
        variant: "destructive",
      });
      setIsLoading(false);
      return;
    }

    try {
      console.log("📝 Attempting signup...");
      
      // Perform signup using AuthContext
      const success = await signup(username, email, password);

      if (success) {
        console.log("✅ Signup successful, checking auth status...");
        
        // Refresh auth status to get updated user data
        await checkAuth();
        
        // Wait a moment for the auth context to update
        setTimeout(() => {
          console.log("✅ Redirecting new user...");
          
          toast({
            title: "Account created!",
            description: `Welcome to Mlima Adventures, ${username}!`,
          });

          // Navigate based on user role (new users are typically not admin)
          if (user?.is_admin) {
            navigate("/admin");
          } else {
            navigate("/");
          }
        }, 500);
      } else {
        toast({
          title: "Signup failed",
          description: "Username or email already exists",
          variant: "destructive",
        });
      }
    } catch (error: any) {
      console.error("❌ Signup error:", error);
      toast({
        title: "Signup failed",
        description: error.message || "An error occurred during registration",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary/5 to-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-6">
          <Link to="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Home
            </Button>
          </Link>
        </div>

        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Mlima Adventures Tours</CardTitle>
            <CardDescription>
              Join us for unforgettable experiences in Central Kenya
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login">Login</TabsTrigger>
                <TabsTrigger value="signup">Sign Up</TabsTrigger>
              </TabsList>

              {/* LOGIN FORM */}
              <TabsContent value="login">
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-username">Username or Email</Label>
                    <Input
                      id="login-username"
                      name="username"
                      type="text"
                      placeholder="Username or Email"
                      required
                      disabled={isLoading}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password">Password</Label>
                    <Input
                      id="login-password"
                      name="password"
                      type="password"
                      placeholder="••••••••"
                      required
                      disabled={isLoading}
                    />
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full" 
                    disabled={isLoading}
                  >
                    {isLoading ? "Logging in..." : "Login"}
                  </Button>
                  <p className="text-xs text-muted-foreground text-center">
                    You can login with either username or email
                  </p>
                </form>
              </TabsContent>

              {/* SIGNUP FORM */}
              <TabsContent value="signup">
                <form onSubmit={handleSignup} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="signup-username">Username</Label>
                    <Input
                      id="signup-username"
                      name="username"
                      type="text"
                      placeholder="Choose a username"
                      required
                      disabled={isLoading}
                    />
                    <p className="text-xs text-muted-foreground">
                      This will be your display name
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-email">Email</Label>
                    <Input
                      id="signup-email"
                      name="email"
                      type="email"
                      placeholder="your@email.com"
                      required
                      disabled={isLoading}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-password">Password</Label>
                    <Input
                      id="signup-password"
                      name="password"
                      type="password"
                      placeholder="••••••••"
                      required
                      minLength={6}
                      disabled={isLoading}
                    />
                    <p className="text-xs text-muted-foreground">
                      Must be at least 6 characters
                    </p>
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full" 
                    disabled={isLoading}
                  >
                    {isLoading ? "Creating account..." : "Create Account"}
                  </Button>
                  <p className="text-xs text-muted-foreground text-center">
                    By signing up, you agree to our Terms & Conditions
                  </p>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Debug info (remove in production) */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">
            <strong>Note:</strong> Using session-based authentication. 
            No token storage needed in localStorage.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Auth;