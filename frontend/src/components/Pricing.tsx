import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Check } from "lucide-react";

interface PricingProps {
  onBookNow: () => void;
}

const Pricing = ({ onBookNow }: PricingProps) => {
  const packages = [
    {
      name: "Day Trip Adventure",
      price: "3,500",
      description: "Perfect for a quick escape from the city",
      features: [
        "Pick up from Nairobi",
        "Visit 1-2 destinations",
        "Guided tour",
        "Lunch included",
        "Transport included",
        "Group networking",
      ],
    },
    {
      name: "Weekend Explorer",
      price: "5,000",
      description: "Immerse yourself in culture and adventure",
      features: [
        "Pick up from Nairobi",
        "Visit 3-4 destinations",
        "Extended guided tours",
        "All meals included",
        "Transport included",
        "Cultural experiences",
        "Farm activities",
      ],
      popular: true,
    },
    {
      name: "Overnight Experience",
      price: "7,000",
      description: "Complete immersion with overnight stay",
      features: [
        "Pick up from Nairobi",
        "Visit 4-5 destinations",
        "Overnight accommodation",
        "All meals included",
        "Transport included",
        "Adventure activities",
        "Farm experiences",
        "Cultural interactions",
      ],
    },
  ];

  return (
    <section className="py-20 px-4">
      <div className="container mx-auto">
        <div className="text-center mb-16 animate-fade-in">
          <h2 className="text-4xl md:text-5xl font-bold mb-4 text-primary">
            Affordable Packages
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Choose the perfect adventure that fits your schedule and budget
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {packages.map((pkg, index) => (
            <Card 
              key={index}
              className={`relative flex flex-col animate-slide-up border-none ${
                pkg.popular ? "border-2 border-accent shadow-xl" : ""
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
                  <span className="text-4xl font-bold text-primary">Ksh {pkg.price}</span>
                  <span className="text-muted-foreground">/person</span>
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
              <CardFooter>
                <Button 
                  className="w-full" 
                  variant={pkg.popular ? "hero" : "default"}
                  onClick={onBookNow}
                >
                  Book Now
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Pricing;
