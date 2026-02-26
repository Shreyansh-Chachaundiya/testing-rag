import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import uuid4


# NEW: Token storage for session management (not in old version)
_active_sessions: Dict[str, Dict[str, Any]] = {}

# NEW: Rate limiting tracker (not in old version)
_login_attempts: Dict[str, list] = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 30


def generate_token(user_id: str, role: str, permissions: list = None) -> str:
    """
    Generate a secure authentication token.

    CHANGED from old version:
    - Uses secrets.token_urlsafe instead of HMAC
    - Adds permissions field
    - Stores session data for server-side validation
    """
    token = secrets.token_urlsafe(48)
    session_id = uuid4().hex

    _active_sessions[token] = {
        "session_id": session_id,
        "user_id": user_id,
        "role": role,
        "permissions": permissions or [],
        "issued_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        "is_active": True,
    }

    return token


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode an authentication token.

    CHANGED from old version:
    - Server-side session validation instead of signature check
    - Checks session is_active flag
    - Validates expiry
    """
    session = _active_sessions.get(token)
    if not session:
        return None

    if not session.get("is_active", False):
        return None

    expires = datetime.fromisoformat(session["expires_at"])
    if expires < datetime.utcnow():
        session["is_active"] = False
        return None

    return {
        "user_id": session["user_id"],
        "role": session["role"],
        "permissions": session["permissions"],
        "expires_at": session["expires_at"],
    }


def revoke_token(token: str) -> bool:
    """NEW: Revoke a token (logout). Not in old version."""
    session = _active_sessions.get(token)
    if session:
        session["is_active"] = False
        return True
    return False


def check_rate_limit(identifier: str) -> bool:
    """NEW: Check if login attempts are rate-limited."""
    now = datetime.utcnow()
    attempts = _login_attempts.get(identifier, [])

    recent = [a for a in attempts if (now - a).total_seconds() < LOCKOUT_MINUTES * 60]
    _login_attempts[identifier] = recent

    return len(recent) < MAX_LOGIN_ATTEMPTS


def record_login_attempt(identifier: str):
    """NEW: Record a login attempt for rate limiting."""
    if identifier not in _login_attempts:
        _login_attempts[identifier] = []
    _login_attempts[identifier].append(datetime.utcnow())


def hash_password_secure(password: str) -> str:
    """
    Hash password using SHA-256 with random salt.

    CHANGED from old version:
    - Uses random salt instead of static salt
    - Returns salt:hash format
    """
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password_secure(password: str, stored: str) -> bool:
    """Verify password against stored salt:hash."""
    if ":" not in stored:
        return False
    salt, expected_hash = stored.split(":", 1)
    actual_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return secrets.compare_digest(actual_hash, expected_hash)
