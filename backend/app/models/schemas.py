"""
Data Schemas
Pydantic models for request/response validation and data structures
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# ============================================================================
# Job Description Models
# ============================================================================

class JDData(BaseModel):
    """Structured job description data"""
    
    role_title: str = Field(..., description="Job title/role")
    hard_skills: List[str] = Field(..., description="Required technical skills")
    key_responsibilities: List[str] = Field(..., description="Main job responsibilities")
    mirror_language: List[str] = Field(..., description="Keywords/phrases to mirror in resume")
    
    @field_validator('hard_skills', 'key_responsibilities', 'mirror_language', mode='before')
    @classmethod
    def ensure_list(cls, v: Any) -> List[str]:
        """Ensure field is always a list"""
        if isinstance(v, str):
            return [v]
        return v


# ============================================================================
# Resume Models
# ============================================================================

class PersonalInfo(BaseModel):
    """Personal information from resume"""
    
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    location: str = Field(..., description="Location/City")
    linkedin: Optional[str] = Field(default="", description="LinkedIn profile URL")


class Entry(BaseModel):
    """Generic entry for experience, education, or leadership"""
    
    company: Optional[str] = Field(None, description="Company name (for experience)")
    organization: Optional[str] = Field(None, description="Organization name (for leadership)")
    school: Optional[str] = Field(None, description="School name (for education)")
    role: Optional[str] = Field(None, description="Role/Position title")
    degree: Optional[str] = Field(None, description="Degree name (for education)")
    thesis: Optional[str] = Field(None, description="Thesis title (for education)")
    location: Optional[str] = Field(..., description="Location")
    dates: Optional[str] = Field(..., description="Date range")
    bullets: List[str] = Field(default_factory=list, description="Bullet points")


class PivotedBullet(BaseModel):
    """A bullet point that has been optimized for the job description"""
    
    original: str = Field(..., description="Original bullet point")
    suggested: str = Field(..., description="Optimized bullet point")
    reason: str = Field(..., description="Reason for the change")


class FullReconstruction(BaseModel):
    """Complete reconstructed resume"""
    
    experience: List[Entry] = Field(default_factory=list, description="Work experience entries")
    education: List[Entry] = Field(default_factory=list, description="Education entries")
    leadership_activities: List[Entry] = Field(default_factory=list, description="Leadership and activities")
    technical_skills: List[str] = Field(default_factory=list, description="Technical skills")
    languages: List[str] = Field(default_factory=list, description="Languages known")
    laboratory: List[str] = Field(default_factory=list, description="Laboratory skills")
    interests: List[str] = Field(default_factory=list, description="Personal interests")


class ResumeAlignment(BaseModel):
    """Complete resume alignment result"""
    
    personal_info: PersonalInfo = Field(..., description="Personal information")
    match_score: int = Field(..., ge=0, le=100, description="Match score (0-100)")
    pivoted_bullets: List[PivotedBullet] = Field(default_factory=list, description="Optimized bullet points")
    full_reconstruction: FullReconstruction = Field(..., description="Complete reconstructed resume")
    missing_skills: List[str] = Field(default_factory=list, description="Skills missing from resume")


# ============================================================================
# Request/Response Models
# ============================================================================

class UserResumeOverrides(BaseModel):
    """User-provided overrides for resume tailoring"""

    candidate_flow: Optional[str] = Field(None, description="Override candidate flow (e.g., 'mid-IC-engineering')")
    experience_years_estimate: Optional[float] = Field(None, description="Override years of experience")
    is_manager: Optional[bool] = Field(None, description="Override management status")
    domain_tags: Optional[List[str]] = Field(None, description="Override domain tags")
    top_skills: Optional[List[str]] = Field(None, description="Skills to highlight prominently")
    include_sections: Optional[List[str]] = Field(None, description="Sections to include (if not provided, use all)")
    exclude_sections: Optional[List[str]] = Field(None, description="Sections to exclude")


class FullAlignmentRequest(BaseModel):
    """Request for full resume alignment"""

    url: str = Field(..., description="Job posting URL")
    file_name: str = Field(..., description="Uploaded file name")
    overrides: Optional[UserResumeOverrides] = Field(None, description="User overrides for resume tailoring")


class FullAlignmentResponse(BaseModel):
    """Response from full resume alignment"""
    
    personal_info: PersonalInfo
    match_score: int
    pivoted_bullets: List[PivotedBullet]
    full_reconstruction: FullReconstruction
    missing_skills: List[str]
    r2_key: Optional[str] = Field(None, description="R2 storage key for generated PDF")


class HistoryRecord(BaseModel):
    """Resume history record"""
    
    id: str = Field(..., description="Record ID")
    user_id: str = Field(..., description="User UUID")
    job_url: str = Field(..., description="Job posting URL")
    role_title: str = Field(..., description="Job role title")
    r2_key: str = Field(..., description="R2 storage key")
    match_score: int = Field(..., description="Match score")
    created_at: datetime = Field(..., description="Creation timestamp")


class HistoryResponse(BaseModel):
    """Response containing user's resume history"""
    
    records: List[HistoryRecord] = Field(default_factory=list, description="History records")


class DownloadURLRequest(BaseModel):
    """Request for download URL generation"""
    
    r2_key: str = Field(..., description="R2 storage key")


class DownloadURLResponse(BaseModel):
    """Response containing presigned download URL"""

    download_url: str = Field(..., description="Presigned download URL")
    expires_in: int = Field(..., description="URL expiry time in seconds")


class ResumePreference(BaseModel):
    """User resume preference profile"""

    id: str = Field(..., description="Preference ID")
    user_id: str = Field(..., description="User UUID")
    name: str = Field(..., description="Preference profile name")
    preferences: UserResumeOverrides = Field(..., description="Resume tailoring preferences")
    is_default: bool = Field(default=False, description="Whether this is the default preference")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CreatePreferenceRequest(BaseModel):
    """Request to create a new preference"""

    name: str = Field(..., description="Preference profile name")
    preferences: UserResumeOverrides = Field(..., description="Resume tailoring preferences")
    is_default: Optional[bool] = Field(default=False, description="Set as default preference")


class UpdatePreferenceRequest(BaseModel):
    """Request to update a preference"""

    name: Optional[str] = Field(None, description="New preference profile name")
    preferences: Optional[UserResumeOverrides] = Field(None, description="Updated preferences")
    is_default: Optional[bool] = Field(None, description="Update default status")


class PreferencesResponse(BaseModel):
    """Response containing user's preferences"""

    preferences: List[ResumePreference] = Field(default_factory=list, description="User's preference profiles")


# ============================================================================
# Error Response Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    error_type: Optional[str] = Field(None, description="Type of error")
    details: Optional[dict] = Field(None, description="Additional error details")