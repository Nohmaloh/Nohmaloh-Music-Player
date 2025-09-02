# backend/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from models import Base

# Create database engine
# Why SQLAlchemy: Excellent ORM, handles connections, migrations, relationships
engine = create_engine(
    settings.DATABASE_URL,
    # Additional settings for development
    echo=settings.DEBUG,  # Log SQL queries when debugging
    pool_pre_ping=True,   # Verify connections before use
)

# Create session factory
# Why sessionmaker: Efficient connection pooling, transaction management
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Dependency function for FastAPI routes
    Ensures database connections are properly managed
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# For development: reset database
def reset_database():
    """Drop and recreate all tables - USE WITH CAUTION"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset complete")

if __name__ == "__main__":
    # Create tables when running this file directly
    create_tables()
    print("Database tables created successfully")

# Why this approach:
# 1. Dependency injection pattern - FastAPI manages connections automatically
# 2. Connection pooling - reuse database connections efficiently
# 3. Proper cleanup - connections are always closed
# 4. Development helpers - easy database reset during testing