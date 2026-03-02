import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { supabase } from "@/lib/supabase";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useSearch, useNavigate } from "@tanstack/react-router";
import { useTheme } from "@/components/providers/theme-provider";
import { ModeToggle } from "@/components/layout/mode-toggle";
import { useEffect } from "react";
import { useAuth } from "@/components/providers/auth-provider";

export function LoginForm() {
  const search = useSearch({ from: "/login" }) as { redirect?: string };
  const { theme } = useTheme();
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  // Default redirect to dashboard, or use the redirect parameter
  const intendedDestination = search.redirect || "/dashboard";

  // Handle redirect when user is authenticated
  useEffect(() => {
    if (!loading && user) {
      navigate({ to: intendedDestination });
    }
  }, [user, loading, navigate, intendedDestination]);

  // Construct callback URL with intended destination preserved as query param
  const callbackUrl = `/auth/callback?redirect=${encodeURIComponent(intendedDestination)}`;

  // Determine actual theme (handle 'system' preference)
  const getActualTheme = () => {
    if (theme === "system") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    }
    return theme;
  };

  const actualTheme = getActualTheme();

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative">
      {/* Theme Toggle Button */}
      <div className="absolute top-4 right-4">
        <ModeToggle />
      </div>

      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">Welcome Back</CardTitle>
          <CardDescription>Sign in to your account to continue</CardDescription>
        </CardHeader>
        <CardContent>
          <Auth
            supabaseClient={supabase}
            appearance={{
              theme: ThemeSupa,
              variables: {
                default: {
                  colors: {
                    brand: "hsl(var(--primary))",
                    brandAccent: "hsl(var(--primary))",
                    brandButtonText: actualTheme === "dark" ? "white" : "white",
                    defaultButtonBackground:
                      actualTheme === "dark"
                        ? "hsl(var(--card))"
                        : "hsl(var(--card))",
                    defaultButtonBackgroundHover:
                      actualTheme === "dark"
                        ? "hsl(var(--accent))"
                        : "hsl(var(--accent))",
                    defaultButtonBorder:
                      actualTheme === "dark"
                        ? "hsl(var(--border))"
                        : "hsl(var(--border))",
                    defaultButtonText:
                      actualTheme === "dark"
                        ? "hsl(var(--foreground))"
                        : "hsl(var(--foreground))",
                    dividerBackground:
                      actualTheme === "dark"
                        ? "hsl(var(--border))"
                        : "hsl(var(--border))",
                    inputBackground:
                      actualTheme === "dark"
                        ? "hsl(var(--background))"
                        : "hsl(var(--background))",
                    inputBorder:
                      actualTheme === "dark"
                        ? "hsl(var(--input))"
                        : "hsl(var(--input))",
                    inputBorderHover:
                      actualTheme === "dark"
                        ? "hsl(var(--ring))"
                        : "hsl(var(--ring))",
                    inputBorderFocus:
                      actualTheme === "dark"
                        ? "hsl(var(--ring))"
                        : "hsl(var(--ring))",
                    inputText:
                      actualTheme === "dark"
                        ? "hsl(var(--foreground))"
                        : "hsl(var(--foreground))",
                    inputLabelText:
                      actualTheme === "dark"
                        ? "hsl(var(--foreground))"
                        : "hsl(var(--foreground))",
                    inputPlaceholder:
                      actualTheme === "dark"
                        ? "hsl(var(--muted-foreground))"
                        : "hsl(var(--muted-foreground))",
                    messageText:
                      actualTheme === "dark"
                        ? "hsl(var(--foreground))"
                        : "hsl(var(--foreground))",
                    messageTextDanger:
                      actualTheme === "dark"
                        ? "hsl(var(--destructive))"
                        : "hsl(var(--destructive))",
                    anchorTextColor:
                      actualTheme === "dark"
                        ? "hsl(var(--primary))"
                        : "hsl(var(--primary))",
                    anchorTextHoverColor:
                      actualTheme === "dark"
                        ? "hsl(var(--primary))"
                        : "hsl(var(--primary))",
                  },
                },
              },
              className: {
                container: "space-y-4",
                button: "!font-medium",
                input: "!rounded-md",
                label: "!text-sm !font-medium",
              },
            }}
            theme={actualTheme}
            providers={["google"]}
            redirectTo={`${window.location.origin}${callbackUrl}`}
          />
        </CardContent>
      </Card>
    </div>
  );
}
