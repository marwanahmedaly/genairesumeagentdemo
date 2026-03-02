"""
Resume Normalizer
Utilities for normalizing resume alignment data into candidate flows and canonical sections
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from ..core.logger import get_logger

logger = get_logger(__name__)


class ResumeNormalizer:
    """
    Normalizes resume alignment data into candidate flows and canonical sections
    """

    # Flow definitions with presentation rules
    FLOW_RULES = {
        "newgrad": {
            "summary_lines": 0,
            "priorities": ["education", "projects", "experience", "leadership_activities", "skills"],
            "bullets_per_entry": 3,
            "collapse_older": False
        },
        "early-IC": {
            "summary_lines": 1,
            "priorities": ["experience", "projects", "education", "leadership_activities", "skills"],
            "bullets_per_entry": 3,
            "collapse_older": False
        },
        "mid-IC": {
            "summary_lines": 2,
            "priorities": ["experience", "projects", "technical_skills", "leadership_activities", "education"],
            "bullets_per_entry": 4,
            "collapse_older": False
        },
        "mid-manager": {
            "summary_lines": 3,
            "priorities": ["experience", "leadership_activities", "projects", "education", "skills"],
            "bullets_per_entry": 4,
            "collapse_older": False
        },
        "senior": {
            "summary_lines": 3,
            "priorities": ["experience", "leadership_activities", "projects", "technical_skills"],
            "bullets_per_entry": 3,
            "collapse_older": True
        }
    }

    # Section priority mapping
    SECTION_PRIORITIES = {
        "experience": 1,
        "education": 2,
        "projects": 3,
        "leadership_activities": 4,
        "technical_skills": 5,
        "languages": 6,
        "laboratory": 7,
        "interests": 8,
        "additional": 99
    }

    @staticmethod
    def estimate_years_experience(experience_entries: List[Dict[str, Any]]) -> float:
        """
        Estimate total years of experience from experience entries

        Args:
            experience_entries: List of experience entry dictionaries

        Returns:
            Estimated years of experience as float
        """
        total_years = 0.0

        for entry in experience_entries:
            dates_str = entry.get('dates', '')
            if dates_str:
                start_date, end_date = ResumeNormalizer._parse_date_range(dates_str)
                if start_date and end_date:
                    # Calculate duration in years
                    duration = (end_date - start_date).days / 365.25
                    total_years += max(0, duration)  # Ensure non-negative

        return round(total_years, 1)

    @staticmethod
    def detect_is_manager(experience_entries: List[Dict[str, Any]]) -> bool:
        """
        Detect if candidate has management experience

        Args:
            experience_entries: List of experience entry dictionaries

        Returns:
            True if management experience detected
        """
        management_keywords = [
            'managed', 'led', 'team', 'direct reports', 'supervisor',
            'manager', 'director', 'vp', 'vice president', 'head of',
            'lead', 'oversaw', 'coordinated', 'mentored'
        ]

        for entry in experience_entries:
            role = entry.get('role', '').lower()
            company = entry.get('company', '').lower()

            # Check role title
            if any(keyword in role for keyword in management_keywords):
                return True

            # Check company description if available
            if any(keyword in company for keyword in management_keywords):
                return True

            # Check bullets for management indicators
            bullets = entry.get('bullets', [])
            for bullet in bullets:
                bullet_lower = bullet.lower()
                if any(keyword in bullet_lower for keyword in management_keywords):
                    return True

        return False

    @staticmethod
    def infer_domain_tags(technical_skills: List[str], experience_entries: List[Dict[str, Any]]) -> List[str]:
        """
        Infer domain tags from skills and experience

        Args:
            technical_skills: List of technical skills
            experience_entries: List of experience entries

        Returns:
            List of domain tags
        """
        domains = []

        # Check technical skills for domain indicators
        skills_text = ' '.join(technical_skills).lower()

        if any(skill in skills_text for skill in ['python', 'java', 'javascript', 'react', 'node', 'aws', 'docker']):
            domains.append('engineering')

        if any(skill in skills_text for skill in ['sql', 'tableau', 'power bi', 'excel', 'analytics']):
            domains.append('data')

        if any(skill in skills_text for skill in ['figma', 'sketch', 'photoshop', 'ux', 'ui']):
            domains.append('design')

        if any(skill in skills_text for skill in ['marketing', 'sales', 'business development']):
            domains.append('business')

        # Check experience for additional context
        for entry in experience_entries:
            role = entry.get('role', '').lower()
            if 'product' in role and 'product' not in domains:
                domains.append('product')
            if 'design' in role and 'design' not in domains:
                domains.append('design')

        return domains[:2]  # Limit to top 2 domains

    @staticmethod
    def determine_candidate_flow(years_experience: float, is_manager: bool, domain_tags: List[str]) -> str:
        """
        Determine the candidate flow based on experience, management status, and domain

        Args:
            years_experience: Estimated years of experience
            is_manager: Whether candidate has management experience
            domain_tags: List of domain tags

        Returns:
            Candidate flow string
        """
        # Determine seniority level
        if years_experience <= 1:
            seniority = "newgrad"
        elif years_experience <= 3:
            seniority = "early"
        elif years_experience <= 7:
            seniority = "mid"
        else:
            seniority = "senior"

        # Determine role type
        if is_manager and years_experience >= 3:
            role_type = "manager"
        else:
            role_type = "IC"

        # Combine seniority and role type
        flow = f"{seniority}-{role_type}"

        # Add primary domain if available
        if domain_tags:
            flow += f"-{domain_tags[0]}"

        return flow

    @staticmethod
    def normalize_sections(full_reconstruction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalize full reconstruction into canonical sections

        Args:
            full_reconstruction: Full reconstruction dictionary

        Returns:
            List of normalized section dictionaries
        """
        sections = []

        # Map existing sections to canonical format
        section_mappings = {
            'experience': ('experience', 'entries'),
            'education': ('education', 'entries'),
            'leadership_activities': ('leadership_activities', 'entries'),
            'technical_skills': ('technical_skills', 'strings'),
            'languages': ('languages', 'strings'),
            'laboratory': ('laboratory', 'strings'),
            'interests': ('interests', 'strings')
        }

        for key, (title_key, section_type) in section_mappings.items():
            if key in full_reconstruction and full_reconstruction[key]:
                section_data = full_reconstruction[key]

                # Create normalized section
                section = {
                    'key': key,
                    'title': title_key.replace('_', ' ').title(),
                    'type': section_type,
                    'priority': ResumeNormalizer.SECTION_PRIORITIES.get(key, 50)
                }

                if section_type == 'entries':
                    # Process entries
                    entries = []
                    for item in section_data:
                        entry = {
                            'company': item.get('company', ''),
                            'organization': item.get('organization', ''),
                            'school': item.get('school', ''),
                            'role': item.get('role', ''),
                            'degree': item.get('degree', ''),
                            'location': item.get('location', ''),
                            'dates': item.get('dates', ''),
                            'bullets': ResumeNormalizer._annotate_bullets(item.get('bullets', [])),
                            'meta': {}
                        }
                        entries.append(entry)
                    section['entries'] = entries

                elif section_type == 'strings':
                    section['values'] = section_data

                sections.append(section)

        # Sort by priority
        sections.sort(key=lambda x: x['priority'])

        return sections

    @staticmethod
    def _parse_date_range(dates_str: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Parse date range string into start and end datetime objects

        Args:
            dates_str: Date range string (e.g., "Jan 2020 - Dec 2022")

        Returns:
            Tuple of (start_date, end_date) or (None, None) if parsing fails
        """
        try:
            # Common date patterns
            patterns = [
                r'(\w{3}\s+\d{4})\s*-\s*(\w{3}\s+\d{4})',  # Jan 2020 - Dec 2022
                r'(\d{4})\s*-\s*(\d{4})',  # 2020 - 2022
                r'(\w{3}\s+\d{4})\s*-\s*Present',  # Jan 2020 - Present
            ]

            for pattern in patterns:
                match = re.search(pattern, dates_str, re.IGNORECASE)
                if match:
                    start_str = match.group(1)
                    end_str = match.group(2) if len(match.groups()) > 1 else 'Present'

                    # Parse start date
                    start_date = ResumeNormalizer._parse_single_date(start_str)

                    # Parse end date
                    if end_str.lower() == 'present':
                        end_date = datetime.now()
                    else:
                        end_date = ResumeNormalizer._parse_single_date(end_str)

                    if start_date and end_date:
                        return start_date, end_date

            return None, None

        except Exception as e:
            logger.warning(f"Failed to parse date range '{dates_str}': {str(e)}")
            return None, None

    @staticmethod
    def _parse_single_date(date_str: str) -> Optional[datetime]:
        """
        Parse a single date string

        Args:
            date_str: Date string (e.g., "Jan 2020" or "2020")

        Returns:
            Datetime object or None if parsing fails
        """
        try:
            # Try full month year format
            try:
                return datetime.strptime(date_str.strip(), '%b %Y')
            except ValueError:
                pass

            # Try just year
            try:
                year = int(date_str.strip())
                return datetime(year, 1, 1)
            except ValueError:
                pass

            return None

        except Exception:
            return None

    @staticmethod
    def _annotate_bullets(bullets: List[str]) -> List[Dict[str, Any]]:
        """
        Annotate bullets with importance scores

        Args:
            bullets: List of bullet strings

        Returns:
            List of bullet dictionaries with annotations
        """
        annotated = []

        for bullet in bullets:
            # Simple heuristics for importance
            importance = 0.5  # Default medium importance

            bullet_lower = bullet.lower()

            # Increase importance for metrics/numbers
            if re.search(r'\d+', bullet):
                importance += 0.2

            # Increase for action verbs
            action_verbs = ['led', 'managed', 'developed', 'created', 'implemented', 'increased', 'reduced']
            if any(verb in bullet_lower for verb in action_verbs):
                importance += 0.2

            # Increase for results/outcomes
            if any(word in bullet_lower for word in ['resulting in', 'leading to', 'achieved', 'delivered']):
                importance += 0.1

            # Cap at 1.0
            importance = min(1.0, importance)

            annotated.append({
                'text': bullet,
                'importance': importance,
                'metric_score': 1.0 if re.search(r'\d+', bullet) else 0.0
            })

        return annotated

    @staticmethod
    def get_flow_settings(candidate_flow: str) -> Dict[str, Any]:
        """
        Get presentation settings for a candidate flow

        Args:
            candidate_flow: Candidate flow string

        Returns:
            Flow settings dictionary
        """
        # Extract base flow (e.g., "mid-IC" from "mid-IC-engineering")
        base_flow = candidate_flow.split('-')[0] + '-' + candidate_flow.split('-')[1]

        return ResumeNormalizer.FLOW_RULES.get(base_flow, ResumeNormalizer.FLOW_RULES['early-IC'])