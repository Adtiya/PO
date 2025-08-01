"""
Enterprise AI System - Database Configuration
PhD-level implementation with connection pooling and error handling
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///enterprise_ai.db')

# Create engine with appropriate settings
if DATABASE_URL.startswith('sqlite'):
    # SQLite configuration for development
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool,
        connect_args={
            'check_same_thread': False,
            'timeout': 20
        },
        echo=False  # Set to True for SQL debugging
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        
else:
    # PostgreSQL configuration for production
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Database dependency for FastAPI/Flask
    Provides database session with automatic cleanup
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """
    Initialize database with tables and default data
    """
    try:
        from models.user import Base
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
        
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False

def test_connection():
    """
    Test database connection
    """
    try:
        db = SessionLocal()
        db.execute(text('SELECT 1'))
        db.close()
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False

