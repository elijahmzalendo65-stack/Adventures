import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface User {
  id: string;
  email: string;
  name: string;
  createdAt: string;
}

interface AuthContextType {
  user: User | null;
  users: User[];
  login: (email: string, password: string) => boolean;
  signup: (email: string, password: string, name: string) => boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    // Load users from localStorage
    const storedUsers = localStorage.getItem("users");
    if (storedUsers) {
      setUsers(JSON.parse(storedUsers));
    }

    // Load current user from localStorage
    const storedUser = localStorage.getItem("currentUser");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const signup = (email: string, password: string, name: string) => {
    // Check if user already exists
    if (users.some((u) => u.email === email)) {
      return false;
    }

    const newUser: User = {
      id: Math.random().toString(36).substr(2, 9),
      email,
      name,
      createdAt: new Date().toISOString(),
    };

    const updatedUsers = [...users, newUser];
    setUsers(updatedUsers);
    localStorage.setItem("users", JSON.stringify(updatedUsers));
    localStorage.setItem(`password_${email}`, password);

    // Auto login after signup
    setUser(newUser);
    localStorage.setItem("currentUser", JSON.stringify(newUser));
    return true;
  };

  const login = (email: string, password: string) => {
    const existingUser = users.find((u) => u.email === email);
    if (!existingUser) {
      return false;
    }

    const storedPassword = localStorage.getItem(`password_${email}`);
    if (storedPassword !== password) {
      return false;
    }

    setUser(existingUser);
    localStorage.setItem("currentUser", JSON.stringify(existingUser));
    return true;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("currentUser");
  };

  return (
    <AuthContext.Provider value={{ user, users, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};