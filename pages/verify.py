import streamlit as st
import textwrap

from components.icons import icon
from database.connection import get_db_session
from database.models import Certificate, User, Course
from utils.helpers import get_all_settings, html_block
from sqlalchemy.orm import joinedload


def render_verify():
    settings = get_all_settings()

    banner_heading  = settings.get("cert_banner_heading",  "Certificate Verification")
    banner_sub      = settings.get("cert_banner_sub",
        "Verify the authenticity of any NextGen MechTech Academy certificate instantly.")
    form_heading    = settings.get("cert_form_heading",    "Enter Certificate ID")
    placeholder     = settings.get("cert_placeholder",     "e.g. NMT-XXXXXXXXXX")
    success_msg_tpl = settings.get("cert_success_msg",     "Certificate verified successfully!")
    error_msg       = settings.get("cert_error_msg",       "No certificate found with that ID.")
    help_text       = settings.get("cert_help_text",
        "Your certificate ID starts with NMT- followed by 10 characters. "
        "You can find it printed on your certificate or in your confirmation email.")

    st.markdown(html_block(f"""
    <div class="nmt-page-banner nmt-page-enter">
      <div class="nmt-page-banner-inner" style="text-align:center;">
        <div class="nmt-page-banner-icon">{icon("award", size=24, color="#fff")}</div>
        <h1>{banner_heading}</h1>
        <p style="text-align:center;max-width:560px;margin:0 auto;">{banner_sub}</p>
      </div>
    </div>
    """), unsafe_allow_html=True)

    st.markdown('<div class="nmt-content">', unsafe_allow_html=True)

    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        st.markdown(html_block(f"""
        <div class="nmt-form-card">
          <div class="nmt-form-title">{icon("search", size=17)} {form_heading}</div>
        </div>
        """), unsafe_allow_html=True)

        with st.form("verify_form"):
            cert_id_input = st.text_input(
                "Certificate ID",
                placeholder=placeholder,
                label_visibility="collapsed"
            )
            submitted = st.form_submit_button("Verify Certificate", type="primary", use_container_width=True)

        if submitted:
            if not cert_id_input.strip():
                st.error("Please enter a certificate ID.")
            else:
                cert_id = cert_id_input.strip().upper()
                db = get_db_session()
                try:
                    cert = (db.query(Certificate)
                        .options(joinedload(Certificate.student), joinedload(Certificate.course))
                        .filter(Certificate.certificate_id == cert_id)
                        .first())
                finally:
                    db.close()

                if not cert:
                    st.error(f" {error_msg}")
                    st.caption(f"Searched for: **{cert_id}**")
                elif cert.is_revoked:
                    st.warning(f" This certificate has been revoked.")
                    if cert.revoke_reason:
                        st.caption(f"Reason: {cert.revoke_reason}")
                else:
                    st.markdown(html_block(f"""
                    <div class="nmt-verify-badge" style="margin-bottom:20px;font-size:16px;padding:14px 24px;">
                      {icon("check-circle", size=20, color="var(--success-tx)")} {success_msg_tpl}
                    </div>
                    """), unsafe_allow_html=True)

                    # Certificate details card
                    completion = cert.completion_date.strftime("%B %d, %Y") if cert.completion_date else "N/A"
                    issued     = cert.issued_at.strftime("%B %d, %Y") if cert.issued_at else "N/A"

                    st.markdown(html_block(f"""
                    <div class="nmt-cert-detail-card" style="background:linear-gradient(135deg,var(--navy-900),var(--blue-600));
                        border-radius:var(--radius-xl);padding:36px;color:#fff;margin-top:8px;">
                      <div style="display:flex;align-items:center;gap:14px;margin-bottom:24px;">
                        <div style="width:52px;height:52px;border-radius:14px;background:rgba(255,255,255,0.15);
                            display:flex;align-items:center;justify-content:center;">
                          {icon("award", size=26, color="#FBBF24")}
                        </div>
                        <div>
                          <div style="font-family:var(--font-head);font-size:20px;font-weight:800;">Certificate of Completion</div>
                          <div style="font-size:13px;color:rgba(255,255,255,0.7);">NextGen MechTech Academy</div>
                        </div>
                      </div>

                      <div class="nmt-cert-detail-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
                        <div>
                          <div style="font-size:11px;color:rgba(255,255,255,0.55);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Certificate ID</div>
                          <div style="font-family:monospace;font-size:15px;font-weight:700;color:#FBBF24;word-break:break-all;">{cert.certificate_id}</div>
                        </div>
                        <div>
                          <div style="font-size:11px;color:rgba(255,255,255,0.55);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Student Name</div>
                          <div style="font-size:15px;font-weight:700;">{cert.student.full_name if cert.student else "N/A"}</div>
                        </div>
                        <div>
                          <div style="font-size:11px;color:rgba(255,255,255,0.55);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Course</div>
                          <div style="font-size:14px;font-weight:600;">{cert.course.title if cert.course else "N/A"}</div>
                        </div>
                        <div>
                          <div style="font-size:11px;color:rgba(255,255,255,0.55);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Category</div>
                          <div style="font-size:14px;color:rgba(255,255,255,0.8);">{cert.course.category if cert.course else "N/A"}</div>
                        </div>
                        <div>
                          <div style="font-size:11px;color:rgba(255,255,255,0.55);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Completion Date</div>
                          <div style="font-size:14px;color:rgba(255,255,255,0.8);">{completion}</div>
                        </div>
                        <div>
                          <div style="font-size:11px;color:rgba(255,255,255,0.55);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Issue Date</div>
                          <div style="font-size:14px;color:rgba(255,255,255,0.8);">{issued}</div>
                        </div>
                        {f'<div><div style="font-size:11px;color:rgba(255,255,255,0.55);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Instructor</div><div style="font-size:14px;color:rgba(255,255,255,0.8);">{cert.instructor_name}</div></div>' if cert.instructor_name else ''}
                      </div>
                    </div>
                    """), unsafe_allow_html=True)

                    if cert.file_data:
                        from utils.cloudinary_service import get_file_bytes
                        st.download_button(
                            "Download Certificate",
                            data=get_file_bytes(cert.file_data),
                            file_name=cert.file_name or f"certificate_{cert.certificate_id}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

        # Help section
        st.markdown(html_block(f"""
        <div style="margin-top:28px;background:var(--surface-soft);border:1px solid var(--line);
            border-radius:var(--radius-md);padding:18px 22px;">
          <div style="font-weight:700;color:var(--ink-900);font-size:13.5px;margin-bottom:8px;">
            {icon("help-circle", size=14)} Where to Find Your Certificate ID
          </div>
          <p style="font-size:13px;color:var(--ink-500);line-height:1.7;margin:0;">{help_text}</p>
        </div>
        """), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)