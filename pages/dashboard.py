import streamlit as st
import textwrap
from datetime import datetime

from components.icons import icon
from database.connection import get_db_session
from database.models import (
    Registration, Certificate, Course,
    User, RegistrationStatus, PaymentStatus
)
from sqlalchemy.orm import joinedload
from utils.email_service import (
    send_registration_confirmation, send_admin_new_registration,
    ADMIN_EMAIL
)
from utils.helpers import html_block, get_enabled_payment_methods, flash_message, check_upload_size
from utils.cloudinary_service import upload_file, resolve_src, get_file_bytes
from pages.home import _get_active_announcements

_STATUS_META = {
    RegistrationStatus.pending: ("clock", "nmt-badge-pending", "Pending Review"),
    RegistrationStatus.approved: ("check-circle", "nmt-badge-approved", "Approved"),
    RegistrationStatus.rejected: ("x-circle", "nmt-badge-rejected", "Rejected"),
    RegistrationStatus.info_requested: ("info", "nmt-badge-info", "Info Requested"),
}
_PAY_META = {
    PaymentStatus.pending: ("clock", "nmt-badge-pending", "Payment Pending"),
    PaymentStatus.verified: ("check-circle", "nmt-badge-approved", "Payment Verified"),
    PaymentStatus.rejected: ("x-circle", "nmt-badge-rejected", "Payment Rejected"),
}


