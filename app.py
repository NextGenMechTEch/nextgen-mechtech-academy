import streamlit as st
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv
load_dotenv()

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NextGen MechTech Academy",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "mailto:support.nextgenmechtech@gmail.com",
        "About": "NextGen MechTech Academy — Learn. Build. Innovate.",
    },
)

# ─── Google Analytics ────────────────────────────────────────────────────────
components.html("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-535DTWSDJ6"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-535DTWSDJ6');
</script>
""", height=0)

# ─── Database init ───────────────────────────────────────────────────────────
# initialize_database() runs schema creation/migration checks plus several
# "seed if empty" COUNT queries against the database. It is idempotent (safe
# to run more than once — it only creates what's missing), but each call is
# a handful of real network round trips to the DB. Wrapping it in
# st.cache_resource means Streamlit runs the function body exactly once per
# server process and reuses that outcome for every user/session/rerun after
# that — matching the fact that "is the schema set up and seeded" is a
# shared, process-wide fact, not something that varies per user or per page
# navigation. st.cache_resource (not st.cache_data) is the correct tool here
# because this call's purpose is its side effects, not a value to hash and
# store — cache_resource skips value hashing/serialization entirely, which
# is exactly what a setup-once function like this needs.
@st.cache_resource(show_spinner=False)
def _run_database_initialization() -> bool:
    from database.init_db import initialize_database
    initialize_database()
    return True

from utils.helpers import perf_timer, html_block

try:
    with perf_timer("database_init"):
        _run_database_initialization()
except Exception as e:
    # This happens before login is even possible (the DB itself is down),
    # so there's no way yet to tell if the visitor is staff — show the same
    # professional message to everyone and rely on server logs for detail.
    import traceback
    print("[ERROR] Database initialization failed:")
    traceback.print_exc()
    st.markdown("""
    <div style="max-width:520px;margin:80px auto;text-align:center;padding:40px 32px;
         background:#fff;border:1px solid #e5e7eb;border-radius:12px;">
      <div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:8px;">
        We're temporarily unavailable
      </div>
      <div style="font-size:13.5px;color:#6b7280;line-height:1.6;">
        We're working to restore service — please try again in a moment.<br>
        Contact <a href="mailto:support.nextgenmechtech@gmail.com">support.nextgenmechtech@gmail.com</a> if this persists.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ─── Imports ─────────────────────────────────────────────────────────────────
from components.styles import inject_css
from components.navbar import render_visible_navbar, render_footer, render_whatsapp_button
from pages.home import render_home
from pages.courses import render_courses
from pages.careers import render_careers
from pages.about import render_about
from pages.contact import render_contact
from pages.login import render_login
from pages.dashboard import render_dashboard
from pages.admin import render_admin
from pages.verify import render_verify
from pages.privacy import render_privacy
from pages.terms import render_terms

# ─── Session State Init ───────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "home"
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "user" not in st.session_state:
    st.session_state.user = None

# ─── Handle URL query params ─────────────────────────────────────────────────
params = st.query_params
if "page" in params:
    allowed_pages = {"home", "courses", "careers", "about", "contact", "login", "dashboard", "admin", "verify", "privacy", "terms"}
    p = params.get("page")
    if p in allowed_pages:
        st.session_state.page = p
if "action" in params:
    action = params.get("action")
    if action in ("verify", "reset_password"):
        st.session_state.page = "login"

# ─── Inject Global CSS ───────────────────────────────────────────────────────
inject_css()

# ─── Routing ─────────────────────────────────────────────────────────────────
current_page = st.session_state.page

ADMIN_PAGES = {"admin"}
AUTH_REQUIRED_PAGES = {"dashboard", "admin"}

if current_page in AUTH_REQUIRED_PAGES and not st.session_state.user:
    st.session_state.page = "login"
    current_page = "login"

if current_page == "admin":
    user = st.session_state.get("user")
    if not user or user.get("role") not in ("admin", "super_admin", "instructor", "content_manager"):
        st.session_state.page = "dashboard"
        current_page = "dashboard"

# ─── Error handling helpers ───────────────────────────────────────────────────
_STAFF_ROLES = {"admin", "super_admin", "instructor", "content_manager"}

def _is_staff_viewer() -> bool:
    user = st.session_state.get("user")
    return bool(user and user.get("role") in _STAFF_ROLES)


def _show_page_error(exc: Exception, where: str) -> None:
    """Public/student visitors see a short, professional message with no
    technical detail. Anyone logged in with a staff role (admin, super_admin,
    instructor, content_manager) sees the real exception, since they're the
    people who'd need it to actually debug the issue. Either way, the full
    traceback is always printed to the server logs (visible in your
    terminal when run locally, or under "Manage app" -> Logs on Streamlit
    Community Cloud) so nothing is lost even when no staff member is looking
    at the screen when the error happens.
    """
    import traceback
    print(f"[ERROR] Unhandled exception in {where}:")
    traceback.print_exc()

    if _is_staff_viewer():
        st.error(f"**{type(exc).__name__}:** {exc}")
        with st.expander("Full technical details (visible to staff only)"):
            st.code(traceback.format_exc())
    else:
        st.markdown(html_block("""
        <div style="max-width:520px;margin:60px auto;text-align:center;padding:40px 32px;
             background:var(--surface,#fff);border:1px solid var(--border,#e5e7eb);
             border-radius:var(--radius-lg,12px);">
          <div style="font-size:15px;font-weight:700;color:var(--ink-900,#111827);margin-bottom:8px;">
            Something went wrong on our end
          </div>
          <div style="font-size:13.5px;color:var(--ink-500,#6b7280);line-height:1.6;">
            We're working on it — please try again in a moment.<br>
            If this keeps happening, contact us at
            <a href="mailto:support.nextgenmechtech@gmail.com">support.nextgenmechtech@gmail.com</a>.
          </div>
        </div>
        """), unsafe_allow_html=True)


# ─── Render Navigation ────────────────────────────────────────────────────────
if current_page not in ADMIN_PAGES:
    with perf_timer("render_navbar"):
        try:
            render_visible_navbar(current_page)
        except Exception as exc:
            _show_page_error(exc, "navbar")

# ─── Flash Messages (queued before a st.rerun() on the previous run) ────────
from utils.helpers import render_flash_messages
render_flash_messages()

# ─── Render Page ─────────────────────────────────────────────────────────────
# Safe, opt-in way to verify this error handling actually works — see the
# testing instructions given alongside this change. Requires BOTH the env
# var and the query param, so it can never fire by accident in normal use,
# and does nothing at all unless ALLOW_TEST_ERROR=1 is explicitly set.
if os.getenv("ALLOW_TEST_ERROR") == "1" and st.query_params.get("trigger_test_error") == "1":
    with perf_timer(f"render_page:{current_page}"):
        try:
            raise RuntimeError("This is a deliberate test error (ALLOW_TEST_ERROR=1) used to verify error handling.")
        except Exception as exc:
            _show_page_error(exc, f"page:{current_page}")
else:
    with perf_timer(f"render_page:{current_page}"):
        try:
            if current_page == "home":
                render_home()
            elif current_page == "courses":
                render_courses()
            elif current_page == "careers":
                render_careers()
            elif current_page == "about":
                render_about()
            elif current_page == "contact":
                render_contact()
            elif current_page == "login":
                render_login()
            elif current_page == "dashboard":
                render_dashboard()
            elif current_page == "admin":
                render_admin()
            elif current_page == "verify":
                render_verify()
            elif current_page == "privacy":
                render_privacy()
            elif current_page == "terms":
                render_terms()
            else:
                st.session_state.page = "home"
                st.rerun()
        except Exception as exc:
            _show_page_error(exc, f"page:{current_page}")

# ─── Footer ──────────────────────────────────────────────────────────────────
if current_page not in {"admin", "dashboard", "login"}:
    with perf_timer("render_footer"):
        try:
            render_footer()
        except Exception as exc:
            _show_page_error(exc, "footer")

# ─── Floating WhatsApp Support Button ────────────────────────────────────────
# Shown on every public-facing page (everything except the internal admin
# backend). Renders nothing if no valid number is configured in Admin Panel
# -> Website Settings -> Contact & Stats.
if current_page not in ADMIN_PAGES:
    with perf_timer("render_whatsapp_button"):
        try:
            render_whatsapp_button()
        except Exception as exc:
            _show_page_error(exc, "whatsapp_button")
