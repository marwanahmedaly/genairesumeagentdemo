import {
  createFileRoute,
  useNavigate,
  useSearch,
} from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ModeToggle } from "@/components/layout/mode-toggle";

export const Route = createFileRoute("/auth/callback")({
  component: AuthCallback,
});

function AuthCallback() {
  const navigate = useNavigate();
  const search = useSearch({ from: "/auth/callback" }) as { redirect?: string };
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Supabase SDK automatically detects and processes OAuth callback parameters
        // (code, access_token, refresh_token, etc.) from the URL because detectSessionInUrl is enabled

        // Wait a moment for the SDK to process the callback
        await new Promise((resolve) => setTimeout(resolve, 100));

        // Check if we now have a valid session
        const {
          data: { session },
          error: sessionError,
        } = await supabase.auth.getSession();

        if (sessionError) {
          console.error("Session error during OAuth callback:", sessionError);
          setError(sessionError.message);
          return;
        }

        if (session) {
          // Successfully authenticated - redirect to intended destination
          const redirectTo = search.redirect || "/dashboard";
          navigate({ to: redirectTo });
        } else {
          // No session yet - wait for auth state change event
          // The AuthProvider's onAuthStateChange will handle the final navigation
          // We'll wait a bit longer for the state change
          await new Promise((resolve) => setTimeout(resolve, 500));

          const {
            data: { session: retrySession },
          } = await supabase.auth.getSession();

          if (retrySession) {
            const redirectTo = search.redirect || "/dashboard";
            navigate({ to: redirectTo });
          } else {
            // If still no session after waiting, something went wrong
            setError("Authentication failed. Please try again.");
            setTimeout(() => {
              navigate({ to: "/login" });
            }, 2000);
          }
        }
      } catch (err) {
        console.error("Error handling auth callback:", err);
        setError("An unexpected error occurred during authentication.");
        setTimeout(() => {
          navigate({ to: "/login" });
        }, 2000);
      }
    };

    handleAuthCallback();
  }, [navigate, search.redirect]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4 relative">
        <div className="absolute top-4 right-4">
          <ModeToggle />
        </div>
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-destructive">
              Authentication Error
            </CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <CardContent className="text-center text-sm text-muted-foreground">
            Redirecting to login page...
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative">
      <div className="absolute top-4 right-4">
        <ModeToggle />
      </div>
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">
            Completing Sign In
          </CardTitle>
          <CardDescription>
            Please wait while we authenticate you...
          </CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </CardContent>
      </Card>
    </div>
  );
}