def render_dashboard():
    user = st.session_state.get("user")
    if not user:
        st.session_state.page = "login"
        st.rerun()
        return

    if user.get("role") == "admin":
        st.session_state.page = "admin"
        st.rerun()
        return

    user_id = user["id"]

    db = get_db_session()
    try:
        registrations = (
            db.query(Registration)
            .options(joinedload(Registration.course))
            .filter(Registration.student_id == user_id)
            .all()
        )
        certificates = (
            db.query(Certificate)
            .options(joinedload(Certificate.course))
            .filter(Certificate.student_id == user_id)
            .all()
        )
        all_courses = db.query(Course).filter(Course.is_published == True).all()

        total_reg = len(registrations)
        pending = len([r for r in registrations if r.registration_status == RegistrationStatus.pending])
        approved = len([r for r in registrations if r.registration_status == RegistrationStatus.approved])
        certs = len(certificates)
    finally:
        db.close()

    # Shares the same cached announcements as the Home page (Phase 2) instead
    # of running its own separate, uncached query for the same public data.
    announcements = _get_active_announcements(5)

    first_name = user["full_name"].split()[0]
    st.markdown(html_block(f"""
    <div class="nmt-app-header">
      <div class="nmt-app-header-inner">
        <div>
          <h1>{icon("layout", size=20, color="#fff")} Welcome back, {first_name}</h1>
          <div class="sub">Student Dashboard</div>
        </div>
        <div class="meta">{icon("calendar", size=14, color="rgba(255,255,255,0.75)")} {datetime.now().strftime("%A, %B %d, %Y")}</div>
      </div>
    </div>
    """), unsafe_allow_html=True)

    st.markdown('<div class="nmt-content">', unsafe_allow_html=True)

    with st.container(key="nmt_stat_row"):
        c1, c2, c3, c4 = st.columns(4)
        cards = [
            ("book-open", str(total_reg), "Total Registrations", "var(--blue-50)", "var(--blue-600)"),
            ("clock", str(pending), "Pending", "var(--warning-bg)", "var(--warning-tx)"),
            ("check-circle", str(approved), "Approved", "var(--success-bg)", "var(--success-tx)"),
            ("award", str(certs), "Certificates", "var(--amber-100)", "var(--amber-600)"),
        ]
        for col, (icon_name, val, label, bg, fg) in zip([c1, c2, c3, c4], cards):
            with col:
                st.markdown(html_block(f"""
                <div class="nmt-stat-card">
                  <div class="icon" style="background:{bg};color:{fg};">{icon(icon_name, size=17)}</div>
                  <div class="val">{val}</div>
                  <div class="lbl">{label}</div>
                </div>
                """), unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    init_tab = st.session_state.get("dashboard_tab", "registrations")
    tab_opts = ["My Registrations", "Register for Course", "My Certificates", "Notifications", "Profile"]
    tabs = st.tabs(tab_opts)

    with tabs[0]:
        _render_my_registrations(user_id)
    with tabs[1]:
        _render_registration_form(user_id, all_courses)
    with tabs[2]:
        _render_certificates(user_id)
    with tabs[3]:
        _render_notifications(announcements, registrations)
    with tabs[4]:
        _render_profile(user)

    st.markdown("</div>", unsafe_allow_html=True)


def _render_my_registrations(user_id: int):
    db = get_db_session()
    try:
        regs = (
            db.query(Registration)
            .options(joinedload(Registration.course))
            .filter(Registration.student_id == user_id)
            .order_by(Registration.created_at.desc())
            .all()
        )

        if not regs:
            st.markdown(html_block(f"""
            <div class="nmt-empty">
              <div class="icon">{icon("book-open", size=40)}</div>
              <div class="title">No Registrations Yet</div>
              <p>Register for a course to get started on your learning journey.</p>
            </div>
            """), unsafe_allow_html=True)
            return

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        for reg in regs:
            icon_name, badge_cls, label = _STATUS_META.get(reg.registration_status, ("help-circle", "nmt-badge-neutral", "Unknown"))
            pay_icon, pay_cls, pay_label = _PAY_META.get(reg.payment_status, ("help-circle", "nmt-badge-neutral", "Unknown"))

            note_html = ""
            if reg.admin_note:
                note_html = f"""
                <div style="background:var(--danger-bg);border-radius:8px;padding:10px 12px;margin-top:12px;font-size:12.5px;color:var(--danger-tx);">
                  <strong>Admin Note:</strong> {reg.admin_note}
                </div>
                """

            st.markdown(html_block(f"""
            <div class="nmt-list-card">
              <div class="nmt-list-row">
                <div>
                  <div class="nmt-list-title">{reg.course.title}</div>
                  <div class="nmt-list-meta">Registered: {reg.created_at.strftime("%B %d, %Y")}</div>
                </div>
                <div style="display:flex;gap:8px;flex-wrap:wrap;">
                  <span class="nmt-badge {badge_cls}">{icon(icon_name, size=11)} {label}</span>
                  <span class="nmt-badge {pay_cls}">{icon(pay_icon, size=11)} {pay_label}</span>
                </div>
              </div>
              {note_html}
            </div>
            """), unsafe_allow_html=True)
    finally:
        db.close()


def _render_registration_form(user_id: int, courses):
    st.markdown('<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:18px;">Register for a Course</h3>', unsafe_allow_html=True)

    preselected_id = st.session_state.get("selected_course_id")

    db = get_db_session()
    try:
        enrolled_ids = [r.course_id for r in db.query(Registration).filter(Registration.student_id == user_id).all()]
    finally:
        db.close()

    available = [c for c in courses if c.id not in enrolled_ids]

    if not available:
        st.info("You've registered for all available courses.")
        return

    course_options = {f"{c.title} — PKR {c.fee:,.0f}": c.id for c in available}
    course_names = list(course_options.keys())

    default_idx = 0
    if preselected_id:
        for i, c in enumerate(available):
            if c.id == preselected_id:
                default_idx = i
                break

    payment_methods = get_enabled_payment_methods()
    if not payment_methods:
        st.error("No payment methods are currently available. Please contact support to complete your registration.")
        return

    pm_labels = [m["label"] for m in payment_methods]
    selected_payment_label = st.selectbox("Payment Method *", pm_labels, key="reg_payment_method_select")
    selected_pm = next((m for m in payment_methods if m["label"] == selected_payment_label), payment_methods[0])
    _render_payment_method_details(selected_pm)

    with st.form("registration_form"):
        selected_course_name = st.selectbox("Select Course *", course_names, index=default_idx)
        selected_course_id = course_options[selected_course_name]

        col1, col2 = st.columns(2)
        with col1:
            phone = st.text_input("Phone Number *", placeholder="+92-300-0000000")
        with col2:
            whatsapp = st.text_input("WhatsApp Number", placeholder="+92-300-0000000")

        col3, col4 = st.columns(2)
        with col3:
            university = st.text_input("University", placeholder="UET Lahore")
        with col4:
            department = st.text_input("Department", placeholder="Mechanical Engineering")

        semester = st.selectbox("Semester", ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "Graduate", "Other"])

        payment_screenshot = st.file_uploader("Payment Screenshot *", type=["png", "jpg", "jpeg", "pdf"])
        notes = st.text_area("Additional Notes", placeholder="Any specific requirements or questions...", height=80)

        st.markdown(html_block(f"""
        <div style="background:var(--blue-50);border-radius:8px;padding:12px 14px;font-size:12.5px;color:var(--navy-900);margin:8px 0;display:flex;gap:8px;align-items:flex-start;">
          {icon("info", size=15, color="var(--blue-600)")}
          <span>Please upload a clear screenshot of your payment proof. Registrations without payment proof may be delayed.</span>
        </div>
        """), unsafe_allow_html=True)

        submitted = st.form_submit_button("Submit Registration", use_container_width=True, type="primary")

        if submitted:
            if not phone:
                st.error("Phone number is required.")
            elif not payment_screenshot:
                st.error("Payment screenshot is required.")
            elif not check_upload_size(payment_screenshot, 5):
                st.error("Payment screenshot is too large. Maximum allowed size is 5MB.")
            else:
                try:
                    screenshot_url = upload_file(payment_screenshot, folder="nextgen_mechtech/payments") if payment_screenshot else None
                except Exception as e:
                    st.error(f"Payment screenshot upload failed: {e}")
                    st.stop()
                user = st.session_state.user

                db = get_db_session()
                try:
                    reg = Registration(
                        student_id=user_id,
                        course_id=selected_course_id,
                        phone=phone,
                        whatsapp=whatsapp or phone,
                        university=university,
                        department=department,
                        semester=semester,
                        payment_method=selected_payment_label,
                        payment_screenshot=screenshot_url,
                        notes=notes,
                    )
                    db.add(reg)
                    db.commit()

                    course_obj = next((c for c in courses if c.id == selected_course_id), None)
                    course_title = course_obj.title if course_obj else "Selected Course"

                    send_registration_confirmation(user["full_name"], user["email"], course_title)
                    send_admin_new_registration(ADMIN_EMAIL, user["full_name"], course_title)

                    if "selected_course_id" in st.session_state:
                        del st.session_state.selected_course_id

                    flash_message("Registration submitted. You'll receive a confirmation email shortly — our team will review your payment and approve within 24-48 hours.")
                    st.rerun()
                except Exception as e:
                    db.rollback()
                    st.error(f"Error submitting registration: {str(e)}")
                finally:
                    db.close()


