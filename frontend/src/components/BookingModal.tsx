import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CalendarIcon, Smartphone } from "lucide-react";
import { format } from "date-fns";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import axios from "axios";

interface BookingModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  adventureId: number;
  adventurePrice: number;
  onBookingCompleted?: (status: "pending" | "completed", bookingId?: number) => void;
}

const BookingModal = ({
  open,
  onOpenChange,
  adventureId,
  adventurePrice,
  onBookingCompleted,
}: BookingModalProps) => {
  const [step, setStep] = useState(1);
  const [date, setDate] = useState<Date>();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    guests: "1",
  });
  const [mpesaPhone, setMpesaPhone] = useState("");
  const [processing, setProcessing] = useState(false);
  const [bookingId, setBookingId] = useState<number | null>(null);

  const totalPrice = adventurePrice * parseInt(formData.guests);

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // -----------------------------
  // Step 1: Create Booking
  // -----------------------------
  const handleBookingSubmit = async () => {
    if (!formData.name || !formData.email || !formData.phone || !date) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields",
        variant: "destructive",
      });
      return;
    }

    try {
      const res = await axios.post(
        "http://localhost:5000/api/bookings/",
        {
          adventure_id: adventureId,
          adventure_date: date.toISOString(),
          number_of_people: parseInt(formData.guests),
          special_requests: "",
        },
        { withCredentials: true }
      );

      const createdBooking = res.data.booking;
      setBookingId(createdBooking.id);

      toast({
        title: "Booking Created!",
        description: "Your booking has been created. Proceed to payment.",
      });

      onBookingCompleted && onBookingCompleted("pending", createdBooking.id);

      setStep(2); // Move to payment
    } catch (err: any) {
      console.error(err);
      toast({
        title: "Booking Failed",
        description: err?.response?.data?.message || "Something went wrong.",
        variant: "destructive",
      });
    }
  };

  // -----------------------------
  // Step 2: Initiate M-Pesa Payment
  // -----------------------------
  const handleMpesaPayment = async () => {
    if (!mpesaPhone || mpesaPhone.length < 10) {
      toast({
        title: "Invalid Phone Number",
        description: "Please enter a valid M-Pesa phone number",
        variant: "destructive",
      });
      return;
    }

    if (!bookingId) {
      toast({
        title: "Booking Not Found",
        description: "Cannot initiate payment without a booking",
        variant: "destructive",
      });
      return;
    }

    setProcessing(true);

    try {
      await axios.post(
        "http://localhost:5000/api/bookings/initiate-payment",
        {
          booking_id: bookingId,
          phone_number: mpesaPhone,
        },
        { withCredentials: true }
      );

      toast({
        title: "Payment Initiated",
        description:
          "Check your phone for the M-Pesa prompt to complete payment",
      });

      // Simulate payment confirmation (replace with real webhook)
      setTimeout(() => {
        toast({
          title: "Booking Confirmed!",
          description: "Payment completed successfully.",
        });

        onBookingCompleted && onBookingCompleted("completed", bookingId);

        // Reset modal state
        onOpenChange(false);
        setStep(1);
        setFormData({ name: "", email: "", phone: "", guests: "1" });
        setMpesaPhone("");
        setDate(undefined);
        setBookingId(null);
      }, 3000);
    } catch (err: any) {
      console.error(err);
      toast({
        title: "Payment Failed",
        description: err?.response?.data?.message || "Payment could not be completed.",
        variant: "destructive",
      });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">
            {step === 1 ? "Book Your Adventure" : "Complete Payment"}
          </DialogTitle>
          <DialogDescription>
            {step === 1
              ? "Fill in your details to reserve your spot"
              : "Pay securely with M-Pesa"}
          </DialogDescription>
        </DialogHeader>

        {step === 1 ? (
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name *</Label>
              <Input
                id="name"
                placeholder="John Doe"
                value={formData.name}
                onChange={(e) => handleInputChange("name", e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email *</Label>
              <Input
                id="email"
                type="email"
                placeholder="john@example.com"
                value={formData.email}
                onChange={(e) => handleInputChange("email", e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number *</Label>
              <Input
                id="phone"
                placeholder="0712345678"
                value={formData.phone}
                onChange={(e) => handleInputChange("phone", e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="guests">Number of Guests *</Label>
              <Select
                value={formData.guests}
                onValueChange={(value) => handleInputChange("guests", value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[1, 2, 3, 4, 5, 6, 7, 8].map((num) => (
                    <SelectItem key={num} value={num.toString()}>
                      {num} {num === 1 ? "Guest" : "Guests"}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Select Date *</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !date && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {date ? format(date, "PPP") : "Pick a date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={date}
                    onSelect={setDate}
                    initialFocus
                    disabled={(date) => date < new Date()}
                  />
                </PopoverContent>
              </Popover>
            </div>

            <div className="pt-4 border-t">
              <div className="flex justify-between items-center text-lg font-semibold">
                <span>Total Amount:</span>
                <span className="text-primary">Ksh {totalPrice.toLocaleString()}</span>
              </div>
            </div>

            <Button className="w-full" onClick={handleBookingSubmit}>
              Proceed to Payment
            </Button>
          </div>
        ) : (
          <div className="space-y-6 py-4">
            <div className="bg-muted p-4 rounded-lg space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Guests:</span>
                <span className="font-semibold">{formData.guests}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Date:</span>
                <span className="font-semibold">{date ? format(date, "PP") : ""}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total:</span>
                <span className="font-semibold">Ksh {totalPrice.toLocaleString()}</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label>M-Pesa Phone Number</Label>
              <div className="relative">
                <Input
                  placeholder="2547XXXXXXXX"
                  value={mpesaPhone}
                  onChange={(e) => setMpesaPhone(e.target.value)}
                  className="pl-10"
                />
                <Smartphone className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              </div>
            </div>

            <Button
              className="w-full"
              onClick={handleMpesaPayment}
              disabled={processing}
            >
              {processing ? "Processing..." : "Pay with M-Pesa"}
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default BookingModal;
