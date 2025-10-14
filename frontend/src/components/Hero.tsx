import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { MapPin, Calendar, DollarSign, LogOut, User as UserIcon } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import heroImage from "@/assets/hero-coffee.jpg";

interface HeroProps {
  onBookNow: () => void;
}

const Hero = ({ onBookNow }: HeroProps) => {
  const { user, logout } = useAuth();

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Auth Navigation */}
      <div className="absolute top-4 right-4 z-20 flex items-center gap-3">
        {user ? (
          <>
            <div className="flex items-center gap-2 bg-background/90 backdrop-blur-sm px-4 py-2 rounded-full shadow-lg">
              <UserIcon className="h-4 w-4" />
              {/* ✅ Changed user.name → user.username */}
              <span className="text-sm font-medium">{user.username}</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              className="bg-background/90 backdrop-blur-sm shadow-lg"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </>
        ) : (
          <Link to="/auth">
            <Button
              variant="outline"
              size="sm"
              className="bg-background/90 backdrop-blur-sm shadow-lg"
            >
              Login / Sign Up
            </Button>
          </Link>
        )}
      </div>

      {/* Hero Background */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: `url(${heroImage})` }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-primary/80 via-primary/60 to-secondary/80" />
      </div>

      {/* Hero Text Content */}
      <div className="relative z-10 container mx-auto px-4 text-center animate-fade-in">
        <h1 className="text-5xl md:text-7xl font-bold mb-6 text-primary-foreground">
          Mulima  Adventures 
        </h1>
        <p className="text-xl md:text-2xl mb-4 text-primary-foreground/95 max-w-3xl mx-auto">
          Experience the heart of Central Kenya through authentic agri-tourism and thrilling adventures
        </p>
        <p className="text-lg md:text-xl mb-8 text-primary-foreground/90 max-w-2xl mx-auto">
          From coffee plantations to mountain trails, discover real farm stories and cultural experiences
        </p>

        <div className="flex flex-wrap justify-center gap-6 mb-8 text-primary-foreground">
          <div className="flex items-center gap-2">
            <DollarSign className="w-5 h-5" />
            <span className="font-semibold">Ksh 7,500 - 42,000</span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            <span className="font-semibold">Day Trips & Overnight Stays</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            <span className="font-semibold">Close to Nairobi</span>
          </div>
        </div>

        {/* <Button
          variant="hero"
          size="lg"
          onClick={onBookNow}
          className="text-lg px-8 py-6"
        >
          Book Your Adventure Now
        </Button> */}
      </div>
    </section>
  );
};

export default Hero;