def _render_payment_method_details(pm: dict):
    """Render the account details for the currently selected payment method,
    sourced live from the Admin Panel/CMS. Falls back to a friendly
    'details coming soon' message when a method is enabled but no account
    details (or custom message) have been configured yet."""
    label = pm["label"]
    account_title = (pm.get("account_title") or "").strip()
    account_number = (pm.get("account_number") or "").strip()
    custom_message = (pm.get("custom_message") or "").strip()

    if account_title or account_number:
        rows_html = ""
        if account_title:
            rows_html += f'<div><strong>Account Title:</strong> {account_title}</div>'
        if account_number:
            rows_html += f'<div><strong>Account Number:</strong> {account_number}</div>'
        note_html = (
            f'<div style="margin-top:8px;color:var(--ink-500);font-size:12px;">{custom_message}</div>'
            if custom_message else ""
        )
        st.markdown(html_block(f"""
        <div style="background:var(--blue-50);border-radius:8px;padding:14px 16px;font-size:13px;color:var(--navy-900);margin:4px 0 16px;">
          <div style="font-weight:700;margin-bottom:6px;">{label} Payment Details</div>
          {rows_html}
          {note_html}
        </div>
        """), unsafe_allow_html=True)
    elif custom_message:
        st.markdown(html_block(f"""
        <div style="background:var(--amber-100);border-radius:8px;padding:14px 16px;font-size:13px;color:var(--amber-600);margin:4px 0 16px;">
          <strong>{label}:</strong> {custom_message}
        </div>
        """), unsafe_allow_html=True)
    else:
        st.markdown(html_block(f"""
        <div style="background:var(--surface-soft);border:1px dashed var(--line);border-radius:8px;padding:14px 16px;font-size:13px;color:var(--ink-500);margin:4px 0 16px;">
          {label} details will be available soon.
        </div>
        """), unsafe_allow_html=True)


