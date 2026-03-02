import { useState, useEffect } from "react";
import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { ModeToggle } from "@/components/layout/mode-toggle";
import { JobPostingInput } from "./job-posting-input";
import { FileUpload } from "./file-upload";
import { ResultsDisplay, ResultsSkeleton } from "./results-display";
import { HistorySidebar } from "./history-sidebar";
import { ResumeTailoringModal } from "./resume-tailoring-modal";
import { PreferencesPanel } from "./preferences-panel";
import { AlignmentResult, apiService, ResumePreference } from "@/lib/api";
import { LogOut, Settings } from "lucide-react";
import { toast } from "sonner";

export function Dashboard() {
  const { user, signOut } = useAuth();
  const [jobUrl, setJobUrl] = useState("");
  const [results, setResults] = useState<AlignmentResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [historyRefreshTrigger, setHistoryRefreshTrigger] = useState(0);
  const [isTailoringModalOpen, setIsTailoringModalOpen] = useState(false);
  const [pendingAlignment, setPendingAlignment] =
    useState<AlignmentResult | null>(null);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [isPreferencesPanelOpen, setIsPreferencesPanelOpen] = useState(false);
  const [selectedPreference, setSelectedPreference] =
    useState<ResumePreference | null>(null);
  const [defaultPreference, setDefaultPreference] =
    useState<ResumePreference | null>(null);

  // Load user preferences on mount to show default preference name
  useEffect(() => {
    const loadDefaultPreference = async () => {
      if (user) {
        try {
          const preferences = await apiService.getUserPreferences();
          const defaultPref =
            preferences.find((pref) => pref.is_default) || null;
          setDefaultPreference(defaultPref);
        } catch (error) {
          console.error("Failed to load default preference:", error);
        }
      }
    };

    loadDefaultPreference();
  }, [user]);

  const refreshDefaultPreference = async () => {
    if (user) {
      try {
        const preferences = await apiService.getUserPreferences();
        const defaultPref = preferences.find((pref) => pref.is_default) || null;
        setDefaultPreference(defaultPref);
      } catch (error) {
        console.error("Failed to refresh default preference:", error);
      }
    }
  };

  const handleResults = (alignmentResults: AlignmentResult) => {
    // Results are now handled directly by FileUpload component
    // This function now just displays the final results
    setResults(alignmentResults);
    setHistoryRefreshTrigger((prev) => prev + 1);
    toast.success("Resume optimized and generated successfully!");
  };

  const handleTailoringConfirm = async (overrides: Record<string, unknown>) => {
    if (!pendingAlignment || !pendingFile) return;

    setIsTailoringModalOpen(false);
    setIsGeneratingPDF(true);

    try {
      // Regenerate with overrides
      const finalResults = await apiService.alignResumeWithOverrides(
        jobUrl,
        pendingFile,
        overrides,
      );

      setResults(finalResults);
      setHistoryRefreshTrigger((prev) => prev + 1);
      toast.success("Resume optimized and generated successfully!");
    } catch (error) {
      console.error("PDF generation failed:", error);
      toast.error("Failed to generate optimized resume. Please try again.");
    } finally {
      setIsGeneratingPDF(false);
      setPendingAlignment(null);
      setPendingFile(null);
    }
  };

  const handleTailoringCancel = () => {
    setIsTailoringModalOpen(false);
    setPendingAlignment(null);
    setSelectedPreference(null);
    // Reset processing state
    setIsProcessing(false);
  };

  const handlePreferenceSelect = (preference: ResumePreference | null) => {
    setSelectedPreference(preference);
    setIsPreferencesPanelOpen(false);

    // Only show tailoring modal if a preference is selected for editing
    // Creating preferences now uses the dedicated onCreatePreference callback
    if (preference) {
      setIsTailoringModalOpen(true);
    }
  };

  const handleCreatePreference = () => {
    setSelectedPreference(null);
    setIsPreferencesPanelOpen(false);
    setIsTailoringModalOpen(true);
  };

  const handleSavePreference = async (
    name: string,
    overrides: Record<string, unknown>,
  ) => {
    try {
      await apiService.createPreference(name, overrides, false); // Don't create as default
      setIsTailoringModalOpen(false);
      setSelectedPreference(null);
      await refreshDefaultPreference(); // Refresh header - new preference might be default if it's first one
      toast.success(`Preference "${name}" saved successfully!`);
    } catch (error) {
      console.error("Failed to save preference:", error);
      toast.error("Failed to save preference. Please try again.");
    }
  };

  const handleUpdatePreference = async (
    preferenceId: string,
    name: string,
    overrides: Record<string, unknown>,
  ) => {
    try {
      await apiService.updatePreference(preferenceId, name, overrides);
      setIsTailoringModalOpen(false);
      setSelectedPreference(null);
      await refreshDefaultPreference(); // Refresh header - updated preference might be the default one
      toast.success(`Preference "${name}" updated successfully!`);
    } catch (error) {
      console.error("Failed to update preference:", error);
      toast.error("Failed to update preference. Please try again.");
    }
  };

  const handleDownload = async () => {
    if (!results?.r2_key) return;

    setIsDownloading(true);
    try {
      const { download_url } = await apiService.getDownloadUrl(results.r2_key);

      // Create a temporary link and trigger download
      const link = document.createElement("a");
      link.href = download_url;
      link.download = `optimized_resume_${Date.now()}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Download failed:", error);
      toast.error("Failed to download resume. Please try again.");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b bg-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h1 className="text-3xl font-bold text-primary tracking-tight">
                🎯 Resume Aligner AI
              </h1>
              <p className="text-sm text-muted-foreground">
                Optimize your resume for job applications with AI-powered
                insights
              </p>
            </div>
            <div className="flex items-center gap-6">
              <ModeToggle />
              {user && (
                <div className="flex items-center gap-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsPreferencesPanelOpen(true)}
                  >
                    <Settings className="w-4 h-4 mr-2" />
                    Preferences
                    {defaultPreference ? ` — ${defaultPreference.name}` : ""}
                  </Button>
                  <span className="text-sm text-muted-foreground hidden sm:inline">
                    {user.email}
                  </span>
                  <Button variant="outline" size="sm" onClick={signOut}>
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign Out
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1 h-135">
            <HistorySidebar refreshTrigger={historyRefreshTrigger} />
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-3 space-y-6 overflow-y-auto scrollbar-thin">
            {/* Job Posting Input */}
            <JobPostingInput
              jobUrl={jobUrl}
              onJobUrlChange={setJobUrl}
              disabled={isProcessing}
            />

            {/* File Upload */}
            <FileUpload
              jobUrl={jobUrl}
              onProcessing={setIsProcessing}
              onResults={handleResults}
              disabled={isProcessing}
              defaultPreference={defaultPreference}
            />

            {/* Results Display */}
            {isProcessing && !results ? (
              <ResultsSkeleton />
            ) : results ? (
              <ResultsDisplay
                results={results}
                onDownload={handleDownload}
                isDownloading={isDownloading}
              />
            ) : null}
          </div>
        </div>
      </div>

      {/* Resume Tailoring Modal */}
      <ResumeTailoringModal
        isOpen={isTailoringModalOpen}
        onClose={handleTailoringCancel}
        onConfirm={handleTailoringConfirm}
        suggestedOverrides={pendingAlignment?.suggested_overrides || null}
        selectedPreference={selectedPreference}
        mode={
          pendingAlignment
            ? "generate_resume"
            : selectedPreference
              ? "edit_preference"
              : "create_preference"
        }
        onSavePreference={handleSavePreference}
        onUpdatePreference={handleUpdatePreference}
        isLoading={isGeneratingPDF}
      />

      {/* Preferences Panel */}
      <PreferencesPanel
        isOpen={isPreferencesPanelOpen}
        onClose={() => setIsPreferencesPanelOpen(false)}
        onPreferenceSelect={handlePreferenceSelect}
        onCreatePreference={handleCreatePreference}
        onDefaultChanged={refreshDefaultPreference}
      />
    </div>
  );
}
