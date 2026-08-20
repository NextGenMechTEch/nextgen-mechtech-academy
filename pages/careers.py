import json
import streamlit as st
import textwrap

from components.icons import icon
from database.connection import get_db_session
from database.models import TutorApplication, JobOpening
from utils.helpers import get_all_settings, html_block, is_valid_email, check_upload_size
from utils.cloudinary_service import upload_file
from utils.email_service import send_tutor_application_received, send_email, _base_template, ADMIN_EMAIL, CAREERS_EMAIL
from pages.cms_admin import get_cms_section


def render_careers():
    settings = get_all_settings()
    banner_heading   = settings.get("careers_banner_heading", "Join Our Team")
    banner_sub       = settings.get("careers_banner_sub",
        "Passionate about teaching technology? We're always looking for talented instructors to join our growing academy.")
    section_heading  = settings.get("careers_section_heading", "Shape the Next Generation of Engineers")
    section_sub      = settings.get("careers_section_sub",
        "At NextGen MechTech Academy, our instructors are the backbone of our success. "
        "We're looking for industry professionals who want to share their expertise and make a real difference.")
    form_heading     = settings.get("careers_form_heading", "Apply Now")
    form_sub         = settings.get("careers_form_sub", "Fill in the form below and we'll be in touch.")
    success_msg      = settings.get("careers_success_msg",
        "Thank you for your application! We'll review it and get back to you within 3–5 business days.")

    st.markdown(html_block(f"""
    <div class="nmt-page-banner nmt-page-enter">
      <div class="nmt-page-banner-inner" style="text-align:center;">
        <div class="nmt-page-banner-icon">{icon("briefcase", size=24, color="#fff")}</div>
        <h1>{banner_heading}</h1>
        <p style="text-align:center;max-width:560px;margin:0 auto;">{banner_sub}</p>
      </div>
    </div>
    """), unsafe_allow_html=True)

    st.markdown('<div class="nmt-content">', unsafe_allow_html=True)

    # ─── Perks Section ───────────────────────────────────────────────────
    perks_sec = get_cms_section("careers", "perks")
    try:
        PERKS = json.loads(perks_sec["content"]) if perks_sec["content"] else []
    except:
        PERKS = []
    if not PERKS:
        PERKS = [
            {"icon": "dollar-sign", "title": "Competitive Compensation", "desc": "Earn well for your time and expertise"},
            {"icon": "clock",       "title": "Flexible Scheduling",       "desc": "Teach at times that suit your schedule"},
            {"icon": "map-pin",     "title": "Online & On-site",          "desc": "Teach from anywhere or in our Lahore studio"},
            {"icon": "trending-up", "title": "Grow Your Brand",           "desc": "Build your profile and reach thousands of students"},
            {"icon": "handshake",   "title": "Supportive Team",           "desc": "Work with a passionate, collaborative team"},
        ]

    col_info, col_form = st.columns([1, 1.5], gap="large")

    with col_info:
        st.markdown(html_block(f"""
        <div style="padding-right:16px;">
          <div class="nmt-eyebrow">{icon("users", size=13, color="var(--amber-600)")} Become an Instructor</div>
          <h2 class="nmt-h2" style="margin-bottom:16px;">{section_heading}</h2>
          <p style="color:var(--ink-500);line-height:1.75;font-size:14.5px;margin-bottom:24px;">{section_sub}</p>
        </div>
        """), unsafe_allow_html=True)

        for perk in PERKS:
            st.markdown(html_block(f"""
            <div style="display:flex;gap:14px;margin-bottom:16px;align-items:flex-start;">
              <div class="nmt-info-icon" style="width:38px;height:38px;flex-shrink:0;">{icon(perk.get('icon','star'), size=16)}</div>
              <div>
                <div style="font-weight:600;color:var(--ink-900);font-size:13.5px;">{perk.get('title','')}</div>
                <div style="color:var(--ink-500);font-size:12.5px;margin-top:2px;">{perk.get('desc','')}</div>
              </div>
            </div>
            """), unsafe_allow_html=True)

    with col_form:
        st.markdown(html_block(f"""
        <div class="nmt-form-card" style="margin-bottom:20px;">
          <div class="nmt-form-title">{form_heading}</div>
          <div class="nmt-form-subtitle">{form_sub}</div>
        </div>
        """), unsafe_allow_html=True)

        with st.form("tutor_application_form"):
            col1, col2 = st.columns(2)
            with col1:
                name  = st.text_input("Full Name *")
                email = st.text_input("Email *")
            with col2:
                phone  = st.text_input("Phone Number *")
                skills = st.text_input("Areas of Expertise *", placeholder="e.g. Python, SOLIDWORKS, Arduino")
            experience = st.text_area("Teaching / Industry Experience *", height=100,
                placeholder="Briefly describe your background and any teaching experience...")
            message = st.text_area("Why do you want to join NextGen MechTech?", height=80)
            resume  = st.file_uploader("Upload Resume/CV (PDF optional)", type=["pdf"])

            submitted = st.form_submit_button("Submit Application", type="primary", use_container_width=True)
            if submitted:
                if not all([name, email, phone, skills, experience]):
                    st.error("Please fill in all required fields.")
                elif not is_valid_email(email):
                    st.error("Please enter a valid email address.")
                elif not check_upload_size(resume, 10):
                    st.error("Resume file is too large. Maximum allowed size is 10MB.")
                else:
                    resume_data = None
                    resume_name = None
                    if resume:
                        try:
                            resume_data = upload_file(resume, folder="nextgen_mechtech/resumes")
                            resume_name = resume.name
                        except Exception as e:
                            st.error(f"Resume upload failed: {e}")
                            st.stop()

                    db = get_db_session()
                    try:
                        db.add(TutorApplication(
                            name=name, email=email, phone=phone,
                            skills=skills, experience=experience,
                            message=message, resume_data=resume_data, resume_name=resume_name
                        ))
                        db.commit()
                        try:
                            send_tutor_application_received(name, email)
                        except:
                            pass
                        st.success(success_msg)
                    except Exception as e:
                        db.rollback()
                        st.error(f"Submission failed: {e}")
                    finally:
                        db.close()

    # ─── Job Openings Section ─────────────────────────────────────────────
    db = get_db_session()
    try:
        jobs        = db.query(JobOpening).filter(JobOpening.is_internship == False, JobOpening.is_open == True).order_by(JobOpening.display_order).all()
        internships = db.query(JobOpening).filter(JobOpening.is_internship == True,  JobOpening.is_open == True).order_by(JobOpening.display_order).all()
    finally:
        db.close()

    if jobs or internships:
        st.markdown("<hr style='margin:36px 0 28px;border-color:var(--line);'>", unsafe_allow_html=True)

    if jobs:
        st.markdown(html_block(f"""
        <div class="nmt-eyebrow">{icon("briefcase", size=13, color="var(--amber-600)")} Open Positions</div>
        <h2 class="nmt-h2" style="margin-bottom:20px;">Current Job Openings</h2>
        """), unsafe_allow_html=True)
        for job in jobs:
            deadline_str = ""
            if job.deadline:
                deadline_str = f" · Deadline: {job.deadline.strftime('%b %d, %Y')}"
            with st.expander(f"{job.title} — {job.employment_type}{deadline_str}"):
                st.markdown(html_block(f"""
                <div class="nmt-job-card" style="margin-bottom:0;border:none;padding:0;">
                  <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px;">
                    <span style="font-size:12px;background:var(--blue-50);border:1px solid var(--blue-100);color:var(--blue-600);padding:3px 10px;border-radius:20px;">{icon("map-pin",size=11)} {job.location}</span>
                    {f'<span style="font-size:12px;background:var(--surface-soft);border:1px solid var(--line);color:var(--ink-600);padding:3px 10px;border-radius:20px;">{job.department}</span>' if job.department else ''}
                  </div>
                  <p style="font-size:13.5px;color:var(--ink-700);line-height:1.75;margin-bottom:12px;">{job.description}</p>
                  {f'<div style="font-size:13px;color:var(--ink-500);margin-bottom:6px;"><strong>Requirements:</strong> {job.requirements}</div>' if job.requirements else ''}
                  {f'<div style="font-size:13px;color:var(--ink-500);"><strong>Benefits:</strong> {job.benefits}</div>' if job.benefits else ''}
                </div>
                """), unsafe_allow_html=True)

    if internships:
        st.markdown(html_block(f"""
        <div class="nmt-eyebrow" style="margin-top:28px;">{icon("star", size=13, color="var(--amber-600)")} Internships</div>
        <h2 class="nmt-h2" style="margin-bottom:20px;">Internship Opportunities</h2>
        """), unsafe_allow_html=True)
        for intern in internships:
            with st.expander(f"{intern.title}"):
                st.markdown(html_block(f"""
                <p style="font-size:13.5px;color:var(--ink-700);line-height:1.75;">{intern.description}</p>
                {f'<div style="font-size:13px;color:var(--ink-500);margin-top:8px;"><strong>Requirements:</strong> {intern.requirements}</div>' if intern.requirements else ''}
                """), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
