from database.connection import get_db_session, init_db
from database.models import (
    Course, WebsiteSettings, User, UserRole, Announcement,
    Instructor, Certificate, EmailTemplate
)
import bcrypt
import secrets
import string


def _gen_cert_id():
    chars = string.ascii_uppercase + string.digits
    return "NMT-" + "".join(secrets.choice(chars) for _ in range(10))


def seed_instructors(db):
    from database.models import Instructor
    existing = db.query(Instructor).count()
    if existing > 0:
        return
    instructors = [
        {"name": "Engr. Ahmed Raza", "designation": "Python & Machine Learning Instructor",
         "qualifications": "MS Computer Science, NUST", "experience": "5+ Years",
         "bio": "Ahmed brings real-world ML project experience to every class, with a focus on practical data science and Python automation.",
         "display_order": 1},
        {"name": "Engr. Sara Khan", "designation": "SOLIDWORKS & CAD Design Instructor",
         "qualifications": "BE Mechanical, UET Lahore", "experience": "4+ Years",
         "bio": "Sara specialises in mechanical CAD and has worked with top engineering firms across Pakistan.",
         "display_order": 2},
        {"name": "Engr. Bilal Chaudhry", "designation": "Arduino & PCB Design Instructor",
         "qualifications": "BE Electronics, COMSATS", "experience": "6+ Years",
         "bio": "Bilal has designed PCBs for consumer electronics and IoT products sold internationally.",
         "display_order": 3},
        {"name": "Dr. Imran Malik", "designation": "AI & Prompt Engineering Instructor",
         "qualifications": "PhD Computer Science", "experience": "10+ Years",
         "bio": "Dr. Malik is a published researcher in AI and holds a PhD with specialisation in neural architectures.",
         "display_order": 4},
    ]
    for d in instructors:
        db.add(Instructor(**d))
    db.commit()
    print("Instructors seeded.")


def seed_courses(db):
    existing = db.query(Course).count()
    if existing > 0:
        return

    courses = [
        {"title": "Python Programming", "description": "Master Python from fundamentals to advanced concepts. Learn data structures, OOP, file handling, and build real-world projects.",
         "category": "Programming", "duration": "8 Weeks", "level": "Beginner to Intermediate", "fee": 4999,
         "image_url": "https://images.unsplash.com/photo-1526379879527-8559ecfcaec0?w=400&h=250&fit=crop",
         "what_you_learn": '["Python syntax and data types","OOP and modules","File handling","Real-world projects"]',
         "certificate_available": True, "is_featured": True},
        {"title": "C Programming", "description": "Build a strong foundation in C programming. Cover pointers, memory management, data structures, and embedded applications.",
         "category": "Programming", "duration": "6 Weeks", "level": "Beginner", "fee": 3999,
         "image_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=400&h=250&fit=crop",
         "certificate_available": True},
        {"title": "MATLAB & Simulink", "description": "Learn MATLAB for numerical computing, data analysis, signal processing, and Simulink for model-based design.",
         "category": "Engineering Tools", "duration": "8 Weeks", "level": "Intermediate", "fee": 5999,
         "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=250&fit=crop",
         "certificate_available": True},
        {"title": "SOLIDWORKS", "description": "Master 3D CAD design with SOLIDWORKS. Create professional parts, assemblies, and engineering drawings.",
         "category": "Engineering Tools", "duration": "10 Weeks", "level": "Beginner to Advanced", "fee": 6999,
         "image_url": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=400&h=250&fit=crop",
         "certificate_available": True, "is_featured": True},
        {"title": "Arduino & Embedded Systems", "description": "Dive into embedded systems with Arduino. Build IoT devices, sensor integrations, motor control systems.",
         "category": "Electronics", "duration": "8 Weeks", "level": "Beginner to Intermediate", "fee": 4999,
         "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&h=250&fit=crop",
         "certificate_available": True},
        {"title": "Internet of Things (IoT)", "description": "Design and deploy IoT solutions using ESP32, MQTT, cloud platforms, and sensor networks.",
         "category": "Electronics", "duration": "10 Weeks", "level": "Intermediate", "fee": 5999,
         "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=250&fit=crop",
         "certificate_available": True},
        {"title": "PCB Design & Manufacturing", "description": "Learn PCB design using industry tools. From schematic to layout, Gerber files, and manufacturers.",
         "category": "Electronics", "duration": "8 Weeks", "level": "Intermediate", "fee": 5499,
         "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&h=250&fit=crop",
         "certificate_available": True},
        {"title": "Prompt Engineering & AI Tools", "description": "Master AI tools and prompt engineering. Leverage ChatGPT, Claude, Midjourney, and automation workflows.",
         "category": "Artificial Intelligence", "duration": "4 Weeks", "level": "Beginner", "fee": 2999,
         "image_url": "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=400&h=250&fit=crop",
         "certificate_available": True, "is_featured": True},
        {"title": "Machine Learning Fundamentals", "description": "Understand ML algorithms, data preprocessing, model training and evaluation with scikit-learn and TensorFlow.",
         "category": "Artificial Intelligence", "duration": "12 Weeks", "level": "Intermediate to Advanced", "fee": 7999,
         "image_url": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=400&h=250&fit=crop",
         "certificate_available": True},
        {"title": "Graphic Design", "description": "Learn professional graphic design using Adobe Photoshop and Illustrator. Create logos, branding, social media content.",
         "category": "Creative Arts", "duration": "6 Weeks", "level": "Beginner to Intermediate", "fee": 3999,
         "image_url": "https://images.unsplash.com/photo-1626785774573-4b799315345d?w=400&h=250&fit=crop",
         "certificate_available": True},
        {"title": "Video Editing", "description": "Master video editing with Adobe Premiere Pro and After Effects. Create cinematic videos and YouTube content.",
         "category": "Creative Arts", "duration": "6 Weeks", "level": "Beginner to Intermediate", "fee": 3999,
         "image_url": "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?w=400&h=250&fit=crop",
         "certificate_available": True},
        {"title": "Microsoft Office Masterclass", "description": "Complete Microsoft Office training covering Word, Excel, PowerPoint, and Outlook for professional productivity.",
         "category": "Productivity", "duration": "4 Weeks", "level": "Beginner", "fee": 1999,
         "image_url": "https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=400&h=250&fit=crop",
         "certificate_available": True},
    ]
    for c in courses:
        db.add(Course(**c))
    db.commit()
    print("Courses seeded.")


