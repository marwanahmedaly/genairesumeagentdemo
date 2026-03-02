import { createContext, useContext, useEffect, useState } from "react";
import { User, supabase } from "@/lib/supabase";

type AuthContextType = {
  user: User | null;
  loading: boolean;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if Supabase is properly configured
    const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
    const supabaseKey = import.meta.env.VITE_SUPABASE_KEY;

    if (!supabaseUrl || !supabaseKey || supabaseUrl.includes("placeholder")) {
      console.warn("Supabase not configured - running in demo mode");
      setLoading(false);
      return;
    }

    // Check for existing session on app load
    const checkInitialSession = async () => {
      try {
        const {
          data: { session },
          error,
        } = await supabase.auth.getSession();
        if (error) {
          console.warn("Session check error:", error);
        } else if (session) {
          setUser({
            id: session.user.id,
            email: session.user.email || "",
            user_metadata: session.user.user_metadata,
          });
        }
      } catch (error) {
        console.warn("Failed to check initial session:", error);
      } finally {
        setLoading(false);
      }
    };

    checkInitialSession();

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log(
        "Auth state change:",
        event,
        session ? "Session exists" : "No session",
      );

      if (session) {
        setUser({
          id: session.user.id,
          email: session.user.email || "",
          user_metadata: session.user.user_metadata,
        });

        // Clean up OAuth parameters from URL after successful authentication
        if (event === "SIGNED_IN") {
          const currentUrl = new URL(window.location.href);
          let needsCleanup = false;

          // Check for hash-based OAuth parameters (implicit flow)
          if (currentUrl.hash.includes("access_token")) {
            currentUrl.hash = "";
            needsCleanup = true;
          }

          // Check for query-based OAuth parameters (PKCE flow)
          if (currentUrl.searchParams.has("code")) {
            currentUrl.searchParams.delete("code");
            needsCleanup = true;
          }

          // Clean up URL without triggering navigation
          if (needsCleanup) {
            window.history.replaceState(
              {},
              document.title,
              currentUrl.pathname + currentUrl.search + currentUrl.hash,
            );
          }
        }
      } else {
        setUser(null);
      }
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signOut = async () => {
    await supabase.auth.signOut();
    // Supabase automatically clears localStorage on signOut
    // Redirect to login page after sign out
    window.location.href = "/login";
  };

  const value = {
    user,
    loading,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
