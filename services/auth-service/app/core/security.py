from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional

import secrets
import uuid as _uuid

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Use argon2id for password hashing.
# Parameters tuned to OWASP minimum (m=19456 / 19 MB, t=2, p=1) so that
# verify_password completes in ~0.5 s even inside Docker/WSL2.
# Existing hashes with higher params will still verify — passlib reads the
# params embedded in the hash string and rehashes on next login automatically.
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=19456,
    argon2__time_cost=2,
    argon2__parallelism=1,
)

# Hard maximum for access token lifetime (policy: 15 minutes)
_ACCESS_TOKEN_MAX_MINUTES = 15


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any],
    role: str,
    email: str,
    company_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed RS256 JWT access token.

    The effective lifetime is capped at ``_ACCESS_TOKEN_MAX_MINUTES`` minutes
    regardless of the ``expires_delta`` argument, enforcing the 15-minute
    policy defined in the HRMS security rulebook.
    """
    max_delta = timedelta(minutes=_ACCESS_TOKEN_MAX_MINUTES)
    if expires_delta is None:
        effective_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        effective_delta = expires_delta

    # Hard cap: never allow more than ACCESS_TOKEN_MAX_MINUTES
    if effective_delta > max_delta:
        effective_delta = max_delta

    expire = datetime.now(timezone.utc) + effective_delta
    to_encode = {
        "exp": expire,
        "jti": str(_uuid.uuid4()),
        "sub": str(subject),
        "type": "access",
        "role": role,
        "email": email,
        "company_id": company_id,
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_PRIVATE_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token() -> str:
    """Generate a cryptographically secure random refresh token secret."""
    return secrets.token_urlsafe(32)
