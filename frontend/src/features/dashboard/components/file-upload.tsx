import { useState, useCallback } from "react";
import { useDropzone, FileRejection } from "react-dropzone";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Upload, FileText, X } from "lucide-react";
import { apiService, AlignmentResult, ResumePreference } from "@/lib/api";
import { toast } from "sonner";

interface FileUploadProps {
  jobUrl: string;
  onProcessing: (processing: boolean) => void;
  onResults: (results: AlignmentResult) => void;
  disabled: boolean;
  defaultPreference?: ResumePreference | null;
}

export function FileUpload({
  jobUrl,
  onProcessing,
  onResults,
  disabled,
  defaultPreference,
}: FileUploadProps) {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setUploadedFile(acceptedFiles[0]);
    }
  }, []);

  const onDropRejected = useCallback((fileRejections: FileRejection[]) => {
    console.log("File rejected:", fileRejections);
    toast.error("Only PDF files are accepted. Please upload a valid PDF file.");
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    onDropRejected,
    accept: {
      "application/pdf": [".pdf"],
    },
    multiple: false,
    disabled: disabled || isProcessing,
  });

  const handleAlignResume = async () => {
    if (!uploadedFile || !jobUrl) {
      console.error("Missing required data:", {
        uploadedFile: !!uploadedFile,
        jobUrl: !!jobUrl,
      });
      return;
    }

    setIsProcessing(true);
    onProcessing(true);

    try {
      console.log("Making API call...");
      let results: AlignmentResult;

      if (defaultPreference) {
        // Use default preference directly - single API call
        console.log("Using default preference for alignment");
        results = await apiService.alignResumeWithOverrides(
          jobUrl,
          uploadedFile,
          defaultPreference.preferences,
        );
      } else {
        // No default preference - use basic alignment
        results = await apiService.alignResume(jobUrl, uploadedFile);
      }

      console.log("API call successful:", results);
      onResults(results);
    } catch (error) {
      console.error("Alignment failed:", error);
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to align resume. Please try again.";
      toast.error(errorMessage);
    } finally {
      setIsProcessing(false);
      onProcessing(false);
    }
  };

  const removeFile = () => {
    setUploadedFile(null);
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-medium">Resume PDF</label>
        {!uploadedFile ? (
          <Card
            className={`border-2 border-dashed transition-colors ${
              isDragActive
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25"
            } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
          >
            <CardContent className="flex flex-col items-center justify-center py-8">
              <div {...getRootProps()}>
                <input {...getInputProps()} />
                <Upload className="w-8 h-8 text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground text-center">
                  {isDragActive
                    ? "Drop your resume PDF here"
                    : "Drag & drop your resume PDF here, or click to select"}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Only PDF files are supported
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="flex items-center justify-between py-4">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-primary" />
                <div>
                  <p className="text-sm font-medium">{uploadedFile.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={removeFile}
                disabled={disabled || isProcessing}
              >
                <X className="w-4 h-4" />
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      <Button
        onClick={handleAlignResume}
        disabled={!uploadedFile || !jobUrl || disabled || isProcessing}
        className="w-full"
        size="lg"
      >
        {isProcessing ? "🚀 Optimizing..." : "🚀 Align Resume"}
      </Button>
    </div>
  );
}
