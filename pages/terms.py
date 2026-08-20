"""
Terms of Service page.

Static, professional legal page that follows the same visual language as the
rest of the site (banner + .nmt-content sections).
"""
import streamlit as st

from components.icons import icon
from utils.helpers import get_all_settings, html_block


def render_terms():
    settings   = get_all_settings()
    site_name  = settings.get("site_name", "NextGen MechTech Academy")
    contact_email = settings.get("footer_email", settings.get("contact_email", "support.nextgenmechtech@gmail.com"))
    last_updated  = settings.get("terms_updated", "July 2026")

    # ─── Banner ──────────────────────────────────────────────────────────
    st.markdown(html_block(f"""
    <div class="nmt-page-banner nmt-page-enter">
      <div class="nmt-page-banner-inner" style="text-align:center;">
        <div class="nmt-page-banner-icon">{icon("file-text", size=24, color="#fff")}</div>
        <h1>Terms of Service</h1>
        <p style="text-align:center;max-width:560px;margin:0 auto;">
          The terms that govern your use of {site_name}.
        </p>
      </div>
    </div>
    """), unsafe_allow_html=True)

    st.markdown('<div class="nmt-content" style="max-width:880px;">', unsafe_allow_html=True)

    st.markdown(html_block(f"""
    <div style="color:var(--ink-500);font-size:13px;margin-bottom:28px;">
      Last updated: {last_updated}
    </div>
    """), unsafe_allow_html=True)

    sections = [
        ("file-text", "Acceptance of Terms",
         f"By accessing or using {site_name}'s website, enrolling in a course, or applying for an instructor "
         f"position through our platform, you agree to be bound by these Terms of Service. If you do not "
         f"agree with any part of these terms, please do not use our services."),
        ("graduation-cap", "Enrollment & Courses",
         "Course enrollment is confirmed once payment (where applicable) has been received and verified. "
         "Course content, schedules, and instructors are subject to change, and we will make reasonable "
         "efforts to notify enrolled students of any material changes."),
        ("award", "Certificates",
         "Certificates are issued upon successful completion of a course's requirements as determined by the "
         "academy. Certificates can be verified using the reference number through our Certificate "
         "Verification page. Misrepresentation or alteration of an issued certificate is strictly prohibited."),
        ("dollar-sign", "Payments & Refunds",
         "Fees for paid courses must be submitted using one of our configured payment methods. Refund "
         "eligibility, where offered, will be communicated at the time of enrollment or upon request to our "
         "support team."),
        ("users", "Instructor Applications",
         "Submitting an instructor application does not guarantee an offer to teach. All applications are "
         "reviewed at the academy's discretion, and applicants will be contacted regarding the outcome."),
        ("shield", "Acceptable Use",
         "You agree not to misuse the platform, including attempting to gain unauthorized access to accounts "
         "or systems, submitting false information, or using the site for any unlawful purpose."),
        ("info", "Limitation of Liability",
         f"{site_name} provides its educational content and services on an \"as is\" basis and makes "
         f"reasonable efforts to ensure accuracy, but does not guarantee uninterrupted or error-free access "
         f"to the platform."),
        ("clock", "Changes to These Terms",
         "We may revise these Terms of Service from time to time. Continued use of the site after changes "
         "are posted constitutes acceptance of the revised terms."),
    ]

    for ic, title, text in sections:
        st.markdown(html_block(f"""
        <div class="nmt-feature nmt-fade-in" style="padding:26px 26px;margin-bottom:16px;">
          <div class="nmt-feature-icon">{icon(ic, size=20)}</div>
          <h3>{title}</h3>
          <p>{text}</p>
        </div>
        """), unsafe_allow_html=True)

    st.markdown(html_block(f"""
    <div style="margin-top:32px;background:linear-gradient(135deg,var(--navy-900),var(--blue-600));
        border-radius:var(--radius-xl);padding:32px;color:#fff;">
      <h3 style="font-family:var(--font-head);font-size:18px;font-weight:800;margin-bottom:10px;">Questions about these terms?</h3>
      <p style="color:rgba(255,255,255,0.78);font-size:13.5px;margin-bottom:14px;">
        Reach out and we'll be happy to clarify anything in our Terms of Service.
      </p>
      <div style="background:rgba(255,255,255,0.08);border-radius:10px;padding:14px 16px;display:inline-block;">
        <div class="contact-line" style="color:#fff;">{icon("mail", size=13, color="#fff")}
          <a href="mailto:{contact_email}" style="color:#fff;text-decoration:underline;">{contact_email}</a>
        </div>
      </div>
    </div>
    """), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
