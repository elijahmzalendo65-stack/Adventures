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
  const [step, setStep] = useState<1 | 2>(1);
  const [date, setDate] = useState<Date | undefined>();
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

  const handleInputChange = (field: keyof typeof formData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Get auth headers from localStorage
  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return token ? { Authorization: `Bearer ${token}` } : {};
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

    setProcessing(true);

    try {
      // Convert date to ISO string with UTC timezone to avoid naive datetime errors
      const adventureDateISO = new Date(date).toISOString();

      const res = await axios.post(
        "http://localhost:5000/api/bookings/",
        {
          adventure_id: adventureId,
          adventure_date: adventureDateISO,
          number_of_people: parseInt(formData.guests),
          customer_name: formData.name,
          customer_email: formData.email,
          customer_phone: formData.phone,
          special_requests: "",
        },
        { withCredentials: true, headers: getAuthHeaders() }
      );

      const createdBooking = res.data.booking;
      setBookingId(createdBooking.id);

      toast({
        title: "Booking Created!",
        description: "Your booking has been created. Proceed to payment.",
      });

      onBookingCompleted?.("pending", createdBooking.id);
      setStep(2);
    } catch (err: any) {
      console.error("Booking creation error:", err);
      const msg =
        err?.response?.status === 401
          ? "Unauthorized. Please log in again."
          : err?.response?.data?.message || "Failed to create booking. Please try again.";
      toast({
        title: "Booking Failed",
        description: msg,
        variant: "destructive",
      });
    } finally {
      setProcessing(false);
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
        { booking_id: bookingId, phone_number: mpesaPhone },
        { withCredentials: true, headers: getAuthHeaders() }
      );

      toast({
        title: "Payment Initiated",
        description: "Check your phone for the M-Pesa prompt to complete payment.",
      });

      // Mock confirmation after 3 seconds
      setTimeout(() => {
        toast({
          title: "Booking Confirmed!",
          description: "Payment completed successfully.",
        });
        onBookingCompleted?.("completed", bookingId);
        resetModal();
      }, 3000);
    } catch (err: any) {
      console.error("Payment initiation error:", err);
      const msg =
        err?.response?.status === 401
          ? "Unauthorized. Please log in again."
          : err?.response?.data?.message || "Payment could not be completed. Please try again.";
      toast({
        title: "Payment Failed",
        description: msg,
        variant: "destructive",
      });
    } finally {
      setProcessing(false);
    }
  };

  const resetModal = () => {
    onOpenChange(false);
    setStep(1);
    setFormData({ name: "", email: "", phone: "", guests: "1" });
    setMpesaPhone("");
    setDate(undefined);
    setBookingId(null);
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
                    disabled={(d) => d < new Date()}
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
            <Button
              className="w-full"
              onClick={handleBookingSubmit}
              disabled={processing}
            >
              {processing ? "Processing..." : "Proceed to Payment"}
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
              <Label>M-Pesa Phone Number *</Label>
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
              disabled={processing || !bookingId}
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
