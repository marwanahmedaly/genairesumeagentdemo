import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import {
  Loader2,
  Settings,
  Star,
  Trash2,
  Plus,
  Pencil,
  Check,
  X,
} from "lucide-react";
import { apiService, ResumePreference } from "@/lib/api";
import { toast } from "sonner";

interface PreferencesPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onPreferenceSelect?: (preference: ResumePreference | null) => void;
  onCreatePreference?: () => void;
  onDefaultChanged?: () => void;
}

export function PreferencesPanel({
  isOpen,
  onClose,
  onPreferenceSelect,
  onCreatePreference,
  onDefaultChanged,
}: PreferencesPanelProps) {
  const [preferences, setPreferences] = useState<ResumePreference[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingPreferenceId, setEditingPreferenceId] = useState<string | null>(
    null,
  );
  const [editingName, setEditingName] = useState("");
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadPreferences();
    }
  }, [isOpen]);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const prefs = await apiService.getUserPreferences();
      setPreferences(prefs);
    } catch (error) {
      console.error("Failed to load preferences:", error);
      toast.error("Failed to load preferences");
    } finally {
      setLoading(false);
    }
  };

  const handleSetDefault = async (preferenceId: string) => {
    try {
      await apiService.setDefaultPreference(preferenceId);
      toast.success("Default preference updated");
      await loadPreferences();
      onDefaultChanged?.();
    } catch (error) {
      console.error("Failed to set default:", error);
      toast.error("Failed to update default preference");
    }
  };

  const confirmDelete = async () => {
    if (!deleteConfirmId) return;

    try {
      await apiService.deletePreference(deleteConfirmId);
      toast.success("Preference deleted");
      setDeleteConfirmId(null);
      await loadPreferences();
      onDefaultChanged?.(); // Notify parent to refresh default preference display
    } catch (error) {
      console.error("Failed to delete preference:", error);
      toast.error("Failed to delete preference");
    }
  };

  const startEditingName = (preference: ResumePreference) => {
    setEditingPreferenceId(preference.id);
    setEditingName(preference.name);
  };

  const cancelEditingName = () => {
    setEditingPreferenceId(null);
    setEditingName("");
  };

  const savePreferenceName = async (preference: ResumePreference) => {
    if (!editingName.trim()) {
      toast.error("Preference name cannot be empty");
      return;
    }

    try {
      await apiService.updatePreference(
        preference.id,
        editingName.trim(),
        preference.preferences,
      );
      toast.success("Preference name updated");
      setEditingPreferenceId(null);
      setEditingName("");
      await loadPreferences();
      onDefaultChanged?.();
    } catch (error) {
      console.error("Failed to update preference name:", error);
      toast.error("Failed to update preference name");
    }
  };

  const formatPreferenceSummary = (pref: ResumePreference) => {
    const parts = [];
    if (pref.preferences.candidate_flow) {
      parts.push(`Flow: ${pref.preferences.candidate_flow}`);
    }
    if (pref.preferences.experience_years_estimate) {
      parts.push(`${pref.preferences.experience_years_estimate} years`);
    }
    if (pref.preferences.domain_tags?.length) {
      parts.push(
        `Domains: ${pref.preferences.domain_tags.slice(0, 2).join(", ")}`,
      );
    }
    return parts.join(" • ") || "Default settings";
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Resume Preferences
            </DialogTitle>
            <DialogDescription>
              Manage your resume tailoring preferences. Create different
              profiles for different career paths or job types.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : preferences.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-8">
                  <Settings className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">
                    No preferences yet
                  </h3>
                  <p className="text-sm text-muted-foreground text-center mb-4">
                    Create your first preference profile to customize how your
                    resume is tailored for different job applications.
                  </p>
                  <Button onClick={() => onCreatePreference?.()}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create First Preference
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {preferences.map((preference) => (
                  <Card
                    key={preference.id}
                    className={`relative ${preference.is_default ? "border-primary bg-primary/5" : ""}`}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 flex-1">
                          {editingPreferenceId === preference.id ? (
                            <div className="flex items-center gap-2 flex-1">
                              <Input
                                value={editingName}
                                onChange={(e) => setEditingName(e.target.value)}
                                className="h-8 text-base"
                                autoFocus
                                onKeyDown={(e) => {
                                  if (e.key === "Enter")
                                    savePreferenceName(preference);
                                  if (e.key === "Escape") cancelEditingName();
                                }}
                              />
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => savePreferenceName(preference)}
                                className="h-8 w-8 p-0"
                              >
                                <Check className="h-4 w-4 text-green-600" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={cancelEditingName}
                                className="h-8 w-8 p-0"
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          ) : (
                            <>
                              <CardTitle className="text-base">
                                {preference.name}
                              </CardTitle>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => startEditingName(preference)}
                                className="h-6 w-6 p-0"
                              >
                                <Pencil className="h-3 w-3" />
                              </Button>
                            </>
                          )}
                          {preference.is_default && (
                            <Badge
                              variant="secondary"
                              className="flex items-center gap-1"
                            >
                              <Star className="h-3 w-3" />
                              Default
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          {!preference.is_default && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleSetDefault(preference.id)}
                            >
                              <Star className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setDeleteConfirmId(preference.id)}
                            className="text-destructive hover:text-destructive"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      <CardDescription className="text-sm">
                        {formatPreferenceSummary(preference)}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onPreferenceSelect?.(preference)}
                      >
                        Edit Settings
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            <Separator />

            <div className="flex justify-between">
              <Button variant="outline" onClick={onClose}>
                Close
              </Button>
              <Button onClick={() => onCreatePreference?.()}>
                <Plus className="h-4 w-4 mr-2" />
                Create New Preference
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={!!deleteConfirmId}
        onOpenChange={() => setDeleteConfirmId(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Preference</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this preference? This action
              cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setDeleteConfirmId(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDelete}>
              Delete
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
