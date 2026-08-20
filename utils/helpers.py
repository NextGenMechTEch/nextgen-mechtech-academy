"""
General-purpose helpers used across pages: logo loading, image encoding,
and website settings (key/value store backed by the WebsiteSettings table).
"""
import base64
import html
import os
import re
import time
from contextlib import contextmanager
from functools import lru_cache
from urllib.parse import parse_qs, urlencode, urlparse

import streamlit as st


# ─── Dev-only performance instrumentation ───────────────────────────────────
# Temporary Phase-2 diagnostic: measures how long a labeled block takes.
# Silent no-op unless DEBUG_PERF=1 is set in the environment/.env, so it
# produces zero output — and effectively zero overhead — in normal/production
# use. Prints to the terminal running `streamlit run`, not to the browser UI.
# Safe to remove entirely once Phase 2 improvements are measured and confirmed.
@contextmanager
def perf_timer(label: str):
    if os.getenv("DEBUG_PERF") != "1":
        yield
        return
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"[PERF] {label}: {elapsed_ms:.1f} ms")


# ─── Flash messages ──────────────────────────────────────────────────────────
# Streamlit clears whatever was on screen the moment st.rerun() is called, so
# any st.success()/st.error()/st.info() shown right before a rerun never
# actually reaches the user. flash_message() queues the message in
# session_state instead; render_flash_messages() (called once per run from
# app.py) displays and clears whatever is queued after the rerun completes.
def flash_message(message: str, kind: str = "success") -> None:
    """Queue a message to be shown after the next st.rerun().

    kind must be one of the streamlit alert functions: "success", "error",
    "info", or "warning".
    """
    queue = st.session_state.get("_flash_messages", [])
    queue.append((kind, message))
    st.session_state["_flash_messages"] = queue


def render_flash_messages() -> None:
    """Display and clear any messages queued by flash_message().

    Safe to call on every run: it's a no-op when the queue is empty.
    """
    queue = st.session_state.pop("_flash_messages", None)
    if not queue:
        return
    for kind, message in queue:
        renderer = getattr(st, kind, st.success)
        renderer(message)


def esc(value) -> str:
    """HTML-escape a value before it is interpolated into a raw HTML string.

    Used to prevent stored XSS from user-submitted free-text fields (e.g.
    instructor-submitted course content) that get rendered via
    st.markdown(..., unsafe_allow_html=True). `None` becomes an empty
    string; non-string values are stringified first. Safe to wrap around
    values that are already plain/trusted text — escaping plain text with
    no special characters leaves it unchanged.
    """
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def is_valid_email(email: str) -> bool:
    """Lightweight email format check (same rule used at registration in
    pages/login.py): requires an "@" and a "." somewhere after it."""
    if not email:
        return False
    email = email.strip()
    if "@" not in email:
        return False
    local, _, domain = email.rpartition("@")
    return bool(local) and "." in domain and not domain.startswith(".")


# ─── YouTube embeds (Hero promo video, etc.) ────────────────────────────────
# 11-char alphanumeric/-/_ is the fixed shape of every YouTube video ID.
_YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_YOUTUBE_HOSTS = {"youtube.com", "youtu.be", "youtube-nocookie.com"}


def extract_youtube_id(url: str) -> str | None:
    """Safely pull the 11-character video ID out of any common YouTube URL
    shape (watch, youtu.be, embed, shorts, live), with or without extra
    tracking query params (e.g. `?si=...`). Returns None for anything that
    isn't a recognizable, well-formed YouTube video URL — callers should
    treat None as "invalid" and not build an embed from it.
    """
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except ValueError:
        return None

    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    elif host.startswith("m."):
        host = host[2:]
    if host not in _YOUTUBE_HOSTS:
        return None

    video_id = None
    if host == "youtu.be":
        video_id = parsed.path.lstrip("/").split("/")[0]
    else:
        path_parts = [p for p in parsed.path.split("/") if p]
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        elif path_parts and path_parts[0] in {"embed", "shorts", "live", "v"} and len(path_parts) > 1:
            video_id = path_parts[1]

    if video_id and _YOUTUBE_ID_RE.match(video_id):
        return video_id
    return None


