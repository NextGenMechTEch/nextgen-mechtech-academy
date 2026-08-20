"""
Email sending service for NextGen MechTech Academy.

Transport: Brevo (formerly Sendinblue) Transactional Email API
(https://api.brevo.com/v3/smtp/email). Every function below that sends an
email (registration, password reset, contact form, notifications,
certificates, tutor applications, etc.) still funnels through the single
`send_email()` choke point — only the transport underneath it changed, so
all calling code elsewhere in the app is unaffected.

Credentials are read directly from the .env file on every call so they
are always current even if os.environ wasn't populated at startup.
"""
import os
import pathlib

import requests

_BRAND_NAVY  = "#0F2D6B"
_BRAND_BLUE  = "#2056D6"
_BRAND_AMBER = "#F59E0B"

_BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
_BREVO_ACCOUNT_URL = "https://api.brevo.com/v3/account"

# Path to the project .env file
_ENV_PATH = pathlib.Path(__file__).parent.parent / ".env"


def _read_env_file() -> dict:
    """Parse the .env file directly and return a key→value dict."""
    result = {}
    try:
        if _ENV_PATH.exists():
            for raw_line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                result[key.strip()] = val.strip()
    except Exception as e:
        print(f"[email_service] Could not read .env: {e}")
    return result


def _get(key: str, default: str = "") -> str:
    """
    Get a config value: .env file takes priority, then os.environ, then default.
    This ensures values are always found even if load_dotenv() didn't run.
    """
    env_file = _read_env_file()
    # .env file is authoritative
    if key in env_file and env_file[key]:
        return env_file[key]
    # Fall back to real environment variable
    val = os.environ.get(key, "")
    if val:
        return val
    return default


def _cfg() -> dict:
    return {
        "api_key":     _get("BREVO_API_KEY", ""),
        "sender_email": _get("BREVO_SENDER_EMAIL", ""),
        "sender_name": _get("BREVO_SENDER_NAME", "NextGen MechTech Academy"),
    }


def _app_url() -> str:
    return _get("APP_URL", "http://localhost:8501")


def _support_email() -> str:
    return _get("SUPPORT_EMAIL") or _get("BREVO_SENDER_EMAIL")


def _admin_email() -> str:
    return _get("ADMIN_EMAIL") or _get("BREVO_SENDER_EMAIL")


def _careers_email() -> str:
    return _get("CAREERS_EMAIL") or _get("ADMIN_EMAIL") or _get("BREVO_SENDER_EMAIL")


# Keep these as callable for backwards-compat with `from utils.email_service import ADMIN_EMAIL`
ADMIN_EMAIL   = _admin_email()   # resolved once at import for legacy callers
SUPPORT_EMAIL = _support_email() # resolved once at import for legacy callers
CAREERS_EMAIL = _careers_email() # resolved once at import for legacy callers


