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
import axios from "axios";

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

const Pricing = () => {
  const [selectedAdventureId, setSelectedAdventureId] = useState<number | null>(null);
  const [selectedPrice, setSelectedPrice] = useState<number>(0);
  const [modalOpen, setModalOpen] = useState(false);
  const [bookingStatuses, setBookingStatuses] = useState<BookingStatus[]>([]);

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
  };

  // Fetch user bookings with token
  const fetchUserBookings = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        console.warn("No auth token found. User might not be logged in.");
        return;
      }

      const res = await axios.get("https://mlima-adventures.onrender.com", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const userBookings: BookingStatus[] = res.data.bookings.map((b: any) => ({
        bookingId: b.id,
        adventureId: b.adventure_id,
        status: b.status,
      }));

      setBookingStatuses(userBookings);
    } catch (err: any) {
      if (err.response?.status === 401) {
        console.error("Unauthorized: Please log in to view bookings.");
      } else {
        console.error("Failed to fetch user bookings", err);
      }
    }
  };

  useEffect(() => {
    fetchUserBookings();

    // Poll every 5 seconds to reflect real-time payment status
    const interval = setInterval(fetchUserBookings, 5000);
    return () => clearInterval(interval);
  }, []);

  // Get latest booking status for a given adventure
  const getBookingStatus = (adventureId: number) => {
    const bookings = bookingStatuses
      .filter((b) => b.adventureId === adventureId)
      .sort((a, b) => b.bookingId - a.bookingId); // latest booking first
    return bookings.length > 0 ? bookings[0].status : null;
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
          </div>

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
                      <span
                        className={`font-semibold text-center transition-colors duration-500 ${
                          status === "completed" ? "text-green-600" : "text-yellow-600"
                        }`}
                      >
                        {status === "completed"
                          ? "Booking Confirmed ✅"
                          : "Pending Payment ⏳"}
                      </span>
                    ) : (
                      <Button
                        className="w-full"
                        variant={pkg.popular ? "hero" : "default"}
                        onClick={() => handleBookNow(pkg)}
                      >
                        Book Now
                      </Button>
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
