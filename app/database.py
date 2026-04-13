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

# Added SSL mode for production databases
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    # Fix for Supabase SSL requirements
    connect_args={"sslmode": "require"} if "localhost" not in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
