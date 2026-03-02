import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Link, ExternalLink } from 'lucide-react'

interface JobPostingInputProps {
  jobUrl: string
  onJobUrlChange: (url: string) => void
  disabled: boolean
}

export function JobPostingInput({ jobUrl, onJobUrlChange, disabled }: JobPostingInputProps) {
  const [inputValue, setInputValue] = useState(jobUrl)

  const handleInputChange = (value: string) => {
    setInputValue(value)
    onJobUrlChange(value)
  }

  const isValidUrl = (url: string) => {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  const handleOpenUrl = () => {
    if (jobUrl && isValidUrl(jobUrl)) {
      window.open(jobUrl, '_blank')
    }
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Link className="w-5 h-5 text-primary" />
            <Label htmlFor="job-url" className="text-base font-medium">
              Job Posting URL
            </Label>
          </div>

          <div className="flex gap-2">
            <div className="flex-1">
              <Input
                id="job-url"
                type="url"
                placeholder="https://example.com/job-posting"
                value={inputValue}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange(e.target.value)}
                disabled={disabled}
                className="pr-10"
              />
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={handleOpenUrl}
              disabled={!jobUrl || !isValidUrl(jobUrl)}
              title="Open job posting in new tab"
            >
              <ExternalLink className="w-4 h-4" />
            </Button>
          </div>

          <div className="text-sm text-muted-foreground">
            <p>
              Paste the URL of the job posting you want to optimize your resume for.
              The AI will analyze the job requirements and suggest improvements to your resume.
            </p>
          </div>

          {jobUrl && !isValidUrl(jobUrl) && (
            <div className="text-sm text-orange-600 bg-orange-50 p-2 rounded border border-orange-200">
              Please enter a valid URL
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}