import streamlit as st
from utils.helpers import html_block, flash_message
import textwrap

from components.icons import icon
from utils.auth import (
    login_user,
    register_user,
    verify_email_token,
    request_password_reset,
    reset_password_with_token,
)


def render_login():
    params = st.query_params
    action = params.get("action")

    st.markdown(html_block(f"""
    <div class="nmt-page-banner">
      <div class="nmt-page-banner-inner" style="text-align:center;">
        <div class="nmt-page-banner-icon">{icon("lock", size=24, color="#fff")}</div>
        <h1>Student &amp; Admin Access</h1>
        <p style="text-align:center;max-width:560px;margin:0 auto;">Log in to manage your courses, or create a free account to get started.</p>
      </div>
    </div>
    """), unsafe_allow_html=True)

    st.markdown('<div class="nmt-content" style="max-width:480px;">', unsafe_allow_html=True)

    if action == "verify":
        _render_verify(params.get("token", ""))
    elif action == "reset_password":
        _render_reset_password(params.get("token", ""))
    else:
        tab_login, tab_register, tab_forgot = st.tabs(["Log In", "Create Account", "Forgot Password"])
        with tab_login:
            _render_login_form()
        with tab_register:
            _render_register_form()
        with tab_forgot:
            _render_forgot_form()

    st.markdown("</div>", unsafe_allow_html=True)


def _render_login_form():
    st.markdown('<div class="nmt-form-card">', unsafe_allow_html=True)
    st.markdown('<div class="nmt-form-title">Welcome back</div>', unsafe_allow_html=True)
    st.markdown('<div class="nmt-form-subtitle">Log in to access your dashboard.</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="you@email.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Log In", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.error("Please enter both your email and password.")
            else:
                success, message = login_user(email, password)
                if success:
                    flash_message(message)
                    redirect = st.session_state.pop("login_redirect", None)
                    role = st.session_state.user.get("role", "")
                    if role in ("admin", "super_admin", "instructor", "content_manager"):
                        st.session_state.page = "admin"
                    else:
                        st.session_state.page = redirect or "dashboard"
                    st.rerun()
                else:
                    if "verify your email" in message:
                        st.warning(message)
                        st.info("Didn't get the email? Check your **Spam** folder, or use Forgot Password to resend.")
                    else:
                        st.error(message)

    st.markdown("</div>", unsafe_allow_html=True)


def _render_register_form():
    st.markdown('<div class="nmt-form-card">', unsafe_allow_html=True)
    st.markdown('<div class="nmt-form-title">Create your account</div>', unsafe_allow_html=True)
    st.markdown('<div class="nmt-form-subtitle">It only takes a minute — registration is free.</div>', unsafe_allow_html=True)

    with st.form("register_form"):
        full_name = st.text_input("Full Name", placeholder="Muhammad Ali")
        email = st.text_input("Email Address", placeholder="ali@email.com")
        password = st.text_input("Password", type="password", placeholder="At least 8 characters")
        confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
        submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

        if submitted:
            if not all([full_name, email, password, confirm]):
                st.error("Please fill in all fields.")
            elif "@" not in email or "." not in email.split("@")[-1]:
                st.error("Please enter a valid email address.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                success, message = register_user(full_name, email, password)
                if success and message == "registration_pending":
                    st.markdown(html_block(f"""
                    <div style="background:var(--success-bg);border:1.5px solid var(--success-line);border-radius:var(--radius-md);padding:20px;margin-top:8px;">
                      <div style="display:flex;align-items:center;gap:8px;font-weight:700;color:var(--success-tx);margin-bottom:6px;">{icon("check-circle", size=16, color="var(--success-tx)")} Registration Successful!</div>
                      <div style="font-size:13.5px;color:var(--ink-700);">
                        Please check your email to verify your account.<br>
                        <strong>If you don't find the email, please check your Spam folder.</strong><br><br>
                        You will not be able to log in until your email is verified.
                      </div>
                    </div>
                    """), unsafe_allow_html=True)
                elif not success:
                    st.error(message)

    st.markdown("</div>", unsafe_allow_html=True)


def _render_forgot_form():
    st.markdown('<div class="nmt-form-card">', unsafe_allow_html=True)
    st.markdown('<div class="nmt-form-title">Reset your password</div>', unsafe_allow_html=True)
    st.markdown('<div class="nmt-form-subtitle">We\'ll email you a secure link to set a new password.</div>', unsafe_allow_html=True)

    with st.form("forgot_form"):
        email = st.text_input("Email Address", placeholder="you@email.com")
        submitted = st.form_submit_button("Send Reset Link", use_container_width=True, type="primary")

        if submitted:
            if not email:
                st.error("Please enter your email address.")
            else:
                success, message = request_password_reset(email)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    st.markdown("</div>", unsafe_allow_html=True)


def _render_verify(token: str):
    st.markdown('<div class="nmt-form-card" style="text-align:center;">', unsafe_allow_html=True)
    if not token:
        st.error("Missing verification token.")
    else:
        success, message = verify_email_token(token)
        if success:
            st.markdown(html_block(f"""
            <div style="background:var(--success-bg);border:1.5px solid var(--success-line);border-radius:var(--radius-md);padding:24px;text-align:center;">
              <div style="font-size:36px;margin-bottom:10px;">{icon("check-circle", size=36, color="var(--success-tx)")}</div>
              <div style="font-weight:700;font-size:18px;color:var(--success-tx);margin-bottom:6px;">Email Verified!</div>
              <div style="color:var(--ink-500);font-size:13.5px;">{message}</div>
            </div>
            """), unsafe_allow_html=True)
        else:
            st.error(message)

    if st.button("Go to Login", use_container_width=True, type="primary"):
        st.query_params.clear()
        st.session_state.page = "login"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _render_reset_password(token: str):
    st.markdown('<div class="nmt-form-card">', unsafe_allow_html=True)
    st.markdown('<div class="nmt-form-title">Set a new password</div>', unsafe_allow_html=True)

    if not token:
        st.error("Missing or invalid reset token.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    with st.form("reset_password_form"):
        new_password = st.text_input("New Password", type="password", placeholder="At least 8 characters")
        confirm = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Update Password", use_container_width=True, type="primary")

        if submitted:
            if len(new_password) < 8:
                st.error("Password must be at least 8 characters long.")
            elif new_password != confirm:
                st.error("Passwords do not match.")
            else:
                success, message = reset_password_with_token(token, new_password)
                if success:
                    st.success(message)
                    st.query_params.clear()
                else:
                    st.error(message)

    st.markdown("</div>", unsafe_allow_html=True)
