import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Users, Calendar, DollarSign, Search, LogOut } from "lucide-react";
import axios from "axios";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/contexts/AuthContext"; // Import AuthContext

interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

interface Booking {
  id: number;
  user: User;
  adventure: { title: string };
  adventure_date: string;
  number_of_people: number;
  total_amount: number;
  status: string;
}

interface DashboardStats {
  total_users: number;
  total_bookings: number;
  total_revenue: number;
}

const Admin = () => {
  const navigate = useNavigate();
  const { user, logout, fetchAdminStats, fetchAdminUsers, fetchAdminBookings } = useAuth(); // Use AuthContext

  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [userSearchTerm, setUserSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  // Check if user is admin
  useEffect(() => {
    if (!user?.is_admin) {
      console.log("❌ User is not admin, redirecting...");
      navigate("/");
    }
  }, [user, navigate]);

  // ----------------------
  // Fetch Dashboard Stats using AuthContext
  // ----------------------
  const fetchDashboard = async () => {
    try {
      console.log("📊 Fetching admin stats...");
      const stats = await fetchAdminStats();
      if (stats) {
        setDashboardStats(stats.dashboard);
        console.log("✅ Dashboard stats loaded:", stats.dashboard);
      }
    } catch (err) {
      console.error("Failed to fetch dashboard stats", err);
      setError("Failed to load dashboard statistics");
    }
  };

  // ----------------------
  // Fetch Users using AuthContext
  // ----------------------
  const fetchUsers = async () => {
    try {
      console.log("👥 Fetching admin users...");
      const adminUsers = await fetchAdminUsers();
      setUsers(adminUsers);
      console.log("✅ Users loaded:", adminUsers.length);
    } catch (err) {
      console.error("Failed to fetch users", err);
      setError("Failed to load users");
    }
  };

  // ----------------------
  // Fetch Bookings using AuthContext
  // ----------------------
  const fetchBookings = async () => {
    try {
      console.log("📋 Fetching admin bookings...");
      const adminBookings = await fetchAdminBookings();
      setBookings(adminBookings);
      console.log("✅ Bookings loaded:", adminBookings.length);
    } catch (err) {
      console.error("Failed to fetch bookings", err);
      setError("Failed to load bookings");
    }
  };

  // ----------------------
  // Fetch all data on load
  // ----------------------
  useEffect(() => {
    const loadData = async () => {
      if (!user?.is_admin) return;
      
      setLoading(true);
      setError("");
      
      try {
        await Promise.all([
          fetchDashboard(),
          fetchUsers(),
          fetchBookings()
        ]);
      } catch (err) {
        console.error("Error loading admin data:", err);
        setError("Failed to load admin data. Please try again.");
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [user]); // Run when user changes

  // ----------------------
  // Logout using AuthContext
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
  // Filtered Data
  // ----------------------
  const filteredBookings = bookings.filter(
    (booking) =>
      booking.user?.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.adventure?.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.id.toString().includes(searchTerm)
  );

  const filteredUsers = users.filter(
    (user) =>
      user.username.toLowerCase().includes(userSearchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(userSearchTerm.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case "confirmed":
        return "bg-green-500/10 text-green-700 dark:text-green-400";
      case "pending":
        return "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400";
      case "completed":
        return "bg-blue-500/10 text-blue-700 dark:text-blue-400";
      case "cancelled":
        return "bg-red-500/10 text-red-700 dark:text-red-400";
      default:
        return "bg-gray-500/10 text-gray-700 dark:text-gray-400";
    }
  };

  if (!user?.is_admin) {
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
                Welcome, {user?.username} 
                {user?.is_admin && <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-1 rounded">Admin</span>}
              </p>
            </div>
          </div>
          <Button variant="outline" onClick={handleLogout}>
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => window.location.reload()}
              className="mt-2"
            >
              Retry
            </Button>
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
              <div className="text-2xl font-bold">{dashboardStats?.total_users ?? 0}</div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Bookings</CardTitle>
              <Calendar className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardStats?.total_bookings ?? 0}</div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Revenue (KSh)</CardTitle>
              <DollarSign className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {dashboardStats?.total_revenue?.toLocaleString() ?? 0}
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Active Bookings</CardTitle>
              <Calendar className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {bookings.filter(b => b.status === 'confirmed' || b.status === 'pending').length}
              </div>
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
                        <TableHead>Booking ID</TableHead>
                        <TableHead>Customer</TableHead>
                        <TableHead>Adventure</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Guests</TableHead>
                        <TableHead>Amount (KSh)</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredBookings.length > 0 ? (
                        filteredBookings.map((booking) => (
                          <TableRow key={booking.id}>
                            <TableCell className="font-medium">{booking.id}</TableCell>
                            <TableCell>{booking.user?.username || "Unknown"}</TableCell>
                            <TableCell>{booking.adventure?.title || "Unknown Adventure"}</TableCell>
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
                            <TableCell>{(booking.total_amount || 0).toLocaleString()}</TableCell>
                            <TableCell>
                              <Badge variant="secondary" className={getStatusColor(booking.status)}>
                                {booking.status || "pending"}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={7} className="text-center text-muted-foreground">
                            {bookings.length === 0 ? "No bookings yet" : "No matching bookings found"}
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
                        <TableHead>User ID</TableHead>
                        <TableHead>Username</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Joined Date</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredUsers.length > 0 ? (
                        filteredUsers.map((user) => (
                          <TableRow key={user.id}>
                            <TableCell className="font-medium">{user.id}</TableCell>
                            <TableCell>{user.username}</TableCell>
                            <TableCell>{user.email}</TableCell>
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
                          <TableCell colSpan={4} className="text-center text-muted-foreground">
                            {users.length === 0 ? "No users yet" : "No matching users found"}
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