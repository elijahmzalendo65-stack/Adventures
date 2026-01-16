import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Users, Calendar, DollarSign, Search, LogOut, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/contexts/AuthContext";

interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
  is_admin?: boolean;
}

interface Booking {
  id: number;
  user: User;
  adventure: { title: string };
  adventure_date: string;
  number_of_people: number;
  total_amount: number;
  status: string;
  booking_reference?: string;
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
}

interface DashboardStats {
  total_users: number;
  total_bookings: number;
  total_revenue: number;
  recent_users?: number;
  recent_bookings?: number;
  recent_revenue?: number;
}

const Admin = () => {
  const navigate = useNavigate();
  const { user, logout, fetchAdminStats, fetchAdminUsers, fetchAdminBookings } = useAuth();

  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [userSearchTerm, setUserSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [retryCount, setRetryCount] = useState(0);

  // Check if user is admin
  useEffect(() => {
    console.log("🔍 Admin component - Current user:", user);
    
    const checkAdminAccess = () => {
      const currentUser = user || getUserFromLocalStorage();
      const isAdmin = currentUser?.is_admin;
      
      console.log("👑 Admin check:", { 
        hasUser: !!user, 
        hasLocalStorageUser: !!currentUser,
        isAdmin: isAdmin 
      });
      
      if (!isAdmin) {
        console.log("❌ User is not admin, redirecting to home");
        navigate("/");
      }
    };
    
    checkAdminAccess();
  }, [user, navigate]);

  // Helper to get user from localStorage
  const getUserFromLocalStorage = (): User | null => {
    try {
      const storedUser = localStorage.getItem('user');
      return storedUser ? JSON.parse(storedUser) : null;
    } catch (error) {
      return null;
    }
  };

  // ----------------------
  // Fetch Dashboard Stats
  // ----------------------
  const fetchDashboard = async () => {
    try {
      console.log("📊 Fetching admin stats...");
      const stats = await fetchAdminStats();
      if (stats) {
        setDashboardStats(stats.dashboard);
        console.log("✅ Dashboard stats loaded:", stats.dashboard);
      } else {
        console.log("⚠️ No stats returned from API");
        // Fallback: Calculate from local data
        const fallbackStats = {
          total_users: users.length,
          total_bookings: bookings.length,
          total_revenue: bookings.reduce((sum, b) => sum + (b.total_amount || 0), 0)
        };
        setDashboardStats(fallbackStats);
      }
    } catch (err) {
      console.error("❌ Failed to fetch dashboard stats:", err);
      // Fallback stats
      const fallbackStats = {
        total_users: users.length,
        total_bookings: bookings.length,
        total_revenue: bookings.reduce((sum, b) => sum + (b.total_amount || 0), 0)
      };
      setDashboardStats(fallbackStats);
    }
  };

  // ----------------------
  // Fetch Users
  // ----------------------
  const fetchUsers = async () => {
    try {
      console.log("👥 Fetching admin users...");
      const adminUsers = await fetchAdminUsers();
      console.log("✅ Users received from API:", adminUsers);
      setUsers(Array.isArray(adminUsers) ? adminUsers : []);
    } catch (err) {
      console.error("❌ Failed to fetch users:", err);
      setUsers([]);
    }
  };

  // ----------------------
  // Fetch Bookings
  // ----------------------
  const fetchBookings = async () => {
    try {
      console.log("📋 Fetching admin bookings...");
      const adminBookings = await fetchAdminBookings();
      console.log("✅ Bookings received from API:", adminBookings);
      setBookings(Array.isArray(adminBookings) ? adminBookings : []);
    } catch (err) {
      console.error("❌ Failed to fetch bookings:", err);
      setBookings([]);
    }
  };

  // ----------------------
  // Fetch all data on load
  // ----------------------
  const loadData = async () => {
    const currentUser = user || getUserFromLocalStorage();
    
    if (!currentUser?.is_admin) {
      console.log("⚠️ Skipping data load - user not admin");
      return;
    }
    
    setLoading(true);
    setError("");
    
    console.log("🔄 Loading admin data...");
    
    try {
      await Promise.all([
        fetchUsers(),
        fetchBookings()
      ]);
      
      // Stats depend on users and bookings
      await fetchDashboard();
      
      console.log("✅ All admin data loaded successfully");
    } catch (err) {
      console.error("❌ Error loading admin data:", err);
      setError("Failed to load admin data. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user, retryCount]); // Re-run when user changes or retry is clicked

  // ----------------------
  // Logout
  // ----------------------
  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (err) {
      console.error("Failed to logout", err);
      // Still redirect to login on error
      navigate("/login");
    }
  };

  // ----------------------
  // Retry loading data
  // ----------------------
  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
  };

  // ----------------------
  // Filtered Data
  // ----------------------
  const filteredBookings = bookings.filter(
    (booking) =>
      booking.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.customer_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.booking_reference?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.id.toString().includes(searchTerm)
  );

  const filteredUsers = users.filter(
    (user) =>
      user.username.toLowerCase().includes(userSearchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(userSearchTerm.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "confirmed":
      case "completed":
      case "paid":
        return "bg-green-500/10 text-green-700 dark:text-green-400";
      case "pending":
      case "awaiting_payment":
        return "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400";
      case "cancelled":
      case "refunded":
        return "bg-red-500/10 text-red-700 dark:text-red-400";
      default:
        return "bg-gray-500/10 text-gray-700 dark:text-gray-400";
    }
  };

  const getStatusText = (status: string) => {
    switch (status?.toLowerCase()) {
      case "awaiting_payment": return "Pending Payment";
      case "completed": return "Completed";
      case "confirmed": return "Confirmed";
      case "paid": return "Paid";
      case "cancelled": return "Cancelled";
      case "refunded": return "Refunded";
      default: return status || "Pending";
    }
  };

  if (!user?.is_admin && !getUserFromLocalStorage()?.is_admin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Access Denied</CardTitle>
            <CardDescription>You don't have permission to access the admin dashboard.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => navigate("/")} className="w-full">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Home
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading admin dashboard...</p>
          <p className="text-sm text-gray-500 mt-2">
            Fetching data from: localhost:5000
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Site
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-primary">Admin Dashboard</h1>
              <p className="text-sm text-muted-foreground">
                Welcome, {user?.username || getUserFromLocalStorage()?.username} 
                <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-1 rounded">Admin</span>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleRetry}
              className="flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            <Button variant="outline" onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Debug Info - Remove in production */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-gray-800">Debug Info:</h3>
                <div className="text-sm text-gray-600 space-y-1 mt-1">
                  <p>API Base: localhost:5000 (check AuthContext.tsx)</p>
                  <p>Users loaded: {users.length}</p>
                  <p>Bookings loaded: {bookings.length}</p>
                  <p>User is admin: {user?.is_admin ? 'Yes' : 'No'}</p>
                  <p>Session active: {user ? 'Yes' : 'No'}</p>
                </div>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => console.log({
                  users, 
                  bookings, 
                  dashboardStats, 
                  authUser: user,
                  localStorageUser: getUserFromLocalStorage()
                })}
              >
                Log Data
              </Button>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 font-medium">{error}</p>
            <p className="text-sm text-red-600 mt-1">
              Check that Flask is running on localhost:5000 and you're logged in as admin.
            </p>
            <div className="flex gap-2 mt-3">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleRetry}
                className="flex items-center gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Retry
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => window.location.reload()}
              >
                Reload Page
              </Button>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Users</CardTitle>
              <Users className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardStats?.total_users || users.length}</div>
              <p className="text-xs text-muted-foreground mt-1">Registered users</p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Bookings</CardTitle>
              <Calendar className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardStats?.total_bookings || bookings.length}</div>
              <p className="text-xs text-muted-foreground mt-1">All time bookings</p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Revenue</CardTitle>
              <DollarSign className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                KSh {(dashboardStats?.total_revenue || bookings.reduce((sum, b) => sum + (b.total_amount || 0), 0)).toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Lifetime revenue</p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Active Bookings</CardTitle>
              <Calendar className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {bookings.filter(b => 
                  ['confirmed', 'pending', 'awaiting_payment'].includes(b.status?.toLowerCase())
                ).length}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Pending/Confirmed</p>
            </CardContent>
          </Card>
        </div>

        {/* Data Tables with Tabs */}
        <Card>
          <Tabs defaultValue="bookings" className="w-full">
            <CardHeader>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="bookings">Bookings ({bookings.length})</TabsTrigger>
                <TabsTrigger value="users">Registered Users ({users.length})</TabsTrigger>
              </TabsList>
            </CardHeader>

            {/* Bookings Tab */}
            <TabsContent value="bookings">
              <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <CardTitle>Recent Bookings</CardTitle>
                  <CardDescription>Manage and track all adventure bookings</CardDescription>
                </div>
                <div className="relative w-full sm:w-64">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search bookings..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Reference</TableHead>
                        <TableHead>Customer</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Guests</TableHead>
                        <TableHead>Amount</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredBookings.length > 0 ? (
                        filteredBookings.map((booking) => (
                          <TableRow key={booking.id}>
                            <TableCell className="font-mono text-xs">{booking.id}</TableCell>
                            <TableCell className="font-mono text-xs">
                              {booking.booking_reference || `BKG-${booking.id}`}
                            </TableCell>
                            <TableCell>
                              <div>
                                <div className="font-medium">{booking.customer_name || booking.user?.username || "Unknown"}</div>
                                {booking.customer_email && (
                                  <div className="text-xs text-muted-foreground">{booking.customer_email}</div>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              {booking.adventure_date ? (
                                new Date(booking.adventure_date).toLocaleDateString("en-GB", {
                                  day: "2-digit",
                                  month: "short",
                                  year: "numeric",
                                })
                              ) : (
                                "N/A"
                              )}
                            </TableCell>
                            <TableCell>{booking.number_of_people || 1}</TableCell>
                            <TableCell>KSh {(booking.total_amount || 0).toLocaleString()}</TableCell>
                            <TableCell>
                              <Badge variant="secondary" className={getStatusColor(booking.status)}>
                                {getStatusText(booking.status)}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                            {bookings.length === 0 ? (
                              <div className="flex flex-col items-center gap-2">
                                <Calendar className="h-8 w-8 text-gray-400" />
                                <p>No bookings found</p>
                                <p className="text-sm">Bookings will appear here once created</p>
                              </div>
                            ) : (
                              "No matching bookings found"
                            )}
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </TabsContent>

            {/* Users Tab */}
            <TabsContent value="users">
              <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <CardTitle>Registered Users</CardTitle>
                  <CardDescription>View all users who have signed up</CardDescription>
                </div>
                <div className="relative w-full sm:w-64">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search users..."
                    value={userSearchTerm}
                    onChange={(e) => setUserSearchTerm(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Username</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Role</TableHead>
                        <TableHead>Joined</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredUsers.length > 0 ? (
                        filteredUsers.map((user) => (
                          <TableRow key={user.id}>
                            <TableCell className="font-mono text-xs">{user.id}</TableCell>
                            <TableCell>
                              <div className="font-medium">{user.username}</div>
                            </TableCell>
                            <TableCell>{user.email}</TableCell>
                            <TableCell>
                              <Badge variant={user.is_admin ? "default" : "secondary"}>
                                {user.is_admin ? "Admin" : "User"}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {user.created_at ? (
                                new Date(user.created_at).toLocaleDateString("en-GB", {
                                  day: "2-digit",
                                  month: "short",
                                  year: "numeric",
                                })
                              ) : (
                                "N/A"
                              )}
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                            {users.length === 0 ? (
                              <div className="flex flex-col items-center gap-2">
                                <Users className="h-8 w-8 text-gray-400" />
                                <p>No users found</p>
                                <p className="text-sm">Users will appear here after registration</p>
                              </div>
                            ) : (
                              "No matching users found"
                            )}
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </TabsContent>
          </Tabs>
        </Card>
      </main>
    </div>
  );
};

export default Admin;