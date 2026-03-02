"""
Configuration Management
Pydantic-based settings for type-safe configuration
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Supabase Configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase anon/public key")
    
    # OpenRouter AI Configuration
    openrouter_api_key: str = Field(..., description="OpenRouter API key for AI models")
    
    # Cloudflare R2 Configuration
    r2_account_id: str = Field(..., description="Cloudflare R2 account ID")
    r2_access_key_id: str = Field(..., description="R2 access key ID")
    r2_secret_access_key: str = Field(..., description="R2 secret access key")
    r2_bucket_name: str = Field(default="resume-agent-pdfs", description="R2 bucket name")
    
    # Application Configuration
    backend_url: str = Field(default="https://api.resume.marwanalytech.com", description="Backend URL")
    environment: str = Field(default="development", description="Environment (development/production)")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # AI Model Configuration
    ai_model: str = Field(default="google/gemini-3-flash-preview", description="AI model name")
    ai_temperature: float = Field(default=0.1, description="AI model temperature")
    ai_max_tokens: int = Field(default=4000, description="AI model max tokens")
    
    # PDF Generation Configuration
    pdf_page_size: str = Field(default="Letter", description="PDF page size")
    pdf_margin_top: str = Field(default="0.50in", description="PDF top margin")
    pdf_margin_bottom: str = Field(default="0.19in", description="PDF bottom margin")
    pdf_margin_left: str = Field(default="0.42in", description="PDF left margin")
    pdf_margin_right: str = Field(default="0.42in", description="PDF right margin")
    
    # JWT Configuration
    jwt_algorithms: list[str] = Field(default=["RS256", "ES256"], description="JWT algorithms")
    jwt_audience: str = Field(default="authenticated", description="JWT audience")
    
    # CORS Configuration
    cors_origins: list[str] = Field(
        default=[
            "https://resumeagent.marwanalytech.com",
            "https://resume.marwanalytech.com",
            "http://localhost:5173",
            "http://localhost:3000"
        ], 
        description="CORS allowed origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="CORS allow credentials")
    cors_allow_methods: list[str] = Field(default=["*"], description="CORS allowed methods")
    cors_allow_headers: list[str] = Field(default=["*"], description="CORS allowed headers")
    
    # Download URL Configuration
    download_url_expiry: int = Field(default=3600, description="Download URL expiry in seconds")
    
    # Temporary Files Configuration
    temp_directory: str = Field(default="/tmp/resume-generator", description="Temporary directory for PDF generation")
    
    @property
    def jwks_url(self) -> str:
        """Get JWKS URL for JWT validation"""
        return f"{self.supabase_url}/auth/v1/.well-known/jwks.json"
    
    @property
    def r2_endpoint_url(self) -> str:
        """Get R2 endpoint URL"""
        return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment.lower() == "production"


# Global settings instance
settings = Settings()
