import streamlit as st
import textwrap
import pandas as pd
import secrets
import string
import io
import json
import re
from datetime import datetime

from components.icons import icon
from database.connection import get_db_session
from database.models import (
    User, Course, Registration, Certificate, TutorApplication,
    ContactMessage, WebsiteSettings, Announcement, Instructor,
    EmailTemplate, RecruitmentDrive, JobOpening, NavItem,
    UserRole, RegistrationStatus, PaymentStatus
)
from sqlalchemy.orm import joinedload
from utils.email_service import (
    send_registration_approved, send_registration_rejected,
    send_tutor_application_approved, send_tutor_application_rejected,
    send_certificate_issued,
    send_email, _base_template, ADMIN_EMAIL
)
from utils.helpers import (
    update_setting, get_all_settings, html_block,
    get_all_payment_methods, update_payment_method, add_payment_method,
    delete_payment_method, flash_message,
)
from utils.cloudinary_service import upload_file, resolve_src, get_file_bytes, is_url
from pages.cms_admin import render_website_cms
from pages.home import _get_featured_courses, _get_active_announcements
import bcrypt


def _lines_from_json(value: str) -> str:
    """Reverse of the Add-Course form's json.dumps(list-of-lines) pattern —
    turns a stored JSON list back into one-item-per-line text for prefilling
    an edit textarea. Falls back to the raw stored value if it isn't valid
    JSON (e.g. legacy/hand-edited data), so nothing is silently dropped.
    """
    if not value:
        return ""
    try:
        items = json.loads(value)
        if isinstance(items, list):
            return "\n".join(str(i) for i in items)
    except (json.JSONDecodeError, TypeError):
        pass
    return value

_MENU_ITEMS = [
    ("grid", "Dashboard"), ("layout", "Website CMS"), ("book-open", "Courses"),
    ("users", "Instructors"), ("users", "Students"), ("file-text", "Registrations"),
    ("award", "Certificates"), ("briefcase", "Tutor Apps"), ("mail", "Messages"),
    ("dollar-sign", "Payment Methods"),
    ("bell", "Announcements"), ("mail", "Email Templates"),
    ("shield", "Roles & Perms"), ("settings", "Settings"),
]

# Which Admin Panel modules each role may see, matching the Permission Matrix
# shown under Roles & Perms → Permission Matrix. None = full access.
_ROLE_ALLOWED_MODULES = {
    "super_admin": None,
    "admin": {
        "Dashboard", "Website CMS", "Courses", "Instructors", "Students",
        "Registrations", "Certificates", "Tutor Apps", "Messages",
        "Payment Methods", "Announcements", "Email Templates", "Settings",
    },
    "instructor": {"Dashboard"},
    "content_manager": {
        "Dashboard", "Website CMS", "Courses", "Instructors",
        "Messages", "Announcements", "Email Templates",
    },
}


def _gen_cert_id():
    chars = string.ascii_uppercase + string.digits
    return "NMT-" + "".join(secrets.choice(chars) for _ in range(10))