def build_youtube_embed_url(video_id: str, autoplay: bool = True, muted: bool = True,
                            loop: bool = True, controls: bool = True) -> str:
    """Build an official youtube.com/embed URL for `video_id` with the given
    player options. Looping a single video requires YouTube's `playlist`
    param to repeat that same ID, so it's added automatically when loop=True.
    """
    params = {
        "autoplay": "1" if autoplay else "0",
        "mute": "1" if muted else "0",
        "controls": "1" if controls else "0",
        "loop": "1" if loop else "0",
        "playsinline": "1",
        "rel": "0",
    }
    if loop:
        params["playlist"] = video_id
    return f"https://www.youtube.com/embed/{video_id}?{urlencode(params)}"


def build_youtube_watch_url(video_id: str) -> str:
    """Canonical youtube.com/watch link for `video_id` — used for the
    "Watch on YouTube" link alongside an embed."""
    return f"https://www.youtube.com/watch?v={video_id}"


def check_upload_size(uploaded_file, max_mb: float) -> bool:
    """Return True if `uploaded_file` is within `max_mb` megabytes.

    Returns True when there's no file to check (None) so callers can use
    this purely as a size gate without needing a separate None-check.
    """
    if uploaded_file is None:
        return True
    size = getattr(uploaded_file, "size", None)
    if size is None:
        return True
    return size <= max_mb * 1024 * 1024


def html_block(text: str) -> str:
    """Strip leading whitespace from every line of an HTML string.

    Streamlit's st.markdown() renders lines indented 4+ spaces as a
    Markdown code block instead of parsing them as HTML. Multi-line f-strings
    built inside nested loops/functions pick up Python's indentation, so
    textwrap.dedent (which only removes the *common* leading whitespace)
    isn't enough when inner lines are indented deeper than the outer line.
    This strips ALL leading whitespace from every line so nothing is left
    that Markdown could mistake for an indented code block.
    """
    return "\n".join(line.lstrip() for line in text.split("\n")).strip()


# ─── Logo ──────────────────────────────────────────────────────────────────
_LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png")


