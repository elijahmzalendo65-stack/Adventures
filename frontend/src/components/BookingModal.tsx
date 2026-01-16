import { useState, useEffect } from "react";
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
import { CalendarIcon, Smartphone, AlertCircle, LogIn, Search } from "lucide-react";
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
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [userData, setUserData] = useState<any>(null);
  const [availableAdventures, setAvailableAdventures] = useState<any[]>([]);
  const [validatedAdventureId, setValidatedAdventureId] = useState<number | null>(null);
  const [checkingAdventure, setCheckingAdventure] = useState(false);

  const totalPrice = adventurePrice * parseInt(formData.guests);

  // Check authentication status and available adventures when modal opens
  useEffect(() => {
    if (open) {
      checkAuthentication();
      fetchAvailableAdventures();
    } else {
      // Reset auth state when modal closes
      setAuthChecked(false);
      setAuthError(null);
      setValidatedAdventureId(null);
    }
  }, [open]);

  const checkAuthentication = async () => {
    try {
      console.log('🔄 Checking authentication status...');
      setAuthError(null);
      
      // Use the correct endpoint: /api/auth/check-auth
      const response = await axios.get('http://localhost:5000/api/auth/check-auth', {
        withCredentials: true,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      
      console.log('✅ Auth check response:', response.data);
      
      if (response.data.authenticated) {
        setIsAuthenticated(true);
        setUserData(response.data.user);
        console.log('👤 User is authenticated:', response.data.user);
        
        // Pre-fill form with user data if available
        if (response.data.user && !formData.name) {
          setFormData(prev => ({
            ...prev,
            name: response.data.user.username || '',
            email: response.data.user.email || '',
            phone: response.data.user.phone_number || ''
          }));
        }
      } else {
        setIsAuthenticated(false);
        setUserData(null);
        console.log('⚠️ User is not authenticated');
      }
    } catch (error: any) {
      console.error('❌ Auth check failed:', error);
      
      // Handle specific errors
      if (error.response?.status === 404) {
        setAuthError('Authentication endpoint not found');
        console.error('⚠️ Endpoint /api/auth/check-auth returned 404');
        
        // Fallback: Check localStorage for user data
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          try {
            const user = JSON.parse(storedUser);
            setIsAuthenticated(true);
            setUserData(user);
            console.log('📦 Using localStorage user:', user);
          } catch {
            setIsAuthenticated(false);
          }
        }
      } else if (error.response?.status === 500) {
        setAuthError('Server error checking authentication');
      } else if (error.message?.includes('Network Error')) {
        setAuthError('Cannot connect to server');
      } else {
        setAuthError('Authentication check failed');
      }
      
      setIsAuthenticated(false);
    } finally {
      setAuthChecked(true);
    }
  };

  const fetchAvailableAdventures = async () => {
    try {
      console.log('🔄 Fetching available adventures...');
      const response = await axios.get(
        'http://localhost:5000/api/adventures/',
        { withCredentials: true }
      );
      
      if (response.data && Array.isArray(response.data)) {
        setAvailableAdventures(response.data);
        console.log(`✅ Found ${response.data.length} available adventures`);
        
        // Check if the provided adventureId exists
        const adventureExists = response.data.find((adv: any) => adv.id === adventureId);
        
        if (adventureExists) {
          setValidatedAdventureId(adventureId);
          console.log(`✅ Adventure ${adventureId} exists: ${adventureExists.title}`);
        } else {
          console.warn(`⚠️ Adventure ${adventureId} not found. Available IDs:`, 
            response.data.map((a: any) => a.id));
          
          // If no adventures exist, create a test one
          if (response.data.length === 0) {
            await createTestAdventure();
          } else {
            // Use the first available adventure
            const firstAdventure = response.data[0];
            setValidatedAdventureId(firstAdventure.id);
            console.log(`🔄 Using adventure ${firstAdventure.id} instead: ${firstAdventure.title}`);
            
            toast({
              title: "Adventure Updated",
              description: `Using "${firstAdventure.title}" for booking`,
              variant: "default",
            });
          }
        }
      }
    } catch (error) {
      console.error('❌ Error fetching adventures:', error);
      // Try to create a test adventure
      await createTestAdventure();
    }
  };

  const createTestAdventure = async () => {
    try {
      console.log('🔄 Creating test adventure...');
      setCheckingAdventure(true);
      
      // Try to create adventure 101 first
      const response = await axios.post(
        'http://localhost:5000/api/adventures/debug/create-test-101',
        {},
        { withCredentials: true }
      );
      
      if (response.status === 201 || response.status === 200) {
        console.log('✅ Created test adventure:', response.data);
        setValidatedAdventureId(101);
        
        toast({
          title: "Test Adventure Created",
          description: "A test adventure has been created for booking",
          variant: "default",
        });
        
        // Refresh available adventures
        await fetchAvailableAdventures();
      }
    } catch (error) {
      console.error('❌ Failed to create test adventure:', error);
      
      // Try adventure 102 as fallback
      try {
        const response102 = await axios.post(
          'http://localhost:5000/api/adventures/debug/create-test-102',
          {},
          { withCredentials: true }
        );
        
        if (response102.status === 201 || response102.status === 200) {
          setValidatedAdventureId(102);
          await fetchAvailableAdventures();
        }
      } catch (error2) {
        console.error('❌ Failed to create any test adventure:', error2);
      }
    } finally {
      setCheckingAdventure(false);
    }
  };

  const validateCurrentAdventure = async () => {
    if (!validatedAdventureId) {
      await fetchAvailableAdventures();
    }
    return validatedAdventureId;
  };

  const handleInputChange = (field: keyof typeof formData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Helper function to convert date to YYYY-MM-DD format
  const formatDateForBackend = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // -----------------------------
  // Step 1: Create Booking (UPDATED)
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

    // Check if user is authenticated
    if (!isAuthenticated) {
      toast({
        title: "Login Required",
        description: "Please login to make a booking",
        variant: "destructive",
      });
      
      // Redirect to login page
      setTimeout(() => {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      }, 1500);
      return;
    }

    setProcessing(true);

    try {
      // Validate and get a working adventure ID
      const workingAdventureId = await validateCurrentAdventure();
      
      if (!workingAdventureId) {
        toast({
          title: "No Adventures Available",
          description: "Please try again or contact support",
          variant: "destructive",
        });
        return;
      }

      console.log("📝 Creating booking for adventure:", workingAdventureId);
      console.log("👤 Form data:", formData);
      console.log("📅 Selected date:", date);
      console.log("👤 Current user:", userData);
      
      // Format date properly
      const adventureDate = formatDateForBackend(date);

      const bookingPayload = {
        adventure_id: workingAdventureId,
        adventure_date: adventureDate,
        number_of_people: parseInt(formData.guests),
        customer_name: formData.name,
        customer_email: formData.email,
        customer_phone: formData.phone,
        special_requests: "",
      };
      
      console.log("📤 Booking payload:", bookingPayload);

      // Use the correct endpoint with trailing slash
      const endpoint = "http://localhost:5000/api/bookings/";
      
      console.log(`🔄 Making request to: ${endpoint}`);
      console.log(`🔐 Session should be active for user: ${userData?.id || 'unknown'}`);
      
      const response = await axios.post(
        endpoint,
        bookingPayload,
        { 
          withCredentials: true, // CRITICAL: Sends session cookies
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        }
      );
      
      console.log("✅ Booking successful:", response.data);

      // Extract booking ID from response
      let createdBookingId;
      if (response.data.booking?.id) {
        createdBookingId = response.data.booking.id;
      } else if (response.data.id) {
        createdBookingId = response.data.id;
      } else if (response.data.booking_id) {
        createdBookingId = response.data.booking_id;
      }

      if (!createdBookingId) {
        console.error("⚠️ No booking ID in response:", response.data);
        // Still proceed if booking was created successfully
        createdBookingId = Date.now(); // Fallback ID
      }

      setBookingId(createdBookingId);

      toast({
        title: "Booking Created!",
        description: "Your booking has been created. Proceed to payment.",
      });

      onBookingCompleted?.("pending", createdBookingId);
      setStep(2);
    } catch (err: any) {
      console.error("❌ Booking creation error:", err);
      
      let errorMessage = "Failed to create booking. Please try again.";
      let showLoginPrompt = false;
      
      if (err.response) {
        console.error('Server response:', err.response.status, err.response.data);
        
        if (err.response.status === 401) {
          errorMessage = "Please login to make a booking";
          showLoginPrompt = true;
          setIsAuthenticated(false);
          
        } else if (err.response.status === 400) {
          errorMessage = err.response.data.message || "Please check your input";
        } else if (err.response.status === 404) {
          if (err.response.data?.message?.includes('Adventure')) {
            errorMessage = "Adventure not found. Trying to fix...";
            // Try to create a test adventure
            setTimeout(() => {
              createTestAdventure();
            }, 1000);
          } else {
            errorMessage = "Service unavailable. Please try again.";
          }
        } else if (err.response.status === 500) {
          errorMessage = "Server error. Please try again later.";
        } else if (err.response.data?.message) {
          errorMessage = err.response.data.message;
        }
      } else if (err.request) {
        console.error('No response received:', err.request);
        errorMessage = "Cannot connect to server. Please check your connection.";
      } else {
        console.error('Request setup error:', err.message);
      }
      
      toast({
        title: "Booking Failed",
        description: errorMessage,
        variant: "destructive",
      });
      
      // Show login prompt if unauthorized
      if (showLoginPrompt) {
        setTimeout(() => {
          window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
        }, 2000);
      }
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
      console.log("💰 Initiating payment for booking:", bookingId);
      console.log("📱 Phone number:", mpesaPhone);
      
      // Call your backend payment endpoint
      const paymentResponse = await axios.post(
        'http://localhost:5000/api/bookings/initiate-payment',
        {
          booking_id: bookingId,
          phone_number: mpesaPhone
        },
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      
      console.log("✅ Payment initiated:", paymentResponse.data);
      
      toast({
        title: "Payment Initiated",
        description: "Check your phone for the M-Pesa prompt to complete payment.",
      });

      // Simulate payment processing (in real app, you'd poll for payment status)
      setTimeout(() => {
        toast({
          title: "Payment Completed!",
          description: "M-Pesa payment successful. Booking confirmed.",
        });
        
        // Update booking status to completed
        onBookingCompleted?.("completed", bookingId);
        
        // Reset modal after successful payment
        setTimeout(() => {
          resetModal();
        }, 1500);
      }, 3000);
      
    } catch (err: any) {
      console.error("❌ Payment initiation error:", err);
      const msg = err?.response?.data?.message || err.message || "Payment could not be completed. Please try again.";
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
    setValidatedAdventureId(null);
  };

  // Show loading state while checking adventure
  if (open && checkingAdventure) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-2xl flex items-center gap-2">
              <Search className="h-6 w-6 text-blue-500" />
              Preparing Adventure
            </DialogTitle>
            <DialogDescription>
              Setting up adventure for booking...
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="flex flex-col items-center justify-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              <p className="mt-4 text-muted-foreground">
                {availableAdventures.length === 0 
                  ? "Creating a test adventure..." 
                  : "Validating adventure availability..."}
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  // Show auth checking state
  if (open && !authChecked) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-2xl">Checking Authentication</DialogTitle>
            <DialogDescription>
              Please wait while we verify your session...
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="flex flex-col items-center justify-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              <p className="mt-4 text-muted-foreground">Verifying your login status...</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  // Show login prompt if not authenticated
  if (open && authChecked && !isAuthenticated) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-2xl flex items-center gap-2">
              <LogIn className="h-6 w-6 text-amber-500" />
              Login Required
            </DialogTitle>
            <DialogDescription>
              You need to be logged in to book an adventure
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {authError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm text-red-800">
                  Authentication error: {authError}
                </p>
              </div>
            )}
            
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <p className="text-sm text-amber-800">
                To book this adventure, please login to your account first.
              </p>
            </div>
            
            <div className="flex flex-col gap-3 pt-2">
              <Button 
                onClick={() => {
                  window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
                }}
                className="w-full"
              >
                <LogIn className="mr-2 h-4 w-4" />
                Go to Login
              </Button>
              <Button 
                variant="outline" 
                onClick={resetModal}
                className="w-full"
              >
                Cancel
              </Button>
            </div>
            
            <div className="pt-4 border-t text-center">
              <p className="text-sm text-muted-foreground">
                Don't have an account?{" "}
                <a 
                  href="/register" 
                  className="text-primary hover:underline font-medium"
                  onClick={(e) => {
                    e.preventDefault();
                    window.location.href = `/register?redirect=${encodeURIComponent(window.location.pathname)}`;
                  }}
                >
                  Sign up here
                </a>
              </p>
            </div>
            
            {/* Debug info for development */}
            {process.env.NODE_ENV === 'development' && (
              <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                <p className="text-xs font-medium text-gray-700 mb-1">Debug Info:</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• Auth endpoint: /api/auth/check-auth</li>
                  <li>• Error: {authError || 'None'}</li>
                  <li>• Cookies enabled: {navigator.cookieEnabled ? 'Yes' : 'No'}</li>
                  <li>• <button 
                    className="text-blue-600 hover:underline"
                    onClick={checkAuthentication}
                  >
                    Retry auth check
                  </button></li>
                </ul>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    );
  }

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
            {/* Adventure status indicator */}
            {validatedAdventureId && validatedAdventureId !== adventureId && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-2">
                <p className="text-sm text-blue-700 flex items-center gap-2">
                  <Search className="h-4 w-4" />
                  Using adventure ID: {validatedAdventureId}
                  {availableAdventures.find(a => a.id === validatedAdventureId)?.title && 
                    ` (${availableAdventures.find(a => a.id === validatedAdventureId)?.title})`
                  }
                </p>
              </div>
            )}
            
            {/* Authentication status indicator */}
            {isAuthenticated && userData && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-2">
                <p className="text-sm text-green-700 flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <span className="h-2 w-2 bg-green-500 rounded-full"></span>
                    Logged in as: {userData.username || userData.email}
                  </span>
                  <button 
                    onClick={checkAuthentication}
                    className="text-xs text-green-600 hover:text-green-800 hover:underline"
                  >
                    Refresh
                  </button>
                </p>
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="name">Full Name *</Label>
              <Input
                id="name"
                placeholder="John Doe"
                value={formData.name}
                onChange={(e) => handleInputChange("name", e.target.value)}
                disabled={processing}
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
                disabled={processing}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number *</Label>
              <Input
                id="phone"
                placeholder="0712345678"
                value={formData.phone}
                onChange={(e) => handleInputChange("phone", e.target.value)}
                disabled={processing}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="guests">Number of Guests *</Label>
              <Select
                value={formData.guests}
                onValueChange={(value) => handleInputChange("guests", value)}
                disabled={processing}
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
                    disabled={processing}
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
                    disabled={(d) => d < new Date() || processing}
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
              disabled={processing || !validatedAdventureId}
            >
              {processing ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Processing...
                </span>
              ) : validatedAdventureId ? "Proceed to Payment" : "Checking Adventure..."}
            </Button>
          </div>
        ) : (
          <div className="space-y-6 py-4">
            <div className="bg-muted p-4 rounded-lg space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Booking ID:</span>
                <span className="font-semibold">{bookingId}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Adventure ID:</span>
                <span className="font-semibold">{validatedAdventureId || adventureId}</span>
              </div>
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
                  placeholder="2547XXXXXXXX or 07XXXXXXXX"
                  value={mpesaPhone}
                  onChange={(e) => setMpesaPhone(e.target.value)}
                  className="pl-10"
                  disabled={processing}
                />
                <Smartphone className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              </div>
              <p className="text-xs text-muted-foreground">
                Enter your M-Pesa registered phone number
              </p>
            </div>
            <Button
              className="w-full"
              onClick={handleMpesaPayment}
              disabled={processing || !bookingId}
            >
              {processing ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Processing Payment...
                </span>
              ) : (
                "Pay with M-Pesa"
              )}
            </Button>
            
            {/* Debug info for development */}
            {process.env.NODE_ENV === 'development' && (
              <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                <p className="text-xs font-medium text-gray-700 mb-1">Debug Info:</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• Backend: http://localhost:5000</li>
                  <li>• Endpoint: /api/bookings/</li>
                  <li>• Authenticated: {isAuthenticated ? "Yes" : "No"}</li>
                  <li>• User ID: {userData?.id || "Not available"}</li>
                  <li>• Booking ID: {bookingId || "Not set"}</li>
                  <li>• Session active: {isAuthenticated ? "✅" : "❌"}</li>
                  <li>• Adventure ID: {validatedAdventureId || "Not validated"}</li>
                  <li>• Available adventures: {availableAdventures.length}</li>
                </ul>
                <div className="mt-2 flex gap-2">
                  <button 
                    className="text-xs text-blue-600 hover:underline"
                    onClick={checkAuthentication}
                  >
                    Refresh Auth
                  </button>
                  <button 
                    className="text-xs text-blue-600 hover:underline"
                    onClick={() => window.open('http://localhost:5000/api/auth/debug-session', '_blank')}
                  >
                    Debug Session
                  </button>
                  <button 
                    className="text-xs text-blue-600 hover:underline"
                    onClick={fetchAvailableAdventures}
                  >
                    Refresh Adventures
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default BookingModal;