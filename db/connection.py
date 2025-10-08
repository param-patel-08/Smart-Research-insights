"""
Database connection and session management
"""
import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Database configuration
# Check for Neon connection string first, otherwise use individual parameters
NEON_DB_STRING = os.getenv('NEON_DB_STRING')

if NEON_DB_STRING:
    # Use Neon connection string directly
    DB_CONFIG = {'dsn': NEON_DB_STRING}
else:
    # Fall back to individual parameters
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'research_insights'),
        'user': os.getenv('DB_USER', 'research_user'),
        'password': os.getenv('DB_PASSWORD', 'research_pass'),
    }

# Connection pool
_connection_pool = None


def init_connection_pool(minconn=1, maxconn=10):
    """Initialize database connection pool"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pool.ThreadedConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            **DB_CONFIG
        )
    return _connection_pool


def get_connection_pool():
    """Get the connection pool, creating it if necessary"""
    if _connection_pool is None:
        init_connection_pool()
    return _connection_pool


@contextmanager
def get_db_connection():
    """
    Context manager for database connections from pool
    
    Usage:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM papers")
    """
    pool = get_connection_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        pool.putconn(conn)


@contextmanager
def get_db_cursor(dict_cursor=True) -> Generator:
    """
    Context manager for database cursor with automatic connection handling
    
    Args:
        dict_cursor: If True, returns results as dictionaries
        
    Usage:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM papers")
            papers = cur.fetchall()
    """
    with get_db_connection() as conn:
        cursor_factory = RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
        finally:
            cursor.close()


def test_connection():
    """Test database connection"""
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"✓ Database connection successful!")
            print(f"  PostgreSQL version: {version['version']}")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def close_connection_pool():
    """Close all connections in the pool"""
    global _connection_pool
    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None


if __name__ == "__main__":
    # Test the connection
    print("Testing database connection...")
    test_connection()