def render_admin():
    user = st.session_state.get("user")
    if not user or user.get("role") not in ("admin", "super_admin", "instructor", "content_manager"):
        st.session_state.page = "login"
        st.rerun()
        return

    is_super = user.get("role") == "super_admin"
    role_label = {
        "super_admin": "Super Admin", "admin": "Admin",
        "instructor": "Instructor", "content_manager": "Content Manager",
    }.get(user.get("role"), "Admin")

    st.markdown(html_block(f"""
    <div class="nmt-app-header">
      <div class="nmt-app-header-inner">
        <div>
          <h1>{icon("settings", size=20, color="#fff")} Admin Panel</h1>
          <div class="sub">NextGen MechTech Academy</div>
        </div>
        <div class="meta">{icon("user", size=14, color="rgba(255,255,255,0.8)")} {user.get('full_name')}
          &nbsp;&middot;&nbsp; <span style="color:var(--amber-400);">{role_label}</span>
          &nbsp;&middot;&nbsp; {icon("calendar", size=14, color="rgba(255,255,255,0.8)")} {datetime.now().strftime("%B %d, %Y")}</div>
      </div>
    </div>
    """), unsafe_allow_html=True)

    allowed_modules = _ROLE_ALLOWED_MODULES.get(user.get("role"))
    visible_menu_items = (
        _MENU_ITEMS if allowed_modules is None
        else [(i, l) for i, l in _MENU_ITEMS if l in allowed_modules]
    )

    if "admin_tab" not in st.session_state:
        st.session_state.admin_tab = "Dashboard"
    if allowed_modules is not None and st.session_state.admin_tab not in allowed_modules:
        st.session_state.admin_tab = "Dashboard"

    st.markdown('<div class="nmt-admin-nav"><div class="nmt-admin-nav-inner" style="padding:10px 24px;">', unsafe_allow_html=True)
    menu_labels = [label for _, label in visible_menu_items]
    cols = st.columns(len(menu_labels) + 1)
    for i, (icon_name, label) in enumerate(visible_menu_items):
        with cols[i]:
            active = st.session_state.admin_tab == label
            if st.button(label, key=f"admin_nav_{label}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.admin_tab = label
                st.rerun()
    with cols[-1]:
        if st.button("Log Out", key="admin_logout", use_container_width=True):
            st.session_state.auth_token = None
            st.session_state.user = None
            st.session_state.page = "home"
            st.rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown('<div class="nmt-content bg-soft"><div class="nmt-shell">', unsafe_allow_html=True)

    tab = st.session_state.admin_tab
    if allowed_modules is not None and tab not in allowed_modules:
        tab = "Dashboard"
    dispatch = {
        "Dashboard": _admin_dashboard,
        "Website CMS": render_website_cms,
        "Courses": _admin_courses,
        "Instructors": _admin_instructors,
        "Students": _admin_students,
        "Registrations": _admin_registrations,
        "Certificates": _admin_certificates,
        "Tutor Apps": _admin_tutor_apps,
        "Messages": _admin_messages,
        "Payment Methods": _admin_payment_methods,
        "Announcements": _admin_announcements,
        "Email Templates": _admin_email_templates,
        "Roles & Perms": _admin_roles_permissions,
        "Settings": _admin_settings,
    }
    if user.get("role") == "instructor":
        dispatch["Dashboard"] = lambda: _instructor_dashboard(user)
    dispatch.get(tab, _admin_dashboard)()

    st.markdown("</div></div>", unsafe_allow_html=True)


# ─── Dashboard ───────────────────────────────────────────────────────────────
def _admin_dashboard():
    db = get_db_session()
    try:
        total_students = db.query(User).filter(User.role == UserRole.student).count()
        verified_students = db.query(User).filter(User.role == UserRole.student, User.is_verified == True).count()
        total_courses = db.query(Course).count()
        pending_regs = db.query(Registration).filter(Registration.registration_status == RegistrationStatus.pending).count()
        total_certs = db.query(Certificate).count()
        tutor_apps = db.query(TutorApplication).count()
        messages = db.query(ContactMessage).filter(ContactMessage.is_read == False).count()
        total_instructors = db.query(Instructor).filter(Instructor.is_visible == True).count()

        recent_regs = (
            db.query(Registration)
            .options(joinedload(Registration.student), joinedload(Registration.course))
            .order_by(Registration.created_at.desc())
            .limit(10).all()
        )
    finally:
        db.close()

    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{icon("bar-chart", size=17)} Overview</h3>', unsafe_allow_html=True)

    cols = st.columns(4)
    cards1 = [
        ("users", total_students, "Total Students", "var(--blue-50)", "var(--blue-600)"),
        ("check-circle", verified_students, "Verified Students", "var(--success-bg)", "var(--success-tx)"),
        ("book-open", total_courses, "Courses", "var(--amber-100)", "var(--amber-600)"),
        ("users", total_instructors, "Instructors", "var(--info-bg)", "var(--info-tx)"),
    ]
    for col, (ic, val, label, bg, fg) in zip(cols, cards1):
        with col:
            st.markdown(html_block(f"""
            <div class="nmt-stat-card">
              <div class="icon" style="background:{bg};color:{fg};">{icon(ic, size=16)}</div>
              <div class="val">{val}</div>
              <div class="lbl">{label}</div>
            </div>
            """), unsafe_allow_html=True)

    cols2 = st.columns(4)
    cards2 = [
        ("clock", pending_regs, "Pending Regs", "var(--warning-bg)", "var(--warning-tx)"),
        ("award", total_certs, "Certificates", "var(--success-bg)", "var(--success-tx)"),
        ("briefcase", tutor_apps, "Tutor Apps", "var(--info-bg)", "var(--info-tx)"),
        ("mail", messages, "Unread Msgs", "var(--danger-bg)", "var(--danger-tx)"),
    ]
    for col, (ic, val, label, bg, fg) in zip(cols2, cards2):
        with col:
            st.markdown(html_block(f"""
            <div class="nmt-stat-card">
              <div class="icon" style="background:{bg};color:{fg};">{icon(ic, size=16)}</div>
              <div class="val">{val}</div>
              <div class="lbl">{label}</div>
            </div>
            """), unsafe_allow_html=True)

    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:16px;font-weight:700;color:var(--ink-900);margin:28px 0 14px;">{icon("file-text", size=16)} Recent Registrations</h3>', unsafe_allow_html=True)
    if recent_regs:
        data = []
        for r in recent_regs:
            data.append({
                "Student": r.student.full_name,
                "Course": r.course.title,
                "Date": r.created_at.strftime("%b %d, %Y"),
                "Status": r.registration_status.value.title(),
                "Payment": r.payment_status.value.title(),
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    else:
        st.info("No registrations yet.")


# ─── Instructor Dashboard (own courses only) ─────────────────────────────────
def _instructor_dashboard(user):
    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:6px;">{icon("grid", size=17)} My Courses</h3>', unsafe_allow_html=True)
    st.markdown('<p style="color:var(--ink-500);font-size:13px;margin-bottom:18px;">View your assigned course(s), see students registered for them, and update course content. New courses you submit are reviewed by the Super Admin before going live.</p>', unsafe_allow_html=True)

    db = get_db_session()
    try:
        my_courses = (db.query(Course)
                      .filter(Course.assigned_instructor_user_id == user["id"])
                      .order_by(Course.created_at.desc())
                      .all())

        # One query for every assigned course's registrations instead of
        # one query per course (was an N+1 pattern) — grouped back out by
        # course_id below, preserving the same per-course ordering.
        course_ids = [c.id for c in my_courses]
        regs_by_course = {}
        if course_ids:
            all_regs = (db.query(Registration)
                        .options(joinedload(Registration.student))
                        .filter(Registration.course_id.in_(course_ids))
                        .order_by(Registration.created_at.desc())
                        .all())
            for r in all_regs:
                regs_by_course.setdefault(r.course_id, []).append(r)

        # Detach-safe plain dicts so we can close the session before rendering
        courses_data = []
        for c in my_courses:
            regs = regs_by_course.get(c.id, [])
            courses_data.append({
                "id": c.id, "title": c.title, "description": c.description,
                "full_description": c.full_description or "", "category": c.category,
                "duration": c.duration, "level": c.level, "fee": c.fee,
                "image_url": c.image_url or "", "banner_url": c.banner_url or "",
                "is_published": c.is_published, "pending_review": c.pending_review,
                "review_note": c.review_note or "",
                "certificate_available": c.certificate_available,
                "enrollment_open": c.enrollment_open,
                "registrations": [
                    {
                        "student_name": r.student.full_name if r.student else "—",
                        "student_email": r.student.email if r.student else "—",
                        "phone": r.phone, "status": r.registration_status.value.title(),
                        "payment_status": r.payment_status.value.title(),
                        "created_at": r.created_at.strftime("%b %d, %Y"),
                    } for r in regs
                ],
            })
    finally:
        db.close()

    pending_courses = [c for c in courses_data if c["pending_review"]]
    live_courses = [c for c in courses_data if not c["pending_review"]]

    if pending_courses:
        st.markdown(f'<h4 style="font-size:15px;font-weight:700;color:var(--ink-900);margin:10px 0 10px;">{icon("clock", size=15)} Awaiting Super Admin Approval</h4>', unsafe_allow_html=True)
        for c in pending_courses:
            note_html = f'<div style="margin-top:8px;color:var(--danger-tx);font-size:12.5px;"><strong>Reviewer note:</strong> {c["review_note"]}</div>' if c["review_note"] else ""
            st.markdown(html_block(f"""
            <div style="background:var(--amber-100);border-radius:8px;padding:14px 16px;margin-bottom:12px;">
              <div style="font-weight:700;color:var(--ink-900);">{c['title']}</div>
              <div style="font-size:12.5px;color:var(--ink-500);margin-top:4px;">{c['description']}</div>
              <div style="margin-top:8px;font-size:12px;color:var(--amber-600);font-weight:600;">Pending review — not yet visible to students.</div>
              {note_html}
            </div>
            """), unsafe_allow_html=True)

    if not live_courses and not pending_courses:
        st.info("No courses are assigned to you yet. Ask the Super Admin to assign you to a course, or submit a new course below for approval.")
    elif live_courses:
        st.markdown(f'<h4 style="font-size:15px;font-weight:700;color:var(--ink-900);margin:18px 0 10px;">{icon("book-open", size=15)} My Assigned Courses</h4>', unsafe_allow_html=True)
        for c in live_courses:
            pub_badge = '<span class="nmt-badge nmt-badge-approved">Published</span>' if c["is_published"] else '<span class="nmt-badge nmt-badge-neutral">Draft</span>'
            with st.expander(f"{c['title']} — PKR {c['fee']:,.0f}"):
                st.markdown(pub_badge, unsafe_allow_html=True)

                st.markdown(f'<div style="font-weight:700;font-size:13px;margin:12px 0 6px;">{icon("edit", size=13)} Edit Course Details</div>', unsafe_allow_html=True)
                st.caption(f"Title: **{c['title']}** (only the Super Admin can rename a course)")
                with st.form(f"instr_edit_course_{c['id']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        e_desc = st.text_area("Short Description", value=c["description"], height=80, key=f"instr_desc_{c['id']}")
                        e_full = st.text_area("Full Description", value=c["full_description"], height=100, key=f"instr_full_{c['id']}")
                        e_duration = st.text_input("Duration", value=c["duration"], key=f"instr_dur_{c['id']}")
                    with col2:
                        e_image = st.text_input("Thumbnail/Picture URL", value=c["image_url"], key=f"instr_img_{c['id']}")
                        e_banner = st.text_input("Banner URL", value=c["banner_url"], key=f"instr_banner_{c['id']}")
                        e_fee = st.number_input("Fee (PKR)", value=float(c["fee"]), step=100.0, key=f"instr_fee_{c['id']}")
                    col3, col4 = st.columns(2)
                    with col3:
                        e_cert = st.checkbox("Certificate Available", value=c["certificate_available"], key=f"instr_cert_{c['id']}")
                    with col4:
                        e_enroll = st.checkbox("Enrolment Open", value=c["enrollment_open"], key=f"instr_enroll_{c['id']}")

                    if st.form_submit_button("Save Changes", type="primary"):
                        db = get_db_session()
                        try:
                            course_row = db.query(Course).filter(Course.id == c["id"]).first()
                            if course_row:
                                course_row.description = e_desc
                                course_row.full_description = e_full or None
                                course_row.duration = e_duration
                                course_row.image_url = e_image or None
                                course_row.banner_url = e_banner or None
                                course_row.fee = e_fee
                                course_row.certificate_available = e_cert
                                course_row.enrollment_open = e_enroll
                                db.commit()
                                _get_featured_courses.clear()
                                flash_message("Course updated.")
                                st.rerun()
                        except Exception as ex:
                            db.rollback()
                            st.error(str(ex))
                        finally:
                            db.close()

                st.markdown(f'<div style="font-weight:700;font-size:13px;margin:18px 0 6px;">{icon("users", size=13)} Registered Students</div>', unsafe_allow_html=True)
                if c["registrations"]:
                    st.dataframe(pd.DataFrame([
                        {
                            "Student": r["student_name"], "Email": r["student_email"],
                            "Phone": r["phone"], "Registered": r["created_at"],
                            "Status": r["status"], "Payment": r["payment_status"],
                        } for r in c["registrations"]
                    ]), use_container_width=True, hide_index=True)
                else:
                    st.info("No students registered for this course yet.")

    st.markdown("<hr style='margin:24px 0;border-color:var(--line);'>", unsafe_allow_html=True)
    st.markdown(f'<div style="font-weight:700;font-size:14px;color:var(--ink-900);margin-bottom:10px;">{icon("plus-circle", size=15)} Submit a New Course</div>', unsafe_allow_html=True)
    st.caption("New courses are sent to the Super Admin for approval and won't be visible to students until approved.")

    with st.form("instr_add_course_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n_title = st.text_input("Title *")
            n_category = st.selectbox("Category *", _CATEGORY_CHOICES)
            n_duration = st.text_input("Duration *", placeholder="8 Weeks")
        with col2:
            n_level = st.selectbox("Level *", _LEVEL_CHOICES)
            n_fee = st.number_input("Fee (PKR) *", min_value=0.0, value=4999.0, step=100.0)
            n_image = st.text_input("Thumbnail URL")

        n_desc = st.text_area("Short Description *", height=80)
        n_full = st.text_area("Full Description", height=100)

        submitted_new = st.form_submit_button("Submit for Approval", type="primary")
        if submitted_new:
            if not n_title or not n_desc or not n_duration:
                st.error("Title, description, and duration are required.")
            else:
                db = get_db_session()
                try:
                    new_course = Course(
                        title=n_title, description=n_desc,
                        full_description=n_full or None,
                        category=n_category, duration=n_duration, level=n_level, fee=n_fee,
                        image_url=n_image or None,
                        assigned_instructor_user_id=user["id"],
                        submitted_by_user_id=user["id"],
                        is_published=False, pending_review=True,
                    )
                    db.add(new_course)
                    db.commit()
                    flash_message(f"'{n_title}' submitted for Super Admin approval.")
                    st.rerun()
                except Exception as e:
                    db.rollback()
                    st.error(str(e))
                finally:
                    db.close()


# ─── Instructors ─────────────────────────────────────────────────────────────
def _admin_instructors():
    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{icon("users", size=17)} Manage Instructors</h3>', unsafe_allow_html=True)

    tab_list, tab_add = st.tabs(["All Instructors", "Add Instructor"])

    with tab_add:
        with st.form("add_instructor_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *", placeholder="Engr. Ahmed Raza")
                designation = st.text_input("Designation *", placeholder="Python & ML Instructor")
                qualifications = st.text_input("Qualifications", placeholder="MS Computer Science, NUST")
                experience = st.text_input("Experience", placeholder="5+ Years")
            with col2:
                linkedin_url = st.text_input("LinkedIn URL")
                github_url = st.text_input("GitHub URL")
                display_order = st.number_input("Display Order", min_value=0, value=0)
                is_visible = st.checkbox("Visible on website", value=True)

            bio = st.text_area("Bio", placeholder="Short instructor biography...", height=100)
            photo_file = st.file_uploader("Photo (JPG/PNG)", type=["jpg", "jpeg", "png"])

            if st.form_submit_button("Add Instructor", type="primary"):
                if not name or not designation:
                    st.error("Name and designation are required.")
                else:
                    photo_url = None
                    if photo_file:
                        try:
                            photo_url = upload_file(photo_file, folder="nextgen_mechtech/instructors")
                        except Exception as e:
                            st.error(f"Photo upload failed: {e}")
                            return
                    db = get_db_session()
                    try:
                        instr = Instructor(
                            name=name, designation=designation,
                            qualifications=qualifications, experience=experience,
                            bio=bio, photo_data=photo_url,
                            linkedin_url=linkedin_url, github_url=github_url,
                            display_order=display_order, is_visible=is_visible
                        )
                        db.add(instr)
                        db.commit()
                        flash_message(f"Instructor '{name}' added successfully.")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(str(e))
                    finally:
                        db.close()

    with tab_list:
        db = get_db_session()
        try:
            instructors = db.query(Instructor).order_by(Instructor.display_order).all()
        finally:
            db.close()

        if not instructors:
            st.info("No instructors found. Add one using the 'Add Instructor' tab.")
            return

        for instr in instructors:
            status_badge = '<span class="nmt-badge nmt-badge-approved">Visible</span>' if instr.is_visible else '<span class="nmt-badge nmt-badge-neutral">Hidden</span>'
            with st.expander(f"{instr.name} — {instr.designation}"):
                st.markdown(status_badge, unsafe_allow_html=True)
                col1, col2 = st.columns([2, 1])
                with col1:
                    with st.form(f"edit_instr_{instr.id}"):
                        e_name = st.text_input("Name", value=instr.name)
                        e_desig = st.text_input("Designation", value=instr.designation)
                        e_qual = st.text_input("Qualifications", value=instr.qualifications or "")
                        e_exp = st.text_input("Experience", value=instr.experience or "")
                        e_bio = st.text_area("Bio", value=instr.bio or "", height=80)
                        e_linkedin = st.text_input("LinkedIn URL", value=instr.linkedin_url or "")
                        e_order = st.number_input("Display Order", value=instr.display_order or 0)
                        e_visible = st.checkbox("Visible", value=instr.is_visible)
                        e_photo = st.file_uploader("Replace Photo", type=["jpg", "jpeg", "png"], key=f"photo_{instr.id}")
                        if st.form_submit_button("Save Changes", type="primary"):
                            e_photo_url = None
                            if e_photo:
                                try:
                                    e_photo_url = upload_file(e_photo, folder="nextgen_mechtech/instructors")
                                except Exception as e:
                                    st.error(f"Photo upload failed: {e}")
                                    st.stop()
                            db = get_db_session()
                            try:
                                i = db.query(Instructor).filter(Instructor.id == instr.id).first()
                                i.name = e_name
                                i.designation = e_desig
                                i.qualifications = e_qual
                                i.experience = e_exp
                                i.bio = e_bio
                                i.linkedin_url = e_linkedin
                                i.display_order = e_order
                                i.is_visible = e_visible
                                if e_photo_url:
                                    i.photo_data = e_photo_url
                                db.commit()
                                flash_message("Saved.")
                                st.rerun()
                            except Exception as ex:
                                db.rollback()
                                st.error(str(ex))
                            finally:
                                db.close()
                with col2:
                    if instr.photo_data:
                        st.markdown(f'<img src="{resolve_src(instr.photo_data)}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;">', unsafe_allow_html=True)

                    toggle_label = "Hide" if instr.is_visible else "Show"
                    if st.button(toggle_label, key=f"toggle_instr_{instr.id}", use_container_width=True):
                        db = get_db_session()
                        try:
                            i = db.query(Instructor).filter(Instructor.id == instr.id).first()
                            i.is_visible = not i.is_visible
                            db.commit()
                            st.rerun()
                        finally:
                            db.close()

                    if st.button("Delete", key=f"del_instr_{instr.id}", use_container_width=True):
                        db = get_db_session()
                        try:
                            i = db.query(Instructor).filter(Instructor.id == instr.id).first()
                            db.delete(i)
                            db.commit()
                            st.rerun()
                        finally:
                            db.close()


# ─── Courses ─────────────────────────────────────────────────────────────────
_CATEGORY_CHOICES = ["Programming", "Engineering Tools", "Electronics", "Artificial Intelligence", "Creative Arts", "Productivity"]
_LEVEL_CHOICES = ["Beginner", "Intermediate", "Advanced", "Beginner to Intermediate", "Intermediate to Advanced", "Beginner to Advanced"]


def _admin_courses():
    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{icon("book-open", size=17)} Manage Courses</h3>', unsafe_allow_html=True)

    current_user = st.session_state.get("user")
    is_super = bool(current_user and current_user.get("role") == "super_admin")

    if is_super:
        tab_list, tab_add, tab_pending = st.tabs(["All Courses", "Add Course", "Pending Approvals"])
    else:
        tab_list, tab_add = st.tabs(["All Courses", "Add Course"])
        tab_pending = None

    # Streamlit's st.tabs() executes every tab's body on every rerun of this
    # function (only the frontend hides the inactive tab's DOM) — so the
    # "always executed" reads for all three tabs below run together no
    # matter which tab is visually selected. They're fetched once, up front,
    # in a single shared session instead of one session per tab.
    #
    # instructor_accounts is also fetched once here instead of twice
    # (previously the Add-Course tab and the All-Courses tab each ran the
    # identical `User.role == instructor` query).
    db = get_db_session()
    try:
        instructors = db.query(Instructor).filter(Instructor.is_visible == True).order_by(Instructor.display_order).all()
        instructor_accounts = db.query(User).filter(User.role == UserRole.instructor).order_by(User.full_name).all()
        courses = db.query(Course).order_by(Course.created_at.desc()).all()

        pending_courses = []
        pending_data = []
        if tab_pending is not None:
            pending_courses = (db.query(Course)
                                .filter(Course.pending_review == True)
                                .order_by(Course.created_at.desc())
                                .all())
            # Bulk-fetch every submitter in one query instead of one query
            # per pending course (was an N+1 pattern).
            submitter_ids = [c.submitted_by_user_id for c in pending_courses if c.submitted_by_user_id]
            submitters_by_id = {}
            if submitter_ids:
                submitter_rows = db.query(User).filter(User.id.in_(submitter_ids)).all()
                submitters_by_id = {u.id: u for u in submitter_rows}
            for c in pending_courses:
                submitter = submitters_by_id.get(c.submitted_by_user_id)
                pending_data.append({
                    "id": c.id, "title": c.title, "description": c.description,
                    "duration": c.duration, "level": c.level, "fee": c.fee,
                    "category": c.category,
                    "submitter_name": submitter.full_name if submitter else "Unknown",
                    "submitter_email": submitter.email if submitter else "—",
                })
    finally:
        db.close()

    instructor_accounts_edit = instructor_accounts if is_super else []

    with tab_add:
        instr_opts = {"None": None}
        instr_opts.update({i.name: i.id for i in instructors})

        if is_super:
            acct_opts = {"Unassigned": None}
            acct_opts.update({f"{a.full_name} ({a.email})": a.id for a in instructor_accounts})

        with st.form("add_course_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Title *")
                category = st.selectbox("Category *", _CATEGORY_CHOICES)
                duration = st.text_input("Duration *", placeholder="8 Weeks")
                fee = st.number_input("Fee (PKR) *", min_value=0.0, value=4999.0, step=100.0)
            with col2:
                level = st.selectbox("Level *", _LEVEL_CHOICES)
                image_url = st.text_input("Thumbnail URL")
                selected_instr = st.selectbox("Instructor", list(instr_opts.keys()))
                is_featured = st.checkbox("Featured Course")

            description = st.text_area("Short Description *", height=80)
            full_description = st.text_area("Full Description", height=120)
            what_you_learn = st.text_area("What You'll Learn (one per line)", height=80)
            prerequisites = st.text_input("Prerequisites")

            st.markdown("**Additional Details**")
            c1, c2 = st.columns(2)
            with c1:
                language = st.text_input("Language", value="Urdu / English")
                skills_learned = st.text_area("Skills Learned (one per line)", height=60,
                    help="Will appear as tags on the course detail page")
                software_used = st.text_area("Software Used (one per line)", height=60)
            with c2:
                projects_included = st.text_area("Projects Included (one per line)", height=60)
                topics_covered = st.text_area("Topics Covered (one per line)", height=60)

            syllabus_json = st.text_area(
                "Syllabus JSON (list of {module, topics:[]} or plain list of strings)",
                height=100,
                help='e.g. [{"module":"Week 1","topics":["Intro","Setup"]},{"module":"Week 2","topics":["Variables"]}]'
            )

            cert_avail = st.checkbox("Certificate Available", value=True)
            is_published = st.checkbox("Published", value=True)
            enrollment_open = st.checkbox("Enrolment Open", value=True)

            assigned_acct_id = None
            if is_super:
                selected_acct = st.selectbox(
                    "Assigned Instructor (login account — controls who manages this course from their Dashboard)",
                    list(acct_opts.keys())
                )
                assigned_acct_id = acct_opts.get(selected_acct)

            if st.form_submit_button("Add Course", type="primary"):
                if not title or not description or not duration:
                    st.error("Title, description, and duration are required.")
                else:
                    wyl = json.dumps([l.strip() for l in what_you_learn.split("\n") if l.strip()]) if what_you_learn else None
                    skl = json.dumps([l.strip() for l in skills_learned.split("\n") if l.strip()]) if skills_learned else None
                    sfw = json.dumps([l.strip() for l in software_used.split("\n") if l.strip()]) if software_used else None
                    prj = json.dumps([l.strip() for l in projects_included.split("\n") if l.strip()]) if projects_included else None
                    tpc = json.dumps([l.strip() for l in topics_covered.split("\n") if l.strip()]) if topics_covered else None
                    syl = syllabus_json.strip() if syllabus_json.strip() else None
                    db = get_db_session()
                    try:
                        course = Course(
                            title=title, description=description,
                            full_description=full_description or None,
                            what_you_learn=wyl, prerequisites=prerequisites or None,
                            skills_learned=skl, software_used=sfw,
                            projects_included=prj, topics_covered=tpc,
                            syllabus=syl, language=language or "Urdu / English",
                            category=category, duration=duration, level=level, fee=fee,
                            image_url=image_url or None,
                            instructor_id=instr_opts.get(selected_instr),
                            assigned_instructor_user_id=assigned_acct_id,
                            is_published=is_published, is_featured=is_featured,
                            certificate_available=cert_avail,
                            enrollment_open=enrollment_open,
                        )
                        db.add(course)
                        db.commit()
                        _get_featured_courses.clear()
                        flash_message(f"Course '{title}' added.")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(str(e))
                    finally:
                        db.close()

    with tab_list:
        if not courses:
            st.info("No courses yet.")

        acct_opts_edit = {"Unassigned": None}
        acct_opts_edit.update({f"{a.full_name} ({a.email})": a.id for a in instructor_accounts_edit})
        acct_id_to_label = {v: k for k, v in acct_opts_edit.items()}

        for course in courses:
            pub_badge = '<span class="nmt-badge nmt-badge-approved">Published</span>' if course.is_published else '<span class="nmt-badge nmt-badge-neutral">Draft</span>'
            feat_badge = '<span class="nmt-badge nmt-badge-info">Featured</span>' if course.is_featured else ""
            with st.expander(f"{course.title} — PKR {course.fee:,.0f}"):
                st.markdown(f"{pub_badge} {feat_badge}", unsafe_allow_html=True)
                col1, col2 = st.columns([3, 1])
                with col1:
                    with st.form(f"edit_course_{course.id}"):
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            e_title = st.text_input("Title", value=course.title)
                            e_cat = st.selectbox("Category", _CATEGORY_CHOICES, index=_CATEGORY_CHOICES.index(course.category) if course.category in _CATEGORY_CHOICES else 0)
                            e_dur = st.text_input("Duration", value=course.duration)
                            e_fee = st.number_input("Fee", value=float(course.fee), step=100.0)
                        with ec2:
                            e_level = st.selectbox("Level", _LEVEL_CHOICES, index=_LEVEL_CHOICES.index(course.level) if course.level in _LEVEL_CHOICES else 0)
                            e_img = st.text_input("Image URL", value=course.image_url or "")
                            e_pub = st.checkbox("Published", value=course.is_published)
                            e_feat = st.checkbox("Featured", value=course.is_featured)
                        e_desc = st.text_area("Description", value=course.description, height=80)
                        e_full_desc = st.text_area("Full Description", value=course.full_description or "", height=120)
                        e_wyl = st.text_area("What You'll Learn (one per line)", value=_lines_from_json(course.what_you_learn), height=80)
                        e_prereq = st.text_input("Prerequisites", value=course.prerequisites or "")

                        st.markdown("**Additional Details**")
                        ec3, ec4 = st.columns(2)
                        with ec3:
                            e_lang = st.text_input("Language", value=course.language or "Urdu / English", key=f"e_lang_{course.id}")
                            e_skills = st.text_area("Skills Learned (one per line)", value=_lines_from_json(course.skills_learned), height=60, key=f"e_skills_{course.id}")
                            e_software = st.text_area("Software Used (one per line)", value=_lines_from_json(course.software_used), height=60, key=f"e_software_{course.id}")
                        with ec4:
                            e_projects = st.text_area("Projects Included (one per line)", value=_lines_from_json(course.projects_included), height=60, key=f"e_projects_{course.id}")
                            e_topics = st.text_area("Topics Covered (one per line)", value=_lines_from_json(course.topics_covered), height=60, key=f"e_topics_{course.id}")

                        e_syllabus = st.text_area(
                            "Syllabus JSON (list of {module, topics:[]} or plain list of strings)",
                            value=course.syllabus or "", height=100, key=f"e_syllabus_{course.id}"
                        )

                        e_cert = st.checkbox("Certificate Available", value=course.certificate_available)
                        e_enroll = st.checkbox("Enrolment Open", value=course.enrollment_open, key=f"e_enroll_{course.id}")

                        e_assigned_label = None
                        if is_super:
                            current_label = acct_id_to_label.get(course.assigned_instructor_user_id, "Unassigned")
                            opts = list(acct_opts_edit.keys())
                            e_assigned_label = st.selectbox(
                                "Assigned Instructor (login account — controls who manages this course from their Dashboard)",
                                opts,
                                index=opts.index(current_label) if current_label in opts else 0,
                                key=f"assign_instr_{course.id}"
                            )

                        if st.form_submit_button("Save", type="primary"):
                            e_wyl_json = json.dumps([l.strip() for l in e_wyl.split("\n") if l.strip()]) if e_wyl else None
                            e_skills_json = json.dumps([l.strip() for l in e_skills.split("\n") if l.strip()]) if e_skills else None
                            e_software_json = json.dumps([l.strip() for l in e_software.split("\n") if l.strip()]) if e_software else None
                            e_projects_json = json.dumps([l.strip() for l in e_projects.split("\n") if l.strip()]) if e_projects else None
                            e_topics_json = json.dumps([l.strip() for l in e_topics.split("\n") if l.strip()]) if e_topics else None
                            e_syllabus_val = e_syllabus.strip() if e_syllabus.strip() else None
                            db = get_db_session()
                            try:
                                c = db.query(Course).filter(Course.id == course.id).first()
                                c.title = e_title
                                c.category = e_cat
                                c.duration = e_dur
                                c.fee = e_fee
                                c.level = e_level
                                c.image_url = e_img or None
                                c.is_published = e_pub
                                c.is_featured = e_feat
                                c.description = e_desc
                                c.full_description = e_full_desc or None
                                c.what_you_learn = e_wyl_json
                                c.prerequisites = e_prereq or None
                                c.language = e_lang or "Urdu / English"
                                c.skills_learned = e_skills_json
                                c.software_used = e_software_json
                                c.projects_included = e_projects_json
                                c.topics_covered = e_topics_json
                                c.syllabus = e_syllabus_val
                                c.certificate_available = e_cert
                                c.enrollment_open = e_enroll
                                if is_super:
                                    c.assigned_instructor_user_id = acct_opts_edit.get(e_assigned_label)
                                db.commit()
                                _get_featured_courses.clear()
                                flash_message("Saved.")
                                st.rerun()
                            except Exception as ex:
                                db.rollback()
                                st.error(str(ex))
                            finally:
                                db.close()
                with col2:
                    if st.button("Delete", key=f"del_c_{course.id}", use_container_width=True):
                        db = get_db_session()
                        try:
                            c = db.query(Course).filter(Course.id == course.id).first()
                            db.delete(c)
                            db.commit()
                            _get_featured_courses.clear()
                            st.rerun()
                        finally:
                            db.close()

    if tab_pending is not None:
        with tab_pending:
            st.markdown('<p style="color:var(--ink-500);font-size:13px;margin-bottom:16px;">New courses submitted by instructors wait here until approved. Approving publishes the course immediately; rejecting keeps it hidden and can include a note back to the instructor.</p>', unsafe_allow_html=True)

            if not pending_data:
                st.info("No pending course submissions.")
            else:
                for c in pending_data:
                    with st.expander(f"{c['title']} — submitted by {c['submitter_name']}"):
                        st.markdown(f"""
                        **Category:** {c['category']}  &nbsp;|&nbsp; **Duration:** {c['duration']}  &nbsp;|&nbsp; **Level:** {c['level']}  &nbsp;|&nbsp; **Fee:** PKR {c['fee']:,.0f}

                        **Description:** {c['description']}

                        **Submitted by:** {c['submitter_name']} ({c['submitter_email']})
                        """)
                        review_note = st.text_area("Note to instructor (optional, shown on rejection)", key=f"pend_note_{c['id']}", height=60)
                        col_a, col_r = st.columns(2)
                        with col_a:
                            if st.button("Approve & Publish", key=f"pend_approve_{c['id']}", type="primary", use_container_width=True):
                                db = get_db_session()
                                try:
                                    row = db.query(Course).filter(Course.id == c["id"]).first()
                                    if row:
                                        row.is_published = True
                                        row.pending_review = False
                                        row.review_note = None
                                        db.commit()
                                        _get_featured_courses.clear()
                                    flash_message(f"'{c['title']}' approved and published.")
                                    st.rerun()
                                finally:
                                    db.close()
                        with col_r:
                            if st.button("Reject", key=f"pend_reject_{c['id']}", use_container_width=True):
                                db = get_db_session()
                                try:
                                    row = db.query(Course).filter(Course.id == c["id"]).first()
                                    if row:
                                        row.pending_review = False
                                        row.is_published = False
                                        row.review_note = review_note.strip() or "Not approved at this time."
                                        db.commit()
                                        _get_featured_courses.clear()
                                    flash_message(f"'{c['title']}' rejected.", kind="warning")
                                    st.rerun()
                                finally:
                                    db.close()


# ─── Students ────────────────────────────────────────────────────────────────
def _admin_students():
    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{icon("users", size=17)} Manage Students</h3>', unsafe_allow_html=True)

    search = st.text_input("Search students", placeholder="Name or email...")

    db = get_db_session()
    try:
        query = db.query(User).filter(User.role == UserRole.student)
        if search:
            q = f"%{search}%"
            query = query.filter((User.full_name.ilike(q)) | (User.email.ilike(q)))
        students = query.order_by(User.created_at.desc()).all()
    finally:
        db.close()

    if not students:
        st.info("No students found.")
        return

    data = []
    for s in students:
        data.append({
            "ID": s.id,
            "Name": s.full_name,
            "Email": s.email,
            "Phone": s.phone or "—",
            "Verified": "✓" if s.is_verified else "✗",
            "Active": "✓" if s.is_active else "Suspended",
            "Joined": s.created_at.strftime("%b %d, %Y"),
        })
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("**Edit Student**")
    student_opts = {f"{s.full_name} ({s.email})": s.id for s in students}
    selected = st.selectbox("Select Student", list(student_opts.keys()))

    if selected:
        sid = student_opts[selected]
        # Already loaded in `students` above (same session's full list) —
        # no need for a second round trip to fetch the same row again.
        s = next((x for x in students if x.id == sid), None)
        if s:
            with st.form(f"edit_student_{sid}"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_name = st.text_input("Full Name", value=s.full_name)
                    e_email = st.text_input("Email", value=s.email)
                    e_phone = st.text_input("Phone", value=s.phone or "")
                    e_city = st.text_input("City", value=s.city or "")
                with ec2:
                    e_uni = st.text_input("University", value=s.university or "")
                    e_dept = st.text_input("Department", value=s.department or "")
                    e_verified = st.checkbox("Email Verified", value=s.is_verified)
                    e_active = st.checkbox("Account Active", value=s.is_active)
                new_pw = st.text_input("Reset Password (leave blank to keep)", type="password")
                col_save, col_del = st.columns(2)
                with col_save:
                    save_clicked = st.form_submit_button("Save Changes", type="primary")
                with col_del:
                    delete_clicked = st.form_submit_button("Delete Student")
                if save_clicked:
                    db2 = get_db_session()
                    try:
                        student = db2.query(User).filter(User.id == sid).first()
                        student.full_name = e_name
                        student.email = e_email
                        student.phone = e_phone or None
                        student.city = e_city or None
                        student.university = e_uni or None
                        student.department = e_dept or None
                        student.is_verified = e_verified
                        student.is_active = e_active
                        if new_pw:
                            student.password_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
                        db2.commit()
                        flash_message("Student updated.")
                        st.rerun()
                    except Exception as ex:
                        db2.rollback()
                        st.error(str(ex))
                    finally:
                        db2.close()
                if delete_clicked:
                    db3 = get_db_session()
                    try:
                        db3.query(Certificate).filter(Certificate.student_id == sid).delete()
                        db3.query(Registration).filter(Registration.student_id == sid).delete()
                        db3.query(User).filter(User.id == sid).delete()
                        db3.commit()
                        flash_message("Student deleted.", kind="warning")
                        st.rerun()
                    except Exception as ex:
                        db3.rollback()
                        st.error(str(ex))
                    finally:
                        db3.close()


# ─── Registrations ───────────────────────────────────────────────────────────
def _admin_registrations():
    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{icon("file-text", size=17)} Manage Registrations</h3>', unsafe_allow_html=True)

    status_filter = st.selectbox("Filter by status", ["All", "Pending", "Approved", "Rejected", "Info Requested"])

    db = get_db_session()
    try:
        query = db.query(Registration).options(joinedload(Registration.student), joinedload(Registration.course))
        if status_filter == "Pending":
            query = query.filter(Registration.registration_status == RegistrationStatus.pending)
        elif status_filter == "Approved":
            query = query.filter(Registration.registration_status == RegistrationStatus.approved)
        elif status_filter == "Rejected":
            query = query.filter(Registration.registration_status == RegistrationStatus.rejected)
        elif status_filter == "Info Requested":
            query = query.filter(Registration.registration_status == RegistrationStatus.info_requested)
        regs = query.order_by(Registration.created_at.desc()).all()
    finally:
        db.close()

    if not regs:
        st.info("No registrations found.")
        return

    for reg in regs:
        status_color = {
            "pending": "nmt-badge-pending", "approved": "nmt-badge-approved",
            "rejected": "nmt-badge-rejected", "info_requested": "nmt-badge-info"
        }.get(reg.registration_status.value, "nmt-badge-neutral")

        with st.expander(f"{reg.student.full_name} → {reg.course.title} ({reg.created_at.strftime('%b %d, %Y')})"):
            st.markdown(f'<span class="nmt-badge {status_color}">{reg.registration_status.value.replace("_", " ").title()}</span>', unsafe_allow_html=True)
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(html_block(f"""
                **Student:** {reg.student.full_name} ({reg.student.email})
                **Course:** {reg.course.title}
                **Phone:** {reg.phone}
                **Payment Method:** {reg.payment_method}
                **Notes:** {reg.notes or 'N/A'}
                """))
                if reg.payment_screenshot:
                    try:
                        # Cloudinary URLs are handed to the browser directly
                        # (same as every other image on the site) instead of
                        # being downloaded through the Python server first —
                        # that server-side download was a real bottleneck:
                        # every registration with a screenshot triggered a
                        # synchronous HTTP fetch to Cloudinary on every render
                        # of this tab, regardless of whether it was expanded.
                        # Legacy base64-stored screenshots (pre-Cloudinary)
                        # still decode locally, no network call either way.
                        if is_url(reg.payment_screenshot):
                            st.image(resolve_src(reg.payment_screenshot, width=400), caption="Payment Screenshot", width=300)
                        else:
                            img_bytes = get_file_bytes(reg.payment_screenshot)
                            st.image(img_bytes, caption="Payment Screenshot", width=300)
                    except Exception:
                        pass
            with col2:
                admin_note = st.text_area("Admin Note", key=f"note_{reg.id}", value=reg.admin_note or "", height=70)
                if st.button("Approve", key=f"approve_{reg.id}", use_container_width=True, type="primary"):
                    _update_registration(reg.id, RegistrationStatus.approved, PaymentStatus.verified, admin_note)
                    send_registration_approved(reg.student.full_name, reg.student.email, reg.course.title)
                    flash_message("Approved and notified.")
                    st.rerun()
                if st.button("Reject", key=f"reject_{reg.id}", use_container_width=True):
                    _update_registration(reg.id, RegistrationStatus.rejected, PaymentStatus.rejected, admin_note)
                    send_registration_rejected(reg.student.full_name, reg.student.email, reg.course.title, admin_note)
                    flash_message("Rejected.", kind="warning")
                    st.rerun()
                if st.button("Request Info", key=f"info_{reg.id}", use_container_width=True):
                    _update_registration(reg.id, RegistrationStatus.info_requested, reg.payment_status, admin_note)
                    flash_message("Info requested.", kind="info")
                    st.rerun()


def _update_registration(reg_id, status, pay_status, note=None):
    db = get_db_session()
    try:
        r = db.query(Registration).filter(Registration.id == reg_id).first()
        if r:
            r.registration_status = status
            r.payment_status = pay_status
            if note:
                r.admin_note = note
            db.commit()
    finally:
        db.close()


# ─── Certificates ─────────────────────────────────────────────────────────────
def _admin_certificates():
    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{icon("award", size=17)} Certificate Management</h3>', unsafe_allow_html=True)

    tab_issue, tab_list = st.tabs(["Issue Certificate", "All Certificates"])

    # Both tabs' unconditional reads run every time this function renders
    # (Streamlit executes every st.tabs() body every rerun), so they share
    # one session instead of opening one each.
    db = get_db_session()
    try:
        students = db.query(User).filter(User.role == UserRole.student, User.is_active == True).all()
        courses = db.query(Course).filter(Course.is_published == True).all()
        instructors = db.query(Instructor).filter(Instructor.is_visible == True).all()
        certs = (db.query(Certificate)
                 .options(joinedload(Certificate.student), joinedload(Certificate.course))
                 .order_by(Certificate.issued_at.desc())
                 .all())
    finally:
        db.close()

    with tab_issue:
        student_opts = {f"{s.full_name} ({s.email})": s.id for s in students}
        course_opts = {c.title: c.id for c in courses}
        instr_opts = {"Select Instructor": ""} | {i.name: i.name for i in instructors}

        if not student_opts or not course_opts:
            st.info("Need at least one active student and one published course.")
            return

        with st.form("issue_cert_form"):
            col1, col2 = st.columns(2)
            with col1:
                sel_student = st.selectbox("Student *", list(student_opts.keys()))
                sel_course = st.selectbox("Course *", list(course_opts.keys()))
                sel_instr = st.selectbox("Instructor Name", list(instr_opts.keys()))
            with col2:
                completion_date = st.date_input("Completion Date", value=datetime.now().date())
                cert_file = st.file_uploader("Certificate PDF (optional)", type=["pdf"])

            if st.form_submit_button("Issue Certificate", type="primary"):
                student_id = student_opts[sel_student]
                course_id = course_opts[sel_course]
                instructor_name = instr_opts.get(sel_instr) or None

                # Generate unique cert ID
                cert_id = _gen_cert_id()
                db = get_db_session()
                try:
                    # Check existing
                    existing = db.query(Certificate).filter(
                        Certificate.student_id == student_id,
                        Certificate.course_id == course_id,
                        Certificate.is_revoked == False
                    ).first()
                    if existing:
                        st.warning(f"Certificate already issued (ID: {existing.certificate_id}). Revoke it first to reissue.")
                    else:
                        try:
                            file_url = upload_file(cert_file, folder="nextgen_mechtech/certificates") if cert_file else None
                        except Exception as e:
                            st.error(f"Certificate file upload failed: {e}")
                            st.stop()
                        cert = Certificate(
                            certificate_id=cert_id,
                            student_id=student_id,
                            course_id=course_id,
                            instructor_name=instructor_name,
                            file_data=file_url,
                            file_name=cert_file.name if cert_file else None,
                            completion_date=datetime.combine(completion_date, datetime.min.time()),
                        )
                        db.add(cert)
                        db.commit()

                        # Send notification
                        import os
                        app_url = os.getenv("APP_URL", "http://localhost:8501")
                        verify_url = f"{app_url}?page=verify&cert_id={cert_id}"
                        student = db.query(User).filter(User.id == student_id).first()
                        course = db.query(Course).filter(Course.id == course_id).first()
                        try:
                            send_certificate_issued(student.full_name, student.email, course.title, cert_id, verify_url)
                        except Exception:
                            pass

                        flash_message(f"Certificate issued! ID: **{cert_id}**")
                        flash_message(f"Verification URL: `{verify_url}`", kind="info")
                        st.rerun()
                except Exception as e:
                    db.rollback()
                    st.error(str(e))
                finally:
                    db.close()

    with tab_list:
        search_cert = st.text_input("Search by student name or cert ID")

        if search_cert:
            certs = [c for c in certs if
                     search_cert.lower() in c.student.full_name.lower() or
                     search_cert.lower() in c.certificate_id.lower()]

        if not certs:
            st.info("No certificates found.")
            return

        import os
        app_url = os.getenv("APP_URL", "http://localhost:8501")

        for cert in certs:
            revoked_badge = '<span class="nmt-badge nmt-badge-rejected">Revoked</span>' if cert.is_revoked else '<span class="nmt-badge nmt-badge-approved">Valid</span>'
            with st.expander(f"{cert.student.full_name} — {cert.course.title} [{cert.certificate_id}]"):
                st.markdown(revoked_badge, unsafe_allow_html=True)
                col1, col2 = st.columns([2, 1])
                with col1:
                    verify_url = f"{app_url}?page=verify&cert_id={cert.certificate_id}"
                    st.markdown(f"""
                    **Certificate ID:** `{cert.certificate_id}`
                    **Student:** {cert.student.full_name} ({cert.student.email})
                    **Course:** {cert.course.title}
                    **Instructor:** {cert.instructor_name or 'N/A'}
                    **Issued:** {cert.issued_at.strftime('%B %d, %Y')}
                    **Verify URL:** {verify_url}
                    """)
                with col2:
                    if not cert.is_revoked:
                        reason = st.text_input("Revoke reason", key=f"rev_reason_{cert.id}")
                        if st.button("Revoke", key=f"revoke_{cert.id}", use_container_width=True):
                            db = get_db_session()
                            try:
                                c = db.query(Certificate).filter(Certificate.id == cert.id).first()
                                c.is_revoked = True
                                c.revoke_reason = reason
                                db.commit()
                                st.rerun()
                            finally:
                                db.close()
                    else:
                        if st.button("Reissue", key=f"reissue_{cert.id}", use_container_width=True, type="primary"):
                            new_id = _gen_cert_id()
                            db = get_db_session()
                            try:
                                c = db.query(Certificate).filter(Certificate.id == cert.id).first()
                                c.is_revoked = False
                                c.revoke_reason = None
                                c.certificate_id = new_id
                                c.issued_at = datetime.utcnow()
                                db.commit()
                                flash_message(f"Reissued with new ID: {new_id}")
                                st.rerun()
                            finally:
                                db.close()

                    new_pdf = st.file_uploader("Replace PDF", type=["pdf"], key=f"replace_pdf_{cert.id}")
                    if new_pdf and st.button("Upload PDF", key=f"upload_pdf_{cert.id}"):
                        try:
                            new_pdf_url = upload_file(new_pdf, folder="nextgen_mechtech/certificates")
                        except Exception as e:
                            st.error(f"Certificate upload failed: {e}")
                            st.stop()
                        db = get_db_session()
                        try:
                            c = db.query(Certificate).filter(Certificate.id == cert.id).first()
                            c.file_data = new_pdf_url
                            c.file_name = new_pdf.name
                            db.commit()
                            flash_message("PDF replaced.")
                            st.rerun()
                        finally:
                            db.close()

                    if st.button("Delete Permanently", key=f"del_cert_{cert.id}", use_container_width=True):
                        db = get_db_session()
                        try:
                            c = db.query(Certificate).filter(Certificate.id == cert.id).first()
                            db.delete(c)
                            db.commit()
                            st.rerun()
                        finally:
                            db.close()


# ─── Tutor Applications ───────────────────────────────────────────────────────
def _admin_tutor_apps():
    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{icon("briefcase", size=17)} Tutor Applications</h3>', unsafe_allow_html=True)

    db = get_db_session()
    try:
        apps = db.query(TutorApplication).order_by(TutorApplication.created_at.desc()).all()
    finally:
        db.close()

    if not apps:
        st.info("No tutor applications received yet.")
        return

    for app in apps:
        badge_cls = {"pending": "nmt-badge-pending", "approved": "nmt-badge-approved", "rejected": "nmt-badge-rejected"}.get(app.status, "nmt-badge-neutral")
        with st.expander(f"{app.name} — {app.email} ({app.created_at.strftime('%b %d, %Y')})"):
            st.markdown(f'<span class="nmt-badge {badge_cls}">{app.status.title()}</span>', unsafe_allow_html=True)
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"""
                **Name:** {app.name}  **Email:** {app.email}  **Phone:** {app.phone}
                **Skills:** {app.skills}
                **Experience:** {app.experience}
                **Message:** {app.message or 'N/A'}
                """)
                if app.resume_data and app.resume_name:
                    st.download_button("Download Resume", data=get_file_bytes(app.resume_data), file_name=app.resume_name, key=f"dl_resume_{app.id}")
            with col2:
                reject_reason = st.text_area("Rejection reason (optional)", key=f"app_reason_{app.id}", height=70)
                if st.button("Approve", key=f"app_approve_{app.id}", use_container_width=True, type="primary"):
                    _upd_tutor(app.id, "approved")
                    send_tutor_application_approved(app.name, app.email)
                    flash_message("Approved and notified.")
                    st.rerun()
                if st.button("Reject", key=f"app_reject_{app.id}", use_container_width=True):
                    _upd_tutor(app.id, "rejected")
                    send_tutor_application_rejected(app.name, app.email, reject_reason)
                    flash_message("Rejected and notified.", kind="warning")
                    st.rerun()


def _upd_tutor(app_id, status):
    db = get_db_session()
    try:
        a = db.query(TutorApplication).filter(TutorApplication.id == app_id).first()
        if a:
            a.status = status
            db.commit()
    finally:
        db.close()


# ─── Payment Methods ──────────────────────────────────────────────────────────
def _admin_payment_methods():
    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:6px;">{icon("dollar-sign", size=17)} Payment Methods</h3>', unsafe_allow_html=True)
    st.markdown('<p style="color:var(--ink-500);font-size:13px;margin-bottom:18px;">Enable or disable payment methods and manage the account details shown to students during registration. Changes take effect immediately on the frontend — no code changes needed.</p>', unsafe_allow_html=True)

    methods = get_all_payment_methods()

    if not methods:
        st.info("No payment methods configured yet. Add one below.")

    for pm in methods:
        status_badge = (
            '<span class="nmt-badge nmt-badge-approved">Enabled</span>' if pm["is_enabled"]
            else '<span class="nmt-badge nmt-badge-rejected">Disabled</span>'
        )
        with st.expander(f"{pm['label']}  ({pm['method_key']})"):
            st.markdown(status_badge, unsafe_allow_html=True)
            with st.form(f"pm_form_{pm['id']}"):
                col1, col2 = st.columns(2)
                with col1:
                    label = st.text_input("Display Name", value=pm["label"], key=f"pm_label_{pm['id']}")
                    account_title = st.text_input("Account Title", value=pm["account_title"], key=f"pm_title_{pm['id']}")
                with col2:
                    enabled = st.checkbox("Enabled", value=pm["is_enabled"], key=f"pm_enabled_{pm['id']}")
                    account_number = st.text_input("Account Number", value=pm["account_number"], key=f"pm_number_{pm['id']}")

                custom_message = st.text_input(
                    "Custom Message (shown when details aren't available yet, e.g. \"Coming Soon\")",
                    value=pm["custom_message"], key=f"pm_msg_{pm['id']}"
                )
                display_order = st.number_input("Display Order", value=pm["display_order"], step=1, key=f"pm_order_{pm['id']}")

                col_save, col_del = st.columns([3, 1])
                with col_save:
                    save = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                with col_del:
                    delete = st.form_submit_button("Delete", use_container_width=True)

                if save:
                    if not label.strip():
                        st.error("Display name cannot be empty.")
                    else:
                        update_payment_method(
                            pm["id"],
                            label=label.strip(),
                            account_title=account_title.strip(),
                            account_number=account_number.strip(),
                            custom_message=custom_message.strip(),
                            is_enabled=enabled,
                            display_order=int(display_order),
                        )
                        flash_message(f"{label.strip()} updated.")
                        st.rerun()
                if delete:
                    delete_payment_method(pm["id"])
                    flash_message(f"{pm['label']} removed.", kind="warning")
                    st.rerun()

    st.markdown("<hr style='margin:20px 0;border-color:var(--line);'>", unsafe_allow_html=True)
    st.markdown(f'<div style="font-weight:700;font-size:14px;color:var(--ink-900);margin-bottom:10px;">{icon("plus-circle", size=15)} Add New Payment Method</div>', unsafe_allow_html=True)

    with st.form("pm_add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_label = st.text_input("Display Name *", placeholder="e.g. SadaPay")
            new_account_title = st.text_input("Account Title")
        with col2:
            new_enabled = st.checkbox("Enabled", value=True)
            new_account_number = st.text_input("Account Number")
        new_custom_message = st.text_input("Custom Message (optional)", placeholder="e.g. Coming Soon")

        added = st.form_submit_button("Add Payment Method", type="primary", use_container_width=True)
        if added:
            if not new_label.strip():
                st.error("Display name is required.")
            else:
                base_key = re.sub(r"[^a-z0-9]+", "_", new_label.strip().lower()).strip("_")
                method_key = base_key or f"method_{int(datetime.now().timestamp())}"
                ok = add_payment_method(
                    method_key=method_key,
                    label=new_label.strip(),
                    account_title=new_account_title.strip(),
                    account_number=new_account_number.strip(),
                    custom_message=new_custom_message.strip(),
                    is_enabled=new_enabled,
                    display_order=len(methods) + 1,
                )
                if ok:
                    flash_message(f"{new_label.strip()} added.")
                    st.rerun()
                else:
                    st.error("A payment method with that name already exists.")


# ─── Messages ─────────────────────────────────────────────────────────────────
def _admin_messages():
    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{icon("mail", size=17)} Contact Messages</h3>', unsafe_allow_html=True)

    filter_unread = st.checkbox("Show unread only", value=False)
    db = get_db_session()
    try:
        query = db.query(ContactMessage).order_by(ContactMessage.created_at.desc())
        if filter_unread:
            query = query.filter(ContactMessage.is_read == False)
        messages = query.all()
    finally:
        db.close()

    if not messages:
        st.info("No messages found.")
        return

    for msg in messages:
        badge = '<span class="nmt-badge nmt-badge-info">Unread</span>' if not msg.is_read else '<span class="nmt-badge nmt-badge-neutral">Read</span>'
        with st.expander(f"{msg.name} — {msg.subject} ({msg.created_at.strftime('%b %d, %Y')})"):
            st.markdown(badge, unsafe_allow_html=True)
            st.markdown(f"**From:** {msg.name} ({msg.email})\n\n**Message:** {msg.message}")
            if msg.reply:
                st.success(f"Your reply: {msg.reply}")

            col1, col2 = st.columns([3, 1])
            with col1:
                reply_text = st.text_area("Reply", key=f"reply_{msg.id}", height=80)
            with col2:
                if st.button("Send Reply", key=f"send_reply_{msg.id}"):
                    if reply_text:
                        content = f"<h2 style='color:#0F2D6B;'>Reply from NextGen MechTech Academy</h2><p><strong>Re:</strong> {msg.subject}</p><div style='background:#F8FAFC;border-radius:8px;padding:16px;'>{reply_text}</div>"
                        send_email(msg.email, f"Re: {msg.subject}", _base_template(content))
                        _mark_replied(msg.id, reply_text)
                        flash_message("Reply sent.")
                        st.rerun()
                if st.button("Delete", key=f"del_msg_{msg.id}"):
                    _del_msg(msg.id)
                    st.rerun()
                if not msg.is_read:
                    if st.button("Mark Read", key=f"read_msg_{msg.id}"):
                        _mark_read(msg.id)
                        st.rerun()


def _mark_replied(mid, reply):
    db = get_db_session()
    try:
        m = db.query(ContactMessage).filter(ContactMessage.id == mid).first()
        if m:
            m.reply = reply
            m.is_read = True
            db.commit()
    finally:
        db.close()


def _mark_read(mid):
    db = get_db_session()
    try:
        m = db.query(ContactMessage).filter(ContactMessage.id == mid).first()
        if m:
            m.is_read = True
            db.commit()
    finally:
        db.close()


def _del_msg(mid):
    db = get_db_session()
    try:
        m = db.query(ContactMessage).filter(ContactMessage.id == mid).first()
        if m:
            db.delete(m)
            db.commit()
    finally:
        db.close()


# ─── Announcements ────────────────────────────────────────────────────────────
def _admin_announcements():
    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{icon("bell", size=17)} Manage Announcements</h3>', unsafe_allow_html=True)

    with st.form("add_announcement"):
        title = st.text_input("Announcement Title *")
        content = st.text_area("Content *", height=100)
        is_active = st.checkbox("Active (visible on website)", value=True)
        if st.form_submit_button("Post Announcement", type="primary"):
            if not title or not content:
                st.error("Title and content are required.")
            else:
                db = get_db_session()
                try:
                    db.add(Announcement(title=title, content=content, is_active=is_active))
                    db.commit()
                    _get_active_announcements.clear()
                    flash_message("Announcement posted.")
                    st.rerun()
                except Exception as e:
                    db.rollback()
                    st.error(str(e))
                finally:
                    db.close()

    db = get_db_session()
    try:
        announcements = db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    finally:
        db.close()

    for ann in announcements:
        badge = '<span class="nmt-badge nmt-badge-approved">Active</span>' if ann.is_active else '<span class="nmt-badge nmt-badge-neutral">Inactive</span>'
        with st.expander(ann.title):
            st.markdown(badge, unsafe_allow_html=True)
            st.write(ann.content)
            col1, col2 = st.columns(2)
            with col1:
                lbl = "Deactivate" if ann.is_active else "Activate"
                if st.button(lbl, key=f"toggle_ann_{ann.id}"):
                    db = get_db_session()
                    try:
                        a = db.query(Announcement).filter(Announcement.id == ann.id).first()
                        a.is_active = not a.is_active
                        db.commit()
                        _get_active_announcements.clear()
                        st.rerun()
                    finally:
                        db.close()
            with col2:
                if st.button("Delete", key=f"del_ann_{ann.id}"):
                    db = get_db_session()
                    try:
                        a = db.query(Announcement).filter(Announcement.id == ann.id).first()
                        db.delete(a)
                        db.commit()
                        _get_active_announcements.clear()
                        st.rerun()
                    finally:
                        db.close()


# ─── Email Templates ──────────────────────────────────────────────────────────
def _admin_email_templates():
    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{icon("mail", size=17)} Email Templates</h3>', unsafe_allow_html=True)

    db = get_db_session()
    try:
        templates = db.query(EmailTemplate).order_by(EmailTemplate.name).all()
    finally:
        db.close()

    if not templates:
        st.info("No email templates found.")
        return

    for tmpl in templates:
        with st.expander(f"{tmpl.name} [{tmpl.event_key}]"):
            badge = '<span class="nmt-badge nmt-badge-approved">Active</span>' if tmpl.is_active else '<span class="nmt-badge nmt-badge-neutral">Inactive</span>'
            st.markdown(badge, unsafe_allow_html=True)
            with st.form(f"edit_tmpl_{tmpl.id}"):
                e_subject = st.text_input("Subject", value=tmpl.subject)
                e_body = st.text_area("Body HTML", value=tmpl.body_html, height=200,
                                      help="Use {{name}}, {{link}}, {{course}}, {{cert_id}} as placeholders")
                e_active = st.checkbox("Active", value=tmpl.is_active)
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Save Template", type="primary"):
                        db = get_db_session()
                        try:
                            t = db.query(EmailTemplate).filter(EmailTemplate.id == tmpl.id).first()
                            t.subject = e_subject
                            t.body_html = e_body
                            t.is_active = e_active
                            db.commit()
                            flash_message("Template saved.")
                            st.rerun()
                        except Exception as ex:
                            db.rollback()
                            st.error(str(ex))
                        finally:
                            db.close()
                with col2:
                    test_email = st.text_input("Test email address", placeholder="test@example.com", key=f"test_email_{tmpl.id}")

            if st.button("Send Test Email", key=f"send_test_{tmpl.id}"):
                if test_email:
                    body = tmpl.body_html.replace("{{name}}", "Test User").replace("{{link}}", "#").replace("{{course}}", "Test Course").replace("{{cert_id}}", "NMT-TEST0001")
                    result = send_email(test_email, f"[TEST] {tmpl.subject}", _base_template(body))
                    if result:
                        st.success(f"Test email sent to {test_email}")
                    else:
                        st.warning("Could not send (check Brevo settings in Website Settings → Email (Brevo)).")
                else:
                    st.error("Enter a test email address.")


# ─── Settings ─────────────────────────────────────────────────────────────────
def _admin_settings():
    st.markdown(f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:16px;">{icon("settings", size=17)} Website Settings</h3>', unsafe_allow_html=True)

    tab_general, tab_contact, tab_social, tab_smtp = st.tabs(["General", "Contact & Stats", "Social Links", "Email (Brevo)"])

    settings = get_all_settings()

    with tab_general:
        with st.form("settings_general"):
            col1, col2 = st.columns(2)
            with col1:
                site_name = st.text_input("Website Name", value=settings.get("site_name", "NextGen MechTech Academy"))
                tagline = st.text_input("Tagline", value=settings.get("tagline", "Learn. Build. Innovate."))
            with col2:
                footer_text = st.text_input("Footer Text", value=settings.get("footer_text", ""))
                about_tagline = st.text_input("About Page Tagline", value=settings.get("about_tagline", ""))
            if st.form_submit_button("Save General Settings", type="primary"):
                for k, v in {"site_name": site_name, "tagline": tagline,
                              "footer_text": footer_text, "about_tagline": about_tagline}.items():
                    update_setting(k, v)
                st.success("Saved.")

    with tab_contact:
        with st.form("settings_contact"):
            col1, col2 = st.columns(2)
            with col1:
                contact_email = st.text_input("Contact Email", value=settings.get("contact_email", ""))
                contact_phone = st.text_input("Contact Phone", value=settings.get("contact_phone", ""))
                contact_address = st.text_input("Address", value=settings.get("contact_address", ""))
                office_hours = st.text_input("Office Hours", value=settings.get("office_hours", "Mon–Sat: 9 AM–6 PM"))
            with col2:
                stat_students = st.text_input("Students Stat", value=settings.get("stat_students", "500+"))
                stat_courses = st.text_input("Courses Stat", value=settings.get("stat_courses", "12+"))
                stat_certs = st.text_input("Certificates Stat", value=settings.get("stat_certificates", "300+"))
                stat_instructors = st.text_input("Instructors Stat", value=settings.get("stat_instructors", "10+"))
            if st.form_submit_button("Save Contact Settings", type="primary"):
                for k, v in {
                    "contact_email": contact_email, "contact_phone": contact_phone,
                    "contact_address": contact_address, "office_hours": office_hours,
                    "stat_students": stat_students, "stat_courses": stat_courses,
                    "stat_certificates": stat_certs, "stat_instructors": stat_instructors,
                }.items():
                    update_setting(k, v)
                st.success("Saved.")

    with tab_social:
        with st.form("settings_social"):
            col1, col2 = st.columns(2)
            with col1:
                fb = st.text_input("Facebook URL", value=settings.get("facebook_url", ""))
                insta = st.text_input("Instagram URL", value=settings.get("instagram_url", ""))
            with col2:
                linkedin = st.text_input("LinkedIn URL", value=settings.get("linkedin_url", ""))
                youtube = st.text_input("YouTube URL", value=settings.get("youtube_url", ""))
            if st.form_submit_button("Save Social Links", type="primary"):
                for k, v in {"facebook_url": fb, "instagram_url": insta, "linkedin_url": linkedin, "youtube_url": youtube}.items():
                    update_setting(k, v)
                st.success("Saved.")

    with tab_smtp:
        from utils.email_service import test_smtp_connection, send_email, _base_template, get_smtp_status

        s = get_smtp_status()

        # ── Config table ─────────────────────────────────────────────────
        env_badge = (
            '<span style="color:var(--success-tx);font-weight:700;">✓ Found</span>'
            if s["env_exists"] else
            '<span style="color:var(--danger-tx);font-weight:700;">✗ Not found</span>'
        )
        key_colour    = "var(--success-tx)" if s["api_key_set"]  else "var(--danger-tx)"
        sender_colour = "var(--success-tx)" if s["sender_email"] else "var(--danger-tx)"
        key_display    = f"✓ Set ({s['api_key_len']} chars)" if s["api_key_set"] else "✗ Not set"
        sender_display = s["sender_email"] if s["sender_email"] else "✗ Not set"

        st.markdown(html_block(f"""
        <div style="background:var(--surface);border:1.5px solid var(--line);
                    border-radius:var(--radius-md);padding:22px 26px;margin-bottom:20px;">
          <div style="font-family:var(--font-head);font-weight:700;font-size:15px;
                      color:var(--ink-900);margin-bottom:16px;">📄 .env file status — Brevo</div>
          <table style="width:100%;border-collapse:collapse;font-size:13.5px;line-height:2;">
            <tr>
              <td style="color:var(--ink-500);width:180px;">.env path</td>
              <td style="font-family:monospace;color:var(--ink-700);">{s["env_path"]}</td>
              <td style="text-align:right;">{env_badge}</td>
            </tr>
            <tr>
              <td style="color:var(--ink-500);">Provider</td>
              <td style="font-family:monospace;color:var(--ink-900);">{s["provider"]}</td><td></td>
            </tr>
            <tr>
              <td style="color:var(--ink-500);">BREVO_API_KEY</td>
              <td style="color:{key_colour};font-weight:600;">{key_display}</td><td></td>
            </tr>
            <tr>
              <td style="color:var(--ink-500);">BREVO_SENDER_EMAIL</td>
              <td style="font-family:monospace;color:{sender_colour};">{sender_display}</td><td></td>
            </tr>
            <tr>
              <td style="color:var(--ink-500);">BREVO_SENDER_NAME</td>
              <td style="font-family:monospace;color:var(--ink-900);">{s["sender_name"]}</td><td></td>
            </tr>
            <tr>
              <td style="color:var(--ink-500);">APP_URL</td>
              <td style="font-family:monospace;color:var(--ink-900);">{s["app_url"]}</td><td></td>
            </tr>
            <tr>
              <td style="color:var(--ink-500);">ADMIN_EMAIL</td>
              <td style="font-family:monospace;color:var(--ink-900);">{s["admin"] or "—"}</td><td></td>
            </tr>
          </table>
        </div>
        """), unsafe_allow_html=True)

        # ── Quick-fix guide (shown only when credentials missing) ─────────
        if not s["api_key_set"] or not s["sender_email"]:
            st.error("Brevo credentials are missing. Follow the steps below then restart Streamlit.")
            st.markdown("""
**How to get Brevo credentials:**

1. Sign in to [app.brevo.com](https://app.brevo.com) (create a free account if needed)
2. Go to **Senders, Domains & Dedicated IPs** and add + verify the email address you'll send from
3. Go to **SMTP & API** → **API Keys** tab → click **Generate a new API key**
4. Copy the generated key
5. Open your `.env` file (in the project root folder) and set:

```
BREVO_API_KEY=xkeysib-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
BREVO_SENDER_EMAIL=youremail@yourdomain.com
BREVO_SENDER_NAME=NextGen MechTech Academy
```

6. **Save the file**, then **restart Streamlit** (`Ctrl+C` → `streamlit run app.py`)
            """)
        else:
            st.success(f"Credentials loaded from .env — sender: **{s['sender_email']}**")

        st.markdown("---")

        # ── Two-step test ─────────────────────────────────────────────────
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Step 1 — Connection test** *(no email sent)*")
            if st.button("🔌 Test Brevo Connection", use_container_width=True, type="primary"):
                with st.spinner("Connecting to Brevo API…"):
                    ok, msg = test_smtp_connection()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

        with col2:
            st.markdown("**Step 2 — Send a real test email**")
            test_addr = st.text_input(
                "Recipient address",
                value=s["sender_email"],
                placeholder="you@example.com",
                key="smtp_test_addr"
            )
            if st.button("📨 Send Test Email", use_container_width=True):
                if not test_addr.strip():
                    st.error("Enter an email address.")
                else:
                    with st.spinner("Sending…"):
                        sent = send_email(
                            test_addr.strip(),
                            "✓ Brevo Test — NextGen MechTech Academy",
                            _base_template(
                                "<h2 style='color:#0F2D6B;'>Brevo is working! ✓</h2>"
                                "<p>This test email was sent from your NextGen MechTech Academy "
                                "admin panel. Your email configuration is correct.</p>",
                                "Brevo test successful"
                            )
                        )
                    if sent:
                        st.success(f"✓ Email delivered to **{test_addr}** — check your inbox.")
                    else:
                        st.error(
                            "Send failed. Check the **terminal window** where Streamlit is "
                            "running — the exact error is printed there."
                        )


# ─── Roles & Permissions ──────────────────────────────────────────────────────
def _admin_roles_permissions():
    from components.icons import icon
    st.markdown(
        f'<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;'
        f'color:var(--ink-900);margin-bottom:16px;">'
        f'{icon("shield", size=17)} Roles & Permissions</h3>',
        unsafe_allow_html=True
    )

    user = st.session_state.get("user")
    is_super = user and user.get("role") == "super_admin"

    if not is_super:
        st.warning("Only Super Admin can manage roles and permissions.")
        return

    tabs = st.tabs(["Manage Users & Roles", "Permission Matrix", "Create Admin / Staff"])

    # ── Tab 1: Manage Users & Roles ───────────────────────────────────────
    with tabs[0]:
        db = get_db_session()
        try:
            staff = db.query(User).filter(
                User.role.in_([UserRole.admin, UserRole.super_admin,
                                UserRole.instructor, UserRole.content_manager])
            ).order_by(User.role, User.full_name).all()
        finally:
            db.close()

        if not staff:
            st.info("No staff members found.")
        else:
            for u in staff:
                role_colors = {
                    "super_admin": "var(--danger-tx)",
                    "admin": "var(--blue-600)",
                    "instructor": "var(--amber-600)",
                    "content_manager": "var(--success-tx)",
                }
                role_val = u.role.value if hasattr(u.role, 'value') else str(u.role)
                color = role_colors.get(role_val, "var(--ink-500)")
                with st.expander(f"{u.full_name} — {u.email}"):
                    st.markdown(
                        f'<span style="background:var(--surface-soft);padding:3px 10px;'
                        f'border-radius:20px;font-size:12px;font-weight:700;color:{color};">'
                        f'{role_val.replace("_", " ").title()}</span>',
                        unsafe_allow_html=True
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_name = st.text_input("Full Name *", value=u.full_name, key=f"name_{u.id}")
                        edit_email = st.text_input("Email *", value=u.email, key=f"email_{u.id}")
                        edit_phone = st.text_input("Phone", value=u.phone or "", key=f"phone_{u.id}")
                    with col2:
                        new_role = st.selectbox(
                            "Change Role",
                            ["student", "admin", "super_admin", "instructor", "content_manager"],
                            index=["student", "admin", "super_admin", "instructor", "content_manager"].index(role_val),
                            key=f"role_sel_{u.id}"
                        )
                        edit_password = st.text_input(
                            "Reset Password",
                            type="password",
                            key=f"pw_{u.id}",
                            help="Leave blank to keep the current password"
                        )
                        is_active = st.checkbox("Account Active", value=u.is_active, key=f"active_{u.id}")

                    st.write(f"Joined: {u.created_at.strftime('%b %d, %Y')}")

                    # Custom permissions JSON
                    perms = st.text_area(
                        "Custom Permissions (JSON list)",
                        value=u.permissions or "[]",
                        height=60,
                        key=f"perms_{u.id}",
                        help='e.g. ["add_courses", "edit_own_courses", "manage_students"]'
                    )

                    col_save, col_del = st.columns(2)
                    with col_save:
                        if st.button("Save Role & Permissions", key=f"save_role_{u.id}", type="primary"):
                            if not edit_name or not edit_email:
                                st.error("Name and email are required.")
                            else:
                                db = get_db_session()
                                try:
                                    usr = db.query(User).get(u.id)
                                    usr.full_name = edit_name
                                    usr.email = edit_email
                                    usr.phone = edit_phone
                                    usr.role = UserRole[new_role]
                                    usr.is_active = is_active
                                    usr.permissions = perms
                                    if edit_password:
                                        usr.password_hash = bcrypt.hashpw(edit_password.encode(), bcrypt.gensalt()).decode()
                                    db.commit()
                                    flash_message("Role updated!")
                                    st.rerun()
                                except Exception as e:
                                    db.rollback()
                                    st.error(str(e))
                                finally:
                                    db.close()
                    with col_del:
                        if st.button("Remove Staff Access", key=f"demote_{u.id}"):
                            db = get_db_session()
                            try:
                                usr = db.query(User).get(u.id)
                                usr.role = UserRole.student
                                db.commit()
                                flash_message("Demoted to student.")
                                st.rerun()
                            finally:
                                db.close()

    # ── Tab 2: Permission Matrix ──────────────────────────────────────────
    with tabs[1]:
        st.markdown("**Permission Matrix — What each role can do**")

        PERMISSION_MATRIX = {
            "Module": ["Dashboard", "Website CMS", "Courses", "Instructors",
                       "Students", "Registrations", "Certificates", "Tutor Apps",
                       "Messages", "Announcements", "Email Templates",
                       "Roles & Perms", "Settings"],
            "Super Admin": ["✅"] * 13,
            "Admin": ["✅", "✅", "✅", "✅", "✅", "✅", "✅", "✅", "✅", "✅", "✅", "❌", "✅"],
            "Instructor": ["✅", "❌", "✅ (own)", "❌", "✅ (own)", "✅ (own)", "❌", "❌", "❌", "❌", "❌", "❌", "❌"],
            "Content Manager": ["✅", "✅", "✅", "✅", "❌", "❌", "❌", "❌", "✅", "✅", "✅", "❌", "❌"],
        }
        st.dataframe(pd.DataFrame(PERMISSION_MATRIX).set_index("Module"), use_container_width=True)

        st.info("Fine-grained permissions can be set per user using the Custom Permissions JSON field above.")

    # ── Tab 3: Create Admin / Staff ──────────────────────────────────────
    with tabs[2]:
        st.markdown("**Create New Admin, Instructor, or Content Manager**")
        with st.form("create_staff"):
            col1, col2 = st.columns(2)
            with col1:
                cs_name = st.text_input("Full Name *")
                cs_email = st.text_input("Email *")
                cs_phone = st.text_input("Phone")
            with col2:
                cs_role = st.selectbox("Role", ["admin", "instructor", "content_manager", "super_admin"])
                cs_password = st.text_input("Temporary Password *", type="password")
                cs_active = st.checkbox("Account Active", value=True)

            cs_perms = st.text_area(
                "Initial Permissions (JSON list, optional)",
                value="[]",
                height=60
            )

            if st.form_submit_button("Create Staff Account", type="primary"):
                if not cs_name or not cs_email or not cs_password:
                    st.error("Name, email, and password are required.")
                else:
                    db = get_db_session()
                    try:
                        existing = db.query(User).filter(User.email == cs_email).first()
                        if existing:
                            st.error("Email already registered.")
                        else:
                            pw_hash = bcrypt.hashpw(cs_password.encode(), bcrypt.gensalt()).decode()
                            db.add(User(
                                full_name=cs_name,
                                email=cs_email,
                                password_hash=pw_hash,
                                phone=cs_phone,
                                role=UserRole[cs_role],
                                is_verified=True,
                                is_active=cs_active,
                                permissions=cs_perms
                            ))
                            db.commit()
                            st.success(f"Staff account created for {cs_name} ({cs_role})!")
                    except Exception as e:
                        db.rollback()
                        st.error(str(e))
                    finally:
                        db.close()