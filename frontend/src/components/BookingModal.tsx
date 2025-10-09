import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CalendarIcon, Smartphone } from "lucide-react";
import { format } from "date-fns";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

interface BookingModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const BookingModal = ({ open, onOpenChange }: BookingModalProps) => {
  const [step, setStep] = useState(1);
  const [date, setDate] = useState<Date>();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    package: "",
    guests: "1",
  });
  const [mpesaPhone, setMpesaPhone] = useState("");
  const [processing, setProcessing] = useState(false);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleBookingSubmit = () => {
    if (!formData.name || !formData.email || !formData.phone || !formData.package || !date) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields",
        variant: "destructive",
      });
      return;
    }
    setStep(2);
  };

  const handleMpesaPayment = () => {
    if (!mpesaPhone || mpesaPhone.length < 10) {
      toast({
        title: "Invalid Phone Number",
        description: "Please enter a valid M-Pesa phone number",
        variant: "destructive",
      });
      return;
    }

    setProcessing(true);
    
    // Simulate M-Pesa payment processing
    setTimeout(() => {
      setProcessing(false);
      toast({
        title: "Payment Initiated!",
        description: "Please check your phone for the M-Pesa prompt to complete payment",
      });
      
      // Simulate payment confirmation
      setTimeout(() => {
        toast({
          title: "Booking Confirmed!",
          description: "We'll send you a confirmation email shortly. See you on your adventure!",
        });
        onOpenChange(false);
        setStep(1);
        setFormData({
          name: "",
          email: "",
          phone: "",
          package: "",
          guests: "1",
        });
        setMpesaPhone("");
        setDate(undefined);
      }, 3000);
    }, 2000);
  };

  const packagePrices: { [key: string]: number } = {
    "day-trip": 3500,
    "weekend": 5000,
    "overnight": 7000,
  };

  const totalPrice = formData.package && formData.guests 
    ? packagePrices[formData.package] * parseInt(formData.guests)
    : 0;

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
              <Label htmlFor="package">Select Package *</Label>
              <Select value={formData.package} onValueChange={(value) => handleInputChange("package", value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose your adventure" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="day-trip">Day Trip Adventure - Ksh 3,500</SelectItem>
                  <SelectItem value="weekend">Weekend Explorer - Ksh 5,000</SelectItem>
                  <SelectItem value="overnight">Overnight Experience - Ksh 7,000</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="guests">Number of Guests *</Label>
              <Select value={formData.guests} onValueChange={(value) => handleInputChange("guests", value)}>
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

            {totalPrice > 0 && (
              <div className="pt-4 border-t">
                <div className="flex justify-between items-center text-lg font-semibold">
                  <span>Total Amount:</span>
                  <span className="text-primary">Ksh {totalPrice.toLocaleString()}</span>
                </div>
              </div>
            )}

            <Button className="w-full" onClick={handleBookingSubmit}>
              Proceed to Payment
            </Button>
          </div>
        ) : (
          <div className="space-y-6 py-4">
            <div className="bg-muted p-4 rounded-lg space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Package:</span>
                <span className="font-semibold">{formData.package.replace("-", " ").toUpperCase()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Guests:</span>
                <span className="font-semibold">{formData.guests}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Date:</span>
                <span className="font-semibold">{date ? format(date, "PP") : ""}</span>
              </div>
              <div className="flex justify-between text-lg pt-2 border-t">
                <span className="font-semibold">Total:</span>
                <span className="font-bold text-primary">Ksh {totalPrice.toLocaleString()}</span>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-center gap-2 text-secondary">
                <Smartphone className="w-6 h-6" />
                <span className="font-semibold text-lg">Pay with M-Pesa</span>
              </div>

              <div className="space-y-2">
                <Label htmlFor="mpesa-phone">M-Pesa Phone Number *</Label>
                <Input
                  id="mpesa-phone"
                  placeholder="0712345678"
                  value={mpesaPhone}
                  onChange={(e) => setMpesaPhone(e.target.value)}
                  maxLength={10}
                />
                <p className="text-xs text-muted-foreground">
                  Enter the phone number registered with M-Pesa
                </p>
              </div>

              <div className="bg-secondary/10 p-4 rounded-lg text-sm space-y-2">
                <p className="font-semibold text-secondary">Payment Instructions:</p>
                <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                  <li>Enter your M-Pesa registered phone number</li>
                  <li>Click "Pay with M-Pesa" button</li>
                  <li>You'll receive a prompt on your phone</li>
                  <li>Enter your M-Pesa PIN to complete payment</li>
                </ol>
              </div>

              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={() => setStep(1)}
                  disabled={processing}
                >
                  Back
                </Button>
                <Button 
                  className="w-full bg-secondary hover:bg-secondary/90" 
                  onClick={handleMpesaPayment}
                  disabled={processing}
                >
                  {processing ? "Processing..." : "Pay with M-Pesa"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default BookingModal;
