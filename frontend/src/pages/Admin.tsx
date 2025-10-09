import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Users, Calendar, DollarSign, TrendingUp, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/contexts/AuthContext";

const Admin = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [userSearchTerm, setUserSearchTerm] = useState("");
  const { users } = useAuth();

  // Mock data - replace with real data from backend
  const stats = [
    { title: "Total Bookings", value: "127", icon: Calendar, change: "+12%" },
    { title: "Revenue (KSh)", value: "643,500", icon: DollarSign, change: "+8%" },
    { title: "Active Users", value: "89", icon: Users, change: "+23%" },
    { title: "Growth Rate", value: "15.3%", icon: TrendingUp, change: "+5%" },
  ];

  const bookings = [
    { id: "BK001", customer: "John Kamau", destination: "Gichugu Coffee Estate", date: "2025-10-05", guests: 2, amount: 7000, status: "confirmed" },
    { id: "BK002", customer: "Mary Wanjiru", destination: "Mt. Kenya Nature Trails", date: "2025-10-08", guests: 4, amount: 14000, status: "pending" },
    { id: "BK003", customer: "Peter Ochieng", destination: "White Water Rafting", date: "2025-10-10", guests: 3, amount: 10500, status: "confirmed" },
    { id: "BK004", customer: "Grace Akinyi", destination: "Nyanyo Tea Zone", date: "2025-10-12", guests: 2, amount: 7000, status: "completed" },
    { id: "BK005", customer: "David Mwangi", destination: "Castle Lounge", date: "2025-10-15", guests: 5, amount: 17500, status: "confirmed" },
  ];

  const filteredBookings = bookings.filter(
    (booking) =>
      booking.customer.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.destination.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredUsers = users.filter(
    (user) =>
      user.name.toLowerCase().includes(userSearchTerm.toLowerCase()) ||
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
      default:
        return "bg-gray-500/10 text-gray-700 dark:text-gray-400";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to Site
                </Button>
              </Link>
              <h1 className="text-2xl font-bold text-primary">Admin Dashboard</h1>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat) => (
            <Card key={stat.title} className="hover:shadow-lg transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                  {stat.change} from last month
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Data Tables with Tabs */}
        <Card>
          <Tabs defaultValue="bookings" className="w-full">
            <CardHeader>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="bookings">Bookings</TabsTrigger>
                <TabsTrigger value="users">Registered Users</TabsTrigger>
              </TabsList>
            </CardHeader>

            <TabsContent value="bookings">
              <CardHeader>
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div>
                    <CardTitle>Recent Bookings</CardTitle>
                    <CardDescription>Manage and track all tour bookings</CardDescription>
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
                </div>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Booking ID</TableHead>
                        <TableHead>Customer</TableHead>
                        <TableHead>Destination</TableHead>
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
                            <TableCell>{booking.customer}</TableCell>
                            <TableCell>{booking.destination}</TableCell>
                            <TableCell>{booking.date}</TableCell>
                            <TableCell>{booking.guests}</TableCell>
                            <TableCell>{booking.amount.toLocaleString()}</TableCell>
                            <TableCell>
                              <Badge variant="secondary" className={getStatusColor(booking.status)}>
                                {booking.status}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={7} className="text-center text-muted-foreground">
                            No bookings found
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </TabsContent>

            <TabsContent value="users">
              <CardHeader>
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
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
                </div>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>User ID</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Joined Date</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredUsers.length > 0 ? (
                        filteredUsers.map((user) => (
                          <TableRow key={user.id}>
                            <TableCell className="font-medium">{user.id}</TableCell>
                            <TableCell>{user.name}</TableCell>
                            <TableCell>{user.email}</TableCell>
                            <TableCell>
                              {new Date(user.createdAt).toLocaleDateString("en-GB", {
                                day: "2-digit",
                                month: "short",
                                year: "numeric",
                              })}
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={4} className="text-center text-muted-foreground">
                            No users found
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
