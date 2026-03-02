"""
Alignment Agent
AI agent for aligning resumes to job descriptions
"""

import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from ..core.config import settings
from ..core.logger import get_logger
from ..core.exceptions import AIServiceError
from ..models.schemas import ResumeAlignment

logger = get_logger(__name__)


class AlignmentAgent:
    """
    AI agent for aligning resumes to job descriptions
    """
    
    def __init__(self):
        """Initialize alignment agent with LLM"""
        try:
            self.llm = ChatOpenAI(
                openai_api_key=settings.openrouter_api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                model_name=settings.ai_model,
                temperature=settings.ai_temperature,
                max_tokens=settings.ai_max_tokens,
                model_kwargs={"response_format": {"type": "json_object"}}
            )
            logger.info(f"Alignment agent initialized with model: {settings.ai_model}")
        except Exception as e:
            logger.error(f"Failed to initialize alignment agent: {str(e)}")
            raise AIServiceError(
                message="Failed to initialize AI alignment agent",
                details={"error": str(e)}
            )
    
    def align_resume_to_jd(
        self,
        resume_text: str,
        jd_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Align resume to job description using AI

        Args:
            resume_text: Resume text
            jd_data: Structured job description data

        Returns:
            Dictionary containing alignment results

        Raises:
            AIServiceError: If alignment fails
        """
        try:
            logger.info("Aligning resume to job description")

            # Create parser for ResumeAlignment schema
            parser = PydanticOutputParser(pydantic_object=ResumeAlignment)

            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                (
                    "system",
                    "You are a professional Harvard-standard resume writer. "
                    "Return ONLY valid JSON that strictly follows the schema. "
                    "Ensure 'thesis' is included in education entries if present. "
                    "All lists must be arrays, all strings must be strings, numbers must be numbers.\n"
                    "{format_instructions}"
                ),
                (
                    "user",
                    "TASK: Reconstruct the entire resume to align with the JD.\n\n"
                    "RESUME:\n{resume}\n\n"
                    "JD DATA:\n{jd_json}"
                )
            ]).partial(format_instructions=parser.get_format_instructions())

            # Create and execute chain with retry logic
            chain = prompt | self.llm | parser

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if attempt == 0:
                        # First attempt
                        result = chain.invoke({
                            "resume": resume_text,
                            "jd_json": json.dumps(jd_data)
                        })
                    else:
                        # Retry with error context
                        result = chain.invoke({
                            "resume": resume_text,
                            "jd_json": json.dumps(jd_data),
                            "error": str(last_error)
                        })
                    logger.info(f"Successfully aligned resume with match score: {result.match_score}%")
                    return result.model_dump()
                except Exception as parse_error:
                    last_error = parse_error
                    if attempt == max_retries - 1:
                        raise parse_error
                    logger.warning(f"Parse attempt {attempt + 1} failed: {str(parse_error)}. Retrying...")

                    # Create correction prompt for next retry
                    correction_prompt = ChatPromptTemplate.from_messages([
                        (
                            "system",
                            "You are a professional Harvard-standard resume writer. The previous response was invalid. "
                            "Return ONLY valid JSON that strictly follows the schema. "
                            "Ensure 'thesis' is included in education entries if present. "
                            "All lists must be arrays, all strings must be strings, numbers must be numbers.\n"
                            "{format_instructions}"
                        ),
                        (
                            "user",
                            "Previous invalid response: {error}\n\n"
                            "TASK: Reconstruct the entire resume to align with the JD.\n\n"
                            "RESUME:\n{resume}\n\n"
                            "JD DATA:\n{jd_json}"
                        )
                    ]).partial(format_instructions=parser.get_format_instructions())

                    chain = correction_prompt | self.llm | parser

            # This should not be reached, but just in case
            raise Exception("Max retries exceeded")

        except Exception as e:
            logger.error(f"Failed to align resume to JD: {str(e)}")
            raise AIServiceError(
                message="Failed to align resume to job description",
                details={"error": str(e)}
            )