def seed_settings(db):
    existing = db.query(WebsiteSettings).count()
    if existing > 0:
        return
    defaults = {
        "site_name": "NextGen MechTech Academy",
        "tagline": "Learn. Build. Innovate.",
        "contact_email": "support.nextgenmechtech@gmail.com",
        "contact_phone": "+92-300-0000000",
        "contact_address": "Lahore, Pakistan",
        "office_hours": "Mon–Sat: 9 AM–6 PM",
        "facebook_url": "https://facebook.com/nextgenmechtech",
        "instagram_url": "https://instagram.com/nextgenmechtech",
        "linkedin_url": "https://linkedin.com/company/nextgenmechtech",
        "youtube_url": "https://youtube.com/nextgenmechtech",
        "footer_text": "© 2025 NextGen MechTech Academy. All rights reserved.",
        "stat_students": "500+",
        "stat_courses": "12+",
        "stat_certificates": "300+",
        "stat_instructors": "10+",
        "about_tagline": "Empowering Pakistan's engineers and technologists since our founding.",
        "hero_video_enabled": "1",
        "hero_video_url": "https://youtu.be/2yORSxSSstw?si=ee1FmVhoxVJJup17",
        "hero_video_autoplay": "1",
        "hero_video_muted": "1",
        "hero_video_loop": "1",
        "hero_video_controls": "1",
        "email_verification_required": "true",
        "verification_token_expiry_hours": "48",
    }
    for key, value in defaults.items():
        db.add(WebsiteSettings(key=key, value=value))
    db.commit()
    print("Settings seeded.")


def seed_announcements(db):
    existing = db.query(Announcement).count()
    if existing > 0:
        return
    announcements = [
        {"title": "New Batch Starting — January 2025", "content": "Registrations are now open for our January 2025 batch. Enroll now and get 10% early bird discount!"},
        {"title": "Machine Learning Course Updated", "content": "Our Machine Learning Fundamentals course has been updated with new modules on Deep Learning and Neural Networks."},
        {"title": "Free Workshop: IoT for Beginners", "content": "Join our free online workshop on IoT Fundamentals this Saturday. Register through the Courses section."},
    ]
    for a in announcements:
        db.add(Announcement(**a))
    db.commit()
    print("Announcements seeded.")


def seed_payment_methods(db):
    from database.models import PaymentMethod
    existing = db.query(PaymentMethod).count()
    if existing > 0:
        return
    methods = [
        {"method_key": "easypaisa", "label": "EasyPaisa", "is_enabled": True, "display_order": 1},
        {"method_key": "jazzcash", "label": "JazzCash", "is_enabled": True, "display_order": 2},
        {"method_key": "bank_transfer", "label": "Bank Transfer", "is_enabled": True, "display_order": 3},
    ]
    for m in methods:
        db.add(PaymentMethod(**m))
    db.commit()
    print("Payment methods seeded.")


