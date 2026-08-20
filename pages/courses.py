import json
import streamlit as st
import textwrap

from components.icons import icon
from utils.helpers import get_all_settings, get_setting, html_block, esc
from utils.cloudinary_service import resolve_src
from database.connection import get_db_session
from database.models import Course, Instructor
from sqlalchemy.orm import joinedload
from pages.cms_admin import get_cms_section


def render_courses():
    if "selected_course_id" in st.session_state and st.session_state.selected_course_id:
        _render_course_detail(st.session_state.selected_course_id)
        return
    _render_courses_grid()


def _render_courses_grid():
    settings = get_all_settings()
    banner_heading  = settings.get("courses_banner_heading", "Our Courses")
    banner_sub      = settings.get("courses_banner_sub", "Explore our full range of industry-relevant technical courses.")
    grid_heading    = settings.get("courses_grid_heading", "All Courses")
    empty_msg       = settings.get("courses_empty_msg", "No courses found in this category.")

    st.markdown(html_block(f"""
    <div class="nmt-page-banner nmt-page-enter">
      <div class="nmt-page-banner-inner" style="text-align:center;">
        <div class="nmt-page-banner-icon">{icon("book-open", size=24, color="#fff")}</div>
        <h1>{banner_heading}</h1>
        <p style="text-align:center;max-width:560px;margin:0 auto;">{banner_sub}</p>
      </div>
    </div>
    """), unsafe_allow_html=True)

    st.markdown('<div class="nmt-content">', unsafe_allow_html=True)
    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{grid_heading}</h3>', unsafe_allow_html=True)

    # Category filter — always derived live from the actual courses in the
    # database, so any category used on a published course (including brand
    # new ones added by an Admin/Super Admin) shows up automatically with no
    # code changes. CMS-configured category ordering (from the "Course
    # Categories" CMS section) is used only to order/prioritize the known
    # names; it never hides a real category that exists in the database.
    db = get_db_session()
    try:
        db_categories = [
            row[0] for row in
            db.query(Course.category)
              .filter(Course.is_published == True, Course.category.isnot(None), Course.category != "")
              .distinct()
              .all()
        ]
    finally:
        db.close()
    db_categories_set = set(db_categories)

    cats_sec = get_cms_section("courses", "categories")
    try:
        cats_data = json.loads(cats_sec["content"]) if cats_sec["content"] else []
        cms_order = [c["name"] for c in cats_data if c.get("name") in db_categories_set]
    except Exception:
        cms_order = []

    remaining = sorted(db_categories_set - set(cms_order))
    CATS = cms_order + remaining

    filter_cols = st.columns([2, 1, 1])
    with filter_cols[0]:
        search = st.text_input("Search courses", placeholder="e.g. Python, Arduino, SOLIDWORKS…", label_visibility="collapsed")
    with filter_cols[1]:
        selected_cat = st.selectbox("Category", ["All Categories"] + CATS, label_visibility="collapsed")
    with filter_cols[2]:
        level_filter = st.selectbox("Level", ["All Levels", "Beginner", "Intermediate", "Advanced", "Beginner to Intermediate", "Beginner to Advanced"], label_visibility="collapsed")

    db = get_db_session()
    try:
        q = db.query(Course).options(joinedload(Course.instructor)).filter(Course.is_published == True)
        if selected_cat != "All Categories":
            q = q.filter(Course.category == selected_cat)
        if level_filter != "All Levels":
            q = q.filter(Course.level.contains(level_filter.split(" ")[0]))
        if search:
            q = q.filter(Course.title.ilike(f"%{search}%") | Course.description.ilike(f"%{search}%"))
        courses = q.order_by(Course.is_featured.desc(), Course.display_order, Course.created_at.desc()).all()
    finally:
        db.close()

    if not courses:
        st.info(empty_msg)
    else:
        st.caption(f"{len(courses)} course(s) found")
        cols = st.columns(3, gap="medium")
        for i, course in enumerate(courses):
            with cols[i % 3]:
                featured_badge = f'<div class="nmt-badge-featured">{icon("star", size=11)} Featured</div>' if course.is_featured else ""
                cert_badge = f'<span style="font-size:10.5px;background:var(--success-bg);color:var(--success-tx);padding:2px 8px;border-radius:20px;font-weight:600;">{icon("award", size=10)} Certificate</span>' if course.certificate_available else ""
                thumb_src = resolve_src(course.image_url, width=400)
                thumb = f'<img src="{esc(thumb_src)}" style="width:100%;height:155px;object-fit:cover;border-radius:10px 10px 0 0;" alt="{esc(course.title)}" onerror="this.style.display=\'none\'">' if thumb_src else ""
                _open = getattr(course, "enrollment_open", True)
                enroll_status = (
                    f'<span class="nmt-status-open">{icon("check-circle", size=11)} Open</span>' if _open
                    else f'<span class="nmt-status-closed">{icon("x-circle", size=11)} Closed</span>'
                )
                _desc = course.description or ""
                _desc_short = _desc[:90].rsplit(" ", 1)[0].rstrip(",.;:") + "…" if len(_desc) > 90 else _desc

                card_html = f"""<div class="nmt-card" style="animation-delay:{i*0.06}s;">{thumb}<div style="padding:18px 18px 14px;">{featured_badge}<div style="font-size:11px;font-weight:700;color:var(--blue-600);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">{esc(course.category)}</div><div class="nmt-card-title">{esc(course.title)}</div><div class="nmt-card-meta">{esc(course.level)} · {esc(course.duration)}</div><div class="nmt-card-desc">{esc(_desc_short)}</div><div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;flex-wrap:wrap;gap:6px;"><div style="font-family:var(--font-head);font-size:17px;font-weight:800;color:var(--navy-900);">PKR {course.fee:,.0f}</div>{cert_badge}</div><div style="font-size:11px;display:flex;align-items:center;gap:4px;margin-top:8px;">{enroll_status}</div></div></div>"""
                st.markdown(card_html, unsafe_allow_html=True)
                if st.button("View Details", key=f"view_c_{course.id}", use_container_width=True, type="primary"):
                    st.session_state.selected_course_id = course.id
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def _render_course_detail(course_id: int):
    settings = get_all_settings()
    enroll_btn_text      = settings.get("enroll_btn_text", "Enrol in This Course")
    related_heading      = settings.get("related_courses_heading", "Related Courses")
    cert_label           = settings.get("cert_section_label", "Certificate")
    faq_label            = settings.get("course_faq_label", "Frequently Asked Questions")

    db = get_db_session()
    try:
        course = db.query(Course).options(joinedload(Course.instructor)).filter(Course.id == course_id).first()
        if not course:
            st.error("Course not found.")
            if st.button("← Back to Courses"):
                st.session_state.selected_course_id = None
                st.rerun()
            return

        related = db.query(Course).filter(
            Course.category == course.category,
            Course.id != course.id,
            Course.is_published == True
        ).limit(3).all()
    finally:
        db.close()

    # Back button
    if st.button("← All Courses", key="back_to_courses"):
        st.session_state.selected_course_id = None
        st.rerun()

    # Banner
    banner_url = resolve_src(getattr(course, "banner_url", None) or course.image_url or "", width=1200)
    if banner_url:
        st.markdown(f'<img src="{esc(banner_url)}" style="width:100%;max-height:280px;object-fit:cover;border-radius:var(--radius-lg);margin-bottom:24px;" alt="{esc(course.title)}">', unsafe_allow_html=True)

    # Header row
    col_main, col_side = st.columns([2, 1], gap="large")

    with col_main:
        st.markdown(html_block(f"""
        <div class="nmt-page-enter">
          <div style="font-size:11.5px;font-weight:700;color:var(--blue-600);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">{esc(course.category)}</div>
          <h1 style="font-family:var(--font-head);font-size:28px;font-weight:800;color:var(--ink-900);margin:0 0 12px;">{esc(course.title)}</h1>
          <p style="color:var(--ink-500);font-size:15px;line-height:1.75;margin-bottom:20px;">{esc(course.description)}</p>
        </div>
        """), unsafe_allow_html=True)

        # Meta tags row
        lang = getattr(course, "language", None) or "Urdu / English"
        meta_items = [
            ("clock", course.duration),
            ("bar-chart", course.level),
            ("globe", lang),
            ("folder", course.category),
        ]
        if course.certificate_available:
            meta_items.append(("award", "Certificate Included"))
        meta_html = "".join(
            f'<span style="display:inline-flex;align-items:center;gap:5px;background:var(--surface-soft);'
            f'border:1px solid var(--line);border-radius:20px;padding:5px 12px;font-size:12.5px;color:var(--ink-700);font-weight:500;">'
            f'{icon(ic, size=12)} {esc(val)}</span>'
            for ic, val in meta_items
        )
        st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px;">{meta_html}</div>', unsafe_allow_html=True)

        # Full description
        if course.full_description:
            st.markdown(html_block(f"""
            <div style="background:var(--surface-soft);border-radius:var(--radius-md);padding:22px;border:1px solid var(--line);margin-bottom:24px;">
              <h3 style="font-family:var(--font-head);font-size:16px;font-weight:700;color:var(--ink-900);margin-bottom:10px;">{icon("info", size=15)} About This Course</h3>
              <p style="color:var(--ink-700);font-size:13.5px;line-height:1.8;">{esc(course.full_description)}</p>
            </div>
            """), unsafe_allow_html=True)

        # What You'll Learn
        if course.what_you_learn:
            try:
                learn_items = json.loads(course.what_you_learn) if course.what_you_learn.startswith('[') else [course.what_you_learn]
            except:
                learn_items = [course.what_you_learn]
            items_html = "".join(
                f'<div style="display:flex;gap:10px;margin-bottom:8px;align-items:flex-start;">'
                f'<span style="color:var(--success-tx);flex-shrink:0;margin-top:1px;">{icon("check-circle", size=14)}</span>'
                f'<span style="font-size:13.5px;color:var(--ink-700);">{esc(item)}</span></div>'
                for item in learn_items
            )
            st.markdown(html_block(f"""
            <div style="background:var(--info-bg);border:1px solid var(--info-line);border-radius:var(--radius-md);padding:22px;margin-bottom:24px;">
              <h3 style="font-family:var(--font-head);font-size:16px;font-weight:700;color:var(--ink-900);margin-bottom:14px;">{icon("check-circle", size=15)} What You'll Learn</h3>
              {items_html}
            </div>
            """), unsafe_allow_html=True)

        # Syllabus / Modules
        if course.syllabus:
            try:
                syllabus_data = json.loads(course.syllabus) if course.syllabus.startswith('[') else []
                if syllabus_data:
                    modules_html = ""
                    for mod in syllabus_data:
                        if isinstance(mod, dict):
                            topics = mod.get("topics", [])
                            topics_html = "".join(f'<li style="font-size:13px;color:var(--ink-500);margin-bottom:4px;">{esc(t)}</li>' for t in topics)
                            modules_html += f'<div style="margin-bottom:12px;"><div style="font-weight:600;color:var(--ink-900);font-size:13.5px;margin-bottom:6px;">{icon("folder", size=13)} {esc(mod.get("module",""))}</div><ul style="margin:0;padding-left:20px;">{topics_html}</ul></div>'
                        else:
                            modules_html += f'<div style="font-size:13.5px;color:var(--ink-700);margin-bottom:6px;">{icon("circle", size=10)} {esc(mod)}</div>'
                    st.markdown(html_block(f"""
                    <div style="background:var(--surface-soft);border-radius:var(--radius-md);padding:22px;border:1px solid var(--line);margin-bottom:24px;">
                      <h3 style="font-family:var(--font-head);font-size:16px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{icon("list", size=15)} Syllabus & Modules</h3>
                      {modules_html}
                    </div>
                    """), unsafe_allow_html=True)
            except:
                st.markdown(html_block(f"""
                <div style="background:var(--surface-soft);border-radius:var(--radius-md);padding:22px;border:1px solid var(--line);margin-bottom:24px;">
                  <h3 style="font-family:var(--font-head);font-size:16px;font-weight:700;color:var(--ink-900);margin-bottom:10px;">Syllabus</h3>
                  <p style="font-size:13.5px;color:var(--ink-700);line-height:1.7;">{esc(course.syllabus)}</p>
                </div>
                """), unsafe_allow_html=True)

        # Skills / Topics
        skills_content = getattr(course, "skills_learned", None) or getattr(course, "topics_covered", None)
        if skills_content:
            try:
                skills = json.loads(skills_content) if skills_content.startswith('[') else [skills_content]
            except:
                skills = [skills_content]
            skills_html = "".join(
                f'<span style="background:var(--blue-50);border:1px solid var(--blue-100);color:var(--blue-600);'
                f'padding:4px 12px;border-radius:20px;font-size:12px;font-weight:500;">{esc(s)}</span>'
                for s in skills
            )
            st.markdown(html_block(f"""
            <div style="margin-bottom:24px;">
              <h3 style="font-family:var(--font-head);font-size:16px;font-weight:700;color:var(--ink-900);margin-bottom:12px;">{icon("zap", size=15)} Skills You Will Learn</h3>
              <div style="display:flex;flex-wrap:wrap;gap:8px;">{skills_html}</div>
            </div>
            """), unsafe_allow_html=True)

        # Prerequisites
        if course.prerequisites:
            st.markdown(html_block(f"""
            <div style="background:var(--warning-bg);border:1px solid var(--warning-line);border-radius:var(--radius-md);padding:18px 22px;margin-bottom:24px;">
              <h3 style="font-family:var(--font-head);font-size:15px;font-weight:700;color:var(--ink-900);margin-bottom:8px;">{icon("alert-circle", size=14)} Prerequisites</h3>
              <p style="font-size:13.5px;color:var(--ink-700);">{esc(course.prerequisites)}</p>
            </div>
            """), unsafe_allow_html=True)

        # Software & Projects
        sw = getattr(course, "software_used", None)
        proj = getattr(course, "projects_included", None)
        if sw or proj:
            sw_col, proj_col = st.columns(2)
            if sw:
                with sw_col:
                    try:
                        sw_list = json.loads(sw) if sw.startswith('[') else [sw]
                    except:
                        sw_list = [sw]
                    sw_html = "".join(f'<div style="font-size:13px;color:var(--ink-700);margin-bottom:4px;">{icon("monitor", size=11)} {esc(s)}</div>' for s in sw_list)
                    st.markdown(html_block(f"""
                    <div style="background:var(--surface-soft);border:1px solid var(--line);border-radius:var(--radius-md);padding:18px;margin-bottom:24px;">
                      <h4 style="font-size:14px;font-weight:700;margin-bottom:10px;">{icon("tool", size=13)} Software Used</h4>
                      {sw_html}
                    </div>
                    """), unsafe_allow_html=True)
            if proj:
                with proj_col:
                    try:
                        proj_list = json.loads(proj) if proj.startswith('[') else [proj]
                    except:
                        proj_list = [proj]
                    proj_html = "".join(f'<div style="font-size:13px;color:var(--ink-700);margin-bottom:4px;">{icon("package", size=11)} {esc(p)}</div>' for p in proj_list)
                    st.markdown(html_block(f"""
                    <div style="background:var(--success-bg);border:1px solid var(--success-line);border-radius:var(--radius-md);padding:18px;margin-bottom:24px;">
                      <h4 style="font-size:14px;font-weight:700;margin-bottom:10px;">{icon("package", size=13)} Projects Included</h4>
                      {proj_html}
                    </div>
                    """), unsafe_allow_html=True)

        # FAQs
        if course.faqs:
            try:
                faqs = json.loads(course.faqs)
                if faqs:
                    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:16px;font-weight:700;margin:24px 0 14px;">{icon("help-circle", size=15)} {faq_label}</h3>', unsafe_allow_html=True)
                    for faq in faqs:
                        with st.expander(faq.get("q", "")):
                            st.markdown(f'<p style="color:var(--ink-500);font-size:13.5px;line-height:1.7;">{esc(faq.get("a",""))}</p>', unsafe_allow_html=True)
            except:
                pass

    # Side card
    with col_side:
        fee_display = f"PKR {course.fee:,.0f}"
        enroll_open = getattr(course, "enrollment_open", True)
        cert_html = ""
        if course.certificate_available:
            cert_html = f"""
            <div style="display:flex;gap:10px;align-items:center;padding:12px 0;border-top:1px solid var(--line);">
              <div style="width:32px;height:32px;border-radius:8px;background:var(--success-bg);display:flex;align-items:center;justify-content:center;">{icon("award", size=15, color="var(--success-tx)")}</div>
              <div>
                <div style="font-weight:600;font-size:13px;color:var(--ink-900);">{cert_label}</div>
                <div style="font-size:11.5px;color:var(--ink-500);">Verifiable online</div>
              </div>
            </div>
            """

        instr_html = ""
        if course.instructor:
            instr = course.instructor
            initials = "".join(p[0] for p in instr.name.replace("Engr. ", "").replace("Dr. ", "").split()[:2]).upper()
            if instr.photo_data:
                ph = f'<img src="{resolve_src(instr.photo_data)}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;" alt="{esc(instr.name)}">'
            elif instr.photo_url:
                ph = f'<img src="{esc(instr.photo_url)}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;" alt="{esc(instr.name)}" onerror="this.style.display=\'none\'">'
            else:
                ph = f'<div style="width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,var(--navy-900),var(--blue-600));display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:14px;">{esc(initials)}</div>'
            instr_html = f"""
            <div style="padding:14px 0;border-top:1px solid var(--line);">
              <div style="font-size:11px;color:var(--ink-500);font-weight:700;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:10px;">Instructor</div>
              <div style="display:flex;align-items:center;gap:12px;">
                {ph}
                <div>
                  <div style="font-weight:700;font-size:13.5px;color:var(--ink-900);">{esc(instr.name)}</div>
                  <div style="font-size:11.5px;color:var(--blue-600);">{esc(instr.designation)}</div>
                </div>
              </div>
            </div>
            """

        status_color = "var(--success-tx)" if enroll_open else "var(--danger-tx)"
        status_text  = "Enrolment Open" if enroll_open else "Enrolment Closed"

        st.markdown(html_block(f"""
        <div class="nmt-glass nmt-course-side" style="padding:24px;border-radius:var(--radius-lg);border:1.5px solid var(--line);">
          <div style="font-family:var(--font-head);font-size:28px;font-weight:800;color:var(--navy-900);margin-bottom:4px;">{fee_display}</div>
          <div style="font-size:12px;font-weight:700;color:{status_color};margin-bottom:18px;">{status_text}</div>
          {instr_html}
          {cert_html}
          <div style="margin-top:14px;padding-top:14px;border-top:1px solid var(--line);">
            <div style="font-size:12px;font-weight:700;color:var(--ink-500);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px;">Quick Info</div>
            <div style="font-size:13px;color:var(--ink-700);margin-bottom:6px;">{icon("clock",size=12)} Duration: {esc(course.duration)}</div>
            <div style="font-size:13px;color:var(--ink-700);margin-bottom:6px;">{icon("bar-chart",size=12)} Level: {esc(course.level)}</div>
            <div style="font-size:13px;color:var(--ink-700);margin-bottom:6px;">{icon("globe",size=12)} Language: {esc(getattr(course, "language", "Urdu / English") or "Urdu / English")}</div>
          </div>
        </div>
        """), unsafe_allow_html=True)

        if enroll_open:
            user = st.session_state.get("user")
            if user:
                if st.button(enroll_btn_text, key=f"enroll_{course.id}", use_container_width=True, type="primary"):
                    st.session_state.enroll_course_id = course.id
                    st.session_state.page = "dashboard"
                    st.rerun()
            else:
                if st.button(enroll_btn_text, key=f"enroll_login_{course.id}", use_container_width=True, type="primary"):
                    st.session_state.page = "login"
                    st.rerun()
                st.caption("Please log in to enrol")

    # ─── Related Courses ─────────────────────────────────────────────────
    if related:
        st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin:32px 0 16px;">{related_heading}</h3>', unsafe_allow_html=True)
        r_cols = st.columns(len(related), gap="medium")
        for i, rc in enumerate(related):
            with r_cols[i]:
                thumb_src = resolve_src(rc.image_url, width=300)
                thumb = f'<img src="{esc(thumb_src)}" style="width:100%;height:120px;object-fit:cover;border-radius:8px 8px 0 0;" alt="{esc(rc.title)}" onerror="this.style.display=\'none\'">' if thumb_src else ""
                st.markdown(html_block(f"""
                <div class="nmt-card" style="animation-delay:{i*0.08}s;">
                  {thumb}
                  <div style="padding:14px;">
                    <div style="font-size:11px;color:var(--blue-600);font-weight:700;text-transform:uppercase;">{esc(rc.category)}</div>
                    <div style="font-weight:700;font-size:14px;color:var(--ink-900);margin:4px 0 6px;">{esc(rc.title)}</div>
                    <div style="font-size:12px;color:var(--ink-500);">{esc(rc.duration)} · PKR {rc.fee:,.0f}</div>
                  </div>
                </div>
                """), unsafe_allow_html=True)
                if st.button("View", key=f"rel_{rc.id}", use_container_width=True):
                    st.session_state.selected_course_id = rc.id
                    st.rerun()
