import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or DATABASE_URL.strip() == "":
    project_ref = os.getenv("SUPABASE_PROJECT_REF")
    password = os.getenv("DATABASE_PASSWORD", "")
    safe_password = urllib.parse.quote_plus(password)
    db_name = os.getenv("DATABASE_NAME", "postgres")
    
    use_pooler = os.getenv("DATABASE_USE_POOLER", "false").lower() == "true"
    
    if project_ref and password:
        if use_pooler:
            region = os.getenv("SUPABASE_POOLER_REGION", "us-east-1")
            port = os.getenv("SUPABASE_POOLER_PORT", "6543")
            DATABASE_URL = f"postgresql://postgres.{project_ref}:{safe_password}@aws-0-{region}.pooler.supabase.com:{port}/{db_name}"
            if port == "6543":
                DATABASE_URL += "?pgbouncer=true"
        else:
            DATABASE_URL = f"postgresql://postgres:{safe_password}@db.{project_ref}.supabase.co:5432/{db_name}"
    else:
        # Fallback to local postgres if config is not present
        DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/sga_db"

# Use SQLite fallback if database is not postgres for easier testing
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Use psycopg2-binary for Postgres
    engine = create_engine(
        DATABASE_URL, 
        pool_size=10, 
        max_overflow=20, 
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
