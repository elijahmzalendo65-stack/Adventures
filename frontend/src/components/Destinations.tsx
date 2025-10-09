import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import teaImage from "@/assets/tea-plantation.jpg";
import hikingImage from "@/assets/hiking-trail.jpg";
import raftingImage from "@/assets/rafting.jpg";

const Destinations = () => {
  const destinations = [
    {
      name: "Gichugu Coffee Estate",
      description: "Experience authentic coffee farming, from bean to cup. Walk through lush plantations and learn traditional processing methods.",
      type: "Coffee Farm",
      image: teaImage,
    },
    {
      name: "Nyanyo Tea Zone",
      description: "Discover the art of tea cultivation in scenic rolling hills. Enjoy fresh tea tastings and beautiful views.",
      type: "Tea Plantation",
      image: teaImage,
    },
    {
      name: "Mt. Kenya Nature Trails",
      description: "Trek through pristine mountain forests with breathtaking views. Perfect for nature lovers and adventure seekers.",
      type: "Hiking",
      image: hikingImage,
    },
    {
      name: "Mwea Rice Paddies",
      description: "Explore vast rice fields and learn about rice farming. A unique cultural and agricultural experience.",
      type: "Agri-Tourism",
      image: teaImage,
    },
    {
      name: "OutDoor Man Cabins",
      description: "Cozy overnight accommodations surrounded by nature. Perfect base for your adventure explorations.",
      type: "Accommodation",
      image: hikingImage,
    },
    {
      name: "White Water Rafting",
      description: "Experience adrenaline-pumping rapids in pristine Kenyan rivers. Professional guides ensure a safe and thrilling adventure.",
      type: "Adventure",
      image: raftingImage,
    },
    {
      name: "Castle Lounge",
      description: "Relax and network in a unique setting. Great food, drinks, and social atmosphere after your adventures.",
      type: "Social Hub",
      image: hikingImage,
    },
    {
      name: "Njine Kabai",
      description: "Immerse yourself in local culture and traditions. Authentic village experiences and community connections.",
      type: "Cultural",
      image: teaImage,
    },
  ];

  return (
    <section className="py-20 px-4 bg-muted/30">
      <div className="container mx-auto">
        <div className="text-center mb-16 animate-fade-in">
          <h2 className="text-4xl md:text-5xl font-bold mb-4 text-primary">
            Featured Destinations
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Explore the best of Central Kenya with our carefully curated locations
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {destinations.map((destination, index) => (
            <Card 
              key={index}
              className="overflow-hidden hover:shadow-xl transition-all duration-300 animate-slide-up border-none"
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <div className="relative h-48 overflow-hidden">
                <img 
                  src={destination.image} 
                  alt={destination.name}
                  className="w-full h-full object-cover transition-transform duration-300 hover:scale-110"
                />
                <Badge className="absolute top-4 right-4 bg-secondary text-secondary-foreground">
                  {destination.type}
                </Badge>
              </div>
              <CardHeader>
                <CardTitle className="text-lg">{destination.name}</CardTitle>
                <CardDescription className="text-sm">
                  {destination.description}
                </CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Destinations;