@lru_cache(maxsize=1)
def get_logo_base64():
    """Return the academy logo as a base64 string, or None if not found."""
    try:
        with open(_LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except (FileNotFoundError, OSError):
        return None


def image_to_base64(image_bytes: bytes) -> str:
    """Encode raw image bytes (e.g. from st.file_uploader) to a base64 string."""
    return base64.b64encode(image_bytes).decode()


# ─── Website settings (key/value store) ─────────────────────────────────────
# TTL=300s (5 min): site settings (name, taglines, stats, social links, hero
# copy, etc.) are edited rarely via the admin panel, so a short window of
# staleness after a save is an acceptable trade-off for cutting this from
# 2-3 DB round trips per page to roughly one every 5 minutes. Returns a
# plain dict (no ORM objects, no per-user data) so it's safe to share the
# cached value across every user's session.
@st.cache_data(ttl=300, show_spinner=False)
def get_all_settings() -> dict:
    """Return all WebsiteSettings rows as a plain dict {key: value}."""
    from database.connection import get_db_session
    from database.models import WebsiteSettings

    db = get_db_session()
    try:
        rows = db.query(WebsiteSettings).all()
        return {row.key: row.value for row in rows}
    finally:
        db.close()


def get_setting(key: str, default: str = "") -> str:
    """Return a single setting value, falling back to `default` if unset."""
    from database.connection import get_db_session
    from database.models import WebsiteSettings

    db = get_db_session()
    try:
        row = db.query(WebsiteSettings).filter(WebsiteSettings.key == key).first()
        return row.value if row and row.value is not None else default
    finally:
        db.close()


def update_setting(key: str, value: str) -> None:
    """Create or update a single website setting."""
    from database.connection import get_db_session
    from database.models import WebsiteSettings

    db = get_db_session()
    try:
        row = db.query(WebsiteSettings).filter(WebsiteSettings.key == key).first()
        if row:
            row.value = value
        else:
            db.add(WebsiteSettings(key=key, value=value))
        db.commit()
    finally:
        db.close()
    # Every settings write goes through this one function, so clearing the
    # get_all_settings() cache here (rather than at each of its many admin
    # call sites) guarantees any saved change is visible on the very next
    # page render instead of waiting out the 5-minute TTL.
    get_all_settings.clear()


# ─── Payment methods (configurable via Admin Panel — no code changes needed) ─
def _payment_method_to_dict(row) -> dict:
    return {
        "id": row.id,
        "method_key": row.method_key,
        "label": row.label,
        "account_title": row.account_title or "",
        "account_number": row.account_number or "",
        "custom_message": row.custom_message or "",
        "is_enabled": bool(row.is_enabled),
        "display_order": row.display_order or 0,
    }


def get_all_payment_methods() -> list:
    """Return every payment method (enabled and disabled) as plain dicts, in
    display order. Used by the Admin Panel to manage the full list."""
    from database.connection import get_db_session
    from database.models import PaymentMethod

    db = get_db_session()
    try:
        rows = (db.query(PaymentMethod)
                .order_by(PaymentMethod.display_order, PaymentMethod.id)
                .all())
        return [_payment_method_to_dict(r) for r in rows]
    finally:
        db.close()


def get_enabled_payment_methods() -> list:
    """Return only the enabled payment methods, in display order, as plain
    dicts. This is what the registration form should offer to students."""
    from database.connection import get_db_session
    from database.models import PaymentMethod

    db = get_db_session()
    try:
        rows = (db.query(PaymentMethod)
                .filter(PaymentMethod.is_enabled == True)
                .order_by(PaymentMethod.display_order, PaymentMethod.id)
                .all())
        return [_payment_method_to_dict(r) for r in rows]
    finally:
        db.close()


def update_payment_method(method_id: int, label: str = None, account_title: str = None,
                          account_number: str = None, custom_message: str = None,
                          is_enabled: bool = None, display_order: int = None) -> bool:
    """Update one or more fields of an existing payment method."""
    from database.connection import get_db_session
    from database.models import PaymentMethod
    from datetime import datetime as _dt

    db = get_db_session()
    try:
        row = db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
        if not row:
            return False
        if label is not None:
            row.label = label
        if account_title is not None:
            row.account_title = account_title or None
        if account_number is not None:
            row.account_number = account_number or None
        if custom_message is not None:
            row.custom_message = custom_message or None
        if is_enabled is not None:
            row.is_enabled = is_enabled
        if display_order is not None:
            row.display_order = display_order
        row.updated_at = _dt.utcnow()
        db.commit()
        return True
    finally:
        db.close()


def add_payment_method(method_key: str, label: str, account_title: str = "",
                       account_number: str = "", custom_message: str = "",
                       is_enabled: bool = True, display_order: int = 0) -> bool:
    """Add a brand-new payment method. Lets the Admin Panel stay future-proof
    beyond the default EasyPaisa / JazzCash / Bank Transfer set."""
    from database.connection import get_db_session
    from database.models import PaymentMethod

    db = get_db_session()
    try:
        existing = db.query(PaymentMethod).filter(PaymentMethod.method_key == method_key).first()
        if existing:
            return False
        db.add(PaymentMethod(
            method_key=method_key, label=label,
            account_title=account_title or None, account_number=account_number or None,
            custom_message=custom_message or None, is_enabled=is_enabled,
            display_order=display_order,
        ))
        db.commit()
        return True
    finally:
        db.close()


def delete_payment_method(method_id: int) -> bool:
    """Remove a payment method from the configurable list."""
    from database.connection import get_db_session
    from database.models import PaymentMethod

    db = get_db_session()
    try:
        row = db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True
    finally:
        db.close()
