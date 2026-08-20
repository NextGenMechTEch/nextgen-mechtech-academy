import json
import streamlit as st
import textwrap

from components.icons import icon
from utils.helpers import (
    get_all_settings, get_setting, html_block, esc,
    extract_youtube_id, build_youtube_embed_url, build_youtube_watch_url,
)
from utils.cloudinary_service import resolve_src
from database.connection import get_db_session
from database.models import Course, Announcement, Instructor
from pages.cms_admin import get_cms_section, get_cms_sections
from components.instructor_slider import render_instructors_slider


# Default returned by get_cms_section() for a page/key that has no row yet —
# kept in sync so get_cms_sections() lookups behave identically for missing keys.
_CMS_SECTION_DEFAULT = {"id": None, "title": "", "content": "", "is_visible": True, "display_order": 0}


# TTL=180s (3 min): which courses are published/featured changes only when
# an admin edits a course, not on every page view. Returns plain dicts
# (not SQLAlchemy model instances) so the cached value can be stored/shared
# safely and carries no per-user data.
@st.cache_data(ttl=180, show_spinner=False)
def _get_featured_courses(limit: int) -> list[dict]:
    db = get_db_session()
    try:
        rows = db.query(Course).filter(Course.is_published == True).limit(limit).all()
        return [{
            "id": c.id, "title": c.title, "category": c.category,
            "level": c.level, "duration": c.duration, "description": c.description,
            "fee": c.fee, "image_url": c.image_url, "is_featured": c.is_featured,
        } for c in rows]
    finally:
        db.close()


# TTL=60s (1 min): announcements are more time-sensitive than settings/CMS
# content, so a shorter window is used. Returns plain dicts, no per-user data.
@st.cache_data(ttl=60, show_spinner=False)
def _get_active_announcements(limit: int) -> list[dict]:
    db = get_db_session()
    try:
        rows = (db.query(Announcement)
                .filter(Announcement.is_active == True)
                .order_by(Announcement.created_at.desc())
                .limit(limit).all())
        return [{"id": a.id, "title": a.title, "content": a.content, "created_at": a.created_at} for a in rows]
    finally:
        db.close()


