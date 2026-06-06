import re
import bcrypt

PASSWORD_MIN_LENGTH = 8
PASSWORD_PATTERN = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).{8,}$'
)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with cost factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def validate_password_strength(password: str) -> bool:
    """Check if password meets complexity requirements."""
    return bool(PASSWORD_PATTERN.match(password))


def get_password_requirements() -> dict:
    """Return password complexity requirements for API responses."""
    return {
        "min_length": PASSWORD_MIN_LENGTH,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digit": True,
        "require_special_character": True,
        "description": (
            "Password must be at least 8 characters and include "
            "1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character."
        ),
    }
