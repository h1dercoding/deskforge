"""DeskForge Exception Hierarchy with error codes 1000-1999."""
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import Request
from fastapi.responses import JSONResponse


class DeskForgeError(Exception):
    """Base exception for all DeskForge errors."""

    def __init__(
        self,
        code: int,
        error_type: str,
        message: str,
        status_code: int = 400,
        details: Optional[list] = None,
    ):
        self.code = code
        self.error_type = error_type
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


# ── Validation (1000-1099) ──

class ValidationError(DeskForgeError):
    def __init__(self, message: str = "Validation error", details: Optional[list] = None):
        super().__init__(1000, "VALIDATION_ERROR", message, 400, details)


class InvalidEmailError(DeskForgeError):
    def __init__(self, email: str = ""):
        super().__init__(1001, "INVALID_EMAIL", "Invalid email format.", 400,
                         [{"field": "email", "issue": "Invalid email format", "value": email}])


class WeakPasswordError(DeskForgeError):
    def __init__(self):
        super().__init__(1002, "WEAK_PASSWORD",
                         "Password must be at least 8 characters with 1 uppercase, 1 lowercase, 1 number, and 1 special character.",
                         400, [{"field": "password", "issue": "Does not meet complexity requirements"}])


class PromptTooShortError(DeskForgeError):
    def __init__(self, length: int = 0):
        super().__init__(1003, "PROMPT_TOO_SHORT",
                         "Your description must be at least 10 characters long.",
                         400, [{"field": "prompt", "issue": f"Minimum 10 characters required, received {length}"}])


class PromptTooLongError(DeskForgeError):
    def __init__(self, length: int = 0):
        super().__init__(1004, "PROMPT_TOO_LONG",
                         "Your description must be at most 2000 characters long.",
                         400, [{"field": "prompt", "issue": f"Maximum 2000 characters allowed, received {length}"}])


class InvalidFileTypeError(DeskForgeError):
    def __init__(self, allowed: str = ".csv, .xlsx, .xls"):
        super().__init__(1005, "INVALID_FILE_TYPE",
                         f"Invalid file type. Allowed types: {allowed}", 400,
                         [{"field": "file", "issue": f"Must be one of: {allowed}"}])


class FileTooLargeError(DeskForgeError):
    def __init__(self, max_mb: int = 200):
        super().__init__(1006, "FILE_TOO_LARGE",
                         f"File exceeds maximum size of {max_mb} MB.",
                         400, [{"field": "file", "issue": f"Max size is {max_mb}MB"}])


class InvalidColumnTypeError(DeskForgeError):
    def __init__(self, column: str = "", col_type: str = ""):
        super().__init__(1007, "INVALID_COLUMN_TYPE",
                         f"Invalid type '{col_type}' for column '{column}'.",
                         400, [{"field": "column_types", "issue": f"Invalid type: {col_type}"}])


# ── Authentication (1100-1199) ──

class AuthenticationError(DeskForgeError):
    def __init__(self, message: str = "Authentication required", code: int = 1100):
        super().__init__(code, "AUTHENTICATION_ERROR", message, 401)


class InvalidCredentialsError(AuthenticationError):
    def __init__(self):
        super().__init__("Invalid email or password.", 1100)


class TokenExpiredError(AuthenticationError):
    def __init__(self):
        super().__init__("Token has expired.", 1101)


class TokenInvalidError(AuthenticationError):
    def __init__(self):
        super().__init__("Invalid token.", 1102)


class EmailNotVerifiedError(AuthenticationError):
    def __init__(self):
        super().__init__("Email address not verified. Please check your inbox.", 1103)


# ── Authorization (1200-1299) ──

class AuthorizationError(DeskForgeError):
    def __init__(self, message: str = "Insufficient permissions", code: int = 1200):
        super().__init__(code, "AUTHORIZATION_ERROR", message, 403)


class InsufficientRoleError(AuthorizationError):
    def __init__(self, required_role: str = "owner"):
        super().__init__(f"This action requires {required_role} role or higher.", 1200)


class NotTeamMemberError(AuthorizationError):
    def __init__(self):
        super().__init__("You are not a member of this team.", 1201)


class PlanLimitError(DeskForgeError):
    def __init__(self, resource: str, limit: int, plan: str):
        super().__init__(
            1202, "PLAN_LIMIT_REACHED",
            f"You've reached the {resource} limit ({limit}) on the {plan} plan. Upgrade to continue.",
            403,
            [{"resource": resource, "limit": limit, "plan": plan}],
        )


class FeatureNotAvailableError(DeskForgeError):
    def __init__(self, feature: str = ""):
        super().__init__(1203, "FEATURE_NOT_AVAILABLE",
                         f"{feature} is not available on your current plan.",
                         403, [{"feature": feature}])


# ── Not Found (1300-1399) ──

class NotFoundError(DeskForgeError):
    def __init__(self, message: str = "Resource not found", code: int = 1300):
        super().__init__(code, "NOT_FOUND", message, 404)


class UserNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("User not found.", 1300)


class TeamNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Team not found.", 1301)


class ToolNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Tool not found.", 1302)


class DataSourceNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Data source not found.", 1303)


class TemplateNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Template not found.", 1304)


class InvitationNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Invitation not found or expired.", 1305)


# ── Conflict (1400-1499) ──

class ConflictError(DeskForgeError):
    def __init__(self, message: str = "Resource conflict", code: int = 1400, details: Optional[list] = None):
        super().__init__(code, "CONFLICT", message, 409, details)


class EmailAlreadyExistsError(ConflictError):
    def __init__(self):
        super().__init__("An account with this email already exists.", 1400,
                         [{"field": "email", "issue": "Already registered"}])


class SlugAlreadyExistsError(ConflictError):
    def __init__(self):
        super().__init__("A tool with this slug already exists.", 1401)


class AlreadyTeamMemberError(ConflictError):
    def __init__(self):
        super().__init__("User is already a member of this team.", 1402)


class InvitationAlreadyAcceptedError(ConflictError):
    def __init__(self):
        super().__init__("This invitation has already been accepted.", 1403)


# ── Rate Limit (1500-1599) ──

class RateLimitError(DeskForgeError):
    def __init__(self, message: str = "Rate limit exceeded", code: int = 1500, retry_after: Optional[int] = None):
        details = [{"retry_after": retry_after}] if retry_after else []
        super().__init__(code, "RATE_LIMIT_EXCEEDED", message, 429, details)


class GenerationQuotaExceededError(RateLimitError):
    def __init__(self):
        super().__init__("Generation quota exceeded. Please wait before trying again.", 1501)


# ── Generation (1600-1699) ──

class GenerationError(DeskForgeError):
    def __init__(self, message: str = "Tool generation failed", code: int = 1605):
        super().__init__(code, "GENERATION_FAILED", message, 422)


class LLMTimeoutError(GenerationError):
    def __init__(self):
        super().__init__("LLM request timed out. Please try again.", 1600)


class LLMError(GenerationError):
    def __init__(self, detail: str = ""):
        super().__init__(f"LLM service error: {detail}" if detail else "LLM service error.", 1601)


class InvalidToolSpecError(GenerationError):
    def __init__(self, detail: str = ""):
        super().__init__(f"Invalid tool specification: {detail}" if detail else "Invalid tool specification.", 1602)


class SpecValidationError(GenerationError):
    def __init__(self, issues: Optional[list] = None):
        super().__init__("Tool specification validation failed.", 1603)
        if issues:
            self.details = issues


class SandboxRenderError(GenerationError):
    def __init__(self):
        super().__init__("Sandbox rendering error.", 1604)


# ── External (1700-1799) ──

class ExternalServiceError(DeskForgeError):
    def __init__(self, message: str = "External service error", code: int = 1700):
        super().__init__(code, "EXTERNAL_SERVICE_ERROR", message, 502)


class GoogleSheetsError(ExternalServiceError):
    def __init__(self, detail: str = ""):
        super().__init__(f"Google Sheets error: {detail}" if detail else "Google Sheets error.", 1700)


class DatabaseConnectionError(ExternalServiceError):
    def __init__(self, detail: str = ""):
        super().__init__(f"Database connection failed: {detail}" if detail else "Database connection failed.", 1701)


class DatabaseQueryError(ExternalServiceError):
    def __init__(self, detail: str = ""):
        super().__init__(f"Database query failed: {detail}" if detail else "Database query failed.", 1702)


class StripeError(ExternalServiceError):
    def __init__(self, detail: str = ""):
        super().__init__(f"Payment processing error: {detail}" if detail else "Payment processing error.", 1703)


class EmailSendError(ExternalServiceError):
    def __init__(self):
        super().__init__("Failed to send email.", 1704)


class S3UploadError(ExternalServiceError):
    def __init__(self):
        super().__init__("File upload failed.", 1705)


# ── Internal (1900-1999) ──

class InternalError(DeskForgeError):
    def __init__(self, message: str = "An unexpected error occurred. Please try again."):
        super().__init__(1900, "INTERNAL_ERROR", message, 500)


class DatabaseError(InternalError):
    def __init__(self):
        super().__init__("A database error occurred.")
        self.code = 1901
        self.error_type = "DATABASE_ERROR"


# ── Exception Handlers ──

async def deskforge_error_handler(request: Request, exc: DeskForgeError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "type": exc.error_type,
                "message": exc.message,
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", None),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        },
    )


async def validation_exception_handler(request: Request, exc: Any) -> JSONResponse:
    details = []
    if hasattr(exc, "errors"):
        for err in exc.errors():
            details.append({
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "issue": err.get("msg", ""),
            })
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 1000,
                "type": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": details,
                "request_id": getattr(request.state, "request_id", None),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        },
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    import logging
    logger = logging.getLogger("deskforge")
    logger.exception(f"Unhandled error: {exc}", extra={"request_id": getattr(request.state, "request_id", None)})
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 1900,
                "type": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "details": [],
                "request_id": getattr(request.state, "request_id", None),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