def render_home():
    # One query for every CMS section on this page instead of 8 separate
    # get_cms_section() round trips — see get_cms_sections() in cms_admin.py.
    home_sections = get_cms_sections("home")
    settings = get_all_settings()
    stat_students     = settings.get("stat_students", "500+")
    stat_courses      = settings.get("stat_courses", "12+")
    stat_certs        = settings.get("stat_certificates", "300+")
    stat_instructors  = settings.get("stat_instructors", "10+")
    stat_students_lbl = settings.get("stat_students_label", "Students Enrolled")
    stat_courses_lbl  = settings.get("stat_courses_label", "Active Courses")
    stat_certs_lbl    = settings.get("stat_certificates_label", "Certificates Issued")
    stat_instr_lbl    = settings.get("stat_instructors_label", "Expert Instructors")

    hero_headline = settings.get("hero_headline", "Where <em>Engineers</em> Learn to Build the Future")
    hero_sub      = settings.get("hero_sub",
        f"From Python to PCB Design, from SOLIDWORKS to Machine Learning — gain "
        f"hands-on skills that industry demands. Join {stat_students} students who "
        f"have already transformed their careers.")
    hero_badge    = settings.get("hero_badge", "New · Prompt Engineering &amp; AI Tools course now live")
    hero_btn1     = settings.get("hero_btn1", "Explore Courses")
    hero_btn2     = settings.get("hero_btn2", "Contact Us")

    # ─── Announcement Bar ─────────────────────────────────────────────────
    ann_text    = settings.get("announcement_bar", "")
    ann_visible = settings.get("announcement_bar_visible", "1") == "1"
    if ann_text and ann_visible:
        st.markdown(f'<div class="nmt-ann-bar">{icon("bell", size=13)} {ann_text}</div>',
                    unsafe_allow_html=True)

    # ─── HERO ─────────────────────────────────────────────────────────────
    hero_sec = home_sections.get("hero", _CMS_SECTION_DEFAULT)
    if hero_sec.get("is_visible", True):
        # ── Hero promotional video (admin-manageable — see cms_admin.py "Hero" tab) ──
        # Settings are plain WebsiteSettings rows, same store/cache as every other
        # hero_* field above, so enable/disable and player-option changes take
        # effect on the very next render after an admin save (see update_setting()).
        hero_video_enabled = settings.get("hero_video_enabled", "1") == "1"
        hero_video_url = settings.get("hero_video_url", "https://youtu.be/2yORSxSSstw?si=ee1FmVhoxVJJup17")
        hero_video_id = extract_youtube_id(hero_video_url) if hero_video_enabled else None

        video_html = ""
        if hero_video_id:
            embed_url = build_youtube_embed_url(
                hero_video_id,
                autoplay=settings.get("hero_video_autoplay", "1") == "1",
                muted=settings.get("hero_video_muted", "1") == "1",
                loop=settings.get("hero_video_loop", "1") == "1",
                controls=settings.get("hero_video_controls", "1") == "1",
            )
            watch_url = build_youtube_watch_url(hero_video_id)
            video_html = f"""
            <div class="nmt-hero-media">
              <div class="nmt-hero-video-frame">
                <iframe src="{esc(embed_url)}" title="NextGen MechTech Academy promo video"
                  loading="lazy" frameborder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowfullscreen></iframe>
              </div>
              <a class="nmt-hero-video-watch" href="{esc(watch_url)}" target="_blank" rel="noopener noreferrer">
                {icon("youtube", size=14, color="#fff")}<span>Watch on YouTube</span>
              </a>
            </div>
            """

        # Only switch to the two-column grid when there's actually a video to
        # show it next to — with no video, the hero renders exactly as before.
        grid_open   = '<div class="nmt-hero-grid">' if video_html else ""
        grid_close  = "</div>" if video_html else ""
        content_open  = '<div class="nmt-hero-content">' if video_html else ""
        content_close = "</div>" if video_html else ""

        st.markdown(html_block(f"""
        <div class="nmt-hero nmt-page-enter">
          <div class="nmt-hero-inner">
            {grid_open}
            {content_open}
            <div class="nmt-hero-badge">{icon("zap", size=14, color="#FBBF24")}<span class="tag">{hero_badge}</span></div>
            <h1>{hero_headline}</h1>
            <p class="nmt-hero-sub">{hero_sub}</p>
            {content_close}
            {video_html}
            {grid_close}
          </div>
        </div>
        """), unsafe_allow_html=True)

        st.markdown('<div class="nmt-shell" style="margin-top:-58px;position:relative;z-index:2;">', unsafe_allow_html=True)
        # Change this line:
        _, hb1, hb2, _ = st.columns([1.5, 1.3, 1.3, 1.5], gap="small")
        with hb1:
            if st.button(hero_btn1, key="hero_explore", use_container_width=True, type="primary"):
                st.session_state.page = "courses"; st.rerun()
        with hb2:
            if st.button(hero_btn2, key="hero_contact", use_container_width=True):
                st.session_state.page = "contact"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(html_block(f"""
        <div class="nmt-hero" style="padding: 40px 0; display: flex; justify-content: center; align-items: center;">
          <div class="nmt-hero-inner" style="width: 100%; display: flex; justify-content: center; align-items: center; padding: 0;">
            <div class="nmt-mini-stats-grid" style="
              display: grid; 
              grid-template-columns: repeat(4, 1fr); 
              align-items: center; 
              justify-items: center; 
              width: 100%; 
              max-width: 1060px; 
              margin: 0 auto; 
              padding: 32px 24px;
              background: linear-gradient(135deg, rgba(255, 255, 255, 0.07) 0%, rgba(255, 255, 255, 0.03) 100%);
              backdrop-filter: blur(10px);
              -webkit-backdrop-filter: blur(10px);
              border: 1px solid rgba(255, 255, 255, 0.12);
              border-radius: 16px;
              box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
            ">
              <div class="nmt-hero-stat" style="width:100%; text-align:center;">
                <div class="v" style="text-shadow: 0 2px 10px rgba(255,255,255,0.1);">{stat_students}</div>
                <div class="l" style="letter-spacing: 0.05em; opacity: 0.85;">{stat_students_lbl}</div>
              </div>
              <div class="nmt-hero-stat" style="width:100%; text-align:center; border-left:1px solid rgba(255,255,255,0.1);">
                <div class="v" style="text-shadow: 0 2px 10px rgba(255,255,255,0.1);">{stat_courses}</div>
                <div class="l" style="letter-spacing: 0.05em; opacity: 0.85;">{stat_courses_lbl}</div>
              </div>
              <div class="nmt-hero-stat" style="width:100%; text-align:center; border-left:1px solid rgba(255,255,255,0.1);">
                <div class="v" style="text-shadow: 0 2px 10px rgba(255,255,255,0.1);">{stat_certs}</div>
                <div class="l" style="letter-spacing: 0.05em; opacity: 0.85;">{stat_certs_lbl}</div>
              </div>
              <div class="nmt-hero-stat" style="width:100%; text-align:center; border-left:1px solid rgba(255,255,255,0.1);">
                <div class="v" style="text-shadow: 0 2px 10px rgba(255,255,255,0.1);">{stat_instructors}</div>
                <div class="l" style="letter-spacing: 0.05em; opacity: 0.85;">{stat_instr_lbl}</div>
              </div>
            </div>
          </div>
        </div>
        """), unsafe_allow_html=True)

    # ─── FEATURED COURSES ─────────────────────────────────────────────────
    fc_sec = home_sections.get("featured_courses", _CMS_SECTION_DEFAULT)
    if fc_sec.get("is_visible", True):
        fc_eyebrow  = settings.get("featured_eyebrow", "What We Offer")
        fc_heading  = settings.get("featured_heading", "Featured Courses")
        fc_sub      = settings.get("featured_sub", "")
        fc_count    = int(settings.get("featured_count", "6"))

        featured_courses = _get_featured_courses(fc_count)

        sub_html = f'<p style="color: var(--ink-500); font-size: 15px; max-width: 600px; margin: 12px auto 0; line-height: 1.6; font-weight: 400;">{fc_sub}</p>' if fc_sub else ""
        st.markdown(html_block(f"""
        <div class="nmt-shell" style="
            background: var(--surface-tint, #f8fafc); 
            border: 1px solid rgba(0, 0, 0, 0.04); 
            border-radius: var(--radius-xl, 24px); 
            padding: 56px 24px; 
            margin: 40px auto;
            max-width: 1140px;
            display: flex; 
            justify-content: center; 
            text-align: center;
        ">
          <div style="max-width: 800px; width: 100%;">
            <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(28, 100, 242, 0.08); color: var(--blue-600); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; padding: 6px 14px; border-radius: 100px; margin-bottom: 16px;">
              {icon("star", size=12, color="var(--blue-600)")} <span>{fc_eyebrow}</span>
            </div>
            <h2 style="font-family: var(--font-head); font-size: 32px; font-weight: 800; color: var(--navy-900); margin: 0; letter-spacing: -0.02em; line-height: 1.2;">{fc_heading}</h2>
            {sub_html}
          </div>
        </div>
        """), unsafe_allow_html=True)

        st.markdown('<div class="nmt-shell">', unsafe_allow_html=True)
        if featured_courses:
            cols = st.columns(min(3, len(featured_courses)), gap="medium")
            for i, course in enumerate(featured_courses):
                with cols[i % 3]:
                    featured_badge = f'<div class="nmt-badge-featured">{icon("star", size=11)} Featured</div>' if course["is_featured"] else ""
                    thumb_src = resolve_src(course["image_url"], width=400)
                    thumb = f'<img src="{esc(thumb_src)}" style="width:100%;height:160px;object-fit:cover;border-radius:10px 10px 0 0;" alt="{esc(course["title"])}" onerror="this.style.display=\'none\'">' if thumb_src else ""
                    _desc = course["description"] or ""
                    if len(_desc) > 100:
                        _desc_short = _desc[:100].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
                    else:
                        _desc_short = _desc
                    st.markdown(html_block(f"""
                    <div class="nmt-card" style="animation-delay:{i*0.08}s;">
                      {thumb}
                      <div style="padding:18px 18px 20px;">
                        {featured_badge}
                        <div style="font-size:11px;font-weight:700;color:var(--blue-600);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">{esc(course["category"])}</div>
                        <div class="nmt-card-title">{esc(course["title"])}</div>
                        <div class="nmt-card-meta">{esc(course["level"])} · {esc(course["duration"])}</div>
                        <div class="nmt-card-desc">{esc(_desc_short)}</div>
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:14px;">
                          <div style="font-family:var(--font-head);font-size:17px;font-weight:800;color:var(--navy-900);">PKR {course["fee"]:,.0f}</div>
                          <div style="font-size:11.5px;color:var(--ink-500);">{icon("clock",size=12)} {esc(course["duration"])}</div>
                        </div>
                      </div>
                    </div>
                    """), unsafe_allow_html=True)
                    if st.button("View Course", key=f"fc_{course['id']}", use_container_width=True):
                        st.session_state.selected_course_id = course["id"]
                        st.session_state.page = "courses"
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ─── CATEGORIES ───────────────────────────────────────────────────────
    cat_sec = home_sections.get("categories", _CMS_SECTION_DEFAULT)
    if cat_sec.get("is_visible", True):
        cat_heading = settings.get("categories_heading", "Explore by Category")
        cat_sub     = settings.get("categories_sub", "")

        # Load from CMS or fallback to defaults
        cats_sec = get_cms_section("courses", "categories")
        try:
            CATEGORIES = json.loads(cats_sec["content"]) if cats_sec["content"] else []
        except:
            CATEGORIES = []
        if not CATEGORIES:
            CATEGORIES = [
                {"icon": "code",      "name": "Programming",            "desc": "Python · C · MATLAB"},
                {"icon": "cog",       "name": "Engineering Tools",      "desc": "SOLIDWORKS · MATLAB & Simulink"},
                {"icon": "zap",       "name": "Electronics",            "desc": "Arduino · IoT · PCB Design"},
                {"icon": "bot",       "name": "Artificial Intelligence","desc": "ML · Deep Learning · Prompt Engineering"},
                {"icon": "palette",   "name": "Creative Arts",          "desc": "Graphic Design · Video Editing"},
                {"icon": "bar-chart", "name": "Productivity",           "desc": "Microsoft Office Masterclass"},
            ]

        sub_html = f'<p style="color: var(--ink-500); font-size: 15px; max-width: 600px; margin: 12px auto 0; line-height: 1.6; font-weight: 400;">{cat_sub}</p>' if cat_sub else ""
        st.markdown(html_block(f"""
        <div style="width: 100%; display: flex; justify-content: center; align-items: center; padding: 20px 0; margin-bottom: 40px;">
          <div class="nmt-shell nmt-section" style="
              background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%); 
              padding: 56px 24px; 
              border-radius: 24px; 
              display: flex; 
              justify-content: center; 
              text-align: center; 
              border: 1px solid #E2E8F0;
              width: 100%;
              max-width: 1100px;
              box-shadow: 0 4px 20px rgba(0, 0, 0, 0.01);
          ">
            <div style="max-width: 800px; width: 100%;">
              <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(217, 119, 6, 0.09); color: var(--amber-600); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; padding: 6px 14px; border-radius: 100px; margin-bottom: 18px;">
                {icon("layers", size=12, color="var(--amber-600)")} <span>Categories</span>
              </div>
              <h2 style="font-family: var(--font-head); font-size: 34px; font-weight: 800; color: var(--navy-900); margin: 0; letter-spacing: -0.02em; line-height: 1.2;">{cat_heading}</h2>
              {sub_html}
            </div>
          </div>
        </div>
        """), unsafe_allow_html=True)

        st.markdown('<div class="nmt-shell">', unsafe_allow_html=True)
        cat_cols = st.columns(3, gap="medium")
        for i, cat in enumerate(CATEGORIES):
            with cat_cols[i % 3]:
                st.markdown(html_block(f"""
                <div class="nmt-cat-card" style="animation-delay:{i*0.07}s;">
                  <div class="nmt-cat-icon">{icon(cat.get('icon','layers'), size=22)}</div>
                  <div class="nmt-cat-title">{cat.get('name','')}</div>
                  <div class="nmt-cat-sub">{cat.get('desc','')}</div>
                </div>
                """), unsafe_allow_html=True)
                if st.button("Browse", key=f"cat_{i}", use_container_width=True):
                    st.session_state.page = "courses"
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ─── WHY CHOOSE US ────────────────────────────────────────────────────
    why_sec = home_sections.get("why_features", _CMS_SECTION_DEFAULT)
    if why_sec.get("is_visible", True):
        why_heading = settings.get("why_heading", "Why Choose NextGen MechTech?")
        why_sub     = settings.get("why_sub", "")

        try:
            features_data = json.loads(why_sec["content"]) if why_sec["content"] else []
        except:
            features_data = []
        if not features_data:
            features_data = [
                {"icon": "award",       "title": "Industry-Expert Instructors",  "desc": "Learn from professionals who bring live projects and real domain experience into every session."},
                {"icon": "target",      "title": "100% Practical Training",      "desc": "Every module is project-based. No passive theory-only lectures — you build from day one."},
                {"icon": "file-text",   "title": "Recognised Certificates",      "desc": "Earn credentials acknowledged by employers across Pakistan and verified for international markets."},
                {"icon": "clock",       "title": "Flexible Scheduling",          "desc": "Weekend and weekday batches available to fit around your university timetable or job."},
                {"icon": "handshake",   "title": "Career Support",               "desc": "Job-placement assistance, CV reviews, and mock interviews included after course completion."},
                {"icon": "dollar-sign", "title": "Affordable Fees",              "desc": "World-class instruction at accessible fees, with easy instalment plans available on request."},
            ]

        sub_html = f'<p style="color: var(--ink-500); font-size: 15px; max-width: 600px; margin: 12px auto 0; line-height: 1.6; font-weight: 400;">{why_sub}</p>' if why_sub else ""
        st.markdown(html_block(f"""
        <div class="nmt-shell" style="
            background: var(--surface-tint, #f8fafc); 
            border: 1px solid rgba(0, 0, 0, 0.04); 
            border-radius: var(--radius-xl, 24px); 
            padding: 56px 24px; 
            margin: 40px auto 24px;
            max-width: 1140px;
            display: flex; 
            justify-content: center; 
            text-align: center;
        ">
          <div style="max-width: 800px; width: 100%;">
            <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(217, 119, 6, 0.08); color: var(--amber-600); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; padding: 6px 14px; border-radius: 100px; margin-bottom: 16px;">
              {icon("star", size=12, color="var(--amber-600)")} <span>Why Us</span>
            </div>
            <h2 style="font-family: var(--font-head); font-size: 32px; font-weight: 800; color: var(--navy-900); margin: 0; letter-spacing: -0.02em; line-height: 1.2;">{why_heading}</h2>
            {sub_html}
          </div>
        </div>
        """), unsafe_allow_html=True)

        st.markdown('<div class="nmt-shell nmt-stagger">', unsafe_allow_html=True)
        feat_cols = st.columns(3, gap="medium")
        for i, feat in enumerate(features_data):
            with feat_cols[i % 3]:
                st.markdown(html_block(f"""
                <div class="nmt-feature nmt-fade-in" style="padding:30px 26px;animation-delay:{i*0.07}s;">
                  <div class="nmt-feature-icon">{icon(feat.get('icon','star'), size=21)}</div>
                  <h3>{feat.get('title','')}</h3>
                  <p>{feat.get('desc','')}</p>
                </div>
                """), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ─── INSTRUCTORS ──────────────────────────────────────────────────────
    instr_sec = home_sections.get("instructors", _CMS_SECTION_DEFAULT)
    if instr_sec.get("is_visible", True):
        instr_heading = settings.get("instructors_heading", "Meet Our Expert Instructors")
        instr_sub     = settings.get("instructors_sub", "")

        db = get_db_session()
        try:
            instructors = (db.query(Instructor)
                .filter(Instructor.is_visible == True)
                .order_by(Instructor.display_order).all())
        finally:
            db.close()

        if instructors:
            sub_html = f'<p style="color: var(--ink-500); font-size: 15px; max-width: 600px; margin: 12px auto 0; line-height: 1.6; font-weight: 400;">{instr_sub}</p>' if 'instr_sub' in locals() or 'instr_sub' in globals() else ""
            st.markdown(html_block(f"""
            <div class="nmt-shell" style="
              background: var(--surface-tint, #f8fafc); 
              border: 1px solid rgba(0, 0, 0, 0.04); 
              border-radius: var(--radius-xl, 24px); 
              padding: 56px 24px; 
              margin: 40px auto 24px;
              max-width: 1140px;
              display: flex; 
              justify-content: center; 
              text-align: center;
            ">
            <div style="max-width: 800px; width: 100%;">
            <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(217, 119, 6, 0.08); color: var(--amber-600); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; padding: 6px 14px; border-radius: 100px; margin-bottom: 16px;">
              {icon("users", size=12, color="var(--amber-600)")} <span>Our Instructors</span>
            </div>
            <h2 style="font-family: var(--font-head); font-size: 32px; font-weight: 800; color: var(--navy-900); margin: 0; letter-spacing: -0.02em; line-height: 1.2;">{settings.get("instructors_heading", "Meet Our Expert Instructors")}</h2>
            {sub_html}
          </div>
        </div>
        """), unsafe_allow_html=True)
            st.markdown('<div class="nmt-shell">', unsafe_allow_html=True)
            st.markdown(html_block(render_instructors_slider(instructors)), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ─── TESTIMONIALS ─────────────────────────────────────────────────────
    test_sec = home_sections.get("testimonials", _CMS_SECTION_DEFAULT)
    if test_sec.get("is_visible", True) and test_sec["content"]:
        testimonials_heading = settings.get("testimonials_heading", "What Our Students Say")
        try:
            testimonials = json.loads(test_sec["content"])
        except:
            testimonials = []
            
        if testimonials:
            # 1. Outer Section Container Box (Matches your screenshot layout)
            st.markdown(html_block(f"""
            <div class="nmt-shell" style="
                background: var(--surface-tint, #f8fafc); 
                border: 1px solid rgba(0, 0, 0, 0.04); 
                border-radius: var(--radius-xl, 24px); 
                padding: 56px 24px; 
                margin: 40px auto;
                max-width: 1140px;
            ">
              
              <!-- Perfectly Centered Header Section Inside the Box -->
              <div style="display: flex; justify-content: center; text-align: center; margin-bottom: 40px;">
                <div style="max-width: 800px; width: 100%;">
                  <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(217, 119, 6, 0.08); color: var(--amber-600); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; padding: 6px 14px; border-radius: 100px; margin-bottom: 16px;">
                    {icon("heart", size=12, color="var(--amber-600)")} <span>Testimonials</span>
                  </div>
                  <h2 style="font-family: var(--font-head); font-size: 32px; font-weight: 800; color: var(--navy-900); margin: 0; letter-spacing: -0.02em; line-height: 1.2;">{testimonials_heading}</h2>
                </div>
              </div>
            """), unsafe_allow_html=True)

            # 2. Card Grid Layout Container
            grid_html = f"""
            <div class="nmt-testimonials-grid" style="
                display: grid; 
                grid-template-columns: repeat({min(3, len(testimonials))}, 1fr); 
                gap: 24px; 
                width: 100%; 
                margin: 0 auto;
            ">
            """

            # EXACT SAME LOOP LOGIC — NO CHANGES MADE
            for i, t in enumerate(testimonials[:3]):
                rating = max(0, min(5, int(t.get("rating", 5) or 5)))
                stars_html = "".join([icon("star", size=13, color="var(--amber-500)") for _ in range(rating)])
                
                name_str = t.get('name', 'Anonymous')
                initial_letter = name_str[0].upper() if name_str else "U"
                role_str = t.get('course', t.get('role', 'Student'))

                avatar_colors = ["var(--navy-900)", "var(--blue-600)", "var(--amber-600)"]
                bg_avatar = avatar_colors[i % len(avatar_colors)]

                grid_html += f"""
                <div style="background: #fff; border: 1px solid rgba(0,0,0,0.05); border-radius: 16px; padding: 24px; text-align: left; box-shadow: 0 4px 14px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
                  <div>
                    <div style="margin-bottom: 12px; display: flex; gap: 2px;">
                      {stars_html}
                    </div>
                    <p style="color: var(--ink-700); font-size: 13.5px; line-height: 1.6; font-weight: 400; margin: 0 0 16px; font-style: italic;">
                      "{t.get('text', '')}"
                    </p>
                  </div>
                  <div style="display: flex; align-items: center; gap: 10px; border-top: 1px solid rgba(0,0,0,0.04); padding-top: 12px; margin-top: auto;">
                    <div style="width: 32px; height: 32px; background: {bg_avatar}; color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; flex-shrink: 0;">
                      {initial_letter}
                    </div>
                    <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                      <div style="font-weight: 700; color: var(--navy-900); font-size: 13px; line-height: 1.3;">{name_str}</div>
                      <div style="font-size: 11px; color: var(--ink-400); margin-top: 1px;">{role_str}</div>
                    </div>
                  </div>
                </div>
                """
            
            grid_html += "</div></div>" # Closes the internal grid and the outer master layout card wrapper
            
            st.markdown(html_block(grid_html), unsafe_allow_html=True)

    # ─── FAQ ──────────────────────────────────────────────────────────────
    faq_sec = home_sections.get("faq", _CMS_SECTION_DEFAULT)
    if faq_sec.get("is_visible", True) and faq_sec["content"]:
        faq_heading = settings.get("faq_heading", "Frequently Asked Questions")
        try:
            faqs = json.loads(faq_sec["content"])
        except:
            faqs = []
        if faqs:
            st.markdown(html_block(f"""
            <div class="nmt-shell nmt-section">
              <div class="nmt-section-head center">
                <div class="nmt-eyebrow">{icon("help-circle", size=13, color="var(--amber-600)")} FAQs</div>
                <h2 class="nmt-h2">{faq_heading}</h2>
              </div>
            </div>
            """), unsafe_allow_html=True)
            st.markdown('<div class="nmt-shell">', unsafe_allow_html=True)
            faq_col, _ = st.columns([2, 1])
            with faq_col:
                for i, faq in enumerate(faqs):
                    with st.expander(faq.get("q", ""), expanded=(i == 0)):
                        st.markdown(f'<p style="color:var(--ink-500);font-size:13.5px;line-height:1.7;">{faq.get("a","")}</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ─── CALL TO ACTION ───────────────────────────────────────────────────
    cta_sec = home_sections.get("cta", _CMS_SECTION_DEFAULT)
    if cta_sec.get("is_visible", True):
        cta_heading = settings.get("cta_heading", "Ready to Start Your Journey?")
        cta_sub     = settings.get("cta_sub", "Join hundreds of students already learning at NextGen MechTech Academy.")
        cta_btn     = settings.get("cta_btn", "Enrol Now")

        st.markdown(html_block(f"""
        <div class="nmt-cta-section" style="border-radius:var(--radius-xl);padding:56px 32px;text-align:center;margin:32px 0;color:#fff;">
          <div class="nmt-eyebrow" style="color:var(--amber-400);">{icon("zap", size=13, color="var(--amber-400)")} Get Started</div>
          <h2 style="font-family:var(--font-head);font-size:28px;font-weight:800;margin:12px 0 10px;">{cta_heading}</h2>
          <p style="color:rgba(255,255,255,0.78);font-size:14.5px;max-width:480px;margin:0 auto 28px;line-height:1.7;">{cta_sub}</p>
        </div>
        """), unsafe_allow_html=True)
        _, cta_c, _ = st.columns([2, 1.5, 2])
        with cta_c:
            if st.button(cta_btn, key="cta_enrol", use_container_width=True, type="primary"):
                st.session_state.page = "courses"; st.rerun()

    # ─── ACTIVE DB ANNOUNCEMENTS ──────────────────────────────────────────
    active_anns = _get_active_announcements(3)

    if active_anns:
        st.markdown('<div class="nmt-shell" style="margin-top:16px;">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{icon("bell", size=17)} Latest Announcements</h3>', unsafe_allow_html=True)
        for ann in active_anns:
            st.markdown(html_block(f"""
            <div class="nmt-announce" style="background:var(--info-bg);border:1.5px solid var(--info-line);border-radius:var(--radius-md);padding:16px 20px;margin-bottom:10px;">
              <div style="font-weight:700;color:var(--ink-900);font-size:14px;margin-bottom:4px;">{ann["title"]}</div>
              <div style="color:var(--ink-500);font-size:13px;">{ann["content"]}</div>
            </div>
            """), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)