def seed_admin(db):
    existing_super = db.query(User).filter(User.role == UserRole.super_admin).count()
    if existing_super > 0:
        return

    existing_user = db.query(User).filter(User.email == "support.nextgenmechtech@gmail.com").first()
    if existing_user:
        existing_user.role = UserRole.super_admin
        db.commit()
        print("Existing admin promoted to Super Admin. Email: support.nextgenmechtech@gmail.com")
        return

    pw = bcrypt.hashpw("Admin@123".encode(), bcrypt.gensalt()).decode()
    db.add(User(
        full_name="NextGen Admin",
        email="support.nextgenmechtech@gmail.com",
        password_hash=pw,
        role=UserRole.super_admin,
        is_verified=True,
        is_active=True,
    ))
    db.commit()
    print("Admin seeded. Email: support.nextgenmechtech@gmail.com | Password: Admin@123")


def seed_email_templates(db):
    existing = db.query(EmailTemplate).count()
    if existing > 0:
        return
    templates = [
        {
            "event_key": "email_verification",
            "name": "Email Verification",
            "subject": "Verify your NextGen MechTech Academy account",
            "body_html": """<h2 style="color:#0F2D6B;margin:0 0 16px;">Verify Your Email</h2>
<p>Hi {{name}},</p>
<p>Thank you for registering with NextGen MechTech Academy! Click the button below to verify your email address and activate your account.</p>
<div style="text-align:center;margin:28px 0;">
  <a href="{{link}}" style="background:#0F2D6B;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;">Verify Email Address</a>
</div>
<p style="color:#67748B;font-size:13px;">This link expires in 48 hours. If you didn't create an account, you can safely ignore this email.</p>"""
        },
        {
            "event_key": "password_reset",
            "name": "Password Reset",
            "subject": "Reset your NextGen MechTech Academy password",
            "body_html": """<h2 style="color:#0F2D6B;margin:0 0 16px;">Reset Your Password</h2>
<p>Hi {{name}},</p>
<p>We received a request to reset your password. Click the button below to set a new password.</p>
<div style="text-align:center;margin:28px 0;">
  <a href="{{link}}" style="background:#0F2D6B;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;">Reset Password</a>
</div>
<p style="color:#67748B;font-size:13px;">This link expires in 2 hours. If you didn't request a reset, ignore this email.</p>"""
        },
        {
            "event_key": "registration_approved",
            "name": "Registration Approved",
            "subject": "Your registration has been approved — NextGen MechTech Academy",
            "body_html": """<h2 style="color:#15803D;margin:0 0 16px;">🎉 Registration Approved!</h2>
<p>Hi {{name}},</p>
<p>Great news! Your registration for <strong>{{course}}</strong> has been approved.</p>
<p>Your learning journey begins now. Log in to your dashboard to access course materials and updates.</p>
<div style="text-align:center;margin:28px 0;">
  <a href="{{link}}" style="background:#0F2D6B;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;">Go to Dashboard</a>
</div>"""
        },
        {
            "event_key": "registration_rejected",
            "name": "Registration Rejected",
            "subject": "Registration update — NextGen MechTech Academy",
            "body_html": """<h2 style="color:#B91C1C;margin:0 0 16px;">Registration Update</h2>
<p>Hi {{name}},</p>
<p>We're sorry, your registration for <strong>{{course}}</strong> could not be approved at this time.</p>
<p><strong>Reason:</strong> {{reason}}</p>
<p>Please contact us at <a href="mailto:support.nextgenmechtech@gmail.com">support.nextgenmechtech@gmail.com</a> if you have questions.</p>"""
        },
        {
            "event_key": "certificate_issued",
            "name": "Certificate Issued",
            "subject": "Your certificate is ready — NextGen MechTech Academy",
            "body_html": """<h2 style="color:#0F2D6B;margin:0 0 16px;">🏆 Certificate Ready!</h2>
<p>Hi {{name}},</p>
<p>Congratulations on completing <strong>{{course}}</strong>! Your certificate has been issued.</p>
<p><strong>Certificate ID:</strong> {{cert_id}}</p>
<div style="text-align:center;margin:28px 0;">
  <a href="{{link}}" style="background:#0F2D6B;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;">View & Download Certificate</a>
</div>"""
        },
    ]
    for t in templates:
        db.add(EmailTemplate(**t))
    db.commit()
    print("Email templates seeded.")


def initialize_database():
    from database.connection import init_db
    init_db()
    db = get_db_session()
    try:
        seed_settings(db)
        seed_courses(db)
        seed_instructors(db)
        seed_announcements(db)
        seed_admin(db)
        seed_email_templates(db)
        seed_payment_methods(db)
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()
