"""
Extraction Agent
AI agent for extracting structured data from job descriptions
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from ..core.config import settings
from ..core.logger import get_logger
from ..core.exceptions import AIServiceError
from ..models.schemas import JDData

logger = get_logger(__name__)


class ExtractionAgent:
    """
    AI agent for extracting structured data from job descriptions
    Singleton pattern to ensure single LLM client instance
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(ExtractionAgent, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize extraction agent with LLM (only once)"""
        if self._initialized:
            return

        try:
            self.llm = ChatOpenAI(
                openai_api_key=settings.openrouter_api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                model_name=settings.ai_model,
                temperature=settings.ai_temperature,
                max_tokens=settings.ai_max_tokens,
                model_kwargs={"response_format": {"type": "json_object"}}
            )
            logger.info(f"Extraction agent initialized with model: {settings.ai_model}")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize extraction agent: {str(e)}")
            raise AIServiceError(
                message="Failed to initialize AI extraction agent",
                details={"error": str(e)}
            )
    
    def extract_jd_data(self, raw_markdown: str) -> Dict[str, Any]:
        """
        Extract structured job description data from markdown

        Args:
            raw_markdown: Job description as markdown string

        Returns:
            Dictionary containing structured JD data

        Raises:
            AIServiceError: If extraction fails
        """
        try:
            logger.info("Extracting structured data from job description")

            # Create parser for JDData schema
            parser = PydanticOutputParser(pydantic_object=JDData)

            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                (
                    "system",
                    "You are a recruitment assistant. Return ONLY valid JSON that strictly follows the schema.\n{format_instructions}\n\nCRITICAL: Ensure all fields are present and correctly typed. Lists must be arrays, not strings."
                ),
                (
                    "user",
                    "Extract from this JD:\n\n{jd_text}"
                )
            ]).partial(format_instructions=parser.get_format_instructions())

            # Create and execute chain with retry logic
            chain = prompt | self.llm | parser

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = chain.invoke({"jd_text": raw_markdown})
                    logger.info(f"Successfully extracted JD data for role: {result.role_title}")
                    return result.model_dump()
                except Exception as parse_error:
                    if attempt == max_retries - 1:
                        raise parse_error
                    logger.warning(f"Parse attempt {attempt + 1} failed: {str(parse_error)}. Retrying...")

                    # Create correction prompt
                    correction_prompt = ChatPromptTemplate.from_messages([
                        (
                            "system",
                            "You are a recruitment assistant. The previous response was invalid. Return ONLY valid JSON.\n{format_instructions}\n\nCRITICAL: Ensure all fields are present and correctly typed. Lists must be arrays, not strings."
                        ),
                        (
                            "user",
                            "Previous invalid response: {error}\n\nExtract from this JD:\n\n{jd_text}"
                        )
                    ]).partial(format_instructions=parser.get_format_instructions())

                    chain = correction_prompt | self.llm | parser

            # This should not be reached, but just in case
            raise Exception("Max retries exceeded")

        except Exception as e:
            logger.error(f"Failed to extract JD data: {str(e)}")
            raise AIServiceError(
                message="Failed to extract job description data",
                details={"error": str(e)}
            )
