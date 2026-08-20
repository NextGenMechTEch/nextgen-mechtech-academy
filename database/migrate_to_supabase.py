#!/usr/bin/env python3
"""
One-time data migration: copies all existing rows from the local SQLite
database (data/nextgen_mechtech.db) into a Supabase PostgreSQL database.

This does NOT change how the app connects at runtime — that is controlled
entirely by the DATABASE_URL environment variable in `.env`
(see database/connection.py). This script is only for moving data that
already exists in the old SQLite file the first time you cut over.

Usage:
    1. Create the Supabase project and get its connection string.
    2. Set DATABASE_URL in your environment (or .env) to the Supabase URL.
    3. Run:  python database/migrate_to_supabase.py

The script:
    - Reads every row from the local SQLite file (regardless of DATABASE_URL).
    - Creates all tables in the target Postgres database (if not already there).
    - Copies rows table-by-table in FK-safe order, preserving primary key IDs.
    - Resets Postgres auto-increment sequences to match the copied data so
      future inserts continue from the correct ID.
    - Is idempotent / safe to re-run: existing rows in the target (matched by
      primary key) are skipped rather than duplicated.
"""
import os
import sys
import pathlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from database.models import (
    Base, User, Instructor, Course, Registration, Certificate,
    TutorApplication, PaymentMethod, ContactMessage, WebsiteSettings,
    Announcement, EmailTemplate, RecruitmentDrive, CmsSection,
    MediaLibrary, JobOpening, NavItem,
)

# Order matters: parent tables before the tables that hold foreign keys to them.
MODELS_IN_FK_ORDER = [
    User,
    Instructor,
    Course,
    Registration,
    Certificate,
    TutorApplication,
    PaymentMethod,
    ContactMessage,
    WebsiteSettings,
    Announcement,
    EmailTemplate,
    RecruitmentDrive,
    CmsSection,
    MediaLibrary,
    JobOpening,
    NavItem,
]


def get_sqlite_engine():
    db_path = pathlib.Path(__file__).parent.parent / "data" / "nextgen_mechtech.db"
    if not db_path.exists():
        print(f"No local SQLite database found at {db_path} — nothing to migrate.")
        sys.exit(0)
    return create_engine(f"sqlite:///{db_path}")


def get_postgres_engine():
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if not db_url or not db_url.startswith("postgresql"):
        print("ERROR: DATABASE_URL must be set to your Supabase PostgreSQL connection "
              "string before running this script.")
        sys.exit(1)
    connect_args = {}
    if "sslmode" not in db_url:
        connect_args["sslmode"] = os.getenv("DATABASE_SSLMODE", "require")
    return create_engine(db_url, connect_args=connect_args)


def copy_table(model, sqlite_session, pg_session):
    rows = sqlite_session.query(model).all()
    if not rows:
        print(f"  {model.__tablename__}: 0 rows (skipped)")
        return 0

    pk_col = inspect(model).primary_key[0].name
    existing_ids = {
        getattr(r, pk_col)
        for r in pg_session.query(getattr(model, pk_col)).all()
    }

    copied = 0
    for row in rows:
        row_id = getattr(row, pk_col)
        if row_id in existing_ids:
            continue
        data = {
            c.key: getattr(row, c.key)
            for c in inspect(model).mapper.column_attrs
        }
        pg_session.add(model(**data))
        copied += 1

    pg_session.commit()
    print(f"  {model.__tablename__}: {copied} row(s) copied "
          f"({len(rows) - copied} already present)")
    return copied


def reset_sequence(pg_engine, model):
    """Ensure the Postgres auto-increment sequence continues after the
    highest migrated ID, so new rows created by the app don't collide."""
    table = model.__tablename__
    pk_col = inspect(model).primary_key[0].name
    with pg_engine.connect() as conn:
        conn.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{table}', '{pk_col}'), "
            f"COALESCE((SELECT MAX({pk_col}) FROM {table}), 1), "
            f"(SELECT MAX({pk_col}) FROM {table}) IS NOT NULL)"
        ))
        conn.commit()


def main():
    print("NextGen MechTech Academy — SQLite → Supabase PostgreSQL data migration")
    print("=" * 72)

    sqlite_engine = get_sqlite_engine()
    pg_engine = get_postgres_engine()

    print(f"Source: {sqlite_engine.url}")
    print(f"Target: {pg_engine.url.render_as_string(hide_password=True)}")
    print()

    print("Creating tables in target database (if not already present)...")
    Base.metadata.create_all(bind=pg_engine)

    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=pg_engine)
    sqlite_session = SqliteSession()
    pg_session = PgSession()

    total = 0
    try:
        print("\nCopying data...")
        for model in MODELS_IN_FK_ORDER:
            total += copy_table(model, sqlite_session, pg_session)

        print("\nResetting Postgres sequences...")
        for model in MODELS_IN_FK_ORDER:
            reset_sequence(pg_engine, model)

        print(f"\nDone. {total} total row(s) migrated to Supabase PostgreSQL.")
    except Exception as e:
        pg_session.rollback()
        print(f"\nERROR during migration: {e}")
        raise
    finally:
        sqlite_session.close()
        pg_session.close()


if __name__ == "__main__":
    main()