def _render_certificates(user_id: int):
    import os
    app_url = os.getenv("APP_URL", "http://localhost:8501")
    db = get_db_session()
    try:
        certs = (
            db.query(Certificate)
            .options(joinedload(Certificate.course))
            .filter(Certificate.student_id == user_id, Certificate.is_revoked == False)
            .all()
        )

        if not certs:
            st.markdown(html_block(f"""
            <div class="nmt-empty">
              <div class="icon">{icon("award", size=40)}</div>
              <div class="title">No Certificates Yet</div>
              <p>Complete a course to earn your certificate.</p>
            </div>
            """), unsafe_allow_html=True)
            return

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        cols = st.columns(3)
        for i, cert in enumerate(certs):
            verify_url = f"{app_url}?page=verify&cert_id={cert.certificate_id}"
            with cols[i % 3]:
                st.markdown(html_block(f"""
                <div class="nmt-cert-card nmt-fade-in">
                  <div class="nmt-cert-icon">{icon("award", size=20)}</div>
                  <div class="nmt-cert-title">{cert.course.title}</div>
                  <div class="nmt-cert-sub">Issued: {cert.issued_at.strftime("%B %d, %Y")}</div>
                  <div style="margin-top:10px;font-size:11px;color:rgba(255,255,255,0.6);">ID: <code style="color:rgba(255,255,255,0.9);">{cert.certificate_id}</code></div>
                  <div style="margin-top:8px;">
                    <a href="{verify_url}" target="_blank" style="display:inline-flex;align-items:center;gap:4px;color:rgba(255,255,255,0.8);font-size:11px;text-decoration:underline;">{icon("external-link", size=11, color="rgba(255,255,255,0.8)")} Verify Online</a>
                  </div>
                </div>
                """), unsafe_allow_html=True)

                if cert.file_data and cert.file_name:
                    try:
                        cert_bytes = get_file_bytes(cert.file_data)
                        st.download_button(
                            label="Download Certificate",
                            data=cert_bytes,
                            file_name=cert.file_name,
                            mime="application/pdf",
                            key=f"dl_cert_{cert.id}",
                            use_container_width=True,
                        )
                    except Exception:
                        # Previously failed silently with no button and no
                        # message at all — the student had no way to know
                        # anything was wrong. Now shows a short, honest
                        # notice instead of the file just not appearing.
                        st.caption("⚠️ Download temporarily unavailable — please try again shortly.")
    finally:
        db.close()


