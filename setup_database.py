"""
Initialize Neon PostgreSQL database with simplified schema
Focus: Paper storage only (no ML/topics)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def init_database():
    """Initialize database with schema"""
    
    print("="*60)
    print("Neon Database Initialization")
    print("Paper Storage Only (No ML/Topics)")
    print("="*60)
    print()
    
    # Get Neon connection string
    neon_string = os.getenv('NEON_DB_STRING')
    
    if not neon_string:
        print("✗ NEON_DB_STRING not found in .env file")
        print("\nPlease add your Neon connection string to .env:")
        print("NEON_DB_STRING=postgresql://user:pass@host/database")
        return False
    
    print(f"✓ Found Neon connection string")
    print()
    
    try:
        # Connect to Neon
        print("Connecting to Neon database...")
        conn = psycopg2.connect(neon_string)
        conn.autocommit = True
        cursor = conn.cursor()
        print("✓ Connected successfully!")
        print()
        
        # Drop existing tables
        print("Dropping existing tables (if any)...")
        cursor.execute("""
            DROP TABLE IF EXISTS ingestion_logs CASCADE;
            DROP TABLE IF EXISTS ingestion_state CASCADE;
            DROP TABLE IF EXISTS papers CASCADE;
            DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
        """)
        print("✓ Existing tables dropped")
        print()
        
        # Read schema file
        schema_file = Path("db/init/01_papers_schema.sql")
        if not schema_file.exists():
            print(f"✗ Schema file not found: {schema_file}")
            return False
        
        print(f"Reading schema from {schema_file}...")
        schema_sql = schema_file.read_text()
        print("✓ Schema file loaded")
        print()
        
        # Execute schema
        print("Creating database schema...")
        cursor.execute(schema_sql)
        print("✓ Schema created successfully!")
        print()
        
        # Verify tables created
        print("Verifying tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"✓ Created {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        print()
        print("="*60)
        print("✓ DATABASE INITIALIZATION COMPLETE!")
        print("="*60)
        print()
        print("Next steps:")
        print("1. Review query parameters in: config/settings.py")
        print("2. Run ingestion: python -m src.sri.ingest_openalex")
        print("3. Check status: python check_papers.py")
        print()
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
