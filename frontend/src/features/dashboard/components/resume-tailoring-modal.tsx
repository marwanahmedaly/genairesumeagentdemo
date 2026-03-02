import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Loader2,
  User,
  Briefcase,
  GraduationCap,
  Code,
  Target,
} from "lucide-react";
import { ResumePreference } from "@/lib/api";
import { toast } from "sonner";

interface SuggestedOverrides {
  candidate_flow?: string;
  experience_years_estimate?: number;
  is_manager?: boolean;
  domain_tags?: string[];
  top_skills?: string[];
  include_sections?: string[];
  exclude_sections?: string[];
}

interface ResumeTailoringModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (overrides: Record<string, unknown>) => void;
  suggestedOverrides: SuggestedOverrides | null;
  selectedPreference?: ResumePreference | null;
  mode?: "generate_resume" | "create_preference" | "edit_preference";
  onSavePreference?: (
    name: string,
    overrides: Record<string, unknown>,
  ) => Promise<void>;
  onUpdatePreference?: (
    preferenceId: string,
    name: string,
    overrides: Record<string, unknown>,
  ) => Promise<void>;
  isLoading?: boolean;
}

const CANDIDATE_FLOWS = [
  {
    value: "newgrad",
    label: "New Graduate (0-1 years)",
    description: "Focus on education, projects, and internships",
  },
  {
    value: "early-IC",
    label: "Early Career (1-3 years)",
    description: "Emphasize experience and technical skills",
  },
  {
    value: "mid-IC",
    label: "Mid-Level IC (3-7 years)",
    description: "Highlight achievements and technical depth",
  },
  {
    value: "mid-manager",
    label: "Mid-Level Manager (3-7 years)",
    description: "Focus on team leadership and impact",
  },
  {
    value: "senior",
    label: "Senior/Principal (7+ years)",
    description: "Show strategic impact and leadership",
  },
];

const DOMAIN_OPTIONS = [
  { value: "engineering", label: "Engineering", icon: Code },
  { value: "data", label: "Data & Analytics", icon: Target },
  { value: "product", label: "Product Management", icon: Briefcase },
  { value: "design", label: "Design & UX", icon: User },
  { value: "business", label: "Business & Operations", icon: Briefcase },
];

