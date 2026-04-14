from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Updated for Supabase/Railway Production
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/fitsnap",
)

# Handle Railway's 'postgres://' vs SQLAlchemy's 'postgresql://' requirement
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Added SSL mode for production databases
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    # Fix for Supabase SSL requirements
    connect_args={"sslmode": "require"} if DATABASE_URL and "localhost" not in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
