"""
Migration script to simplify papers table schema
- Remove: id, authors, language, institution_id, citations, url columns
- Make openalex_id the primary key
- Keep: openalex_id (PK), title, abstract, publication_date, year, journal, doi, university, concepts, primary_field, is_open_access, timestamps
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.connection import get_db_cursor


def run_migration():
    """Run the schema migration"""
    
    print("Starting schema migration...")
    print("=" * 60)
    
    with get_db_cursor() as cur:
        # Step 1: Check current state
        print("\n1. Checking current table state...")
        cur.execute("SELECT COUNT(*) as count FROM papers")
        result = cur.fetchone()
        paper_count = result['count']
        print(f"   Current papers: {paper_count}")
        
        # Step 2: Drop old indexes that reference columns we're removing
        print("\n2. Dropping indexes on columns to be removed...")
        indexes_to_drop = [
            'idx_papers_institution',
            'idx_papers_citations'
        ]
        for idx in indexes_to_drop:
            try:
                cur.execute(f"DROP INDEX IF EXISTS {idx}")
                print(f"   ✓ Dropped {idx}")
            except Exception as e:
                print(f"   ⚠ Could not drop {idx}: {e}")
        
        # Step 3: Make openalex_id NOT NULL if it isn't already
        print("\n3. Ensuring openalex_id is NOT NULL...")
        cur.execute("""
            ALTER TABLE papers 
            ALTER COLUMN openalex_id SET NOT NULL
        """)
        print("   ✓ openalex_id set to NOT NULL")
        
        # Step 4: Drop the old UUID primary key constraint
        print("\n4. Dropping old UUID primary key...")
        cur.execute("""
            ALTER TABLE papers 
            DROP CONSTRAINT IF EXISTS papers_pkey CASCADE
        """)
        print("   ✓ Dropped old primary key")
        
        # Step 5: Add new primary key on openalex_id
        print("\n5. Adding openalex_id as primary key...")
        cur.execute("""
            ALTER TABLE papers 
            ADD PRIMARY KEY (openalex_id)
        """)
        print("   ✓ openalex_id is now the primary key")
        
        # Step 6: Drop unnecessary columns
        print("\n6. Dropping unnecessary columns...")
        columns_to_drop = [
            'id',
            'authors',
            'language',
            'institution_id',
            'citations',
            'url'
        ]
        for col in columns_to_drop:
            try:
                cur.execute(f"ALTER TABLE papers DROP COLUMN IF EXISTS {col}")
                print(f"   ✓ Dropped column: {col}")
            except Exception as e:
                print(f"   ⚠ Could not drop {col}: {e}")
        
        # Step 7: Drop old openalex_id unique index (now redundant since it's PK)
        print("\n7. Cleaning up redundant indexes...")
        cur.execute("DROP INDEX IF EXISTS idx_papers_openalex")
        print("   ✓ Dropped idx_papers_openalex (redundant with PK)")
        
        # Step 8: Verify final state
        print("\n8. Verifying final state...")
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'papers'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        
        print("\n   Final schema:")
        print("   " + "-" * 56)
        print(f"   {'Column':<30} {'Type':<20} {'Nullable'}")
        print("   " + "-" * 56)
        for col in columns:
            print(f"   {col['column_name']:<30} {col['data_type']:<20} {col['is_nullable']}")
        print("   " + "-" * 56)
        
        # Verify paper count unchanged
        cur.execute("SELECT COUNT(*) as count FROM papers")
        result = cur.fetchone()
        final_count = result['count']
        print(f"\n   Papers before migration: {paper_count}")
        print(f"   Papers after migration:  {final_count}")
        
        if paper_count == final_count:
            print("   ✓ All papers preserved!")
        else:
            print("   ⚠ WARNING: Paper count changed!")
            return False
    
    print("\n" + "=" * 60)
    print("✓ Migration completed successfully!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = run_migration()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