export function ResumeTailoringModal({
  isOpen,
  onClose,
  onConfirm,
  suggestedOverrides,
  selectedPreference,
  mode = "generate_resume",
  onSavePreference,
  onUpdatePreference,
  isLoading = false,
}: ResumeTailoringModalProps) {
  const [candidateFlow, setCandidateFlow] = useState("");
  const [experienceYears, setExperienceYears] = useState("");
  const [isManager, setIsManager] = useState(false);
  const [selectedDomains, setSelectedDomains] = useState<string[]>([]);
  const [topSkills, setTopSkills] = useState("");
  const [includeSections, setIncludeSections] = useState<string[]>([]);
  const [excludeSections, setExcludeSections] = useState<string[]>([]);
  const [preferenceName, setPreferenceName] = useState("");

  // Initialize form with suggested values or selected preference
  useEffect(() => {
    if (isOpen) {
      let source = suggestedOverrides;
      if (selectedPreference) {
        source = selectedPreference.preferences;
      }

      // Always reset form fields when modal opens
      // If there's a source (suggestions or selected preference), use those values
      // Otherwise, clear to defaults
      setCandidateFlow(source?.candidate_flow || "");
      setExperienceYears(source?.experience_years_estimate?.toString() || "");
      setIsManager(source?.is_manager || false);
      setSelectedDomains(source?.domain_tags || []);
      setTopSkills(source?.top_skills?.join(", ") || "");
      setIncludeSections(source?.include_sections || []);
      setExcludeSections(source?.exclude_sections || []);

      // Initialize preference name for editing
      if (selectedPreference) {
        setPreferenceName(selectedPreference.name);
      } else {
        setPreferenceName("");
      }
    }
  }, [suggestedOverrides, selectedPreference, isOpen]);

  const handleDomainToggle = (domain: string) => {
    setSelectedDomains((prev) =>
      prev.includes(domain)
        ? prev.filter((d) => d !== domain)
        : [...prev, domain],
    );
  };

  const handleSectionToggle = (
    section: string,
    type: "include" | "exclude",
  ) => {
    if (type === "include") {
      setIncludeSections((prev) =>
        prev.includes(section)
          ? prev.filter((s) => s !== section)
          : [...prev, section],
      );
      setExcludeSections((prev) => prev.filter((s) => s !== section));
    } else {
      setExcludeSections((prev) =>
        prev.includes(section)
          ? prev.filter((s) => s !== section)
          : [...prev, section],
      );
      setIncludeSections((prev) => prev.filter((s) => s !== section));
    }
  };

  const handleConfirm = async () => {
    const overrides: Record<string, unknown> = {
      candidate_flow: candidateFlow,
      experience_years_estimate: experienceYears
        ? parseFloat(experienceYears)
        : undefined,
      is_manager: isManager,
      domain_tags: selectedDomains,
      top_skills: topSkills
        ? topSkills
            .split(",")
            .map((s) => s.trim())
            .filter((s) => s)
        : undefined,
      include_sections:
        includeSections.length > 0 ? includeSections : undefined,
      exclude_sections:
        excludeSections.length > 0 ? excludeSections : undefined,
    };

    // Remove undefined values
    Object.keys(overrides).forEach((key) => {
      if (overrides[key] === undefined) {
        delete overrides[key];
      }
    });

    if (mode === "create_preference") {
      if (!preferenceName.trim()) {
        toast.error("Please enter a preference name");
        return;
      }
      if (onSavePreference) {
        await onSavePreference(preferenceName.trim(), overrides);
      }
    } else if (mode === "edit_preference" && selectedPreference) {
      if (!preferenceName.trim()) {
        toast.error("Please enter a preference name");
        return;
      }
      if (onUpdatePreference) {
        await onUpdatePreference(
          selectedPreference.id,
          preferenceName.trim(),
          overrides,
        );
      }
    } else {
      onConfirm(overrides);
    }
  };

  const getFlowDescription = (flow: string) => {
    return CANDIDATE_FLOWS.find((f) => f.value === flow)?.description || "";
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GraduationCap className="h-5 w-5" />
            {mode === "create_preference"
              ? "Create Resume Preference"
              : "Resume Tailoring Preferences"}
            {selectedPreference && (
              <span className="text-sm font-normal text-muted-foreground">
                — {selectedPreference.name}
              </span>
            )}
          </DialogTitle>
          <DialogDescription>
            {mode === "create_preference"
              ? "Configure your resume tailoring preferences and save them for future use."
              : "Review and customize how your resume will be optimized for this job application. These settings control the presentation style and content emphasis."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Preference Name (for create and edit modes) */}
          {(mode === "create_preference" || mode === "edit_preference") && (
            <Card>
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <Label htmlFor="preference-name">Preference Name</Label>
                  <Input
                    id="preference-name"
                    placeholder="e.g., Engineering IC, Product Manager"
                    value={preferenceName}
                    onChange={(e) => setPreferenceName(e.target.value)}
                  />
                  <p className="text-sm text-muted-foreground">
                    Give this preference profile a descriptive name for easy
                    identification.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Candidate Level & Experience */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <User className="h-4 w-4" />
                Career Level & Experience
              </CardTitle>
              <CardDescription>
                This determines the overall presentation style and content focus
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="candidate-flow">Career Level</Label>
                  <select
                    id="candidate-flow"
                    value={candidateFlow}
                    onChange={(e) => setCandidateFlow(e.target.value)}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="">Select career level</option>
                    {CANDIDATE_FLOWS.map((flow) => (
                      <option key={flow.value} value={flow.value}>
                        {flow.label}
                      </option>
                    ))}
                  </select>
                  {candidateFlow && (
                    <p className="text-sm text-muted-foreground">
                      {getFlowDescription(candidateFlow)}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="experience-years">Years of Experience</Label>
                  <Input
                    id="experience-years"
                    type="number"
                    step="0.5"
                    min="0"
                    max="30"
                    placeholder="e.g., 5.5"
                    value={experienceYears}
                    onChange={(e) => setExperienceYears(e.target.value)}
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is-manager"
                  checked={isManager}
                  onCheckedChange={(checked) => setIsManager(checked === true)}
                />
                <Label htmlFor="is-manager">
                  I have management or leadership experience
                </Label>
              </div>
            </CardContent>
          </Card>

          {/* Domain Focus */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Briefcase className="h-4 w-4" />
                Domain Focus
              </CardTitle>
              <CardDescription>
                Select the areas where you want to emphasize your expertise
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                {DOMAIN_OPTIONS.map((domain) => {
                  const Icon = domain.icon;
                  return (
                    <div
                      key={domain.value}
                      className={`flex items-center space-x-2 p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedDomains.includes(domain.value)
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/50"
                      }`}
                      onClick={() => handleDomainToggle(domain.value)}
                    >
                      <Checkbox
                        checked={selectedDomains.includes(domain.value)}
                        onChange={() => handleDomainToggle(domain.value)}
                      />
                      <Icon className="h-4 w-4" />
                      <span className="text-sm font-medium">
                        {domain.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Skills Highlighting */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Code className="h-4 w-4" />
                Skills to Highlight
              </CardTitle>
              <CardDescription>
                List the top skills you want prominently featured
                (comma-separated)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Input
                placeholder="e.g., Python, React, AWS, Machine Learning"
                value={topSkills}
                onChange={(e) => setTopSkills(e.target.value)}
              />
              {topSkills && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {topSkills
                    .split(",")
                    .map((skill) => skill.trim())
                    .filter(Boolean)
                    .map((skill) => (
                      <Badge key={skill} variant="secondary">
                        {skill}
                      </Badge>
                    ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Section Filtering */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Content Sections</CardTitle>
              <CardDescription>
                Optionally include or exclude specific sections from your resume
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-sm font-medium text-green-700">
                  Include Only These Sections
                </Label>
                <div className="flex flex-wrap gap-2 mt-2">
                  {[
                    "experience",
                    "education",
                    "projects",
                    "leadership_activities",
                    "technical_skills",
                    "languages",
                  ].map((section) => (
                    <div key={section} className="flex items-center space-x-2">
                      <Checkbox
                        checked={includeSections.includes(section)}
                        onCheckedChange={() =>
                          handleSectionToggle(section, "include")
                        }
                      />
                      <Label className="text-sm capitalize">
                        {section.replace("_", " ")}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>

              <Separator />

              <div>
                <Label className="text-sm font-medium text-red-700">
                  Exclude These Sections
                </Label>
                <div className="flex flex-wrap gap-2 mt-2">
                  {[
                    "experience",
                    "education",
                    "projects",
                    "leadership_activities",
                    "technical_skills",
                    "languages",
                  ].map((section) => (
                    <div key={section} className="flex items-center space-x-2">
                      <Checkbox
                        checked={excludeSections.includes(section)}
                        onCheckedChange={() =>
                          handleSectionToggle(section, "exclude")
                        }
                      />
                      <Label className="text-sm capitalize">
                        {section.replace("_", " ")}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={
              isLoading ||
              ((mode === "create_preference" || mode === "edit_preference") &&
                !preferenceName.trim())
            }
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {mode === "create_preference"
              ? "Save Preference"
              : mode === "edit_preference"
                ? "Update Preference"
                : "Generate Optimized Resume"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
