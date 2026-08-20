import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from database.models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Supabase (and some other hosts/PaaS) hand out connection strings using the
# legacy "postgres://" scheme. SQLAlchemy 1.4+/2.x requires "postgresql://".
# Normalize here so a Supabase connection string works unmodified.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
    import pathlib
    db_path = pathlib.Path(__file__).parent.parent / "data" / "nextgen_mechtech.db"
    db_path.parent.mkdir(exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_path}"
    _is_sqlite = True
else:
    _is_sqlite = False

if _is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # ── PostgreSQL / Supabase ────────────────────────────────────────────────
    # Supabase requires SSL on all connections. If DATABASE_URL doesn't already
    # specify sslmode, default to "require" so this works out of the box.
    connect_args = {}
    if "sslmode" not in DATABASE_URL:
        connect_args["sslmode"] = os.getenv("DATABASE_SSLMODE", "require")

    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE", "300")),
        pool_size=int(os.getenv("DATABASE_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "10")),
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    return SessionLocal()


def init_db():
    # Step 1: Run safe column-level migrations for existing databases
    try:
        from database.migrate import run_migrations
        run_migrations()
    except Exception as e:
        print(f"Migration warning (non-fatal): {e}")
    # Step 2: Create any brand-new tables
    Base.metadata.create_all(bind=engine)


def get_db_type() -> str:
    return "sqlite" if _is_sqlite else "postgresql"
