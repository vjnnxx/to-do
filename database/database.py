from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Or construct from individual variables
# DB_HOST = os.getenv("DB_HOST", "mysql")
# DB_PORT = os.getenv("DB_PORT", "3306")
# DB_USER = os.getenv("DB_USER", "fastapi_user")
# DB_PASSWORD = os.getenv("DB_PASSWORD", "fastapi_password")
# DB_NAME = os.getenv("DB_NAME", "fastapi_db")
# DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()