from fastapi import HTTPException, status
import structlog

logger = structlog.get_logger("analisaai-sync")

class APIError(HTTPException):
    """Base API error class"""
    def __init__(
        self, 
        status_code: int, 
        detail: str, 
        error_code: str = None,
        log_level: str = "error"
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "error": detail,
                "code": error_code or str(status_code)
            }
        )
        # Log the error
        log_method = getattr(logger, log_level)
        log_method(
            "API error", 
            status_code=status_code, 
            detail=detail, 
            error_code=error_code
        )

class AuthError(APIError):
    """Authentication error"""
    def __init__(self, detail: str = "Authentication failed", error_code: str = "auth_error"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code
        )

class ForbiddenError(APIError):
    """Forbidden error"""
    def __init__(self, detail: str = "Not enough permissions", error_code: str = "forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code
        )
        
class NotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, detail: str = "Resource not found", error_code: str = "not_found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code
        )

class ValidationError(APIError):
    """Validation error"""
    def __init__(self, detail: str = "Validation error", error_code: str = "validation_error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code
        )

class ExternalAPIError(APIError):
    """External API error"""
    def __init__(self, detail: str = "External API error", error_code: str = "external_api_error"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
            error_code=error_code
        )

class SocialTokenError(APIError):
    """Social token error"""
    def __init__(self, detail: str = "Social token error", error_code: str = "social_token_error"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code
        )