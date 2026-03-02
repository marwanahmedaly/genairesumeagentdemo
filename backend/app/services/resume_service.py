"""
Resume Service
Business logic for resume alignment operations
"""

import os
import pdfplumber
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from crawl4ai import AsyncWebCrawler
from ..core.logger import get_logger
from ..core.exceptions import ScrapingError, ValidationError, AIServiceError
from ..models.schemas import JDData, ResumeAlignment
from ..utils.normalizer import ResumeNormalizer

logger = get_logger(__name__)


class JDCache:
    """
    Simple in-memory cache for job description data
    Caches scraped markdown and extracted JD data to avoid redundant AI calls
    """

    def __init__(self, max_age_minutes: int = 60):
        self._cache = {}
        self._max_age = timedelta(minutes=max_age_minutes)

    def _is_expired(self, timestamp: datetime) -> bool:
        return datetime.utcnow() - timestamp > self._max_age

    def get_scraped_content(self, url: str) -> Optional[str]:
        """Get cached scraped markdown content for URL"""
        if url in self._cache:
            entry = self._cache[url]
            if not self._is_expired(entry['timestamp']):
                logger.debug(f"Cache hit for scraped content: {url}")
                return entry['markdown']
            else:
                logger.debug(f"Cache expired for scraped content: {url}")
                del self._cache[url]
        return None

    def set_scraped_content(self, url: str, markdown: str):
        """Cache scraped markdown content for URL"""
        self._cache[url] = {
            'markdown': markdown,
            'timestamp': datetime.utcnow(),
            'type': 'scraped'
        }
        logger.debug(f"Cached scraped content for: {url}")

    def get_extracted_data(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached extracted JD data for URL"""
        cache_key = f"extracted_{url}"
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if not self._is_expired(entry['timestamp']):
                logger.debug(f"Cache hit for extracted data: {url}")
                return entry['data']
            else:
                logger.debug(f"Cache expired for extracted data: {url}")
                del self._cache[cache_key]
        return None

    def set_extracted_data(self, url: str, data: Dict[str, Any]):
        """Cache extracted JD data for URL"""
        cache_key = f"extracted_{url}"
        self._cache[cache_key] = {
            'data': data,
            'timestamp': datetime.utcnow(),
            'type': 'extracted'
        }
        logger.debug(f"Cached extracted data for: {url}")


# Global cache instance
jd_cache = JDCache()


class ResumeService:
    """
    Service for resume alignment and processing operations
    """
    
    @staticmethod
    async def scrape_job_description(url: str) -> str:
        """
        Scrape job description from URL with caching

        Args:
            url: Job posting URL

        Returns:
            Job description as markdown string

        Raises:
            ScrapingError: If scraping fails
        """
        # Check cache first
        cached_content = jd_cache.get_scraped_content(url)
        if cached_content:
            return cached_content

        try:
            logger.info(f"Scraping job description from: {url}")

            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)

                if not result.markdown:
                    raise ScrapingError(
                        message="No content found at provided URL",
                        details={"url": url}
                    )

                logger.info(f"Successfully scraped job description from: {url}")

                # Cache the result
                jd_cache.set_scraped_content(url, result.markdown)

                return result.markdown

        except ScrapingError:
            raise
        except Exception as e:
            logger.error(f"Failed to scrape job description: {str(e)}")
            raise ScrapingError(
                message="Failed to scrape job description",
                details={"url": url, "error": str(e)}
            )
    
    @staticmethod
    def extract_resume_text(pdf_path: str) -> str:
        """
        Extract text from PDF resume
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text as string
            
        Raises:
            ValidationError: If PDF extraction fails
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            raise ValidationError(
                message="PDF file not found",
                details={"pdf_path": pdf_path}
            )
        
        try:
            logger.info(f"Extracting text from PDF: {pdf_path}")
            
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )
                
                if not text.strip():
                    raise ValidationError(
                        message="No text found in PDF",
                        details={"pdf_path": pdf_path}
                    )
                
                logger.info(f"Successfully extracted text from PDF: {pdf_path}")
                return text
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {str(e)}")
            # Check if it's a PDF parsing error (corrupted or invalid PDF)
            error_msg = str(e).lower()
            if 'pdf' in error_msg or 'invalid' in error_msg or 'corrupt' in error_msg:
                raise ValidationError(
                    message="Invalid or corrupted PDF file. Please upload a valid PDF file.",
                    details={"pdf_path": pdf_path, "error": str(e)}
                )
            raise ValidationError(
                message="Failed to extract text from PDF",
                details={"pdf_path": pdf_path, "error": str(e)}
            )
    
    @staticmethod
    def extract_jd_data(jd_markdown: str) -> JDData:
        """
        Extract structured data from job description markdown
        
        Args:
            jd_markdown: Job description as markdown string
            
        Returns:
            Structured JDData object
            
        Raises:
            AIServiceError: If AI extraction fails
        """
        from ..agents.extraction_agent import ExtractionAgent
        
        try:
            logger.info("Extracting JD data using AI agent")
            agent = ExtractionAgent()
            jd_dict = agent.extract_jd_data(jd_markdown)
            return JDData(**jd_dict)
        except Exception as e:
            logger.error(f"Failed to extract JD data: {str(e)}")
            raise
    
    @staticmethod
    def align_resume_to_jd(resume_text: str, jd_data: JDData) -> ResumeAlignment:
        """
        Align resume to job description using AI
        
        Args:
            resume_text: Resume text
            jd_data: Structured job description data
            
        Returns:
            ResumeAlignment object with match score and optimizations
            
        Raises:
            AIServiceError: If AI alignment fails
        """
        from ..agents.alignment_agent import AlignmentAgent
        
        try:
            logger.info("Aligning resume to job description")
            agent = AlignmentAgent()
            alignment_dict = agent.align_resume_to_jd(resume_text, jd_data.model_dump())
            return ResumeAlignment(**alignment_dict)
        except Exception as e:
            logger.error(f"Failed to align resume to JD: {str(e)}")
            raise
    
    @staticmethod
    async def process_resume_alignment(
        url: str,
        pdf_path: str,
        overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process complete resume alignment workflow

        This orchestrates the entire alignment process:
        1. Scrape job description
        2. Extract resume text
        3. Extract JD data (AI) - with caching
        4. Align resume to JD (AI)

        Args:
            url: Job posting URL
            pdf_path: Path to uploaded PDF resume

        Returns:
            Dictionary containing alignment results

        Raises:
            ScrapingError: If scraping fails
            ValidationError: If PDF extraction fails
            AIServiceError: If AI operations fail
        """
        logger.info(f"Starting resume alignment process for URL: {url}")

        # Step 1: Scrape job description
        jd_markdown = await ResumeService.scrape_job_description(url)

        # Step 2: Extract resume text
        resume_text = ResumeService.extract_resume_text(pdf_path)

        # Step 3: Extract JD data (AI) - with caching
        # Check cache first
        cached_jd_data = jd_cache.get_extracted_data(url)
        if cached_jd_data:
            jd_data = JDData(**cached_jd_data)
        else:
            jd_data = ResumeService.extract_jd_data(jd_markdown)
            # Cache the extracted data
            jd_cache.set_extracted_data(url, jd_data.model_dump())

        # Step 4: Align resume to JD (AI)
        alignment = ResumeService.align_resume_to_jd(resume_text, jd_data)

        # Add role title to result for filename generation
        result = alignment.model_dump()
        result['role_title'] = jd_data.role_title

        # Normalize result for dynamic template rendering
        result = ResumeService._normalize_alignment(result, overrides)

        logger.info("Resume alignment process completed successfully")

        return result

    @staticmethod
    def _normalize_alignment(alignment_result: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Normalize alignment result for dynamic template rendering

        Args:
            alignment_result: Raw alignment result dictionary
            overrides: User-provided overrides for tailoring

        Returns:
            Normalized result with sections and candidate_flow
        """
        try:
            full_reconstruction = alignment_result.get('full_reconstruction', {})

            # Use auto-detected values as defaults, override with user preferences
            overrides = overrides or {}

            # Estimate years of experience (use override if provided)
            experience_entries = full_reconstruction.get('experience', [])
            years_experience = overrides.get('experience_years_estimate')
            if years_experience is None:
                years_experience = ResumeNormalizer.estimate_years_experience(experience_entries)

            # Detect management experience (use override if provided)
            is_manager = overrides.get('is_manager')
            if is_manager is None:
                is_manager = ResumeNormalizer.detect_is_manager(experience_entries)

            # Infer domain tags (use override if provided)
            domain_tags = overrides.get('domain_tags')
            if domain_tags is None:
                technical_skills = full_reconstruction.get('technical_skills', [])
                domain_tags = ResumeNormalizer.infer_domain_tags(technical_skills, experience_entries)

            # Determine candidate flow (use override if provided)
            candidate_flow = overrides.get('candidate_flow')
            if candidate_flow is None:
                candidate_flow = ResumeNormalizer.determine_candidate_flow(
                    years_experience, is_manager, domain_tags
                )

            # Normalize sections
            sections = ResumeNormalizer.normalize_sections(full_reconstruction)

            # Apply section filtering if specified in overrides
            if overrides.get('include_sections'):
                sections = [s for s in sections if s['key'] in overrides['include_sections']]
            if overrides.get('exclude_sections'):
                sections = [s for s in sections if s['key'] not in overrides['exclude_sections']]

            # Add normalized data to result
            alignment_result['candidate_flow'] = candidate_flow
            alignment_result['experience_years_estimate'] = years_experience
            alignment_result['is_manager'] = is_manager
            alignment_result['domain_tags'] = domain_tags
            alignment_result['sections'] = sections

            # Add suggested overrides for UI display
            alignment_result['suggested_overrides'] = {
                'candidate_flow': candidate_flow,
                'experience_years_estimate': years_experience,
                'is_manager': is_manager,
                'domain_tags': domain_tags,
                'top_skills': overrides.get('top_skills', full_reconstruction.get('technical_skills', [])[:5])
            }

            logger.debug(f"Normalized alignment for flow: {candidate_flow}, sections: {len(sections)}")

            return alignment_result

        except Exception as e:
            logger.warning(f"Failed to normalize alignment result: {str(e)}")
            # Return original result if normalization fails
            return alignment_result

    @staticmethod
    def delete_resume_record(user_id: str, record_id: str) -> bool:
        """
        Delete a resume record and its associated PDF from storage

        Args:
            user_id: User's UUID
            record_id: Record UUID to delete

        Returns:
            True if successfully deleted

        Raises:
            DatabaseError: If database operation fails
            StorageError: If storage operation fails
        """
        from .storage_service import StorageService
        from ..repositories.resume_repository import ResumeRepository

        logger.info(f"Deleting resume record {record_id} for user {user_id}")

        # Get the record to find the R2 key
        repo = ResumeRepository()
        record = repo.get_resume_by_id(record_id)

        # Verify ownership
        if record['user_id'] != user_id:
            logger.warning(f"Ownership check failed: user {user_id} does not own record {record_id}")
            return False

        # Delete the PDF from storage
        storage_service = StorageService()
        if record.get('r2_key'):
            try:
                storage_service.delete_pdf(record['r2_key'])
                logger.info(f"Deleted PDF from storage: {record['r2_key']}")
            except Exception as e:
                logger.error(f"Failed to delete PDF from storage: {str(e)}")
                # Continue with record deletion even if storage deletion fails

        # Delete the record from database
        deleted = repo.delete_user_resume(user_id, record_id)

        if deleted:
            logger.info(f"Successfully deleted resume record {record_id}")
        else:
            logger.warning(f"Failed to delete resume record {record_id}")

        return deleted

    @staticmethod
    def cleanup_temp_files(*file_paths: str) -> None:
        """
        Clean up temporary files

        Args:
            *file_paths: Variable number of file paths to delete
        """
        for file_path in file_paths:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up file {file_path}: {str(e)}")
