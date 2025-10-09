import { useState } from "react";
import Hero from "@/components/Hero";
import About from "@/components/About";
import Destinations from "@/components/Destinations";
import Pricing from "@/components/Pricing";
import BookingModal from "@/components/BookingModal";
import Footer from "@/components/Footer";

const Index = () => {
  const [bookingOpen, setBookingOpen] = useState(false);

  const handleBookNow = () => {
    setBookingOpen(true);
  };

  return (
    <div className="min-h-screen">
      <Hero onBookNow={handleBookNow} />
      <About />
      <Destinations />
      <Pricing onBookNow={handleBookNow} />
      <Footer />
      <BookingModal open={bookingOpen} onOpenChange={setBookingOpen} />
    </div>
  );
};

export default Index;
