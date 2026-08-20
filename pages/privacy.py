"""
Privacy Policy page.

Static, professional legal page that follows the same visual language as the
rest of the site (banner + .nmt-content sections). Contact details are pulled
from WebsiteSettings so the page always reflects whatever the Admin Panel has
configured, without needing any code changes.
"""
import streamlit as st

from components.icons import icon
from utils.helpers import get_all_settings, html_block


def render_privacy():
    settings   = get_all_settings()
    site_name  = settings.get("site_name", "NextGen MechTech Academy")
    contact_email = settings.get("footer_email", settings.get("contact_email", "support.nextgenmechtech@gmail.com"))
    contact_phone = settings.get("footer_phone", settings.get("contact_phone", ""))
    contact_addr  = settings.get("footer_address", settings.get("contact_address", "Lahore, Pakistan"))
    last_updated  = settings.get("privacy_updated", "July 2026")

    # ─── Banner ──────────────────────────────────────────────────────────
    st.markdown(html_block(f"""
    <div class="nmt-page-banner nmt-page-enter">
      <div class="nmt-page-banner-inner" style="text-align:center;">
        <div class="nmt-page-banner-icon">{icon("shield", size=24, color="#fff")}</div>
        <h1>Privacy Policy</h1>
        <p style="text-align:center;max-width:560px;margin:0 auto;">
          How {site_name} collects, uses, and protects your information.
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
        ("info", "Information We Collect",
         f"When you register for a course, apply for a job, verify a certificate, or contact us through "
         f"{site_name}, we may collect personal details such as your name, email address, phone number, "
         f"educational background, and payment details necessary to process enrollments. We also collect "
         f"basic technical information (such as browser type and pages visited) to help us improve the "
         f"platform."),
        ("target", "How We Use Your Information",
         "We use the information you provide to create and manage your student account, process course "
         "enrollments and payments, issue and verify certificates, respond to enquiries and job applications, "
         "and send important updates about your courses. We do not use your personal data for any purpose "
         "beyond operating and improving the academy's services."),
        ("shield", "How We Protect Your Data",
         "We apply reasonable technical and organizational safeguards to protect your personal information "
         "from unauthorized access, alteration, disclosure, or destruction. Access to student and applicant "
         "records is restricted to authorized staff who need it to perform their role."),
        ("users", "Sharing of Information",
         "We do not sell, rent, or trade your personal information to third parties. Limited information may "
         "be shared with trusted service providers (for example, payment processors or email delivery "
         "services) strictly to the extent needed to provide our services, and only under confidentiality "
         "obligations."),
        ("award", "Certificates & Public Verification",
         "Certificate verification is a public-facing feature. When you look up a certificate using its "
         "reference number, we display only the minimal information needed to confirm its authenticity (such "
         "as the student's name, course title, and issue date)."),
        ("lock", "Cookies & Session Data",
         "We use session data to keep you logged in and to remember your preferences while you browse the "
         "site. This information is used solely to operate the platform and is not shared with advertisers."),
        ("file-text", "Your Rights",
         "You may request access to, correction of, or deletion of your personal data at any time by "
         "contacting us using the details below. We will respond to all reasonable requests within a "
         "reasonable timeframe."),
        ("clock", "Changes to This Policy",
         "We may update this Privacy Policy from time to time to reflect changes in our practices or for "
         "legal, operational, or regulatory reasons. The \"Last updated\" date above indicates when this "
         "policy was last revised."),
    ]

    for ic, title, text in sections:
        st.markdown(html_block(f"""
        <div class="nmt-feature nmt-fade-in" style="padding:26px 26px;margin-bottom:16px;">
          <div class="nmt-feature-icon">{icon(ic, size=20)}</div>
          <h3>{title}</h3>
          <p>{text}</p>
        </div>
        """), unsafe_allow_html=True)

    contact_lines = f'<div class="contact-line" style="color:var(--ink-700);">{icon("mail", size=13, color="var(--blue-600)")} <a href="mailto:{contact_email}" style="color:var(--blue-600);text-decoration:none;">{contact_email}</a></div>'
    if contact_phone:
        contact_lines += f'<div class="contact-line" style="color:var(--ink-700);margin-top:6px;">{icon("phone", size=13, color="var(--blue-600)")} <a href="tel:{"".join(ch for ch in contact_phone if ch.isdigit() or ch == "+")}" style="color:var(--blue-600);text-decoration:none;">{contact_phone}</a></div>'

    st.markdown(html_block(f"""
    <div style="margin-top:32px;background:linear-gradient(135deg,var(--navy-900),var(--blue-600));
        border-radius:var(--radius-xl);padding:32px;color:#fff;">
      <h3 style="font-family:var(--font-head);font-size:18px;font-weight:800;margin-bottom:10px;">Questions about this policy?</h3>
      <p style="color:rgba(255,255,255,0.78);font-size:13.5px;margin-bottom:14px;">
        If you have any questions about how {site_name} handles your data, reach out to us anytime.
      </p>
      <div style="background:rgba(255,255,255,0.08);border-radius:10px;padding:14px 16px;display:inline-block;">
        {contact_lines}
      </div>
    </div>
    """), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
