"""
Navigation bar and footer — CMS-driven with database fallback to hardcoded defaults.
"""
import re
import streamlit as st
import textwrap
import json
from components.icons import icon
from utils.helpers import get_logo_base64, get_all_settings, html_block
from database.connection import get_db_session
from database.models import NewsletterSubscriber


_DEFAULT_NAV = [
    {"label": "Home",                "page_key": "home",    "icon_name": "home"},
    {"label": "Courses",             "page_key": "courses", "icon_name": "book-open"},
    {"label": "About",               "page_key": "about",   "icon_name": "info"},
    {"label": "Careers",             "page_key": "careers", "icon_name": "briefcase"},
    {"label": "Contact",             "page_key": "contact", "icon_name": "mail"},
    {"label": "Verify Certificate",  "page_key": "verify",  "icon_name": "award"},
]


# TTL=300s (5 min): nav items are edited very rarely via the admin panel.
# Returns plain dicts (no ORM objects, no per-user data), so the cached
# value is safe to share across every user's session.
@st.cache_data(ttl=300, show_spinner=False)
def _get_nav_items() -> list[dict]:
    """Return nav items from DB if available, else return defaults."""
    try:
        from database.connection import get_db_session
        from database.models import NavItem
        db = get_db_session()
        try:
            items = (db.query(NavItem)
                .filter(NavItem.is_visible == True)
                .order_by(NavItem.display_order)
                .all())
            if items:
                return [{"label": i.label, "page_key": i.page_key, "icon_name": i.icon_name or ""} for i in items]
        finally:
            db.close()
    except Exception:
        pass
    return _DEFAULT_NAV


def render_visible_navbar(current_page: str):
    logo_b64   = get_logo_base64()
    settings   = get_all_settings()
    site_name  = settings.get("site_name", "NextGen MechTech Academy")
    nav_items  = _get_nav_items()

    logo_html = (f'<img src="data:image/png;base64,{logo_b64}" '
                 f'style="height:36px;width:auto;border-radius:8px;" alt="{site_name}">'
                 if logo_b64 else f'<span class="nmt-nav-brand-text">{site_name}</span>')

    user = st.session_state.get("user")

    with st.container(key="nmt_navbar"):
        st.markdown(html_block(f"""
        <div class="nmt-nav">
          <div class="nmt-nav-inner">
            <div class="nmt-nav-brand">
              {logo_html}
              <span class="nmt-nav-brand-text">{site_name}</span>
            </div>
            <nav class="nmt-nav-links-placeholder"></nav>
          </div>
        </div>
        """), unsafe_allow_html=True)

        # Render nav buttons in a single horizontal row
        nav_col_count = len(nav_items) + (2 if user else 1)
        cols = st.columns([2] + [1] * len(nav_items) + ([1, 1] if user else [1]))

        for i, item in enumerate(nav_items):
            with cols[i + 1]:
                is_active = current_page == item["page_key"]
                btn_type = "primary" if is_active else "secondary"
                if st.button(item["label"], key=f"nav_{item['page_key']}", use_container_width=True, type=btn_type):
                    st.session_state.page = item["page_key"]
                    st.session_state.selected_course_id = None
                    st.rerun()

        if user:
            with cols[-2]:
                if st.button("Dashboard", key="nav_dash", use_container_width=True,
                             type="primary" if current_page == "dashboard" else "secondary"):
                    st.session_state.page = "dashboard"; st.rerun()
            with cols[-1]:
                if st.button("Log Out", key="nav_logout", use_container_width=True):
                    st.session_state.auth_token = None
                    st.session_state.user = None
                    st.session_state.page = "home"
                    st.rerun()
        else:
            with cols[-1]:
                if st.button("Login / Register", key="nav_login", use_container_width=True, type="primary"):
                    st.session_state.page = "login"; st.rerun()


