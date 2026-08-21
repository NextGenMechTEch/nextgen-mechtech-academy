"""
Authentication helpers: password hashing, registration, login, session
helpers, email verification tokens, and password-reset tokens.
"""
import os
import secrets
from datetime import datetime, timedelta

import bcrypt
import streamlit as st

from database.connection import get_db_session
from database.models import User, UserRole, NewsletterSubscriber


# ─── Login lockout (brute-force protection) ─────────────────────────────────
# In-memory only (process-lifetime, no DB schema change): tracks failed
# password attempts per email. After MAX_FAILED_ATTEMPTS consecutive
# failures for the same email, that email is locked out for LOCKOUT_MINUTES.
# A successful login clears the counter. Since this lives in a plain module
# dict rather than st.session_state, it persists across a user's session
# reruns and isn't reset just by refreshing the login page.
_MAX_FAILED_ATTEMPTS = 5
_LOCKOUT_MINUTES = 15
_failed_login_attempts = {}  # {email: {"count": int, "locked_until": datetime|None}}


def _lockout_check(email: str):
    """Return (is_locked: bool, message: str|None) for the given email."""
    entry = _failed_login_attempts.get(email)
    if not entry:
        return False, None
    locked_until = entry.get("locked_until")
    if locked_until and datetime.utcnow() < locked_until:
        remaining = locked_until - datetime.utcnow()
        minutes_left = max(1, int(remaining.total_seconds() // 60) + 1)
        return True, (
            f"Too many failed login attempts. This account is temporarily "
            f"locked. Please try again in {minutes_left} minute(s)."
        )
    if locked_until and datetime.utcnow() >= locked_until:
        # Lockout window has expired — reset the counter.
        _failed_login_attempts.pop(email, None)
    return False, None


def _record_failed_attempt(email: str):
    entry = _failed_login_attempts.setdefault(email, {"count": 0, "locked_until": None})
    entry["count"] += 1
    if entry["count"] >= _MAX_FAILED_ATTEMPTS:
        entry["locked_until"] = datetime.utcnow() + timedelta(minutes=_LOCKOUT_MINUTES)


def _clear_failed_attempts(email: str):
    _failed_login_attempts.pop(email, None)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), password_hash.encode())
    except (ValueError, TypeError):
        return False


def is_logged_in() -> bool:
    return bool(st.session_state.get("user"))


def is_admin() -> bool:
    user = st.session_state.get("user")
    if not user:
        return False
    role = user.get("role", "")
    return role in ("admin", "super_admin")


def is_super_admin() -> bool:
    user = st.session_state.get("user")
    return bool(user and user.get("role") == "super_admin")


def _user_to_session_dict(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else user.role,
        "phone": user.phone,
        "university": user.university,
        "department": user.department,
        "semester": user.semester,
        "profile_photo": user.profile_photo,
        "is_verified": user.is_verified,
        "permissions": user.permissions or "",
    }


def login_user(email: str, password: str):
    """Attempt login. Returns (success: bool, message: str)."""
    email_norm = email.strip().lower()

    is_locked, lock_message = _lockout_check(email_norm)
    if is_locked:
        return False, lock_message

    db = get_db_session()
    try:
        user = db.query(User).filter(User.email == email_norm).first()
        if not user or not verify_password(password, user.password_hash):
            _record_failed_attempt(email_norm)
            still_locked, lock_message = _lockout_check(email_norm)
            if still_locked:
                return False, lock_message
            return False, "Incorrect email or password."
        if not user.is_active:
            return False, "This account has been suspended. Contact support for help."
        # Check email verification
        if not user.is_verified:
            return False, "Please verify your email address before logging in. Check your inbox (and Spam folder)."

        _clear_failed_attempts(email_norm)
        st.session_state.user = _user_to_session_dict(user)
        st.session_state.auth_token = secrets.token_hex(16)
        return True, "Login successful."
    finally:
        db.close()


def register_user(full_name: str, email: str, password: str):
    """Create a new student account. Returns (success: bool, message: str)."""
    from utils.email_service import send_verification_email

    db = get_db_session()
    try:
        email_norm = email.strip().lower()
        existing = db.query(User).filter(User.email == email_norm).first()
        if existing:
            return False, "An account with this email already exists. Try logging in instead."

        token = secrets.token_urlsafe(32)
        user = User(
            full_name=full_name.strip(),
            email=email_norm,
            password_hash=hash_password(password),
            role=UserRole.student,
            is_verified=False,
            is_active=True,
            verification_token=token,
        )
        db.add(user)
        db.commit()

        # Auto-subscribe the new student to the newsletter so they receive
        # announcement emails automatically, without needing to subscribe
        # separately. Wrapped so a failure here never blocks the (already
        # committed) account creation above.
        try:
            existing_sub = db.query(NewsletterSubscriber).filter(
                NewsletterSubscriber.email == email_norm
            ).first()
            if existing_sub:
                existing_sub.is_active = True
            else:
                db.add(NewsletterSubscriber(email=email_norm))
            db.commit()
        except Exception:
            db.rollback()

        send_verification_email(user.full_name, user.email, token)
        return True, "registration_pending"
    except Exception as e:
        db.rollback()
        return False, f"Could not create account: {e}"
    finally:
        db.close()


def verify_email_token(token: str):
    """Mark a user's email as verified given a verification token."""
    db = get_db_session()
    try:
        user = db.query(User).filter(User.verification_token == token).first()
        if not user:
            return False, "This verification link is invalid or has already been used."
        user.is_verified = True
        user.verification_token = None
        db.commit()
        return True, f"Email verified for {user.full_name}. You can now log in."
    finally:
        db.close()


def request_password_reset(email: str):
    from utils.email_service import send_password_reset_email

    db = get_db_session()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user:
            return True, "If an account exists for that email, a reset link has been sent."

        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=2)
        db.commit()

        send_password_reset_email(user.full_name, user.email, token)
        return True, "If an account exists for that email, a reset link has been sent."
    finally:
        db.close()


def reset_password_with_token(token: str, new_password: str):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.reset_token == token).first()
        if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
            return False, "This reset link is invalid or has expired. Please request a new one."

        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.commit()
        return True, "Your password has been reset. You can now log in."
    finally:
        db.close()
