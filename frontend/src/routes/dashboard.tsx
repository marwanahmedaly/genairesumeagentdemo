import { createFileRoute, redirect } from "@tanstack/react-router";
import { Dashboard } from "@/features/dashboard/components/dashboard";
import { supabase } from "@/lib/supabase";

export const Route = createFileRoute("/dashboard")({
  beforeLoad: async () => {
    // Check if user is authenticated using proper Supabase session validation
    // Note: OAuth callbacks are now handled by /auth/callback route first,
    // so this check won't interrupt the PKCE flow
    const {
      data: { session },
      error,
    } = await supabase.auth.getSession();

    if (error || !session) {
      throw redirect({
        to: "/login",
        search: {
          redirect: "/dashboard",
        },
      });
    }
  },
  component: () => <Dashboard />,
});
