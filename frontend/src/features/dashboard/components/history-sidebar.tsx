import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { RefreshCw, Download, History, Trash2, Search } from "lucide-react";
import { HistoryItem, apiService } from "@/lib/api";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";

interface HistorySidebarProps {
  refreshTrigger?: number;
}

export function HistorySidebar({ refreshTrigger = 0 }: HistorySidebarProps) {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [filteredHistory, setFilteredHistory] = useState<HistoryItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [deletingItems, setDeletingItems] = useState<Set<string>>(new Set());
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const historyData = await apiService.getHistory();
      setHistory(historyData);
    } catch (error) {
      console.error("Failed to fetch history:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDownload = async (r2Key: string, itemId: string) => {
    setDownloading(itemId);
    try {
      const { download_url } = await apiService.getDownloadUrl(r2Key);
      window.open(download_url, "_blank");
    } catch (error) {
      console.error("Download failed:", error);
      toast.error("Failed to download resume. Please try again.");
    } finally {
      setDownloading(null);
    }
  };

  const handleDelete = async (itemId: string) => {
    setDeleteTarget(itemId);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;

    const isBulkDelete = selectedItems.has(deleteTarget);
    const itemsToDelete = isBulkDelete
      ? Array.from(selectedItems)
      : [deleteTarget];

    // Add items to deleting set for visual feedback
    setDeletingItems(new Set(itemsToDelete));
    setDeleteDialogOpen(false);

    // Optimistically remove items from UI
    setHistory((prev) =>
      prev.filter((item) => !itemsToDelete.includes(item.id)),
    );
    setSelectedItems(new Set());

    try {
      // Delete all selected items using allSettled to continue even if some fail
      const results = await Promise.allSettled(
        itemsToDelete.map((id) => apiService.deleteResume(id)),
      );

      // Check for failures
      const failures = results.filter((r) => r.status === "rejected");

      if (failures.length > 0) {
        console.error(`${failures.length} delete(s) failed:`, failures);

        // Refresh history to show accurate state
        try {
          const freshHistory = await apiService.getHistory();
          setHistory(freshHistory);
        } catch (fetchError) {
          console.error(
            "Failed to refresh history after partial delete:",
            fetchError,
          );
        }

        if (failures.length === itemsToDelete.length) {
          toast.error(
            "Failed to delete all selected resumes. Please try again.",
          );
        } else {
          toast.warning(
            `Deleted ${results.length - failures.length} of ${itemsToDelete.length} resumes. ${failures.length} failed.`,
          );
        }
      } else {
        toast.success(
          `Successfully deleted ${itemsToDelete.length} ${itemsToDelete.length > 1 ? "resumes" : "resume"}`,
        );
      }
    } catch (error) {
      console.error("Unexpected error during delete:", error);

      // Revert optimistic update
      try {
        const freshHistory = await apiService.getHistory();
        setHistory(freshHistory);
      } catch (fetchError) {
        console.error("Failed to refresh history after error:", fetchError);
      }

      toast.error("An unexpected error occurred. Please try again.");
    } finally {
      setDeletingItems(new Set());
      setDeleteTarget(null);
    }
  };

  const handleSelectItem = (itemId: string, checked: boolean) => {
    setSelectedItems((prev) => {
      const newSet = new Set(prev);
      if (checked) {
        newSet.add(itemId);
      } else {
        newSet.delete(itemId);
      }
      return newSet;
    });
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedItems(new Set(history.map((item) => item.id)));
    } else {
      setSelectedItems(new Set());
    }
  };

  const handleBulkDelete = () => {
    if (selectedItems.size === 0) return;
    setDeleteTarget(Array.from(selectedItems)[0]); // Just for dialog trigger
    setDeleteDialogOpen(true);
  };

  const allSelected =
    history.length > 0 && selectedItems.size === history.length;

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory, refreshTrigger]);

  useEffect(() => {
    if (searchQuery.trim() === "") {
      setFilteredHistory(history);
    } else {
      const filtered = history.filter(
        (item) =>
          item.role_title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          new Date(item.created_at)
            .toLocaleDateString()
            .toLowerCase()
            .includes(searchQuery.toLowerCase()),
      );
      setFilteredHistory(filtered);
    }
  }, [history, searchQuery]);

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="border-b space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Checkbox
              checked={allSelected}
              onCheckedChange={handleSelectAll}
              className="data-[state=checked]:bg-primary data-[state=checked]:border-primary"
            />
            <div>
              <CardTitle className="flex items-center gap-2">History</CardTitle>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {selectedItems.size > 0 && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleBulkDelete}
                disabled={deletingItems.size > 0}
              >
                <Trash2 className="w-3 h-3 mr-2" />
                Delete ({selectedItems.size})
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={fetchHistory}
              disabled={loading}
            >
              <RefreshCw
                className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
              />
            </Button>
          </div>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by role or date..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto scrollbar-thin py-3 px-3">
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <Card key={index} className="border">
                <CardContent className="p-3">
                  <div className="space-y-2">
                    <div className="flex items-start gap-2">
                      <Skeleton className="w-4 h-4 rounded" />
                      <div className="flex-1 space-y-1">
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-3 w-1/2" />
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Skeleton className="h-8 flex-1" />
                      <Skeleton className="h-8 w-8" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : history.length === 0 ? (
          <div className="text-center py-8">
            <History className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">No history yet</p>
            <p className="text-xs text-muted-foreground mt-1">
              Your completed optimizations will appear here
            </p>
          </div>
        ) : filteredHistory.length === 0 ? (
          <div className="text-center py-8">
            <Search className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">No matches found</p>
            <p className="text-xs text-muted-foreground mt-1">
              Try adjusting your search terms
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredHistory.map((item) => (
              <Card key={item.id} className="border">
                <CardContent className="p-3">
                  <div className="space-y-2">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Checkbox
                          checked={selectedItems.has(item.id)}
                          onCheckedChange={(checked) =>
                            handleSelectItem(item.id, checked as boolean)
                          }
                          className="data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium">
                            {item.role_title || "Resume Optimization"}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(item.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleDownload(item.r2_key, item.id)}
                        disabled={downloading === item.id}
                      >
                        <Download className="w-3 h-3 mr-2" />
                        {downloading === item.id ? "Downloading..." : "Get PDF"}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="px-3"
                        onClick={() => handleDelete(item.id)}
                        disabled={deletingItems.has(item.id)}
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </CardContent>

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Delete Resume{selectedItems.size > 1 ? "s" : ""}
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete{" "}
              {selectedItems.size > 1
                ? `these ${selectedItems.size} resumes`
                : "this resume"}
              ? This action cannot be undone and will permanently remove the
              resume{selectedItems.size > 1 ? "s" : ""} from your history and
              storage.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              disabled={deletingItems.size > 0}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDelete}
              disabled={deletingItems.size > 0}
            >
              {deletingItems.size > 0 ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
