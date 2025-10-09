import { Coffee, Mountain, Users, DollarSign } from "lucide-react";
import { Card } from "@/components/ui/card";

const About = () => {
  const features = [
    {
      icon: Coffee,
      title: "Authentic Agri-Tourism",
      description: "Visit real coffee and tea farms, experience the harvest, and learn the stories behind your cup",
    },
    {
      icon: Mountain,
      title: "Thrilling Adventures",
      description: "Rafting, hiking, waterfalls, and nature trails through the stunning Central Kenya landscape",
    },
    {
      icon: Users,
      title: "Cultural Connections",
      description: "Connect with local communities, share real farm stories, and enjoy networking vibes",
    },
    {
      icon: DollarSign,
      title: "Affordable Experiences",
      description: "Day trips and overnight stays from Ksh 3,500 to 7,000 with low transport costs from Nairobi",
    },
  ];

  return (
    <section className="py-20 px-4">
      <div className="container mx-auto">
        <div className="text-center mb-16 animate-fade-in">
          <h2 className="text-4xl md:text-5xl font-bold mb-4 text-primary">
            Why Choose Us?
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Experience Central Kenya like never before with authentic tours, affordable prices, and unforgettable memories
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <Card 
              key={index}
              className="p-6 hover:shadow-lg transition-all duration-300 animate-slide-up border-none bg-card"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <feature.icon className="w-12 h-12 mb-4 text-secondary" />
              <h3 className="text-xl font-semibold mb-2 text-card-foreground">
                {feature.title}
              </h3>
              <p className="text-muted-foreground">
                {feature.description}
              </p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default About;