def _render_notifications(announcements, registrations):
    st.markdown('<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:18px;">Notifications &amp; Announcements</h3>', unsafe_allow_html=True)

    if not announcements and not registrations:
        st.info("No notifications at this time.")
        return

    recent_updates = sorted(registrations, key=lambda r: r.updated_at, reverse=True)[:5]
    if recent_updates:
        st.markdown(html_block(f"""<p style="font-weight:600;font-size:13.5px;color:var(--ink-700);margin-bottom:10px;">
            {icon("file-text", size=14, color="var(--ink-700)")} Recent Registration Updates</p>"""), unsafe_allow_html=True)
        for reg in recent_updates:
            icon_name, badge_cls, label = _STATUS_META.get(reg.registration_status, ("help-circle", "nmt-badge-neutral", "Unknown"))
            st.markdown(html_block(f"""
            <div style="background:var(--surface-soft);border-radius:10px;padding:12px 16px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">
              <span class="nmt-badge {badge_cls}" style="margin-right:8px;">{icon(icon_name, size=11)} {label}</span>
              <span style="font-size:13px;font-weight:500;color:var(--ink-900);flex:1;margin-left:4px;">{reg.course.title}</span>
              <span style="font-size:11.5px;color:var(--ink-500);">{reg.updated_at.strftime("%b %d, %Y")}</span>
            </div>
            """), unsafe_allow_html=True)

    if announcements:
        st.markdown(html_block(f"""<p style="font-weight:600;font-size:13.5px;color:var(--ink-700);margin:18px 0 10px;">
            {icon("bell", size=14, color="var(--ink-700)")} Latest Announcements</p>"""), unsafe_allow_html=True)
        for ann in announcements:
            st.markdown(html_block(f"""
            <div class="nmt-announce" style="margin-bottom:10px;">
              <div class="nmt-announce-icon">{icon("bell", size=16)}</div>
              <div>
                <div class="nmt-announce-title">{ann["title"]}</div>
                <div class="nmt-announce-text">{ann["content"]}</div>
                <div style="font-size:11px;color:var(--ink-300);margin-top:6px;">{ann["created_at"].strftime("%B %d, %Y")}</div>
              </div>
            </div>
            """), unsafe_allow_html=True)


def _render_profile(user: dict):
    st.markdown('<h3 style="font-family:var(--font-head);font-size:18px;font-weight:700;color:var(--ink-900);margin-bottom:18px;">My Profile</h3>', unsafe_allow_html=True)

    col_photo, col_form = st.columns([1, 2], gap="large")

    with col_photo:
        if user.get("profile_photo"):
            st.markdown(f'<img src="{resolve_src(user["profile_photo"], width=220)}" style="width:110px;height:110px;border-radius:50%;object-fit:cover;border:3px solid var(--blue-100);">', unsafe_allow_html=True)
        else:
            initial = user.get("full_name", "U")[0].upper()
            st.markdown(f'<div class="nmt-profile-avatar">{initial}</div>', unsafe_allow_html=True)

        st.markdown(html_block(f"""
        <div style="margin-top:16px;text-align:center;">
          <div style="font-family:var(--font-head);font-size:15px;font-weight:700;color:var(--ink-900);">{user.get('full_name')}</div>
          <div style="font-size:12.5px;color:var(--ink-500);">{user.get('email')}</div>
        </div>
        """), unsafe_allow_html=True)

    with col_form:
        new_photo = st.file_uploader("Update Profile Photo", type=["png", "jpg", "jpeg"])

        with st.form("profile_form"):
            phone = st.text_input("Phone Number", value=user.get("phone") or "")
            university = st.text_input("University", value=user.get("university") or "")
            department = st.text_input("Department", value=user.get("department") or "")
            semester = st.selectbox(
                "Semester",
                ["", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "Graduate", "Other"],
                index=0
            )

            saved = st.form_submit_button("Save Changes", use_container_width=True, type="primary")

            if saved:
                if new_photo and not check_upload_size(new_photo, 5):
                    st.error("Profile photo is too large. Maximum allowed size is 5MB.")
                    return
                new_photo_url = None
                if new_photo:
                    try:
                        new_photo_url = upload_file(new_photo, folder="nextgen_mechtech/profile_photos")
                    except Exception as e:
                        st.error(f"Profile photo upload failed: {e}")
                        return
                db = get_db_session()
                try:
                    u = db.query(User).filter(User.id == user["id"]).first()
                    if u:
                        u.phone = phone or u.phone
                        u.university = university or u.university
                        u.department = department or u.department
                        u.semester = semester or u.semester
                        if new_photo_url:
                            u.profile_photo = new_photo_url
                        db.commit()

                        st.session_state.user["phone"] = u.phone
                        st.session_state.user["university"] = u.university
                        st.session_state.user["department"] = u.department
                        st.session_state.user["semester"] = u.semester
                        if new_photo:
                            st.session_state.user["profile_photo"] = u.profile_photo

                        flash_message("Profile updated successfully.")
                        st.rerun()
                except Exception as e:
                    db.rollback()
                    st.error(f"Error updating profile: {str(e)}")
                finally:
                    db.close()