def render_footer():
    settings = get_all_settings()
    site_name    = settings.get("site_name",       "NextGen MechTech Academy")
    footer_tag   = settings.get("footer_tagline",  "Learn. Build. Innovate.")
    footer_desc  = settings.get("footer_desc",
        "Premier technical education institute based in Lahore, Pakistan. "
        "Empowering engineers and technologists with industry-relevant skills.")
    f_email      = settings.get("footer_email",    settings.get("contact_email",   "support.nextgenmechtech@gmail.com"))
    f_phone      = settings.get("footer_phone",    settings.get("contact_phone",   ""))
    f_address    = settings.get("footer_address",  settings.get("contact_address", "Lahore, Pakistan"))
    f_hours      = settings.get("footer_hours",    "Mon–Sat: 9 AM–6 PM")
    copyright_t  = settings.get("footer_copyright",f"© 2025 {site_name}. All rights reserved.")
    fb_url       = settings.get("facebook_url",    "https://facebook.com/nextgenmechtech")
    ig_url       = settings.get("instagram_url",   "https://instagram.com/nextgenmechtech")
    li_url       = settings.get("linkedin_url",    "https://linkedin.com/company/nextgenmechtech")
    yt_url       = settings.get("youtube_url",     "https://youtube.com/nextgenmechtech")

    logo_b64 = get_logo_base64()
    logo_html = (f'<img src="data:image/png;base64,{logo_b64}" '
                 f'style="height:32px;width:auto;border-radius:6px;" alt="{site_name}">'
                 if logo_b64 else "")

    # Quick links from CMS
    try:
        from pages.cms_admin import get_cms_section
        sec = get_cms_section("footer", "quick_links")
        quick_links = json.loads(sec["content"]) if sec["content"] else []
    except:
        quick_links = []
    if not quick_links:
        quick_links = [
            {"label": "Home",               "page": "home"},
            {"label": "Courses",            "page": "courses"},
            {"label": "About Us",           "page": "about"},
            {"label": "Careers",            "page": "careers"},
            {"label": "Contact",            "page": "contact"},
            {"label": "Verify Certificate", "page": "verify"},
        ]

    # Internal pages the app already knows how to route to (kept in sync with
    # the allowed_pages set in app.py). Any quick link pointing elsewhere
    # simply falls back to the home page instead of producing a dead link.
    _ROUTABLE_PAGES = {"home", "courses", "careers", "about", "contact", "login", "verify", "privacy", "terms"}

    def _page_href(page_key: str) -> str:
        page_key = page_key if page_key in _ROUTABLE_PAGES else "home"
        return f"?page={page_key}"

    links_html = "".join(
        f'<a class="flink" href="{_page_href(lnk.get("page", "home"))}" target="_self">{lnk["label"]}</a>'
        for lnk in quick_links
    )

    # Digits (and a leading +) only, so "tel:" always gets a dialable number
    # even when the display text has spaces, dashes, or parentheses.
    phone_digits = "".join(ch for ch in f_phone if ch.isdigit() or ch == "+")
    phone_row = (
        f'<a class="contact-line" href="tel:{phone_digits}" style="color:#A9B6CE;text-decoration:none;">'
        f'{icon("phone", size=13, color="#8C9AB5")} {f_phone}</a>'
        if f_phone else ""
    )

    # Privacy Policy / Terms of Service: prefer an externally configured URL
    # (set via the Admin Panel) and fall back to the built-in pages.
    privacy_url = settings.get("privacy_url", "").strip()
    terms_url_s = settings.get("terms_url", "").strip()
    privacy_href = f'href="{privacy_url}" target="_blank" rel="noopener"' if privacy_url else f'href="{_page_href("privacy")}" target="_self"'
    terms_href   = f'href="{terms_url_s}" target="_blank" rel="noopener"' if terms_url_s else f'href="{_page_href("terms")}" target="_self"'

    social_html = ""
    for url, ic_name, bg in [
        (fb_url, "facebook", "#1877F2"),
        (ig_url, "instagram", "#E4405F"),
        (li_url, "linkedin",  "#0A66C2"),
        (yt_url, "youtube",   "#FF0000"),
    ]:
        if url:
            social_html += f'<a href="{url}" target="_blank" rel="noopener" class="nmt-social-btn" style="background:{bg};width:32px;height:32px;">{icon(ic_name, size=14, color="#fff")}</a>'

    st.markdown(html_block(f"""
    <div class="nmt-footer">
      <div class="nmt-footer-inner">
        <div class="nmt-footer-grid">
          <div>
            <div class="nmt-footer-brand">
              {logo_html}
              <span class="nmt-footer-brand-text">{site_name}</span>
            </div>
            <p class="desc">{footer_desc}</p>
            <div style="font-size:12.5px;color:var(--amber-400);font-weight:600;margin-bottom:14px;">{footer_tag}</div>
            <div class="nmt-social-row">{social_html}</div>
          </div>
          <div>
            <h4>Quick Links</h4>
            {links_html}
          </div>
          <div>
            <h4>Contact</h4>
            <a class="contact-line" href="mailto:{f_email}" style="color:#A9B6CE;text-decoration:none;">{icon("mail", size=13, color="#8C9AB5")} {f_email}</a>
            {phone_row}
            <div class="contact-line">{icon("map-pin", size=13, color="#8C9AB5")} {f_address}</div>
            <div class="contact-line">{icon("clock", size=13, color="#8C9AB5")} {f_hours}</div>
          </div>
          <div>
            <h4>Academy</h4>
            <a class="flink" href="{_page_href('login')}" target="_self">Student Login</a>
            <a class="flink" href="{_page_href('verify')}" target="_self">Certificate Verify</a>
            <a class="flink" href="{_page_href('careers')}" target="_self">Apply as Instructor</a>
            <a class="flink" {privacy_href}>Privacy Policy</a>
            <a class="flink" {terms_href}>Terms of Service</a>
          </div>
        </div>
      </div>
    </div>
    """), unsafe_allow_html=True)

    # Newsletter bar — integrated as a bordered strip between the footer grid
    # and the copyright bar, functionally wired to NewsletterSubscriber.
    # Wrapped in a keyed container so CSS in styles.py (.st-key-footer_newsletter)
    # can theme it to match the footer above/below. Heading/text sits left,
    # the subscribe form sits right on desktop, and stacks on narrow screens
    # (Streamlit's own horizontal-block layout already wraps to vertical there).
    with st.container(key="footer_newsletter"):
        nl_text_col, nl_form_col = st.columns([1, 1.15], gap="large")
        with nl_text_col:
            st.markdown(html_block(f"""
            <div class="nmt-footer-nl-text">
              <div class="nmt-footer-nl-heading">{icon("mail", size=15, color="var(--amber-400)")} Get Course Updates</div>
              <p class="nmt-footer-nl-sub">Get updates on new courses, workshops, and opportunities.</p>
            </div>
            """), unsafe_allow_html=True)
        with nl_form_col:
            with st.form("footer_newsletter_form", clear_on_submit=True, border=False):
                nl_col1, nl_col2 = st.columns([3, 1], gap="small")
                with nl_col1:
                    nl_email = st.text_input("Email", placeholder="Enter your email address", label_visibility="collapsed", key="footer_nl_email")
                with nl_col2:
                    nl_submitted = st.form_submit_button("Subscribe", use_container_width=True)
            if nl_submitted:
                nl_email_clean = (nl_email or "").strip().lower()
                if not nl_email_clean or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", nl_email_clean):
                    st.error("Please enter a valid email address.")
                else:
                    db = get_db_session()
                    try:
                        existing = db.query(NewsletterSubscriber).filter(
                            NewsletterSubscriber.email == nl_email_clean
                        ).first()
                        if existing:
                            if existing.is_active:
                                st.info("You're already subscribed!")
                            else:
                                existing.is_active = True
                                db.commit()
                                st.success("Welcome back! You're subscribed again.")
                        else:
                            db.add(NewsletterSubscriber(email=nl_email_clean))
                            db.commit()
                            st.success("Thanks for subscribing!")
                    except Exception as e:
                        db.rollback()
                        st.error(str(e))
                    finally:
                        db.close()

    st.markdown(html_block(f"""
    <div class="nmt-footer nmt-footer-bottombar">
      <div class="nmt-footer-inner">
        <div class="nmt-footer-bottom">
          <span>{copyright_t}</span>
          <span style="color:#4A5568;font-size:12px;">Powered by NextGen MechTech Academy</span>
        </div>
      </div>
    </div>
    """), unsafe_allow_html=True)
