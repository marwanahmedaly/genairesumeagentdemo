"""
PDF Generator
PDF generation from HTML templates using pdfkit and Jinja2
"""

import os
import uuid
import pdfkit
from jinja2 import Template
from typing import Optional, Dict, Any
from ..core.config import settings
from ..core.logger import get_logger
from ..core.exceptions import PDFGenerationError

logger = get_logger(__name__)


class PDFGenerator:
    """
    Generator for creating PDF resumes from HTML templates
    """
    
    def __init__(self, output_path: str = None):
        """
        Initialize PDF generator
        
        Args:
            output_path: Path where PDF will be saved (defaults to temp directory)
        """
        if output_path is None:
            # Use temp directory with unique filename
            temp_dir = settings.temp_directory
            os.makedirs(temp_dir, exist_ok=True)
            output_path = os.path.join(temp_dir, f"temp_{uuid.uuid4()}_Tailored_Resume.pdf")
        self.output_path = output_path
        self.template_path = "templates/harvard.html"
    
    def create_pdf(self, full_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate PDF from resume data
        
        Args:
            full_data: Dictionary containing resume data
            
        Returns:
            Path to generated PDF or None if failed
            
        Raises:
            PDFGenerationError: If PDF generation fails
        """
        try:
            # Step 1: Load HTML template
            template = self._load_template()
            
            # Step 2: Render HTML
            html_content = self._render_template(template, full_data)
            
            # Step 3: Generate PDF
            pdf_path = self._generate_pdf(html_content)
            
            logger.info(f"PDF generated successfully: {pdf_path}")
            return pdf_path
            
        except PDFGenerationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in PDF generation: {str(e)}")
            raise PDFGenerationError(
                message="Unexpected error during PDF generation",
                details={"error": str(e)}
            )
    
    def _load_template(self) -> Template:
        """
        Load HTML template from file
        
        Returns:
            Jinja2 Template object
            
        Raises:
            PDFGenerationError: If template loading fails
        """
        try:
            logger.debug(f"Loading template from: {self.template_path}")
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
                return Template(template_content)
        except FileNotFoundError:
            logger.error(f"Template file not found: {self.template_path}")
            raise PDFGenerationError(
                message="Template file not found",
                details={"template_path": self.template_path}
            )
        except Exception as e:
            logger.error(f"Failed to load template: {str(e)}")
            raise PDFGenerationError(
                message="Failed to load template",
                details={"template_path": self.template_path, "error": str(e)}
            )
    
    def _render_template(self, template: Template, data: Dict[str, Any]) -> str:
        """
        Render template with data
        
        Args:
            template: Jinja2 Template object
            data: Dictionary of template variables
            
        Returns:
            Rendered HTML string
            
        Raises:
            PDFGenerationError: If rendering fails
        """
        try:
            logger.debug("Rendering HTML template")
            html_out = template.render(**data)
            return html_out
        except Exception as e:
            logger.error(f"Failed to render template: {str(e)}")
            raise PDFGenerationError(
                message="Failed to render template",
                details={"error": str(e)}
            )
    
    def _generate_pdf(self, html_content: str) -> str:
        """
        Generate PDF from HTML content
        
        Args:
            html_content: HTML string to convert
            
        Returns:
            Path to generated PDF
            
        Raises:
            PDFGenerationError: If PDF generation fails
        """
        try:
            logger.debug(f"Generating PDF to: {self.output_path}")
            
            # Get PDF options from settings
            options = self._get_pdf_options()
            
            # Find wkhtmltopdf binary
            binary_path = self._find_wkhtmltopdf_binary()
            if not binary_path:
                logger.error("wkhtmltopdf binary not found")
                raise PDFGenerationError(
                    message="wkhtmltopdf binary not found",
                    details={}
                )
            
            # Configure pdfkit
            config = pdfkit.configuration(wkhtmltopdf=binary_path)
            
            # Generate PDF
            pdfkit.from_string(
                html_content,
                self.output_path,
                options=options,
                configuration=config
            )
            
            return self.output_path
            
        except PDFGenerationError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate PDF: {str(e)}")
            raise PDFGenerationError(
                message="Failed to generate PDF",
                details={"error": str(e)}
            )
    
    def _get_pdf_options(self) -> Dict[str, Any]:
        """
        Get PDF generation options from settings

        Returns:
            Dictionary of pdfkit options
        """
        return {
            'page-size': settings.pdf_page_size,
            'margin-top': settings.pdf_margin_top,
            'margin-bottom': settings.pdf_margin_bottom,
            'margin-left': settings.pdf_margin_left,
            'margin-right': settings.pdf_margin_right,
            'encoding': "UTF-8",
            'enable-local-file-access': None,
            'quiet': '',
            # Options to ensure text is selectable (may be ignored in reduced wkhtmltopdf)
            'disable-smart-shrinking': None,
            # Use low quality to reduce file size but keep text readable
            'lowquality': None,
        }
    
    def _find_wkhtmltopdf_binary(self) -> Optional[str]:
        """
        Find wkhtmltopdf binary in common locations
        
        Returns:
            Path to binary or None if not found
        """
        common_paths = [
            '/usr/bin/wkhtmltopdf',
            '/usr/local/bin/wkhtmltopdf',
            '/opt/homebrew/bin/wkhtmltopdf',  # macOS
            'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe',  # Windows
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                logger.debug(f"Found wkhtmltopdf at: {path}")
                return path
        
        logger.warning("wkhtmltopdf binary not found in common locations")
        return None