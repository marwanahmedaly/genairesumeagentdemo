import { supabase } from "./supabase";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export interface AlignmentResult {
  match_score: number;
  missing_skills: string[];
  pivoted_bullets: Array<{
    original: string;
    suggested: string;
  }>;
  r2_key?: string;
  suggested_overrides?: {
    candidate_flow: string;
    experience_years_estimate: number;
    is_manager: boolean;
    domain_tags: string[];
    top_skills: string[];
  };
}

export interface HistoryItem {
  id: string;
  created_at: string;
  role_title: string;
  r2_key: string;
}

export interface ResumePreference {
  id: string;
  user_id: string;
  name: string;
  preferences: {
    candidate_flow?: string;
    experience_years_estimate?: number;
    is_manager?: boolean;
    domain_tags?: string[];
    top_skills?: string[];
    include_sections?: string[];
    exclude_sections?: string[];
  };
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

class ApiService {
  private async getValidAccessToken(): Promise<string> {
    // Get fresh session from Supabase to ensure token validity
    const {
      data: { session },
      error,
    } = await supabase.auth.getSession();

    // Debug logging in development mode
    if (import.meta.env.DEV) {
      console.log("[Auth Debug] Session check:", {
        hasSession: !!session,
        hasAccessToken: !!session?.access_token,
        error: error?.message,
        expiresAt: session?.expires_at
          ? new Date(session.expires_at * 1000).toISOString()
          : "N/A",
      });
    }

    if (error) {
      console.error("[Auth Error] Failed to get session:", error.message);
      throw new Error(`Authentication error: ${error.message}`);
    }

    if (!session?.access_token) {
      console.error(
        "[Auth Error] No session or access token found. LocalStorage keys:",
        Object.keys(localStorage).filter(
          (k) => k.includes("sb-") || k.includes("supabase"),
        ),
      );
      throw new Error("No valid session found. Please log in again.");
    }

    return session.access_token;
  }

  private getHeaders(accessToken: string) {
    return {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    };
  }

  async alignResume(jobUrl: string, file: File): Promise<AlignmentResult> {
    const accessToken = await this.getValidAccessToken();

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(
      `${BACKEND_URL}/full-alignment?url=${encodeURIComponent(jobUrl)}`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        body: formData,
      },
    );

    if (!response.ok) {
      const errorText = await response.text();
      const userMessage = this.extractErrorMessage(errorText);
      throw new Error(userMessage);
    }

    return response.json();
  }

  private extractErrorMessage(errorText: string): string {
    try {
      const errorJson = JSON.parse(errorText);
      if (errorJson.detail) {
        return errorJson.detail;
      }
    } catch {
      // Not JSON, return as is
    }
    return errorText || "An unexpected error occurred";
  }

  async alignResumeWithOverrides(
    jobUrl: string,
    file: File,
    overrides: Record<string, unknown>,
  ): Promise<AlignmentResult> {
    const accessToken = await this.getValidAccessToken();

    const formData = new FormData();
    formData.append("file", file);
    formData.append("overrides", JSON.stringify(overrides));

    const response = await fetch(
      `${BACKEND_URL}/full-alignment?url=${encodeURIComponent(jobUrl)}`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        body: formData,
      },
    );

    if (!response.ok) {
      const errorText = await response.text();
      const userMessage = this.extractErrorMessage(errorText);
      throw new Error(userMessage);
    }

    return response.json();
  }

  async getHistory(): Promise<HistoryItem[]> {
    const accessToken = await this.getValidAccessToken();

    const response = await fetch(`${BACKEND_URL}/history`, {
      headers: this.getHeaders(accessToken),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch history: ${response.statusText}`);
    }

    return response.json();
  }

  async getDownloadUrl(r2Key: string): Promise<{ download_url: string }> {
    const accessToken = await this.getValidAccessToken();

    const response = await fetch(
      `${BACKEND_URL}/generate-download-url?r2_key=${encodeURIComponent(r2Key)}`,
      {
        headers: this.getHeaders(accessToken),
      },
    );

    if (!response.ok) {
      throw new Error(`Failed to get download URL: ${response.statusText}`);
    }

    return response.json();
  }

  async deleteResume(recordId: string): Promise<{ message: string }> {
    const accessToken = await this.getValidAccessToken();

    const response = await fetch(`${BACKEND_URL}/history/${recordId}`, {
      method: "DELETE",
      headers: this.getHeaders(accessToken),
    });

    if (!response.ok) {
      throw new Error(`Failed to delete resume: ${response.statusText}`);
    }

    return response.json();
  }

  // Preferences API methods
  async getUserPreferences(): Promise<ResumePreference[]> {
    const accessToken = await this.getValidAccessToken();

    const response = await fetch(`${BACKEND_URL}/user/preferences`, {
      headers: this.getHeaders(accessToken),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch preferences: ${response.statusText}`);
    }

    const data = await response.json();
    return data.preferences || [];
  }

  async createPreference(
    name: string,
    preferences: Record<string, unknown>,
    isDefault = false,
  ): Promise<ResumePreference> {
    const accessToken = await this.getValidAccessToken();

    const response = await fetch(`${BACKEND_URL}/user/preferences`, {
      method: "POST",
      headers: this.getHeaders(accessToken),
      body: JSON.stringify({
        name,
        preferences,
        is_default: isDefault,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create preference: ${response.statusText}`);
    }

    return response.json();
  }

  async updatePreference(
    id: string,
    name?: string,
    preferences?: Record<string, unknown>,
    isDefault?: boolean,
  ): Promise<ResumePreference> {
    const accessToken = await this.getValidAccessToken();

    const updateData: Record<string, unknown> = {};
    if (name !== undefined) updateData.name = name;
    if (preferences !== undefined) updateData.preferences = preferences;
    if (isDefault !== undefined) updateData.is_default = isDefault;

    const response = await fetch(`${BACKEND_URL}/user/preferences/${id}`, {
      method: "PUT",
      headers: this.getHeaders(accessToken),
      body: JSON.stringify(updateData),
    });

    if (!response.ok) {
      throw new Error(`Failed to update preference: ${response.statusText}`);
    }

    return response.json();
  }

  async deletePreference(id: string): Promise<{ message: string }> {
    const accessToken = await this.getValidAccessToken();

    const response = await fetch(`${BACKEND_URL}/user/preferences/${id}`, {
      method: "DELETE",
      headers: this.getHeaders(accessToken),
    });

    if (!response.ok) {
      throw new Error(`Failed to delete preference: ${response.statusText}`);
    }

    return response.json();
  }

  async setDefaultPreference(id: string): Promise<{ message: string }> {
    const accessToken = await this.getValidAccessToken();

    const response = await fetch(
      `${BACKEND_URL}/user/preferences/${id}/default`,
      {
        method: "POST",
        headers: this.getHeaders(accessToken),
      },
    );

    if (!response.ok) {
      throw new Error(
        `Failed to set default preference: ${response.statusText}`,
      );
    }

    return response.json();
  }
}

export const apiService = new ApiService();
