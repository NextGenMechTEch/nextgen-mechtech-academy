"""
Website CMS — Admin Module
Full page-by-page content management for NextGen MechTech Academy.
Every website page, section, text, image, and navigation item is manageable here.
No source code edits required after deployment.
"""

import streamlit as st
import json
from datetime import datetime

from components.icons import icon
from database.connection import get_db_session
from database.models import (
    WebsiteSettings, CmsSection, MediaLibrary, NavItem,
    JobOpening, Course, Instructor, Announcement
)
from utils.helpers import (
    update_setting, get_all_settings, flash_message, check_upload_size,
    extract_youtube_id,
)
from utils.cloudinary_service import upload_file, resolve_src
from components.navbar import _get_nav_items


# ─── CMS helpers ─────────────────────────────────────────────────────────────

# TTL=120s (2 min): CMS section content (hero, featured-courses blurb,
# testimonials, FAQ, etc.) is edited more often than settings/nav during
# active content work, so a shorter window is used. page/key are simple
# strings, so Streamlit can hash them as the cache key without issue.
# Returns a plain dict — no ORM objects, no per-user data.
@st.cache_data(ttl=120, show_spinner=False)
def get_cms_section(page: str, key: str) -> dict:
    db = get_db_session()
    try:
        row = db.query(CmsSection).filter(
            CmsSection.page == page, CmsSection.section_key == key
        ).first()
        if row:
            return {
                "id": row.id, "title": row.title or "",
                "content": row.content or "", "is_visible": row.is_visible,
                "display_order": row.display_order,
            }
        return {"id": None, "title": "", "content": "", "is_visible": True, "display_order": 0}
    finally:
        db.close()


# Batched variant of get_cms_section(): fetches every CmsSection row for a
# given page in a single query instead of one round trip per section key.
# Same TTL/shape reasoning as get_cms_section() above — same cached data,
# just grouped by page instead of by (page, key). Returns
# {section_key: {id, title, content, is_visible, display_order}}; a page
# with no rows yet returns an empty dict, and callers should still apply
# the same per-key defaults get_cms_section() uses (id=None, title="",
# content="", is_visible=True, display_order=0) for any key missing from
# the result — this function does not manufacture placeholder rows for
# keys that were never saved.
@st.cache_data(ttl=120, show_spinner=False)
def get_cms_sections(page: str) -> dict:
    db = get_db_session()
    try:
        rows = db.query(CmsSection).filter(CmsSection.page == page).all()
        return {
            row.section_key: {
                "id": row.id, "title": row.title or "",
                "content": row.content or "", "is_visible": row.is_visible,
                "display_order": row.display_order,
            }
            for row in rows
        }
    finally:
        db.close()


def save_cms_section(page: str, key: str, title: str, content: str,
                     is_visible: bool = True, display_order: int = 0,
                     section_type: str = "custom"):
    db = get_db_session()
    try:
        row = db.query(CmsSection).filter(
            CmsSection.page == page, CmsSection.section_key == key
        ).first()
        if row:
            row.title = title
            row.content = content
            row.is_visible = is_visible
            row.display_order = display_order
            row.updated_at = datetime.utcnow()
        else:
            db.add(CmsSection(
                page=page, section_key=key, title=title,
                content=content, is_visible=is_visible,
                display_order=display_order, section_type=section_type
            ))
        db.commit()
        # save_cms_section() is the single write path for CmsSection rows,
        # so clearing here guarantees an admin's save is visible on the
        # very next page render instead of waiting out the 2-minute TTL.
        # Both the per-key and the per-page batched cache are cleared —
        # they cache the same underlying rows, just grouped differently.
        get_cms_section.clear()
        get_cms_sections.clear()
        return True
    except Exception as e:
        db.rollback()
        st.error(f"Save failed: {e}")
        return False
    finally:
        db.close()


def _section_header(title: str, icon_name: str = "layout"):
    st.markdown(
        f'<h3 style="font-family:var(--font-head);font-size:17px;font-weight:700;'
        f'color:var(--ink-900);margin:24px 0 14px;border-left:3px solid var(--amber-500);'
        f'padding-left:12px;">{icon(icon_name, size=16)} {title}</h3>',
        unsafe_allow_html=True
    )


def _save_btn(label="Save Section", key=None):
    return st.form_submit_button(label, type="primary", use_container_width=True)


# ─── MAIN CMS ROUTER ─────────────────────────────────────────────────────────

def render_website_cms():
    st.markdown(
        f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;'
        f'color:var(--ink-900);margin-bottom:6px;">'
        f'{icon("layout", size=17)} Website CMS</h3>'
        f'<p style="color:var(--ink-500);font-size:13px;margin-bottom:20px;">'
        f'Edit every page, section, and element from here. No code editing required.</p>',
        unsafe_allow_html=True
    )

    cms_pages = [
        ("🏠", "Home Page"), ("ℹ️", "About Page"), ("📚", "Courses Page"),
        ("💼", "Career Page"), ("🏆", "Certificate Page"), ("📞", "Contact Page"),
        ("🗂️", "Navigation Bar"), ("📁", "Media Library"), ("🔗", "Footer"),
    ]

    

    if "cms_page" not in st.session_state:
        st.session_state.cms_page = "Home Page"

    # Page selector tabs
    cols = st.columns(len(cms_pages))
    for i, (emoji, label) in enumerate(cms_pages):
        with cols[i]:
            active = st.session_state.cms_page == label
            if st.button(
                f"{emoji} {label.split()[0]}",
                key=f"cms_nav_{label}",
                use_container_width=True,
                type="primary" if active else "secondary"
            ):
                st.session_state.cms_page = label
                st.rerun()

    st.markdown("<hr style='margin:16px 0 24px;border-color:var(--line);'>", unsafe_allow_html=True)

    dispatch = {
        "Home Page": _cms_home,
        "About Page": _cms_about,
        "Courses Page": _cms_courses,
        "Career Page": _cms_careers,
        "Certificate Page": _cms_certificate,
        "Contact Page": _cms_contact,
        "Navigation Bar": _cms_navigation,
        "Media Library": _cms_media_library,
        "Footer": _cms_footer,
    }
    dispatch.get(st.session_state.cms_page, _cms_home)()


# ─── HOME PAGE CMS ────────────────────────────────────────────────────────────

