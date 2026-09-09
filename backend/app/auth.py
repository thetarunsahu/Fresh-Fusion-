import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("FRESHFUSION_AUTH_TOKEN_MINUTES", "480"))
AUTH_SECRET = os.getenv("FRESHFUSION_AUTH_SECRET", "freshfusion-local-demo-change-me")
PBKDF2_ITERATIONS = int(os.getenv("FRESHFUSION_PASSWORD_ITERATIONS", "310000"))
_bearer = HTTPBearer(auto_error=False)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64url(salt)}${_b64url(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iterations, salt_text, digest_text = password_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        salt = _b64url_decode(salt_text)
        expected = _b64url_decode(digest_text)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user: User) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    header_part = _b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_part = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}".encode("ascii")
    signature = hmac.new(AUTH_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{_b64url(signature)}", expires_at


def _decode_access_token(token: str) -> dict:
    try:
        header_part, payload_part, signature_part = token.split(".", 2)
        signing_input = f"{header_part}.{payload_part}".encode("ascii")
        expected = hmac.new(AUTH_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
        supplied = _b64url_decode(signature_part)
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("bad signature")
        header = json.loads(_b64url_decode(header_part))
        payload = json.loads(_b64url_decode(payload_part))
        if header.get("alg") != JWT_ALGORITHM or header.get("typ") != "JWT":
            raise ValueError("unsupported token")
        if int(payload.get("exp", 0)) <= int(time.time()):
            raise ValueError("expired")
        return payload
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _decode_access_token(credentials.credentials)
    try:
        user_id = int(payload.get("sub", ""))
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid session subject")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive or unavailable")
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role for this action")
        return user

    return dependency
