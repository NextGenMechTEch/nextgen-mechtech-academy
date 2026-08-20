"""
Safe schema migration for NextGen MechTech Academy v2.
Adds new columns / tables without dropping any data.
Run automatically on startup via initialize_database().
"""
import sqlite3
import pathlib
import os

def get_db_path():
    db_path = pathlib.Path(__file__).parent.parent / "data" / "nextgen_mechtech.db"
    return str(db_path)

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols

def table_exists(cursor, table):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None

def run_migrations():
    db_url = os.getenv("DATABASE_URL", "")
    if db_url and not db_url.startswith("sqlite"):
        print("Non-SQLite DB detected — skipping SQLite migration script.")
        return

    db_path = get_db_path()
    if not pathlib.Path(db_path).exists():
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    migrations = []

    # ── courses table ────────────────────────────────────────────────────────
    course_cols = [
        ("full_description",    "TEXT"),
        ("what_you_learn",      "TEXT"),
        ("prerequisites",       "TEXT"),
        ("topics_covered",      "TEXT"),
        ("learning_outcomes",   "TEXT"),
        ("course_features",     "TEXT"),
        ("faqs",                "TEXT"),
        ("banner_url",          "TEXT"),
        ("is_featured",         "INTEGER DEFAULT 0"),
        ("certificate_available","INTEGER DEFAULT 1"),
        ("display_order",       "INTEGER DEFAULT 0"),
        ("instructor_id",       "INTEGER"),
        ("language",            "TEXT DEFAULT 'Urdu / English'"),
        ("software_used",       "TEXT"),
        ("projects_included",   "TEXT"),
        ("skills_learned",      "TEXT"),
        ("syllabus",            "TEXT"),
        ("enrollment_open",     "INTEGER DEFAULT 1"),
        ("assigned_instructor_user_id", "INTEGER"),
        ("submitted_by_user_id",        "INTEGER"),
        ("pending_review",              "INTEGER DEFAULT 0"),
        ("review_note",                 "TEXT"),
    ]
    for col, col_type in course_cols:
        if not column_exists(cur, "courses", col):
            cur.execute(f"ALTER TABLE courses ADD COLUMN {col} {col_type}")
            migrations.append(f"courses.{col}")

    # ── users table ──────────────────────────────────────────────────────────
    user_cols = [
        ("address",     "TEXT"),
        ("country",     "TEXT"),
        ("city",        "TEXT"),
        ("permissions", "TEXT"),
    ]
    for col, col_type in user_cols:
        if not column_exists(cur, "users", col):
            cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            migrations.append(f"users.{col}")

    # ── certificates table ───────────────────────────────────────────────────
    cert_cols = [
        ("certificate_id",   "TEXT"),
        ("instructor_name",  "TEXT"),
        ("completion_date",  "DATETIME"),
        ("is_revoked",       "INTEGER DEFAULT 0"),
        ("revoke_reason",    "TEXT"),
    ]
    for col, col_type in cert_cols:
        if not column_exists(cur, "certificates", col):
            cur.execute(f"ALTER TABLE certificates ADD COLUMN {col} {col_type}")
            migrations.append(f"certificates.{col}")

    # Back-fill certificate_id
    cur.execute("SELECT id FROM certificates WHERE certificate_id IS NULL OR certificate_id = ''")
    rows = cur.fetchall()
    if rows:
        import secrets, string
        chars = string.ascii_uppercase + string.digits
        for (cid,) in rows:
            new_id = "NMT-" + "".join(secrets.choice(chars) for _ in range(10))
            cur.execute("UPDATE certificates SET certificate_id = ? WHERE id = ?", (new_id, cid))
        migrations.append(f"back-filled {len(rows)} certificate IDs")

    # ── instructors table ────────────────────────────────────────────────────
    if not table_exists(cur, "instructors"):
        cur.execute("""
            CREATE TABLE instructors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                designation VARCHAR(200) NOT NULL,
                qualifications VARCHAR(300),
                bio TEXT,
                experience VARCHAR(100),
                photo_data TEXT,
                photo_url TEXT,
                linkedin_url TEXT,
                github_url TEXT,
                twitter_url TEXT,
                display_order INTEGER DEFAULT 0,
                is_visible INTEGER DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME
            )
        """)
        migrations.append("created table: instructors")

    # ── email_templates table ────────────────────────────────────────────────
    if not table_exists(cur, "email_templates"):
        cur.execute("""
            CREATE TABLE email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_key VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                subject VARCHAR(300) NOT NULL,
                body_html TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                updated_at DATETIME
            )
        """)
        migrations.append("created table: email_templates")

    # ── recruitment_drives table ─────────────────────────────────────────────
    if not table_exists(cur, "recruitment_drives"):
        cur.execute("""
            CREATE TABLE recruitment_drives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(300) NOT NULL,
                description TEXT NOT NULL,
                company VARCHAR(200),
                requirements TEXT,
                deadline DATETIME,
                is_published INTEGER DEFAULT 0,
                notification_sent INTEGER DEFAULT 0,
                created_at DATETIME
            )
        """)
        migrations.append("created table: recruitment_drives")

    # ── cms_sections table (NEW) ─────────────────────────────────────────────
    if not table_exists(cur, "cms_sections"):
        cur.execute("""
            CREATE TABLE cms_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page VARCHAR(100) NOT NULL,
                section_key VARCHAR(200) NOT NULL,
                title VARCHAR(300),
                content TEXT,
                is_visible INTEGER DEFAULT 1,
                display_order INTEGER DEFAULT 0,
                section_type VARCHAR(100) DEFAULT 'custom',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(page, section_key)
            )
        """)
        migrations.append("created table: cms_sections")

    # ── media_library table (NEW) ────────────────────────────────────────────
    if not table_exists(cur, "media_library"):
        cur.execute("""
            CREATE TABLE media_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(300) NOT NULL,
                file_data TEXT NOT NULL,
                media_type VARCHAR(100) DEFAULT 'image',
                folder VARCHAR(200) DEFAULT 'general',
                file_size INTEGER DEFAULT 0,
                uploaded_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        migrations.append("created table: media_library")

    # ── job_openings table (NEW) ─────────────────────────────────────────────
    if not table_exists(cur, "job_openings"):
        cur.execute("""
            CREATE TABLE job_openings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(300) NOT NULL,
                department VARCHAR(200),
                description TEXT NOT NULL,
                requirements TEXT,
                benefits TEXT,
                employment_type VARCHAR(100) DEFAULT 'Full-time',
                location VARCHAR(200) DEFAULT 'Lahore, Pakistan',
                deadline DATETIME,
                is_open INTEGER DEFAULT 1,
                is_internship INTEGER DEFAULT 0,
                display_order INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        migrations.append("created table: job_openings")

    # ── nav_items table (NEW) ────────────────────────────────────────────────
    if not table_exists(cur, "nav_items"):
        cur.execute("""
            CREATE TABLE nav_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label VARCHAR(200) NOT NULL,
                page_key VARCHAR(100) NOT NULL,
                icon_name VARCHAR(100),
                display_order INTEGER DEFAULT 0,
                is_visible INTEGER DEFAULT 1,
                parent_id INTEGER DEFAULT NULL
            )
        """)
        migrations.append("created table: nav_items")

    conn.commit()
    conn.close()

    if migrations:
        print(f"Migrations applied: {', '.join(migrations)}")
    else:
        print("Schema up-to-date — no migrations needed.")

if __name__ == "__main__":
    run_migrations()
