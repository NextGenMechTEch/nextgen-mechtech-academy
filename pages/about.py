import json
import streamlit as st
import textwrap

from components.icons import icon
from utils.helpers import get_logo_base64, get_all_settings, html_block
from database.connection import get_db_session
from database.models import Instructor
from pages.cms_admin import get_cms_section
from components.instructor_slider import render_instructors_slider


def render_about():
    settings  = get_all_settings()
    logo_b64  = get_logo_base64()

    banner_heading = settings.get("about_banner_heading", "About Us")
    banner_sub     = settings.get("about_banner_sub", "Empowering Pakistan's engineers and technologists since our founding.")
    eyebrow        = settings.get("about_eyebrow", "Who We Are")
    heading        = settings.get("about_heading", "NextGen MechTech Academy")
    para1          = settings.get("about_para1",
        "NextGen MechTech Academy is a premier technical education institute based in Lahore, Pakistan. "
        "We specialize in delivering cutting-edge, hands-on training in engineering, programming, electronics, "
        "and creative technology disciplines.")
    para2          = settings.get("about_para2",
        "Founded with a mission to bridge the gap between academic theory and industry practice, "
        "we have empowered hundreds of students to transform their careers and build solutions that matter.")
    team_heading   = settings.get("team_heading", "Meet the Instructors")
    team_eyebrow   = settings.get("team_eyebrow", "Our Team")

    # ─── Banner ──────────────────────────────────────────────────────────
    st.markdown(html_block(f"""
    <div class="nmt-page-banner nmt-page-enter">
      <div class="nmt-page-banner-inner" style="text-align:center;">
        <div class="nmt-page-banner-icon">{icon("info", size=24, color="#fff")}</div>
        <h1>{banner_heading}</h1>
        <p style="text-align:center;max-width:560px;margin:0 auto;">{banner_sub}</p>
      </div>
    </div>
    """), unsafe_allow_html=True)

    st.markdown('<div class="nmt-content">', unsafe_allow_html=True)

    # ─── About text + Quick Facts ─────────────────────────────────────────
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        if logo_b64:
            st.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="width:120px;height:auto;margin-bottom:24px;border-radius:14px;" alt="NextGen MechTech Academy logo">', unsafe_allow_html=True)
        st.markdown(html_block(f"""
        <div class="nmt-eyebrow">{icon("graduation-cap", size=13, color="var(--amber-600)")} {eyebrow}</div>
        <h2 class="nmt-h2">{heading}</h2>
        <p style="color:var(--ink-500);line-height:1.8;font-size:14.5px;margin-bottom:16px;">{para1}</p>
        <p style="color:var(--ink-500);line-height:1.8;font-size:14.5px;">{para2}</p>
        """), unsafe_allow_html=True)

    with col2:
        # Quick facts from CMS
        f1v = settings.get("about_fact1_val", "2022");  f1l = settings.get("about_fact1_lbl", "Founded")
        f2v = settings.get("about_fact2_val", "500+");  f2l = settings.get("about_fact2_lbl", "Graduates")
        f3v = settings.get("about_fact3_val", "12+");   f3l = settings.get("about_fact3_lbl", "Courses")
        f4v = settings.get("about_fact4_val", "10+");   f4l = settings.get("about_fact4_lbl", "Instructors")
        facts = [(f1v, f1l), (f2v, f2l), (f3v, f3l), (f4v, f4l)]
        fact_html = "".join(
            f'<div style="background:rgba(255,255,255,0.1);border-radius:12px;padding:20px;text-align:center;">'
            f'<div style="font-family:var(--font-head);font-size:34px;font-weight:800;color:#fff;">{v}</div>'
            f'<div style="font-size:11.5px;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:0.08em;margin-top:4px;">{l}</div></div>'
            for v, l in facts
        )
        st.markdown(html_block(f"""
        <div style="background:linear-gradient(135deg,var(--navy-900),var(--blue-600));border-radius:20px;padding:36px;color:white;height:100%;min-height:360px;">
          <h3 style="font-family:var(--font-head);font-size:20px;font-weight:700;margin-bottom:22px;">Quick Facts</h3>
          <div class="nmt-quickfacts-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">{fact_html}</div>
        </div>
        """), unsafe_allow_html=True)

    # ─── Mission / Vision / Values ────────────────────────────────────────
    mvv_sec = get_cms_section("about", "mvv")
    try:
        MVV = json.loads(mvv_sec["content"]) if mvv_sec["content"] else []
    except:
        MVV = []
    if not MVV:
        MVV = [
            {"icon": "target",      "title": "Our Mission", "text": "To provide accessible, practical, and industry-relevant technical education that equips students with the skills to innovate, build, and succeed."},
            {"icon": "trending-up", "title": "Our Vision",  "text": "To become Pakistan's most impactful technical academy — consistently producing graduates who drive innovation and build startups."},
            {"icon": "shield",      "title": "Our Values",  "text": "Excellence in everything we teach. Integrity in how we operate. Accessibility so no motivated student is left behind. Innovation through continuous curriculum updates."},
        ]

    st.markdown('<div style="margin-top:56px;">', unsafe_allow_html=True)
    mvv_cols = st.columns(len(MVV), gap="medium")
    for i, item in enumerate(MVV):
        with mvv_cols[i]:
            st.markdown(html_block(f"""
            <div class="nmt-feature nmt-fade-in" style="padding:30px 26px;animation-delay:{i*0.1}s;">
              <div class="nmt-feature-icon">{icon(item.get('icon','star'), size=21)}</div>
              <h3>{item.get('title','')}</h3>
              <p>{item.get('text','')}</p>
            </div>
            """), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ─── Team ─────────────────────────────────────────────────────────────
    db = get_db_session()
    try:
        instructors = (db.query(Instructor)
            .filter(Instructor.is_visible == True)
            .order_by(Instructor.display_order).all())
    finally:
        db.close()

    st.markdown(html_block(f"""
    <div style="margin-top:56px;">
      <div class="nmt-eyebrow">{icon("users", size=13, color="var(--amber-600)")} {team_eyebrow}</div>
      <h2 class="nmt-h2" style="margin-bottom:28px;">{team_heading}</h2>
    </div>
    """), unsafe_allow_html=True)

    if instructors:
        st.markdown(html_block(render_instructors_slider(instructors)), unsafe_allow_html=True)
    else:
        st.info("No instructors found.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ─── CTA ─────────────────────────────────────────────────────────────
    cta_text = settings.get("about_cta_text", "Ready to start learning?")
    cta_btn  = settings.get("about_cta_btn", "View Courses")
    st.markdown(html_block(f"""
    <div style="margin-top:48px;background:linear-gradient(135deg,var(--navy-900),var(--blue-600));
        border-radius:var(--radius-xl);padding:40px 32px;text-align:center;color:#fff;">
      <h3 style="font-family:var(--font-head);font-size:22px;font-weight:800;margin-bottom:8px;">{cta_text}</h3>
    </div>
    """), unsafe_allow_html=True)
    _, btn_c, _ = st.columns([2, 1.2, 2])
    with btn_c:
        if st.button(cta_btn, key="about_cta", use_container_width=True, type="primary"):
            st.session_state.page = "courses"; st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)