"""
Auth Routes
Authentication endpoints (currently handled via dependencies)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Note: Authentication is handled via JWT tokens from Supabase
# No separate auth endpoints are needed at this time
# All endpoints use the get_current_user dependency from deps.py