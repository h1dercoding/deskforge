from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db, get_current_user
from src.auth.service import (
    register_user,
    login_user,
    login_with_google,
    refresh_access_token,
    logout_user,
    verify_email,
    resend_verification,
    forgot_password,
    reset_password,
    update_profile,
)
from src.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    GoogleLoginRequest,
    TokenResponse,
    RefreshRequest,
    VerifyEmailRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserResponse,
    UpdateProfileRequest,
    AuthDataResponse,
    MessageResponse,
    ResendVerificationResponse,
)
from src.models.user import User
from src.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


@router.post("/register", response_model=dict, status_code=201)
async def register(
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await register_user(db, body.email, body.password, body.name)
    set_refresh_cookie(response, result["refresh_token"])
    return {
        "data": {
            "user": UserResponse.model_validate(result["user"]),
            "tokens": TokenResponse(
                access_token=result["access_token"],
                refresh_token=result["refresh_token"],
            ),
        }
    }


@router.post("/login", response_model=dict)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await login_user(db, body.email, body.password)
    set_refresh_cookie(response, result["refresh_token"])
    return {
        "data": {
            "user": UserResponse.model_validate(result["user"]),
            "tokens": TokenResponse(
                access_token=result["access_token"],
                refresh_token=result["refresh_token"],
            ),
        }
    }


@router.post("/login/google", response_model=dict)
async def google_login(
    body: GoogleLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await login_with_google(db, body.id_token)
    set_refresh_cookie(response, result["refresh_token"])
    return {
        "data": {
            "user": UserResponse.model_validate(result["user"]),
            "tokens": TokenResponse(
                access_token=result["access_token"],
                refresh_token=result["refresh_token"],
            ),
        }
    }


@router.post("/refresh", response_model=dict)
async def refresh(
    request: Request,
    response: Response,
    body: RefreshRequest = None,
    db: AsyncSession = Depends(get_db),
):
    token = None
    if body and body.refresh_token:
        token = body.refresh_token
    else:
        token = request.cookies.get("refresh_token")

    if not token:
        from src.exceptions import AuthenticationError
        raise AuthenticationError("No refresh token provided.", 1101)

    result = await refresh_access_token(db, token)
    set_refresh_cookie(response, result["refresh_token"])
    return {
        "data": {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        }
    }


@router.post("/logout", response_model=dict)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    token = request.cookies.get("refresh_token")
    if token:
        await logout_user(token)
    response.delete_cookie("refresh_token", path="/")
    return {"data": {"success": True}}


@router.post("/verify-email", response_model=dict)
async def verify_email_endpoint(
    body: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    await verify_email(db, body.token)
    return {"data": {"verified": True}}


@router.post("/resend-verification", response_model=dict)
async def resend_verification_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await resend_verification(db, current_user.id)
    return {"data": {"sent": True}}


@router.post("/forgot-password", response_model=dict)
async def forgot_password_endpoint(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    await forgot_password(db, body.email)
    return {"data": {"sent": True}}


@router.post("/reset-password", response_model=dict)
async def reset_password_endpoint(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    await reset_password(db, body.token, body.new_password)
    return {"data": {"success": True}}


@router.get("/me", response_model=dict)
async def get_me(current_user: User = Depends(get_current_user)):
    return {"data": {"user": UserResponse.model_validate(current_user)}}


@router.patch("/me", response_model=dict)
async def update_me(
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await update_profile(
        db, current_user,
        name=body.name,
        email=body.email,
        avatar_url=body.avatar_url,
    )
    return {"data": {"user": UserResponse.model_validate(user)}}
