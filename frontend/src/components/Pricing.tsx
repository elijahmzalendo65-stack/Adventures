import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Check } from "lucide-react";
import BookingModal from "@/components/BookingModal";
import { useAuth } from "@/contexts/AuthContext";

interface Package {
  id: number;
  name: string;
  price: number;
  description: string;
  features: string[];
  popular?: boolean;
}

interface BookingStatus {
  bookingId: number;
  adventureId: number;
  status: "pending" | "completed";
}

// Define a type for the booking response
interface ApiBooking {
  id?: number;
  booking_id?: number;
  bookingId?: number;
  adventure_id?: number;
  adventureId?: number;
  adventure?: { id?: number };
  status?: string;
  payment_status?: string;
}

const Pricing = () => {
  const [selectedAdventureId, setSelectedAdventureId] = useState<number | null>(null);
  const [selectedPrice, setSelectedPrice] = useState<number>(0);
  const [modalOpen, setModalOpen] = useState(false);
  const [bookingStatuses, setBookingStatuses] = useState<BookingStatus[]>([]);
  const [loadingBookings, setLoadingBookings] = useState(false);
  const [bookingError, setBookingError] = useState<string>("");

  // Get auth context
  const { user, fetchUserBookings } = useAuth();

  // List of packages
  const packages: Package[] = [
    {
      id: 101,
      name: "Budget Package",
      price: 7500,
      description: "Perfect for a quick escape from the city",
      features: [
        "Pick up from Nairobi",
        "Visit 3-4 destinations",
        "2 days one Night",
        "Guided tour",
        "Lunch included",
        "Transport included",
        "Group networking",
      ],
    },
    {
      id: 102,
      name: "Mid-Range Package",
      price: 14000,
      description: "Immerse yourself in culture and adventure",
      features: [
        "Pick up from Nairobi",
        "Visit 4-6 destinations",
        "3 days two Nights",
        "Extended guided tours",
        "All meals included",
        "Transport included",
        "Cultural experiences",
        "Farm activities",
      ],
      popular: true,
    },
    {
      id: 103,
      name: "Premium Package",
      price: 42000,
      description: "Complete immersion with overnight stay",
      features: [
        "Pick up from Nairobi",
        "Visit 6-8 destinations",
        "4 days three Nights",
        "All meals included",
        "Transport included",
        "Adventure activities",
        "Farm experiences",
        "Cultural interactions",
      ],
    },
  ];

  // Open booking modal
  const handleBookNow = (pkg: Package) => {
    setSelectedAdventureId(pkg.id);
    setSelectedPrice(pkg.price);
    setModalOpen(true);
  };

  // Update booking status after completion or payment
  const handleBookingCompleted = (
    status: "pending" | "completed",
    bookingId?: number
  ) => {
    if (!bookingId || !selectedAdventureId) return;

    setBookingStatuses((prev) => {
      const existing = prev.find((b) => b.bookingId === bookingId);
      if (existing) {
        return prev.map((b) =>
          b.bookingId === bookingId ? { ...b, status } : b
        );
      } else {
        return [...prev, { bookingId, adventureId: selectedAdventureId, status }];
      }
    });
    
    // Refresh bookings after new booking
    loadUserBookings();
  };

  // Fetch user bookings using AuthContext or direct API call
  const loadUserBookings = async () => {
    try {
      console.log("🔄 Loading user bookings...");
      
      if (!user) {
        console.log("👤 User not logged in, skipping booking fetch");
        setBookingStatuses([]);
        setBookingError("");
        return;
      }

      setLoadingBookings(true);
      setBookingError("");
      
      // Try using AuthContext first
      const response = await fetchUserBookings();
      console.log("📊 Received bookings response from AuthContext:", response);
      
      // Handle different response structures
      let bookingsData: any[] = [];
      
      if (Array.isArray(response)) {
        // Direct array response
        bookingsData = response;
        console.log("✅ Received direct array of bookings");
      } else if (response && typeof response === 'object') {
        // Object response - check for nested bookings
        if (Array.isArray((response as any).bookings)) {
          bookingsData = (response as any).bookings;
          console.log("✅ Received bookings in 'bookings' property");
        } else if (Array.isArray((response as any).data)) {
          bookingsData = (response as any).data;
          console.log("✅ Received bookings in 'data' property");
        } else {
          // If empty object or different structure, try direct API call
          console.log("⚠️ Unexpected response structure, trying direct API call");
          const directResponse = await fetchUserBookingsDirectly();
          if (directResponse) {
            bookingsData = directResponse;
          }
        }
      } else {
        // If response is null/undefined, try direct API call
        console.log("⚠️ Null/undefined response, trying direct API call");
        const directResponse = await fetchUserBookingsDirectly();
        if (directResponse) {
          bookingsData = directResponse;
        }
      }
      
      console.log("📋 Final bookings data:", bookingsData);

      // Safely map the bookings data
      const userBookings: BookingStatus[] = bookingsData
        .filter((booking: any) => booking != null) // Filter out null/undefined
        .map((booking: ApiBooking) => {
          // Extract adventure ID from different possible locations
          let adventureId = 0;
          if (booking.adventure_id) {
            adventureId = booking.adventure_id;
          } else if (booking.adventureId) {
            adventureId = booking.adventureId;
          } else if (booking.adventure?.id) {
            adventureId = booking.adventure.id;
          }
          
          // Extract booking ID
          let bookingId = 0;
          if (booking.id) {
            bookingId = booking.id;
          } else if (booking.booking_id) {
            bookingId = booking.booking_id;
          } else if (booking.bookingId) {
            bookingId = booking.bookingId;
          }
          
          // Determine status
          let status: "pending" | "completed" = "pending";
          if (booking.status === "completed" || booking.payment_status === "completed" || booking.status === "confirmed") {
            status = "completed";
          } else if (booking.status === "pending" || booking.payment_status === "pending") {
            status = "pending";
          }
          
          return {
            bookingId,
            adventureId,
            status
          };
        })
        .filter((booking: BookingStatus) => booking.bookingId > 0 && booking.adventureId > 0); // Filter valid bookings

      console.log("✅ Processed bookings:", userBookings);
      setBookingStatuses(userBookings);
      
      if (userBookings.length === 0) {
        console.log("ℹ️ No bookings found for user");
      }
    } catch (err: any) {
      console.error("❌ Failed to fetch user bookings:", err);
      
      // Handle specific error cases
      if (err.message?.includes("Unauthorized") || err.status === 401) {
        setBookingError("Please log in to view your bookings.");
      } else if (err.message?.includes("404") || err.message?.includes("Not Found")) {
        setBookingError("Bookings endpoint not found. Please check backend setup.");
      } else {
        setBookingError("Unable to load bookings. Please try again later.");
      }
    } finally {
      setLoadingBookings(false);
    }
  };

  // Direct API call as fallback if AuthContext fails
  const fetchUserBookingsDirectly = async (): Promise<any[]> => {
    try {
      console.log("🔄 Attempting direct API call for bookings...");
      const API_BASE_URL = "https://mlima-adventures.onrender.com";
      
      const response = await fetch(`${API_BASE_URL}/api/bookings`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Accept": "application/json"
        }
      });

      console.log("📡 Direct API response status:", response.status);

      if (!response.ok) {
        // Try alternative endpoints
        const altResponse = await fetch(`${API_BASE_URL}/api/user/bookings`, {
          method: "GET",
          credentials: "include",
          headers: {
            "Accept": "application/json"
          }
        });

        if (altResponse.ok) {
          const data = await altResponse.json();
          return Array.isArray(data) ? data : data.bookings || data.data || [];
        }

        throw new Error(`Failed to fetch bookings: ${response.status}`);
      }

      const data = await response.json();
      return Array.isArray(data) ? data : data.bookings || data.data || [];
    } catch (error) {
      console.error("❌ Direct API call failed:", error);
      return [];
    }
  };

  useEffect(() => {
    loadUserBookings();

    // Only poll if user is logged in
    const interval = user ? setInterval(loadUserBookings, 60000) : null; // Reduced to 60 seconds
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [user]); // Re-run when user changes

  // Get latest booking status for a given adventure
  const getBookingStatus = (adventureId: number) => {
    const bookings = bookingStatuses
      .filter((b) => b.adventureId === adventureId)
      .sort((a, b) => b.bookingId - a.bookingId); // latest booking first
    return bookings.length > 0 ? bookings[0].status : null;
  };

  // Handle login prompt
  const handleBookNowWithCheck = (pkg: Package) => {
    if (!user) {
      alert("Please login to book an adventure!");
      return;
    }
    handleBookNow(pkg);
  };

  return (
    <>
      <section className="py-20 px-4 bg-gradient-to-b from-background to-muted/20">
        <div className="container mx-auto">
          <div className="text-center mb-16 animate-fade-in">
            <h2 className="text-4xl md:text-5xl font-bold mb-4 text-primary">
              Affordable Packages
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Choose the perfect adventure that fits your schedule and budget.
            </p>
            
            {!user && (
              <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg max-w-md mx-auto">
                <p className="text-yellow-800">
                  <span className="font-semibold">Note:</span> Please login to book adventures and view your bookings.
                </p>
              </div>
            )}
          </div>

          {bookingError && (
            <div className="text-center mb-8">
              <div className="inline-block p-4 bg-red-50 border border-red-200 rounded-lg max-w-md mx-auto">
                <p className="text-red-700">{bookingError}</p>
                <p className="text-sm text-red-600 mt-1">
                  You can still proceed with new bookings.
                </p>
              </div>
            </div>
          )}

          {loadingBookings ? (
            <div className="text-center mb-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="text-muted-foreground mt-2">Loading your bookings...</p>
            </div>
          ) : !user ? (
            <div className="text-center mb-8 p-4 bg-blue-50 border border-blue-200 rounded-lg max-w-md mx-auto">
              <p className="text-blue-800">
                Login to see your booking status and make new bookings.
              </p>
            </div>
          ) : bookingStatuses.length > 0 ? (
            <div className="text-center mb-8 p-4 bg-green-50 border border-green-200 rounded-lg max-w-md mx-auto">
              <p className="text-green-700">
                Found {bookingStatuses.length} booking{bookingStatuses.length !== 1 ? 's' : ''}
              </p>
            </div>
          ) : null}

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {packages.map((pkg, index) => {
              const status = getBookingStatus(pkg.id);

              return (
                <Card
                  key={pkg.id}
                  className={`relative flex flex-col border-none rounded-2xl shadow-md hover:shadow-lg transition-transform hover:-translate-y-1 ${
                    pkg.popular ? "border-2 border-accent" : ""
                  }`}
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  {pkg.popular && (
                    <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                      <span className="bg-accent text-accent-foreground px-4 py-1 rounded-full text-sm font-semibold">
                        Most Popular
                      </span>
                    </div>
                  )}

                  <CardHeader className="text-center">
                    <CardTitle className="text-2xl">{pkg.name}</CardTitle>
                    <CardDescription>{pkg.description}</CardDescription>
                    <div className="mt-4">
                      <span className="text-4xl font-bold text-primary">
                        Ksh {pkg.price.toLocaleString()}
                      </span>
                      <span className="text-muted-foreground"> / person</span>
                    </div>
                  </CardHeader>

                  <CardContent className="flex-grow">
                    <ul className="space-y-3">
                      {pkg.features.map((feature, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <Check className="w-5 h-5 text-secondary shrink-0 mt-0.5" />
                          <span className="text-sm">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>

                  <CardFooter className="flex flex-col gap-2">
                    {status ? (
                      <div className="text-center">
                        <span
                          className={`font-semibold text-center transition-colors duration-500 block ${
                            status === "completed" ? "text-green-600" : "text-yellow-600"
                          }`}
                        >
                          {status === "completed"
                            ? "Booking Confirmed ✅"
                            : "Pending Payment ⏳"}
                        </span>
                        {status === "pending" && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Complete payment to confirm
                          </p>
                        )}
                      </div>
                    ) : (
                      <Button
                        className="w-full"
                        variant={pkg.popular ? "hero" : "default"}
                        onClick={() => handleBookNowWithCheck(pkg)}
                        disabled={!user}
                      >
                        {!user ? "Login to Book" : "Book Now"}
                      </Button>
                    )}
                    
                    {!user && (
                      <p className="text-xs text-muted-foreground text-center mt-1">
                        Login required to book
                      </p>
                    )}
                  </CardFooter>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {selectedAdventureId && (
        <BookingModal
          open={modalOpen}
          onOpenChange={setModalOpen}
          adventureId={selectedAdventureId}
          adventurePrice={selectedPrice}
          onBookingCompleted={handleBookingCompleted}
        />
      )}
    </>
  );
};

export default Pricing;