# ─── Core sender ─────────────────────────────────────────────────────────────
def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send one HTML email via the Brevo transactional email API.
    Returns True on success, False on failure. Same signature and return
    contract as before, so every caller elsewhere in the app is unaffected.
    """
    cfg = _cfg()
    api_key     = cfg["api_key"]
    sender_email = cfg["sender_email"]
    sender_name  = cfg["sender_name"]

    if not api_key:
        print("EMAIL ERROR: BREVO_API_KEY is not set in .env")
        return False
    if not sender_email:
        print("EMAIL ERROR: BREVO_SENDER_EMAIL is not set in .env")
        return False
    if not to_email:
        print("EMAIL ERROR: recipient address is empty")
        return False

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body,
    }
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        resp = requests.post(_BREVO_API_URL, json=payload, headers=headers, timeout=15)

        if resp.status_code in (200, 201):
            print(f"EMAIL OK: '{subject}' → {to_email}")
            return True

        if resp.status_code == 401:
            print(
                f"EMAIL ERROR: Brevo authentication failed (401).\n"
                "  Fix: check BREVO_API_KEY is a valid, active API key from "
                "the Brevo dashboard (SMTP & API → API Keys)."
            )
            return False

        try:
            detail = resp.json().get("message", resp.text)
        except Exception:
            detail = resp.text
        print(f"EMAIL ERROR: Brevo API returned {resp.status_code}: {detail}")
        return False

    except requests.exceptions.Timeout:
        print("EMAIL ERROR: Timed out connecting to Brevo API")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"EMAIL ERROR: Could not connect to Brevo API — {e}")
        return False
    except Exception as e:
        print(f"EMAIL ERROR: {type(e).__name__}: {e}")
        return False


def test_smtp_connection() -> tuple:
    """
    Verify Brevo API credentials without sending any message, by calling
    Brevo's /account endpoint. Kept under this name (rather than renaming to
    e.g. `test_brevo_connection`) so the Admin Panel's existing "Email
    Settings" tab continues to work with zero changes to its import line.
    Returns (success: bool, message: str).
    """
    cfg = _cfg()
    api_key      = cfg["api_key"]
    sender_email = cfg["sender_email"]

    if not api_key:
        return False, "BREVO_API_KEY is not set in your .env file."
    if not sender_email:
        return False, "BREVO_SENDER_EMAIL is not set in your .env file."

    try:
        resp = requests.get(
            _BREVO_ACCOUNT_URL,
            headers={"api-key": api_key, "Accept": "application/json"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            plan_email = data.get("email", sender_email)
            return True, f"✓ Connected and authenticated with Brevo — account: {plan_email}"

        if resp.status_code == 401:
            return False, (
                f"Authentication failed for Brevo API key.\n\n"
                "**Steps to fix:**\n"
                "1. Go to [app.brevo.com](https://app.brevo.com) → **SMTP & API** → **API Keys**\n"
                "2. Create (or copy) a valid API key\n"
                "3. Set `BREVO_API_KEY` in your `.env` file to that key\n"
                "4. Make sure `BREVO_SENDER_EMAIL` is a sender you've **verified** in "
                "Brevo → **Senders, Domains & Dedicated IPs**\n"
                "5. Restart Streamlit"
            )

        return False, f"Brevo API returned {resp.status_code}: {resp.text}"

    except requests.exceptions.Timeout:
        return False, "Timed out connecting to `api.brevo.com`. Check your network connection."
    except requests.exceptions.ConnectionError as e:
        return False, f"Network error connecting to Brevo API: `{e}`"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def get_smtp_status() -> dict:
    """Return a dict of current Brevo config for display in the admin panel.
    Kept under this name for backwards-compat with the existing Admin Panel
    import; field names describe Brevo credentials instead of raw SMTP ones.
    """
    cfg = _cfg()
    api_key = cfg["api_key"]
    return {
        "provider":       "Brevo (Transactional Email API)",
        "api_url":        _BREVO_API_URL,
        "api_key_set":    bool(api_key),
        "api_key_len":    len(api_key),
        "sender_email":   cfg["sender_email"],
        "sender_name":    cfg["sender_name"],
        "app_url":        _app_url(),
        "support":        _support_email(),
        "admin":          _admin_email(),
        "env_path":       str(_ENV_PATH),
        "env_exists":     _ENV_PATH.exists(),
    }


# ─── Template helpers ─────────────────────────────────────────────────────────
def _base_template(content_html: str, preheader: str = "") -> str:
    support = _support_email()
    return f"""
    <html>
    <body style="margin:0;padding:0;background:#F6F8FB;font-family:-apple-system,Segoe UI,Inter,sans-serif;">
      <div style="display:none;max-height:0;overflow:hidden;">{preheader}</div>
      <table width="100%" cellpadding="0" cellspacing="0" style="padding:32px 16px;">
        <tr><td align="center">
          <table width="560" cellpadding="0" cellspacing="0"
                 style="background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #E3E8F0;">
            <tr>
              <td style="background:linear-gradient(135deg,{_BRAND_NAVY},{_BRAND_BLUE});padding:28px 32px;">
                <span style="color:#ffffff;font-size:18px;font-weight:800;">NextGen MechTech Academy</span><br>
                <span style="color:rgba(255,255,255,0.7);font-size:11.5px;letter-spacing:0.08em;text-transform:uppercase;">Learn. Build. Innovate.</span>
              </td>
            </tr>
            <tr>
              <td style="padding:32px 32px 28px;color:#0E1726;font-size:14px;line-height:1.7;">
                {content_html}
              </td>
            </tr>
            <tr>
              <td style="padding:20px 32px;background:#F6F8FB;border-top:1px solid #E3E8F0;color:#67748B;font-size:12px;">
                NextGen MechTech Academy &middot; Lahore, Pakistan<br>
                Need help? <a href="mailto:{support}" style="color:{_BRAND_BLUE};">{support}</a>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """


def _button(label: str, url: str) -> str:
    return (
        f'<a href="{url}" style="display:inline-block;background:{_BRAND_NAVY};color:#ffffff;'
        f'text-decoration:none;padding:12px 26px;border-radius:8px;font-weight:600;font-size:14px;'
        f'margin:18px 0;">{label}</a>'
    )


# ─── Transactional emails ─────────────────────────────────────────────────────
def send_verification_email(full_name: str, to_email: str, token: str) -> bool:
    link = f"{_app_url()}?action=verify&token={token}"
    content = f"""
    <h2 style="color:{_BRAND_NAVY};margin:0 0 12px;">Welcome, {full_name}!</h2>
    <p>Thanks for creating an account with NextGen MechTech Academy. Please verify your
    email address to activate your account and start registering for courses.</p>
    {_button("Verify My Email", link)}
    <p style="color:#67748B;font-size:12.5px;">If you didn't create this account, you can safely ignore this email.</p>
    """
    return send_email(to_email, "Verify your email — NextGen MechTech Academy",
                      _base_template(content, "Verify your email to get started"))


def send_password_reset_email(full_name: str, to_email: str, token: str) -> bool:
    link = f"{_app_url()}?action=reset_password&token={token}"
    content = f"""
    <h2 style="color:{_BRAND_NAVY};margin:0 0 12px;">Reset your password</h2>
    <p>Hi {full_name}, we received a request to reset your password. This link is valid for 2 hours.</p>
    {_button("Reset Password", link)}
    <p style="color:#67748B;font-size:12.5px;">If you didn't request this, ignore this email.</p>
    """
    return send_email(to_email, "Reset your password — NextGen MechTech Academy",
                      _base_template(content, "Reset your password"))


def send_contact_confirmation(name: str, to_email: str, subject: str) -> bool:
    content = f"""
    <h2 style="color:{_BRAND_NAVY};margin:0 0 12px;">We've received your message</h2>
    <p>Hi {name}, thanks for reaching out. Your message regarding <strong>"{subject}"</strong>
    has been received and our team will respond within 24 hours.</p>
    """
    return send_email(to_email, "We've received your message — NextGen MechTech Academy",
                      _base_template(content, "Thanks for contacting us"))


def send_tutor_application_received(name: str, to_email: str) -> bool:
    content = f"""
    <h2 style="color:{_BRAND_NAVY};margin:0 0 12px;">Application Received</h2>
    <p>Hi {name}, thank you for applying to join our team. We will review your application
    and get back to you within 5–7 business days.</p>
    """
    return send_email(to_email, "Application Received — NextGen MechTech Academy",
                      _base_template(content, "Your tutor application has been received"))


def send_registration_confirmation(full_name: str, to_email: str, course_title: str) -> bool:
    content = f"""
    <h2 style="color:{_BRAND_NAVY};margin:0 0 12px;">Registration Submitted</h2>
    <p>Hi {full_name}, your registration for <strong>{course_title}</strong> has been submitted.
    Our team will verify your payment and confirm your seat within 24–48 hours.</p>
    """
    return send_email(to_email, f"Registration Received: {course_title}",
                      _base_template(content, "Your course registration is being reviewed"))


def send_admin_new_registration(to_email: str, full_name: str, course_title: str) -> bool:
    content = f"""
    <h2 style="color:{_BRAND_NAVY};margin:0 0 12px;">New Course Registration</h2>
    <p><strong>{full_name}</strong> has registered for <strong>{course_title}</strong>.
    Please review and approve or reject from the Admin Panel.</p>
    """
    return send_email(to_email, f"New Registration: {course_title}",
                      _base_template(content, "A student submitted a new registration"))


def send_registration_approved(full_name: str, to_email: str, course_title: str) -> bool:
    content = f"""
    <h2 style="color:#15803D;margin:0 0 12px;">Registration Approved ✓</h2>
    <p>Hi {full_name}, your registration for <strong>{course_title}</strong> has been approved.</p>
    {_button("Go to Dashboard", _app_url())}
    """
    return send_email(to_email, f"Approved: {course_title}",
                      _base_template(content, "Your registration has been approved"))


def send_registration_rejected(full_name: str, to_email: str, course_title: str,
                                reason: str = "") -> bool:
    reason_html = (
        f'<p style="background:#F6F8FB;border-radius:8px;padding:12px 16px;">{reason}</p>'
    ) if reason else ""
    content = f"""
    <h2 style="color:#B91C1C;margin:0 0 12px;">Registration Update</h2>
    <p>Hi {full_name}, we could not approve your registration for <strong>{course_title}</strong>.</p>
    {reason_html}
    <p>Please contact support if you believe this is a mistake.</p>
    """
    return send_email(to_email, f"Update on your registration: {course_title}",
                      _base_template(content, "An update on your course registration"))


def send_tutor_application_approved(name: str, to_email: str) -> bool:
    content = f"""
    <h2 style="color:#15803D;margin:0 0 12px;">Application Approved ✓</h2>
    <p>Hi {name}, congratulations! Your application to join the NextGen MechTech Academy
    team as a tutor has been approved.</p>
    <p>Our team will be in touch shortly with onboarding details. In the meantime, you can
    log in to your dashboard to get started.</p>
    {_button("Go to Dashboard", _app_url())}
    """
    return send_email(to_email, "Tutor Application Approved — NextGen MechTech Academy",
                      _base_template(content, "Your tutor application has been approved"))


def send_tutor_application_rejected(name: str, to_email: str, reason: str = "") -> bool:
    reason_html = (
        f'<p style="background:#F6F8FB;border-radius:8px;padding:12px 16px;">{reason}</p>'
    ) if reason else ""
    content = f"""
    <h2 style="color:#B91C1C;margin:0 0 12px;">Application Update</h2>
    <p>Hi {name}, thank you for your interest in joining the NextGen MechTech Academy team.
    After careful review, we won't be moving forward with your application at this time.</p>
    {reason_html}
    <p>We encourage you to apply again in the future as new opportunities open up.</p>
    """
    return send_email(to_email, "Update on your Tutor Application — NextGen MechTech Academy",
                      _base_template(content, "An update on your tutor application"))


def send_certificate_issued(full_name: str, to_email: str, course_title: str,
                             certificate_id: str, verify_url: str) -> bool:
    content = f"""
    <h2 style="color:{_BRAND_NAVY};margin:0 0 12px;">🏆 Certificate Issued!</h2>
    <p>Hi {full_name}, congratulations on completing <strong>{course_title}</strong>!
    Your certificate has been issued.</p>
    <p style="background:#F6F8FB;border-radius:8px;padding:12px 16px;">
      <strong>Certificate ID:</strong> <code>{certificate_id}</code>
    </p>
    {_button("View & Verify Certificate", verify_url)}
    <p style="color:#67748B;font-size:12.5px;">You can verify this certificate at any time using the Certificate ID above.</p>
    """
    return send_email(to_email, f"Your certificate for {course_title} is ready — NextGen MechTech Academy",
                      _base_template(content, "Your certificate has been issued"))
