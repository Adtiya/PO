"""
Database connection and session management for PostgreSQL.
Supports both synchronous and asynchronous operations.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
import structlog
from typing import AsyncGenerator, Generator

from app.core.config import settings

# Setup logger
logger = structlog.get_logger(__name__)

# ============================================================================
# DATABASE ENGINES
# ============================================================================

# Synchronous engine for migrations and admin tasks
sync_engine = create_engine(
    settings.database_url_sync,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    echo=settings.is_development,
    future=True
)

# Asynchronous engine for API operations
async_engine = create_async_engine(
    settings.database_url_async,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    echo=settings.is_development,
    future=True
)

# ============================================================================
# SESSION FACTORIES
# ============================================================================

# Synchronous session factory
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Asynchronous session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# ============================================================================
# BASE MODEL
# ============================================================================

# SQLAlchemy declarative base
Base = declarative_base()

# Metadata for table creation
metadata = MetaData()

# ============================================================================
# SESSION DEPENDENCIES
# ============================================================================

def get_sync_db() -> Generator:
    """
    Dependency for synchronous database sessions.
    Used for migrations and admin operations.
    """
    db = SyncSessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for asynchronous database sessions.
    Used for API operations.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Async database session error", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

async def create_tables():
    """Create all database tables."""
    try:
        # Import all models to ensure they're registered
        from app.models import *  # noqa
        
        async with async_engine.begin() as conn:
            # Note: In production, use Alembic migrations instead
            if settings.is_development:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created successfully")
            else:
                logger.info("Skipping table creation in production (use migrations)")
                
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise

async def drop_tables():
    """Drop all database tables. Use with caution!"""
    if not settings.is_development:
        raise RuntimeError("Cannot drop tables in production environment")
    
    try:
        from app.models import *  # noqa
        
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("All database tables dropped")
            
    except Exception as e:
        logger.error("Failed to drop database tables", error=str(e))
        raise

async def check_database_connection() -> bool:
    """Check if database connection is working."""
    try:
        async with async_engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error("Database connection check failed", error=str(e))
        return False

def check_sync_database_connection() -> bool:
    """Check if synchronous database connection is working."""
    try:
        with sync_engine.begin() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error("Sync database connection check failed", error=str(e))
        return False

# ============================================================================
# DATABASE UTILITIES
# ============================================================================

class DatabaseManager:
    """Database management utilities."""
    
    @staticmethod
    async def get_database_info():
        """Get database information and statistics."""
        try:
            async with AsyncSessionLocal() as session:
                # Get PostgreSQL version
                result = await session.execute("SELECT version()")
                version = result.scalar()
                
                # Get database size
                result = await session.execute(
                    "SELECT pg_size_pretty(pg_database_size(current_database()))"
                )
                size = result.scalar()
                
                # Get connection count
                result = await session.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                )
                connections = result.scalar()
                
                return {
                    "version": version,
                    "size": size,
                    "connections": connections,
                    "pool_size": settings.DATABASE_POOL_SIZE,
                    "max_overflow": settings.DATABASE_MAX_OVERFLOW
                }
                
        except Exception as e:
            logger.error("Failed to get database info", error=str(e))
            return {"error": str(e)}
    
    @staticmethod
    async def get_table_stats():
        """Get table statistics."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples
                    FROM pg_stat_user_tables
                    ORDER BY n_live_tup DESC
                """)
                
                tables = []
                for row in result:
                    tables.append({
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "inserts": row.inserts,
                        "updates": row.updates,
                        "deletes": row.deletes,
                        "live_tuples": row.live_tuples,
                        "dead_tuples": row.dead_tuples
                    })
                
                return tables
                
        except Exception as e:
            logger.error("Failed to get table stats", error=str(e))
            return []

# ============================================================================
# CONNECTION POOL MONITORING
# ============================================================================

def get_pool_status():
    """Get connection pool status."""
    pool = async_engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid()
    }

# ============================================================================
# HEALTH CHECK
# ============================================================================

async def database_health_check():
    """Comprehensive database health check."""
    health_status = {
        "database": "unknown",
        "connection_pool": "unknown",
        "details": {}
    }
    
    try:
        # Check basic connection
        if await check_database_connection():
            health_status["database"] = "healthy"
            
            # Get database info
            db_info = await DatabaseManager.get_database_info()
            health_status["details"]["database_info"] = db_info
            
            # Check connection pool
            pool_status = get_pool_status()
            health_status["details"]["pool_status"] = pool_status
            
            # Determine pool health
            if pool_status["checked_out"] < pool_status["size"] * 0.9:
                health_status["connection_pool"] = "healthy"
            else:
                health_status["connection_pool"] = "degraded"
                
        else:
            health_status["database"] = "unhealthy"
            health_status["connection_pool"] = "unhealthy"
            
    except Exception as e:
        health_status["database"] = "unhealthy"
        health_status["connection_pool"] = "unhealthy"
        health_status["details"]["error"] = str(e)
    
    return health_status

# Export commonly used items
__all__ = [
    "Base",
    "async_engine",
    "sync_engine",
    "AsyncSessionLocal",
    "SyncSessionLocal",
    "get_async_db",
    "get_sync_db",
    "create_tables",
    "drop_tables",
    "check_database_connection",
    "check_sync_database_connection",
    "DatabaseManager",
    "database_health_check",
    "get_pool_status"
]

