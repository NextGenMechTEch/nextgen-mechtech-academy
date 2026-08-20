from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, Enum, LargeBinary, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    student = "student"
    admin = "admin"
    super_admin = "super_admin"
    instructor = "instructor"
    content_manager = "content_manager"


class RegistrationStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    info_requested = "info_requested"


class PaymentStatus(enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(500), nullable=False)
    phone = Column(String(50), nullable=True)
    university = Column(String(200), nullable=True)
    department = Column(String(200), nullable=True)
    semester = Column(String(50), nullable=True)
    address = Column(String(300), nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    profile_photo = Column(Text, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.student, nullable=False)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    verification_token = Column(String(500), nullable=True)
    reset_token = Column(String(500), nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    permissions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    registrations = relationship("Registration", back_populates="student")
    certificates = relationship("Certificate", back_populates="student")


class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    designation = Column(String(200), nullable=False)
    qualifications = Column(String(300), nullable=True)
    bio = Column(Text, nullable=True)
    experience = Column(String(100), nullable=True)
    photo_data = Column(Text, nullable=True)
    photo_url = Column(Text, nullable=True)
    linkedin_url = Column(Text, nullable=True)
    github_url = Column(Text, nullable=True)
    twitter_url = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    courses = relationship("Course", back_populates="instructor")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    full_description = Column(Text, nullable=True)
    what_you_learn = Column(Text, nullable=True)
    prerequisites = Column(Text, nullable=True)
    topics_covered = Column(Text, nullable=True)
    learning_outcomes = Column(Text, nullable=True)
    course_features = Column(Text, nullable=True)
    faqs = Column(Text, nullable=True)
    skills_learned = Column(Text, nullable=True)
    syllabus = Column(Text, nullable=True)
    software_used = Column(Text, nullable=True)
    projects_included = Column(Text, nullable=True)
    language = Column(String(100), nullable=True, default="Urdu / English")
    enrollment_open = Column(Boolean, default=True)
    category = Column(String(100), nullable=False)
    duration = Column(String(100), nullable=False)
    level = Column(String(50), nullable=False)
    fee = Column(Float, nullable=False)
    image_url = Column(Text, nullable=True)
    banner_url = Column(Text, nullable=True)
    is_published = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    certificate_available = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=True)
    assigned_instructor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    pending_review = Column(Boolean, default=False)
    review_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    instructor = relationship("Instructor", back_populates="courses")
    registrations = relationship("Registration", back_populates="course")
    certificates = relationship("Certificate", back_populates="course")


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    phone = Column(String(50), nullable=False)
    whatsapp = Column(String(50), nullable=True)
    university = Column(String(200), nullable=True)
    department = Column(String(200), nullable=True)
    semester = Column(String(50), nullable=True)
    payment_method = Column(String(100), nullable=False)
    payment_screenshot = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    registration_status = Column(Enum(RegistrationStatus), default=RegistrationStatus.pending)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("User", back_populates="registrations")
    course = relationship("Course", back_populates="registrations")


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(String(50), unique=True, nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    instructor_name = Column(String(200), nullable=True)
    file_data = Column(Text, nullable=True)
    file_name = Column(String(200), nullable=True)
    completion_date = Column(DateTime, nullable=True)
    issued_at = Column(DateTime, default=datetime.utcnow)
    is_revoked = Column(Boolean, default=False)
    revoke_reason = Column(Text, nullable=True)

    student = relationship("User", back_populates="certificates")
    course = relationship("Course", back_populates="certificates")


class TutorApplication(Base):
    __tablename__ = "tutor_applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(50), nullable=False)
    skills = Column(Text, nullable=False)
    experience = Column(Text, nullable=False)
    resume_data = Column(Text, nullable=True)
    resume_name = Column(String(200), nullable=True)
    message = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class PaymentMethod(Base):
    """Configurable payment methods (EasyPaisa, JazzCash, Bank Transfer, etc.).

    Fully manageable from the Admin Panel — enabling/disabling a method, editing
    account details, or adding new methods in the future requires no code changes.
    `label` is the exact string stored in `Registration.payment_method` when a
    student registers, so this table only adds configurability on top of the
    existing registration workflow without altering it.
    """
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    method_key = Column(String(100), unique=True, nullable=False)
    label = Column(String(150), nullable=False)
    account_title = Column(String(200), nullable=True)
    account_number = Column(String(150), nullable=True)
    custom_message = Column(Text, nullable=True)
    is_enabled = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    subject = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    reply = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class WebsiteSettings(Base):
    __tablename__ = "website_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(200), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    event_key = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    subject = Column(String(300), nullable=False)
    body_html = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecruitmentDrive(Base):
    __tablename__ = "recruitment_drives"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    company = Column(String(200), nullable=True)
    requirements = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    is_published = Column(Boolean, default=False)
    notification_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CmsSection(Base):
    """Stores CMS page sections with their content and visibility settings."""
    __tablename__ = "cms_sections"

    id = Column(Integer, primary_key=True, index=True)
    page = Column(String(100), nullable=False)
    section_key = Column(String(200), nullable=False)
    title = Column(String(300), nullable=True)
    content = Column(Text, nullable=True)
    is_visible = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    section_type = Column(String(100), default="custom")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MediaLibrary(Base):
    """Central media storage for all uploaded images, docs, logos."""
    __tablename__ = "media_library"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False)
    file_data = Column(Text, nullable=False)
    media_type = Column(String(100), default="image")
    folder = Column(String(200), default="general")
    file_size = Column(Integer, default=0)
    uploaded_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class JobOpening(Base):
    """Job openings & internship opportunities for the Careers page."""
    __tablename__ = "job_openings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    department = Column(String(200), nullable=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)
    employment_type = Column(String(100), default="Full-time")
    location = Column(String(200), default="Lahore, Pakistan")
    deadline = Column(DateTime, nullable=True)
    is_open = Column(Boolean, default=True)
    is_internship = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class NavItem(Base):
    """Dynamic navigation menu items."""
    __tablename__ = "nav_items"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(200), nullable=False)
    page_key = Column(String(100), nullable=False)
    icon_name = Column(String(100), nullable=True)
    display_order = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)
    parent_id = Column(Integer, nullable=True)
