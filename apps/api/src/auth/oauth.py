import httpx
from typing import Optional
from src.config import settings
from src.exceptions import AuthenticationError


async def verify_google_id_token(id_token: str) -> Optional[dict]:
    """Verify a Google ID token and return user info."""
    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url)
            if response.status_code != 200:
                return None
            data = response.json()
            if data.get("aud") != settings.GOOGLE_CLIENT_ID:
                return None
            return {
                "google_id": data.get("sub"),
                "email": data.get("email", "").lower(),
                "name": data.get("name", ""),
                "avatar_url": data.get("picture"),
                "email_verified": data.get("email_verified", "false") == "true",
            }
        except httpx.HTTPError:
            return None


async def get_google_auth_url() -> str:
    """Build Google OAuth consent URL for Sheets API access."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "openid",
        "email",
        "profile",
    ]
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


async def exchange_google_code(code: str) -> Optional[dict]:
    """Exchange Google OAuth code for tokens."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            if response.status_code != 200:
                return None
            return response.json()
        except httpx.HTTPError:
            return None


async def refresh_google_token(refresh_token: str) -> Optional[dict]:
    """Refresh a Google OAuth access token."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "refresh_token": refresh_token,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                },
            )
            if response.status_code != 200:
                return None
            return response.json()
        except httpx.HTTPError:
            return None
