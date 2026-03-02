import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.warn(
    "⚠️ Supabase environment variables not configured. Authentication features will not work.",
  );
  console.warn(
    "Please set VITE_SUPABASE_URL and SUPABASE_KEY in your .env file.",
  );
}

// Create client with default localStorage storage (battle-tested and reliable)
export const supabase = createClient(
  supabaseUrl || "https://placeholder.supabase.co",
  supabaseKey || "placeholder-key",
  {
    auth: {
      flowType: "pkce",
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
      // Using default localStorage - more reliable for PKCE OAuth flow
    },
  },
);

export type User = {
  id: string;
  email: string;
  user_metadata: {
    full_name?: string;
    avatar_url?: string;
  };
};

export type Session = {
  access_token: string;
  refresh_token: string;
  user: User;
};