def _cms_home():
    _section_header("Home Page — Content Manager", "home")

    settings = get_all_settings()

    tabs = st.tabs([
        "Hero", "Stats", "Announcement Bar", "Featured Courses",
        "Categories", "Why Choose Us", "Instructors", "Testimonials",
        "FAQ", "Call to Action", "Newsletter"
    ])

    # ── Hero Section ──────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("**Hero Banner & Buttons**")
        sec = get_cms_section("home", "hero")
        with st.form("cms_home_hero"):
            col1, col2 = st.columns(2)
            with col1:
                hero_headline = st.text_input(
                    "Hero Headline",
                    value=settings.get("hero_headline", "Where Engineers Learn to Build the Future")
                )
                hero_sub = st.text_area(
                    "Hero Sub-text", height=80,
                    value=settings.get("hero_sub",
                        "From Python to PCB Design, from SOLIDWORKS to Machine Learning — "
                        "gain hands-on skills that industry demands.")
                )
                hero_badge = st.text_input(
                    "Badge Text (top of hero)",
                    value=settings.get("hero_badge", "New · Prompt Engineering & AI Tools course now live")
                )
            with col2:
                hero_btn1 = st.text_input("Primary Button Text",
                    value=settings.get("hero_btn1", "Explore Courses"))
                hero_btn2 = st.text_input("Secondary Button Text",
                    value=settings.get("hero_btn2", "Contact Us"))
                hero_visible = st.checkbox("Hero section visible", value=True)

            if _save_btn("Save Hero", "save_hero"):
                for k, v in {
                    "hero_headline": hero_headline, "hero_sub": hero_sub,
                    "hero_badge": hero_badge, "hero_btn1": hero_btn1,
                    "hero_btn2": hero_btn2
                }.items():
                    update_setting(k, v)
                save_cms_section("home", "hero", "Hero", "", hero_visible)
                st.success("Hero section saved!")

        # ── Hero Promotional Video (YouTube) ────────────────────────────────
        st.markdown("**Hero Promotional Video (YouTube)**")
        st.caption("Fills the empty space on the right of the headline. Stacks below the text on mobile.")
        with st.form("cms_home_hero_video"):
            hv_enabled = st.checkbox(
                "Show promotional video in Hero",
                value=settings.get("hero_video_enabled", "1") == "1"
            )
            hv_url = st.text_input(
                "YouTube URL",
                value=settings.get("hero_video_url", "https://youtu.be/2yORSxSSstw?si=ee1FmVhoxVJJup17"),
                help="Any YouTube link works: youtube.com/watch?v=..., youtu.be/..., or youtube.com/embed/..."
            )
            vc1, vc2, vc3, vc4 = st.columns(4)
            with vc1:
                hv_autoplay = st.checkbox("Autoplay", value=settings.get("hero_video_autoplay", "1") == "1")
            with vc2:
                hv_muted = st.checkbox("Muted", value=settings.get("hero_video_muted", "1") == "1")
            with vc3:
                hv_loop = st.checkbox("Loop", value=settings.get("hero_video_loop", "1") == "1")
            with vc4:
                hv_controls = st.checkbox("Controls", value=settings.get("hero_video_controls", "1") == "1")
            st.caption("Most browsers block autoplay unless Muted is also on.")

            if _save_btn("Save Video Settings", "save_hero_video"):
                video_id = extract_youtube_id(hv_url) if hv_url.strip() else None
                if hv_enabled and not video_id:
                    st.error("That doesn't look like a valid YouTube URL — check the link and try again.")
                else:
                    for k, v in {
                        "hero_video_enabled":  "1" if hv_enabled else "0",
                        "hero_video_url":      hv_url.strip(),
                        "hero_video_autoplay": "1" if hv_autoplay else "0",
                        "hero_video_muted":    "1" if hv_muted else "0",
                        "hero_video_loop":     "1" if hv_loop else "0",
                        "hero_video_controls": "1" if hv_controls else "0",
                    }.items():
                        update_setting(k, v)
                    st.success("Hero video settings saved!")

    # ── Stats ─────────────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("**Statistics Counters**")
        with st.form("cms_home_stats"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                s1 = st.text_input("Students Stat", value=settings.get("stat_students", "500+"))
                s1l = st.text_input("Label", value=settings.get("stat_students_label", "Students Enrolled"), key="sl1")
            with col2:
                s2 = st.text_input("Courses Stat", value=settings.get("stat_courses", "12+"))
                s2l = st.text_input("Label", value=settings.get("stat_courses_label", "Active Courses"), key="sl2")
            with col3:
                s3 = st.text_input("Certificates Stat", value=settings.get("stat_certificates", "300+"))
                s3l = st.text_input("Label", value=settings.get("stat_certificates_label", "Certificates Issued"), key="sl3")
            with col4:
                s4 = st.text_input("Instructors Stat", value=settings.get("stat_instructors", "10+"))
                s4l = st.text_input("Label", value=settings.get("stat_instructors_label", "Expert Instructors"), key="sl4")
            if _save_btn("Save Stats"):
                for k, v in {
                    "stat_students": s1, "stat_students_label": s1l,
                    "stat_courses": s2, "stat_courses_label": s2l,
                    "stat_certificates": s3, "stat_certificates_label": s3l,
                    "stat_instructors": s4, "stat_instructors_label": s4l,
                }.items():
                    update_setting(k, v)
                st.success("Statistics saved!")

    # ── Announcement Bar ──────────────────────────────────────────────────
    with tabs[2]:
        with st.form("cms_home_ann"):
            ann_text = st.text_input(
                "Announcement Bar Text",
                value=settings.get("announcement_bar", "")
            )
            ann_visible = st.checkbox("Show announcement bar", value=bool(settings.get("announcement_bar_visible", "1") == "1"))
            if _save_btn("Save Announcement Bar"):
                update_setting("announcement_bar", ann_text)
                update_setting("announcement_bar_visible", "1" if ann_visible else "0")
                st.success("Announcement bar saved!")

    # ── Featured Courses Heading ──────────────────────────────────────────
    with tabs[3]:
        with st.form("cms_home_featured"):
            fc_eyebrow = st.text_input("Eyebrow Text", value=settings.get("featured_eyebrow", "What We Offer"))
            fc_heading = st.text_input("Section Heading", value=settings.get("featured_heading", "Featured Courses"))
            fc_sub = st.text_area("Section Sub-text", height=60, value=settings.get("featured_sub", ""))
            fc_count = st.number_input("Number of courses to show", min_value=1, max_value=12, value=int(settings.get("featured_count", "6")))
            fc_visible = st.checkbox("Show Featured Courses section", value=True)
            if _save_btn("Save Featured Courses Settings"):
                for k, v in {
                    "featured_eyebrow": fc_eyebrow, "featured_heading": fc_heading,
                    "featured_sub": fc_sub, "featured_count": str(fc_count)
                }.items():
                    update_setting(k, v)
                save_cms_section("home", "featured_courses", "Featured Courses", "", fc_visible)
                st.success("Featured courses settings saved!")

    # ── Categories ────────────────────────────────────────────────────────
    with tabs[4]:
        with st.form("cms_home_cats"):
            cat_heading = st.text_input("Categories Heading", value=settings.get("categories_heading", "Explore by Category"))
            cat_sub = st.text_area("Categories Sub-text", height=60, value=settings.get("categories_sub", ""))
            cat_visible = st.checkbox("Show Categories section", value=True)
            if _save_btn("Save Categories"):
                update_setting("categories_heading", cat_heading)
                update_setting("categories_sub", cat_sub)
                save_cms_section("home", "categories", "Categories", "", cat_visible)
                st.success("Saved!")

    # ── Why Choose Us ─────────────────────────────────────────────────────
    with tabs[5]:
        with st.form("cms_home_why"):
            why_heading = st.text_input("Section Heading", value=settings.get("why_heading", "Why Choose NextGen MechTech?"))
            why_sub = st.text_area("Sub-text", height=60, value=settings.get("why_sub", ""))
            why_visible = st.checkbox("Show section", value=True)
            st.markdown("**Feature Cards** (6 features shown)")
            features_json_default = json.dumps([
                {"icon": "award", "title": "Industry-Expert Instructors", "desc": "Learn from professionals who bring live projects and real domain experience."},
                {"icon": "target", "title": "100% Practical Training", "desc": "Every module is project-based. No passive theory-only lectures — you build from day one."},
                {"icon": "file-text", "title": "Recognised Certificates", "desc": "Earn credentials acknowledged by employers across Pakistan."},
                {"icon": "clock", "title": "Flexible Scheduling", "desc": "Weekend and weekday batches available."},
                {"icon": "handshake", "title": "Career Support", "desc": "Job-placement assistance, CV reviews, and mock interviews included."},
                {"icon": "dollar-sign", "title": "Affordable Fees", "desc": "World-class instruction at accessible fees with instalment plans."},
            ], indent=2)
            sec = get_cms_section("home", "why_features")
            features_json = st.text_area(
                "Features JSON (icon, title, desc for each card)",
                value=sec["content"] if sec["content"] else features_json_default,
                height=200
            )
            if _save_btn("Save Why Choose Us"):
                update_setting("why_heading", why_heading)
                update_setting("why_sub", why_sub)
                save_cms_section("home", "why_features", "Why Choose Us Features", features_json, why_visible)
                st.success("Saved!")
        st.caption("Tip: Edit the JSON above to change feature card icons, titles, and descriptions.")

    # ── Instructor Section ────────────────────────────────────────────────
    with tabs[6]:
        with st.form("cms_home_instr"):
            instr_heading = st.text_input("Instructors Heading", value=settings.get("instructors_heading", "Meet Our Expert Instructors"))
            instr_sub = st.text_area("Sub-text", height=60, value=settings.get("instructors_sub", ""))
            instr_visible = st.checkbox("Show Instructors section", value=True)
            if _save_btn("Save Instructors Section"):
                update_setting("instructors_heading", instr_heading)
                update_setting("instructors_sub", instr_sub)
                save_cms_section("home", "instructors", "Instructors Section", "", instr_visible)
                st.success("Saved! Manage instructor profiles in the Instructors tab.")

    # ── Testimonials ─────────────────────────────────────────────────────
    with tabs[7]:
        sec = get_cms_section("home", "testimonials")
        with st.form("cms_home_testimonials"):
            t_heading = st.text_input("Testimonials Heading", value=settings.get("testimonials_heading", "What Our Students Say"))
            t_visible = st.checkbox("Show Testimonials section", value=sec.get("is_visible", True))
            default_testimonials = json.dumps([
                {"name": "Ali Hassan", "course": "Python Programming", "text": "The best learning experience I've had. Practical, hands-on, and highly relevant.", "rating": 5},
                {"name": "Sara Noor", "course": "SOLIDWORKS", "text": "I landed my first engineering job thanks to this course. Exceptional instructors!", "rating": 5},
                {"name": "Bilal Ahmed", "course": "Arduino & IoT", "text": "Completely changed my career direction. Now building IoT products professionally.", "rating": 5},
            ], indent=2)
            t_json = st.text_area(
                "Testimonials JSON (name, course, text, rating)",
                value=sec["content"] if sec["content"] else default_testimonials,
                height=200
            )
            if _save_btn("Save Testimonials"):
                update_setting("testimonials_heading", t_heading)
                save_cms_section("home", "testimonials", "Testimonials", t_json, t_visible)
                st.success("Testimonials saved!")

    # ── FAQ ───────────────────────────────────────────────────────────────
    with tabs[8]:
        sec = get_cms_section("home", "faq")
        with st.form("cms_home_faq"):
            faq_heading = st.text_input("FAQ Heading", value=settings.get("faq_heading", "Frequently Asked Questions"))
            faq_visible = st.checkbox("Show FAQ section", value=sec.get("is_visible", True))
            default_faqs = json.dumps([
                {"q": "How do I enrol in a course?", "a": "Create a free account, pick a course, and submit the enrolment form with your payment screenshot."},
                {"q": "Are certificates recognised?", "a": "Yes — our certificates are issued with unique IDs and can be verified online by employers."},
                {"q": "Can I attend online?", "a": "Most courses are available both in-person at our Lahore campus and online via video sessions."},
            ], indent=2)
            faq_json = st.text_area(
                "FAQs JSON (q, a)",
                value=sec["content"] if sec["content"] else default_faqs,
                height=180
            )
            if _save_btn("Save FAQ"):
                update_setting("faq_heading", faq_heading)
                save_cms_section("home", "faq", "FAQ", faq_json, faq_visible)
                st.success("FAQ saved!")

    # ── Call to Action ────────────────────────────────────────────────────
    with tabs[9]:
        with st.form("cms_home_cta"):
            cta_heading = st.text_input("CTA Heading", value=settings.get("cta_heading", "Ready to Start Your Journey?"))
            cta_sub = st.text_area("CTA Sub-text", height=60, value=settings.get("cta_sub", "Join hundreds of students already learning at NextGen MechTech Academy."))
            cta_btn = st.text_input("CTA Button Text", value=settings.get("cta_btn", "Enrol Now"))
            cta_visible = st.checkbox("Show CTA section", value=True)
            if _save_btn("Save CTA"):
                for k, v in {
                    "cta_heading": cta_heading, "cta_sub": cta_sub, "cta_btn": cta_btn
                }.items():
                    update_setting(k, v)
                save_cms_section("home", "cta", "Call to Action", "", cta_visible)
                st.success("CTA saved!")

    # ── Newsletter ────────────────────────────────────────────────────────
    with tabs[10]:
        with st.form("cms_home_newsletter"):
            nl_heading = st.text_input("Newsletter Heading", value=settings.get("newsletter_heading", "Stay Updated"))
            nl_sub = st.text_input("Newsletter Sub-text", value=settings.get("newsletter_sub", "Get course updates and announcements in your inbox."))
            nl_btn = st.text_input("Button Text", value=settings.get("newsletter_btn", "Subscribe"))
            nl_visible = st.checkbox("Show Newsletter section", value=True)
            if _save_btn("Save Newsletter"):
                for k, v in {
                    "newsletter_heading": nl_heading, "newsletter_sub": nl_sub, "newsletter_btn": nl_btn
                }.items():
                    update_setting(k, v)
                save_cms_section("home", "newsletter", "Newsletter", "", nl_visible)
                st.success("Newsletter section saved!")


# ─── ABOUT PAGE CMS ───────────────────────────────────────────────────────────

def _cms_about():
    _section_header("About Page — Content Manager", "info")

    settings = get_all_settings()
    tabs = st.tabs(["Banner", "About Text", "Mission/Vision/Values", "Quick Facts", "Team Section", "CTA"])

    with tabs[0]:
        with st.form("cms_about_banner"):
            b_heading = st.text_input("Banner Heading", value=settings.get("about_banner_heading", "About Us"))
            b_sub = st.text_area("Banner Sub-text", height=60,
                value=settings.get("about_banner_sub", "Empowering Pakistan's engineers and technologists since our founding."))
            if _save_btn("Save Banner"):
                update_setting("about_banner_heading", b_heading)
                update_setting("about_banner_sub", b_sub)
                st.success("Banner saved!")

    with tabs[1]:
        with st.form("cms_about_text"):
            col1, col2 = st.columns(2)
            with col1:
                eyebrow = st.text_input("Eyebrow Text", value=settings.get("about_eyebrow", "Who We Are"))
                heading = st.text_input("Heading", value=settings.get("about_heading", "NextGen MechTech Academy"))
            with col2:
                tagline = st.text_input("About Tagline", value=settings.get("about_tagline", ""))
            para1 = st.text_area("Paragraph 1", height=100, value=settings.get("about_para1",
                "NextGen MechTech Academy is a premier technical education institute based in Lahore, Pakistan."))
            para2 = st.text_area("Paragraph 2", height=100, value=settings.get("about_para2",
                "Founded with a mission to bridge the gap between academic theory and industry practice."))
            if _save_btn("Save About Text"):
                for k, v in {
                    "about_eyebrow": eyebrow, "about_heading": heading,
                    "about_tagline": tagline, "about_para1": para1, "about_para2": para2
                }.items():
                    update_setting(k, v)
                st.success("About text saved!")

    with tabs[2]:
        sec = get_cms_section("about", "mvv")
        default_mvv = json.dumps([
            {"icon": "target", "title": "Our Mission", "text": "To provide accessible, practical, and industry-relevant technical education."},
            {"icon": "trending-up", "title": "Our Vision", "text": "To become Pakistan's most impactful technical academy."},
            {"icon": "shield", "title": "Our Values", "text": "Excellence. Integrity. Accessibility. Innovation."},
        ], indent=2)
        with st.form("cms_about_mvv"):
            mvv_json = st.text_area(
                "Mission / Vision / Values JSON (icon, title, text)",
                value=sec["content"] if sec["content"] else default_mvv,
                height=200
            )
            if _save_btn("Save Mission/Vision/Values"):
                save_cms_section("about", "mvv", "Mission/Vision/Values", mvv_json)
                st.success("Saved!")

    with tabs[3]:
        with st.form("cms_about_facts"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                f1v = st.text_input("Value 1", value=settings.get("about_fact1_val", "2022"))
                f1l = st.text_input("Label 1", value=settings.get("about_fact1_lbl", "Founded"))
            with col2:
                f2v = st.text_input("Value 2", value=settings.get("about_fact2_val", "500+"))
                f2l = st.text_input("Label 2", value=settings.get("about_fact2_lbl", "Graduates"))
            with col3:
                f3v = st.text_input("Value 3", value=settings.get("about_fact3_val", "12+"))
                f3l = st.text_input("Label 3", value=settings.get("about_fact3_lbl", "Courses"))
            with col4:
                f4v = st.text_input("Value 4", value=settings.get("about_fact4_val", "10+"))
                f4l = st.text_input("Label 4", value=settings.get("about_fact4_lbl", "Instructors"))
            if _save_btn("Save Quick Facts"):
                for k, v in {
                    "about_fact1_val": f1v, "about_fact1_lbl": f1l,
                    "about_fact2_val": f2v, "about_fact2_lbl": f2l,
                    "about_fact3_val": f3v, "about_fact3_lbl": f3l,
                    "about_fact4_val": f4v, "about_fact4_lbl": f4l,
                }.items():
                    update_setting(k, v)
                st.success("Quick facts saved!")

    with tabs[4]:
        with st.form("cms_about_team"):
            t_heading = st.text_input("Team Section Heading", value=settings.get("team_heading", "Meet the Instructors"))
            t_eyebrow = st.text_input("Eyebrow Text", value=settings.get("team_eyebrow", "Our Team"))
            if _save_btn("Save Team Section"):
                update_setting("team_heading", t_heading)
                update_setting("team_eyebrow", t_eyebrow)
                st.success("Saved! Manage instructor profiles in the Instructors tab.")

    with tabs[5]:
        with st.form("cms_about_cta"):
            cta_text = st.text_input("CTA Text", value=settings.get("about_cta_text", "Ready to start learning?"))
            cta_btn = st.text_input("CTA Button Text", value=settings.get("about_cta_btn", "View Courses"))
            if _save_btn("Save CTA"):
                update_setting("about_cta_text", cta_text)
                update_setting("about_cta_btn", cta_btn)
                st.success("Saved!")


# ─── COURSES PAGE CMS ─────────────────────────────────────────────────────────

def _cms_courses():
    _section_header("Courses Page — Content Manager", "book-open")

    settings = get_all_settings()
    tabs = st.tabs(["Banner & Headings", "Category Labels", "Course Detail Page"])

    with tabs[0]:
        with st.form("cms_courses_banner"):
            col1, col2 = st.columns(2)
            with col1:
                b_heading = st.text_input("Banner Heading", value=settings.get("courses_banner_heading", "Our Courses"))
                b_sub = st.text_area("Banner Sub-text", height=60,
                    value=settings.get("courses_banner_sub", "Explore our full range of industry-relevant technical courses."))
            with col2:
                grid_heading = st.text_input("Grid Heading", value=settings.get("courses_grid_heading", "All Courses"))
                empty_msg = st.text_input("Empty State Message", value=settings.get("courses_empty_msg", "No courses found in this category."))
            if _save_btn("Save Courses Page Settings"):
                for k, v in {
                    "courses_banner_heading": b_heading,
                    "courses_banner_sub": b_sub,
                    "courses_grid_heading": grid_heading,
                    "courses_empty_msg": empty_msg,
                }.items():
                    update_setting(k, v)
                st.success("Saved!")

    with tabs[1]:
        sec = get_cms_section("courses", "categories")
        default_cats = json.dumps([
            {"icon": "code", "name": "Programming", "desc": "Python · C · MATLAB"},
            {"icon": "cog", "name": "Engineering Tools", "desc": "SOLIDWORKS · MATLAB & Simulink"},
            {"icon": "zap", "name": "Electronics", "desc": "Arduino · IoT · PCB Design"},
            {"icon": "bot", "name": "Artificial Intelligence", "desc": "ML · Deep Learning · Prompt Engineering"},
            {"icon": "palette", "name": "Creative Arts", "desc": "Graphic Design · Video Editing"},
            {"icon": "bar-chart", "name": "Productivity", "desc": "Microsoft Office Masterclass"},
        ], indent=2)
        with st.form("cms_courses_cats"):
            cats_json = st.text_area(
                "Categories JSON (icon, name, desc)",
                value=sec["content"] if sec["content"] else default_cats,
                height=200
            )
            if _save_btn("Save Categories"):
                save_cms_section("courses", "categories", "Course Categories", cats_json)
                st.success("Categories saved!")

    with tabs[2]:
        with st.form("cms_courses_detail"):
            st.markdown("**Course Detail Page Default Labels**")
            col1, col2 = st.columns(2)
            with col1:
                enroll_btn = st.text_input("Enroll Button Text", value=settings.get("enroll_btn_text", "Enrol in This Course"))
                cert_label = st.text_input("Certificate Label", value=settings.get("cert_section_label", "Certificate"))
            with col2:
                related_heading = st.text_input("Related Courses Heading", value=settings.get("related_courses_heading", "Related Courses"))
                faq_label = st.text_input("FAQ Section Label", value=settings.get("course_faq_label", "Frequently Asked Questions"))
            if _save_btn("Save Detail Page Labels"):
                for k, v in {
                    "enroll_btn_text": enroll_btn, "cert_section_label": cert_label,
                    "related_courses_heading": related_heading, "course_faq_label": faq_label
                }.items():
                    update_setting(k, v)
                st.success("Saved!")


# ─── CAREER PAGE CMS ──────────────────────────────────────────────────────────

def _cms_careers():
    _section_header("Career Page — Content Manager", "briefcase")

    settings = get_all_settings()
    tabs = st.tabs(["Banner & Text", "Perks/Benefits", "Job Openings", "Internships", "Application Form"])

    with tabs[0]:
        with st.form("cms_careers_banner"):
            col1, col2 = st.columns(2)
            with col1:
                b_heading = st.text_input("Banner Heading", value=settings.get("careers_banner_heading", "Join Our Team"))
                b_sub = st.text_area("Banner Sub-text", height=80,
                    value=settings.get("careers_banner_sub",
                        "Passionate about teaching technology? We're always looking for talented instructors."))
            with col2:
                section_heading = st.text_input("Section Heading",
                    value=settings.get("careers_section_heading", "Shape the Next Generation of Engineers"))
                section_sub = st.text_area("Section Sub-text", height=80,
                    value=settings.get("careers_section_sub",
                        "At NextGen MechTech Academy, our instructors are the backbone of our success."))
            if _save_btn("Save Banner"):
                for k, v in {
                    "careers_banner_heading": b_heading, "careers_banner_sub": b_sub,
                    "careers_section_heading": section_heading, "careers_section_sub": section_sub
                }.items():
                    update_setting(k, v)
                st.success("Saved!")

    with tabs[1]:
        sec = get_cms_section("careers", "perks")
        default_perks = json.dumps([
            {"icon": "dollar-sign", "title": "Competitive Compensation", "desc": "Earn well for your time and expertise"},
            {"icon": "clock", "title": "Flexible Scheduling", "desc": "Teach at times that suit your schedule"},
            {"icon": "map-pin", "title": "Online & On-site", "desc": "Teach from anywhere or in our Lahore studio"},
            {"icon": "trending-up", "title": "Grow Your Brand", "desc": "Build your profile and reach thousands of students"},
            {"icon": "handshake", "title": "Supportive Team", "desc": "Work with a passionate, collaborative team"},
        ], indent=2)
        with st.form("cms_careers_perks"):
            perks_json = st.text_area(
                "Perks/Benefits JSON (icon, title, desc)",
                value=sec["content"] if sec["content"] else default_perks,
                height=200
            )
            if _save_btn("Save Perks"):
                save_cms_section("careers", "perks", "Perks & Benefits", perks_json)
                st.success("Perks saved!")

    with tabs[2]:
        st.markdown("**Manage Job Openings**")
        db = get_db_session()
        try:
            jobs = db.query(JobOpening).filter(JobOpening.is_internship == False).order_by(JobOpening.display_order).all()
        finally:
            db.close()

        with st.expander("➕ Create New Job Opening", expanded=False):
            with st.form("create_job"):
                col1, col2 = st.columns(2)
                with col1:
                    j_title = st.text_input("Job Title *")
                    j_dept = st.text_input("Department")
                    j_type = st.selectbox("Employment Type", ["Full-time", "Part-time", "Contract", "Freelance"])
                with col2:
                    j_loc = st.text_input("Location", value="Lahore, Pakistan")
                    j_deadline = st.date_input("Application Deadline")
                    j_open = st.checkbox("Position Open", value=True)
                j_desc = st.text_area("Job Description *", height=100)
                j_req = st.text_area("Requirements", height=80)
                j_benefits = st.text_area("Benefits", height=80)
                if st.form_submit_button("Create Job Opening", type="primary"):
                    if j_title and j_desc:
                        db = get_db_session()
                        try:
                            db.add(JobOpening(
                                title=j_title, department=j_dept, description=j_desc,
                                requirements=j_req, benefits=j_benefits,
                                employment_type=j_type, location=j_loc,
                                deadline=datetime.combine(j_deadline, datetime.min.time()) if j_deadline else None,
                                is_open=j_open
                            ))
                            db.commit()
                            flash_message("Job opening created!")
                            st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(str(e))
                        finally:
                            db.close()
                    else:
                        st.error("Title and description are required.")

        for job in jobs:
            status_badge = "🟢 Open" if job.is_open else "🔴 Closed"
            with st.expander(f"{status_badge} — {job.title} ({job.employment_type})"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Toggle Open/Close", key=f"toggle_job_{job.id}"):
                        db = get_db_session()
                        try:
                            j = db.query(JobOpening).get(job.id)
                            j.is_open = not j.is_open
                            db.commit()
                            st.rerun()
                        finally:
                            db.close()
                with col2:
                    if st.button("Archive", key=f"arch_job_{job.id}"):
                        db = get_db_session()
                        try:
                            j = db.query(JobOpening).get(job.id)
                            j.is_open = False
                            db.commit()
                            st.rerun()
                        finally:
                            db.close()
                with col3:
                    if st.button("Delete", key=f"del_job_{job.id}"):
                        db = get_db_session()
                        try:
                            j = db.query(JobOpening).get(job.id)
                            db.delete(j)
                            db.commit()
                            st.rerun()
                        finally:
                            db.close()
                st.caption(f"Location: {job.location} | Dept: {job.department or 'N/A'}")
                st.write(job.description[:200] + "..." if len(job.description) > 200 else job.description)

    with tabs[3]:
        st.markdown("**Manage Internship Opportunities**")
        db = get_db_session()
        try:
            internships = db.query(JobOpening).filter(JobOpening.is_internship == True).order_by(JobOpening.display_order).all()
        finally:
            db.close()

        with st.expander("➕ Add Internship Opportunity", expanded=False):
            with st.form("create_internship"):
                i_title = st.text_input("Internship Title *")
                i_dept = st.text_input("Department")
                i_desc = st.text_area("Description *", height=100)
                i_req = st.text_area("Requirements", height=80)
                i_open = st.checkbox("Currently Accepting Applications", value=True)
                if st.form_submit_button("Add Internship", type="primary"):
                    if i_title and i_desc:
                        db = get_db_session()
                        try:
                            db.add(JobOpening(
                                title=i_title, department=i_dept, description=i_desc,
                                requirements=i_req, is_open=i_open, is_internship=True
                            ))
                            db.commit()
                            flash_message("Internship added!")
                            st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(str(e))
                        finally:
                            db.close()

        for intern in internships:
            status = "🟢 Open" if intern.is_open else "🔴 Closed"
            with st.expander(f"{status} — {intern.title}"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Toggle", key=f"ti_{intern.id}"):
                        db = get_db_session()
                        try:
                            i = db.query(JobOpening).get(intern.id)
                            i.is_open = not i.is_open
                            db.commit()
                            st.rerun()
                        finally:
                            db.close()
                with col2:
                    if st.button("Delete", key=f"di_{intern.id}"):
                        db = get_db_session()
                        try:
                            i = db.query(JobOpening).get(intern.id)
                            db.delete(i)
                            db.commit()
                            st.rerun()
                        finally:
                            db.close()

    with tabs[4]:
        with st.form("cms_careers_form"):
            form_heading = st.text_input("Application Form Heading",
                value=settings.get("careers_form_heading", "Apply Now"))
            form_sub = st.text_input("Form Sub-text",
                value=settings.get("careers_form_sub", "Fill in the form below and we'll be in touch."))
            success_msg = st.text_area("Success Message", height=80,
                value=settings.get("careers_success_msg",
                    "Thank you for your application! We'll review it and get back to you within 3–5 business days."))
            if _save_btn("Save Form Settings"):
                for k, v in {
                    "careers_form_heading": form_heading,
                    "careers_form_sub": form_sub,
                    "careers_success_msg": success_msg,
                }.items():
                    update_setting(k, v)
                st.success("Saved!")


# ─── CERTIFICATE PAGE CMS ─────────────────────────────────────────────────────

def _cms_certificate():
    _section_header("Certificate Verification Page — Content Manager", "award")

    settings = get_all_settings()
    with st.form("cms_cert_page"):
        col1, col2 = st.columns(2)
        with col1:
            banner_heading = st.text_input("Banner Heading",
                value=settings.get("cert_banner_heading", "Certificate Verification"))
            banner_sub = st.text_area("Banner Sub-text", height=60,
                value=settings.get("cert_banner_sub",
                    "Verify the authenticity of any NextGen MechTech Academy certificate instantly."))
            form_heading = st.text_input("Form Heading",
                value=settings.get("cert_form_heading", "Enter Certificate ID"))
            placeholder_text = st.text_input("Input Placeholder",
                value=settings.get("cert_placeholder", "e.g. NMT-XXXXXXXXXX"))
        with col2:
            success_msg = st.text_area("Verification Success Message", height=80,
                value=settings.get("cert_success_msg", "Certificate verified successfully!"))
            error_msg = st.text_input("Verification Error Message",
                value=settings.get("cert_error_msg", "No certificate found with that ID."))
            help_text = st.text_area("Help Section Text", height=80,
                value=settings.get("cert_help_text",
                    "Your certificate ID starts with NMT- followed by 10 characters. "
                    "You can find it printed on your certificate or in your confirmation email."))
        if _save_btn("Save Certificate Page"):
            for k, v in {
                "cert_banner_heading": banner_heading, "cert_banner_sub": banner_sub,
                "cert_form_heading": form_heading, "cert_placeholder": placeholder_text,
                "cert_success_msg": success_msg, "cert_error_msg": error_msg,
                "cert_help_text": help_text,
            }.items():
                update_setting(k, v)
            st.success("Certificate page settings saved!")


# ─── CONTACT PAGE CMS ─────────────────────────────────────────────────────────

def _cms_contact():
    _section_header("Contact Page — Content Manager", "mail")

    settings = get_all_settings()
    tabs = st.tabs(["Banner & Info", "Contact Details", "Social Links", "Form Settings"])

    with tabs[0]:
        with st.form("cms_contact_banner"):
            col1, col2 = st.columns(2)
            with col1:
                b_heading = st.text_input("Banner Heading", value=settings.get("contact_banner_heading", "Contact Us"))
                b_sub = st.text_area("Banner Sub-text", height=60,
                    value=settings.get("contact_banner_sub",
                        "Have a question? We'd love to hear from you."))
                section_heading = st.text_input("Info Section Heading",
                    value=settings.get("contact_section_heading", "We're Here to Help"))
            with col2:
                eyebrow = st.text_input("Eyebrow Text",
                    value=settings.get("contact_eyebrow", "Get in Touch"))
                success_msg = st.text_area("Form Success Message", height=60,
                    value=settings.get("contact_success_msg",
                        "Your message has been sent! We'll get back to you within 24 hours."))
            if _save_btn("Save Banner"):
                for k, v in {
                    "contact_banner_heading": b_heading, "contact_banner_sub": b_sub,
                    "contact_section_heading": section_heading, "contact_eyebrow": eyebrow,
                    "contact_success_msg": success_msg
                }.items():
                    update_setting(k, v)
                st.success("Saved!")

    with tabs[1]:
        with st.form("cms_contact_details"):
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("Contact Email",
                    value=settings.get("contact_email", "support.nextgenmechtech@gmail.com"))
                phone = st.text_input("Phone Number", value=settings.get("contact_phone", ""))
                address = st.text_input("Address", value=settings.get("contact_address", "Lahore, Pakistan"))
            with col2:
                careers_email = st.text_input("Careers Email",
                    value=settings.get("careers_email", "careers.nextgenmechtech@gmail.com"))
                office_hours = st.text_input("Office Hours",
                    value=settings.get("office_hours", "Mon–Sat: 9:00 AM – 6:00 PM"))
                map_embed = st.text_area("Google Maps Embed URL", height=60,
                    value=settings.get("map_embed_url", ""))
            if _save_btn("Save Contact Details"):
                for k, v in {
                    "contact_email": email, "contact_phone": phone,
                    "contact_address": address, "careers_email": careers_email,
                    "office_hours": office_hours, "map_embed_url": map_embed
                }.items():
                    update_setting(k, v)
                st.success("Contact details saved!")

    with tabs[2]:
        with st.form("cms_contact_social"):
            col1, col2 = st.columns(2)
            with col1:
                fb = st.text_input("Facebook URL", value=settings.get("facebook_url", "https://facebook.com/nextgenmechtech"))
                insta = st.text_input("Instagram URL", value=settings.get("instagram_url", "https://instagram.com/nextgenmechtech"))
            with col2:
                li = st.text_input("LinkedIn URL", value=settings.get("linkedin_url", "https://linkedin.com/company/nextgenmechtech"))
                yt = st.text_input("YouTube URL", value=settings.get("youtube_url", "https://youtube.com/nextgenmechtech"))
            if _save_btn("Save Social Links"):
                for k, v in {
                    "facebook_url": fb, "instagram_url": insta, "linkedin_url": li, "youtube_url": yt
                }.items():
                    update_setting(k, v)
                st.success("Social links saved!")

    with tabs[3]:
        with st.form("cms_contact_form"):
            form_heading = st.text_input("Form Heading", value=settings.get("contact_form_heading", "Send a Message"))
            form_btn = st.text_input("Submit Button Text", value=settings.get("contact_form_btn", "Send Message"))
            if _save_btn("Save Form Settings"):
                update_setting("contact_form_heading", form_heading)
                update_setting("contact_form_btn", form_btn)
                st.success("Saved!")


# ─── NAVIGATION BAR CMS ───────────────────────────────────────────────────────

def _cms_navigation():
    _section_header("Navigation Bar — Content Manager", "menu")

    db = get_db_session()
    try:
        nav_items = db.query(NavItem).order_by(NavItem.display_order).all()
    finally:
        db.close()

    # Default nav if none exist
    default_nav = [
        ("Home", "home", "home", 1, True),
        ("Courses", "courses", "book-open", 2, True),
        ("About", "about", "info", 3, True),
        ("Careers", "careers", "briefcase", 4, True),
        ("Contact", "contact", "mail", 5, True),
        ("Verify Certificate", "verify", "award", 6, True),
    ]

    if not nav_items:
        st.info("No nav items configured. Click below to seed defaults.")
        if st.button("Seed Default Navigation", type="primary"):
            db = get_db_session()
            try:
                for label, page_key, icon_name, order, visible in default_nav:
                    db.add(NavItem(label=label, page_key=page_key, icon_name=icon_name,
                                   display_order=order, is_visible=visible))
                db.commit()
                _get_nav_items.clear()
                flash_message("Default navigation seeded!")
                st.rerun()
            except Exception as e:
                db.rollback()
                st.error(str(e))
            finally:
                db.close()
        return

    st.markdown("**Current Navigation Items** (visible on public website)")
    for item in nav_items:
        vis_badge = "👁️" if item.is_visible else "🚫"
        with st.expander(f"{vis_badge} {item.label} → /{item.page_key} (order: {item.display_order})"):
            with st.form(f"nav_edit_{item.id}"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    new_label = st.text_input("Label", value=item.label, key=f"nl_{item.id}")
                with col2:
                    new_page = st.text_input("Page Key", value=item.page_key, key=f"np_{item.id}")
                with col3:
                    new_order = st.number_input("Order", value=item.display_order, min_value=0, key=f"no_{item.id}")
                with col4:
                    new_visible = st.checkbox("Visible", value=item.is_visible, key=f"nv_{item.id}")
                col_save, col_del = st.columns(2)
                with col_save:
                    if st.form_submit_button("Save", type="primary"):
                        db = get_db_session()
                        try:
                            nav = db.query(NavItem).get(item.id)
                            nav.label = new_label
                            nav.page_key = new_page
                            nav.display_order = new_order
                            nav.is_visible = new_visible
                            db.commit()
                            _get_nav_items.clear()
                            flash_message("Saved!")
                            st.rerun()
                        finally:
                            db.close()
                with col_del:
                    if st.form_submit_button("Delete", type="secondary"):
                        db = get_db_session()
                        try:
                            nav = db.query(NavItem).get(item.id)
                            db.delete(nav)
                            db.commit()
                            _get_nav_items.clear()
                            st.rerun()
                        finally:
                            db.close()

    st.markdown("---")
    st.markdown("**Add New Nav Item**")
    with st.form("add_nav_item"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            new_label = st.text_input("Label *", placeholder="e.g. Blog")
        with col2:
            new_page = st.text_input("Page Key *", placeholder="e.g. blog")
        with col3:
            new_icon = st.text_input("Icon Name", placeholder="e.g. file-text")
        with col4:
            new_order = st.number_input("Display Order", value=len(nav_items) + 1, min_value=0)
        new_visible = st.checkbox("Visible on website", value=True)
        if st.form_submit_button("Add Navigation Item", type="primary"):
            if new_label and new_page:
                db = get_db_session()
                try:
                    db.add(NavItem(label=new_label, page_key=new_page,
                                   icon_name=new_icon, display_order=new_order,
                                   is_visible=new_visible))
                    db.commit()
                    _get_nav_items.clear()
                    flash_message("Navigation item added!")
                    st.rerun()
                except Exception as e:
                    db.rollback()
                    st.error(str(e))
                finally:
                    db.close()
            else:
                st.error("Label and page key are required.")


# ─── MEDIA LIBRARY ────────────────────────────────────────────────────────────

def _cms_media_library():
    _section_header("Media Library — Central File Storage", "image")

    db = get_db_session()
    try:
        folders = db.query(MediaLibrary.folder).distinct().all()
        folder_list = ["general"] + [f[0] for f in folders if f[0] != "general"]
    finally:
        db.close()

    tabs = st.tabs(["📤 Upload Media", "🖼️ Browse Library", "📂 Manage Folders"])

    with tabs[0]:
        with st.form("upload_media"):
            col1, col2 = st.columns(2)
            with col1:
                upload_name = st.text_input("File Name / Title *")
                folder_choice = st.selectbox("Folder", ["general", "logos", "banners", "instructors", "courses", "documents"])
                media_type = st.selectbox("Type", ["image", "document", "logo", "icon"])
            with col2:
                uploaded_file = st.file_uploader(
                    "Upload File",
                    type=["jpg", "jpeg", "png", "gif", "webp", "pdf", "svg"]
                )

            if st.form_submit_button("Upload to Library", type="primary"):
                if not upload_name or not uploaded_file:
                    st.error("Name and file are required.")
                elif not check_upload_size(uploaded_file, 5):
                    st.error("File is too large. Maximum allowed size is 5MB.")
                else:
                    try:
                        file_url = upload_file(uploaded_file, folder=f"nextgen_mechtech/media/{folder_choice}")
                    except Exception as e:
                        st.error(f"Upload failed: {e}")
                        st.stop()
                    db = get_db_session()
                    try:
                        db.add(MediaLibrary(
                            name=upload_name,
                            file_data=file_url,
                            media_type=media_type,
                            folder=folder_choice,
                            file_size=uploaded_file.size,
                        ))
                        db.commit()
                        flash_message(f"'{upload_name}' uploaded to library!")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(str(e))
                    finally:
                        db.close()

    with tabs[1]:
        filter_folder = st.selectbox("Filter by Folder", ["All"] + folder_list)
        db = get_db_session()
        try:
            q = db.query(MediaLibrary)
            if filter_folder != "All":
                q = q.filter(MediaLibrary.folder == filter_folder)
            media_items = q.order_by(MediaLibrary.created_at.desc()).all()
        finally:
            db.close()

        if not media_items:
            st.info("No media uploaded yet. Use the Upload tab to add files.")
        else:
            st.caption(f"{len(media_items)} file(s) in library")
            cols = st.columns(4)
            for i, item in enumerate(media_items):
                with cols[i % 4]:
                    if item.media_type == "image" and item.file_data:
                        try:
                            # Detect common image types
                            ext = item.name.lower().split(".")[-1] if "." in item.name else "jpeg"
                            mime = {"png": "image/png", "gif": "image/gif",
                                    "webp": "image/webp", "svg": "image/svg+xml"}.get(ext, "image/jpeg")
                            st.image(
                                resolve_src(item.file_data, mime=mime),
                                caption=item.name, use_column_width=True
                            )
                        except:
                            st.info(f"📄 {item.name}")
                    else:
                        st.info(f"📄 {item.name}")

                    st.caption(f"📁 {item.folder}")
                    if st.button("🗑️ Delete", key=f"del_media_{item.id}", use_container_width=True):
                        db = get_db_session()
                        try:
                            m = db.query(MediaLibrary).get(item.id)
                            db.delete(m)
                            db.commit()
                            st.rerun()
                        finally:
                            db.close()

    with tabs[2]:
        st.markdown("**Folder Summary**")
        db = get_db_session()
        try:
            all_media = db.query(MediaLibrary).all()
        finally:
            db.close()

        if all_media:
            from collections import Counter
            folder_counts = Counter(m.folder for m in all_media)
            for folder, count in folder_counts.items():
                st.markdown(f"📂 **{folder}** — {count} file(s)")
        else:
            st.info("No files uploaded yet.")


# ─── FOOTER CMS ───────────────────────────────────────────────────────────────

def _cms_footer():
    _section_header("Footer — Content Manager", "layout")

    settings = get_all_settings()
    tabs = st.tabs(["Branding & Description", "Quick Links", "Contact Info", "Social Links", "Copyright"])

    with tabs[0]:
        with st.form("cms_footer_brand"):
            col1, col2 = st.columns(2)
            with col1:
                site_name = st.text_input("Site Name", value=settings.get("site_name", "NextGen MechTech Academy"))
                footer_tagline = st.text_input("Footer Tagline", value=settings.get("footer_tagline", "Learn. Build. Innovate."))
            with col2:
                footer_desc = st.text_area("Footer Description", height=80,
                    value=settings.get("footer_desc",
                        "Premier technical education institute based in Lahore, Pakistan."))
            if _save_btn("Save Branding"):
                for k, v in {
                    "site_name": site_name, "footer_tagline": footer_tagline, "footer_desc": footer_desc
                }.items():
                    update_setting(k, v)
                st.success("Footer branding saved!")

    with tabs[1]:
        sec = get_cms_section("footer", "quick_links")
        default_links = json.dumps([
            {"label": "Home", "page": "home"},
            {"label": "Courses", "page": "courses"},
            {"label": "About Us", "page": "about"},
            {"label": "Careers", "page": "careers"},
            {"label": "Contact", "page": "contact"},
            {"label": "Verify Certificate", "page": "verify"},
        ], indent=2)
        with st.form("cms_footer_links"):
            links_json = st.text_area(
                "Quick Links JSON (label, page)",
                value=sec["content"] if sec["content"] else default_links,
                height=200
            )
            if _save_btn("Save Quick Links"):
                save_cms_section("footer", "quick_links", "Quick Links", links_json)
                st.success("Quick links saved!")

    with tabs[2]:
        with st.form("cms_footer_contact"):
            col1, col2 = st.columns(2)
            with col1:
                f_email = st.text_input("Email", value=settings.get("footer_email", settings.get("contact_email", "")))
                f_phone = st.text_input("Phone", value=settings.get("footer_phone", settings.get("contact_phone", "")))
            with col2:
                f_address = st.text_input("Address", value=settings.get("footer_address", settings.get("contact_address", "Lahore, Pakistan")))
                f_hours = st.text_input("Office Hours", value=settings.get("footer_hours", "Mon–Sat: 9 AM–6 PM"))
            if _save_btn("Save Footer Contact"):
                for k, v in {
                    "footer_email": f_email, "footer_phone": f_phone,
                    "footer_address": f_address, "footer_hours": f_hours
                }.items():
                    update_setting(k, v)
                st.success("Footer contact saved!")

    with tabs[3]:
        with st.form("cms_footer_social"):
            col1, col2 = st.columns(2)
            with col1:
                fb = st.text_input("Facebook URL", value=settings.get("facebook_url", ""))
                insta = st.text_input("Instagram URL", value=settings.get("instagram_url", ""))
            with col2:
                li = st.text_input("LinkedIn URL", value=settings.get("linkedin_url", ""))
                yt = st.text_input("YouTube URL", value=settings.get("youtube_url", ""))
            if _save_btn("Save Social Links"):
                for k, v in {
                    "facebook_url": fb, "instagram_url": insta, "linkedin_url": li, "youtube_url": yt
                }.items():
                    update_setting(k, v)
                st.success("Social links saved!")

    with tabs[4]:
        with st.form("cms_footer_copyright"):
            copyright_text = st.text_input(
                "Copyright Text",
                value=settings.get("footer_copyright",
                    f"© {datetime.now().year} NextGen MechTech Academy. All rights reserved.")
            )
            privacy_url = st.text_input("Privacy Policy URL", value=settings.get("privacy_url", ""))
            terms_url = st.text_input("Terms of Service URL", value=settings.get("terms_url", ""))
            if _save_btn("Save Copyright"):
                for k, v in {
                    "footer_copyright": copyright_text, "privacy_url": privacy_url, "terms_url": terms_url
                }.items():
                    update_setting(k, v)
                st.success("Copyright info saved!")
