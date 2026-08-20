import streamlit as st
import textwrap

from components.icons import icon
from database.connection import get_db_session
from database.models import ContactMessage
from utils.helpers import get_all_settings, html_block, is_valid_email
from utils.email_service import send_contact_confirmation, send_email, _base_template, SUPPORT_EMAIL


def render_contact():
    settings = get_all_settings()

    banner_heading   = settings.get("contact_banner_heading", "Contact Us")
    banner_sub       = settings.get("contact_banner_sub", "Have a question? We'd love to hear from you. Send us a message and we'll respond within 24 hours.")
    section_heading  = settings.get("contact_section_heading", "We're Here to Help")
    eyebrow          = settings.get("contact_eyebrow", "Get in Touch")
    success_msg      = settings.get("contact_success_msg", "Your message has been sent! We'll get back to you within 24 hours.")
    form_heading     = settings.get("contact_form_heading", "Send a Message")
    form_btn         = settings.get("contact_form_btn", "Send Message")

    contact_email    = settings.get("contact_email",   "support.nextgenmechtech@gmail.com")
    careers_email    = settings.get("careers_email",   "careers.nextgenmechtech@gmail.com")
    contact_phone    = settings.get("contact_phone",   "")
    contact_address  = settings.get("contact_address", "Lahore, Pakistan")
    office_hours     = settings.get("office_hours",    "Mon–Sat: 9:00 AM – 6:00 PM")
    facebook_url     = settings.get("facebook_url",    "https://facebook.com/nextgenmechtech")
    instagram_url    = settings.get("instagram_url",   "https://instagram.com/nextgenmechtech")
    linkedin_url     = settings.get("linkedin_url",    "https://linkedin.com/company/nextgenmechtech")
    youtube_url      = settings.get("youtube_url",     "https://youtube.com/nextgenmechtech")

    st.markdown(html_block(f"""
    <div class="nmt-page-banner nmt-page-enter">
      <div class="nmt-page-banner-inner" style="text-align:center;">
        <div class="nmt-page-banner-icon">{icon("mail", size=24, color="#fff")}</div>
        <h1>{banner_heading}</h1>
        <p style="text-align:center;max-width:560px;margin:0 auto;">{banner_sub}</p>
      </div>
    </div>
    """), unsafe_allow_html=True)

    st.markdown('<div class="nmt-content">', unsafe_allow_html=True)
    col_info, col_form = st.columns([1, 1.5], gap="large")

    with col_info:
        contact_items = [
            ("mail",      "Email",         contact_email,  "General inquiries & support"),
            ("briefcase", "Careers Email", careers_email,  "Job & tutor applications"),
            ("map-pin",   "Location",      contact_address,"Main campus"),
            ("clock",     "Office Hours",  office_hours,   "PKT (Pakistan Standard Time)"),
        ]
        if contact_phone:
            contact_items.insert(2, ("phone", "Phone", contact_phone, "Call us directly"))

        st.markdown(html_block(f"""
        <div class="nmt-eyebrow">{icon("phone", size=13, color="var(--amber-600)")} {eyebrow}</div>
        <h2 class="nmt-h2" style="margin-bottom:22px;">{section_heading}</h2>
        """), unsafe_allow_html=True)

        for icon_name, label, value, note in contact_items:
            st.markdown(html_block(f"""
            <div class="nmt-info-row">
              <div class="nmt-info-icon">{icon(icon_name, size=18)}</div>
              <div>
                <div class="nmt-info-label">{label}</div>
                <div class="nmt-info-value">{value}</div>
                <div class="nmt-info-note">{note}</div>
              </div>
            </div>
            """), unsafe_allow_html=True)

        # Social links
        social_buttons = []
        if facebook_url:
            social_buttons.append((facebook_url, "#1877F2", "facebook"))
        if instagram_url:
            social_buttons.append((instagram_url, "#E4405F", "instagram"))
        if linkedin_url:
            social_buttons.append((linkedin_url,  "#0A66C2", "linkedin"))
        if youtube_url:
            social_buttons.append((youtube_url,   "#FF0000", "youtube"))

        if social_buttons:
            social_html = "".join(
                f'<a class="nmt-social-btn" style="background:{color}" href="{url}" target="_blank" rel="noopener">'
                f'{icon(ic, size=16, color="#fff")}</a>'
                for url, color, ic in social_buttons
            )
            st.markdown(html_block(f"""
            <div style="margin-top:22px;">
              <div style="font-size:12.5px;font-weight:700;color:var(--ink-500);text-transform:uppercase;letter-spacing:0.07em;margin-bottom:12px;">Follow Us</div>
              <div class="nmt-social-row">{social_html}</div>
            </div>
            """), unsafe_allow_html=True)

    with col_form:
        st.markdown(html_block(f"""
        <div class="nmt-form-card" style="margin-bottom:20px;">
          <div class="nmt-form-title">{form_heading}</div>
        </div>
        """), unsafe_allow_html=True)

        with st.form("contact_form"):
            col1, col2 = st.columns(2)
            with col1:
                name    = st.text_input("Your Name *")
                email   = st.text_input("Your Email *")
            with col2:
                subject = st.text_input("Subject *")
            message = st.text_area("Message *", height=140, placeholder="How can we help you?")

            if st.form_submit_button(form_btn, type="primary", use_container_width=True):
                if not all([name, email, subject, message]):
                    st.error("Please fill in all required fields.")
                elif not is_valid_email(email):
                    st.error("Please enter a valid email address.")
                else:
                    db = get_db_session()
                    try:
                        db.add(ContactMessage(name=name, email=email, subject=subject, message=message))
                        db.commit()
                        try:
                            send_contact_confirmation(name, email)
                        except:
                            pass
                        st.success(success_msg)
                    except Exception as e:
                        db.rollback()
                        st.error(f"Failed to send: {e}")
                    finally:
                        db.close()

    # Google Maps embed if configured
    map_url = settings.get("map_embed_url", "")
    if map_url:
        st.markdown(html_block(f"""
        <div style="margin-top:32px;">
          <iframe src="{map_url}" width="100%" height="300" style="border:0;border-radius:var(--radius-lg);" allowfullscreen="" loading="lazy"></iframe>
        </div>
        """), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
