import { createFileRoute } from "@tanstack/react-router";
import { useAuth } from "@/components/providers/auth-provider";
import { ModeToggle } from "@/components/layout/mode-toggle";

export const Route = createFileRoute("/")({
  component: IndexComponent,
});

function IndexComponent() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background relative">
        <div className="absolute top-4 right-4">
          <ModeToggle />
        </div>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (user) {
    // Redirect to dashboard if authenticated
    window.location.href = "/dashboard";
    return null;
  }

  // Redirect to login if not authenticated
  window.location.href = "/login";
  return null;
}
