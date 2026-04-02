"""
Router for the error handler module.
Provides endpoints to list error codes.
"""

from fastapi import APIRouter
from src.foundation._013_errors.schemas import ErrorCodesResponse
from src.foundation._013_errors.service import get_error_codes

router = APIRouter(prefix="/api/v1/errors", tags=["error-handler"])


@router.get("/codes", response_model=ErrorCodesResponse)
async def list_error_codes() -> ErrorCodesResponse:
    """List all error codes with descriptions.

    Returns a list of all defined error codes, their corresponding HTTP status codes,
    descriptions, and example messages.
    """
    codes = get_error_codes()
    return ErrorCodesResponse(
        codes=codes,
        total=len(codes)
    )
