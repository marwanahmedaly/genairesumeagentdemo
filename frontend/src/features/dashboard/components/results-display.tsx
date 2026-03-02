import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Download, CheckCircle, AlertCircle, Target, Copy } from 'lucide-react'
import { AlignmentResult } from '@/lib/api'
import { toast } from 'sonner'
import { Skeleton } from '@/components/ui/skeleton'

export function ResultsSkeleton() {
  return (
    <div className="space-y-6">
      {/* Match Score Skeleton */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent>
          <div className="text-center">
            <Skeleton className="h-16 w-24 mx-auto mb-2" />
            <Skeleton className="h-4 w-32 mx-auto" />
          </div>
        </CardContent>
      </Card>

      {/* Missing Skills Skeleton */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-6 w-20" />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Suggested Improvements Skeleton */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 2 }).map((_, index) => (
              <div key={index} className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Download Button Skeleton */}
      <Card>
        <CardContent className="pt-6">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-3 w-48 mx-auto mt-2" />
        </CardContent>
      </Card>
    </div>
  )
}

interface ResultsDisplayProps {
  results: AlignmentResult
  onDownload: () => void
  isDownloading?: boolean
}

export function ResultsDisplay({ results, onDownload, isDownloading = false }: ResultsDisplayProps) {
  const getMatchScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-700 dark:text-green-300'
    if (score >= 60) return 'text-amber-700 dark:text-amber-300'
    return 'text-red-700 dark:text-red-300'
  }

  const getMatchScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800'
    if (score >= 60) return 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800'
    return 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800'
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success('Copied to clipboard!')
    } catch (error) {
      console.error('Failed to copy:', error)
      toast.error('Failed to copy to clipboard')
    }
  }

  return (
    <div className="space-y-6">
      {/* Match Score */}
      <Card className={getMatchScoreBg(results.match_score)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            Match Score
          </CardTitle>
          <CardDescription>
            How well your resume aligns with the job requirements
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center">
            <div className={`text-6xl font-bold ${getMatchScoreColor(results.match_score)}`}>
              {results.match_score}%
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              {results.match_score >= 80 ? 'Excellent match!' :
               results.match_score >= 60 ? 'Good match' :
               'Needs improvement'}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Missing Skills */}
      {results.missing_skills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-600">
              <AlertCircle className="w-5 h-5" />
              Missing Skills
            </CardTitle>
            <CardDescription>
              Skills mentioned in the job posting but not found in your resume
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {results.missing_skills.map((skill, index) => (
                <Badge key={index} variant="outline" className="text-orange-700 border-orange-300">
                  {skill}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Suggested Improvements */}
      {results.pivoted_bullets.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-600">
              <CheckCircle className="w-5 h-5" />
              Suggested Improvements
            </CardTitle>
            <CardDescription>
              AI-recommended changes to better align your resume
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {results.pivoted_bullets.map((bullet, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                    <div className="flex-1 space-y-2">
                      <div className="text-sm text-muted-foreground">
                        <strong>Original:</strong> {bullet.original}
                      </div>
                      <Separator />
                      <div className="text-sm text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-950/20 p-2 rounded border flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <strong>Suggested:</strong> {bullet.suggested}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 hover:bg-green-100 dark:hover:bg-green-900/30"
                          onClick={() => copyToClipboard(bullet.suggested)}
                        >
                          <Copy className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                  {index < results.pivoted_bullets.length - 1 && <Separator />}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Download Button */}
      <Card>
        <CardContent className="pt-6">
          <Button
            onClick={onDownload}
            disabled={isDownloading}
            className="w-full"
            size="lg"
          >
            <Download className="w-4 h-4 mr-2" />
            {isDownloading ? 'Downloading...' : 'Download Optimized Resume'}
          </Button>
          <p className="text-xs text-muted-foreground text-center mt-2">
            {isDownloading ? 'Preparing download...' : 'Your optimized resume is ready for download'}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}