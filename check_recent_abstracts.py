"""Check if recent papers have abstracts"""
from db.connection import get_db_cursor

with get_db_cursor() as cur:
    # Check recent 100 papers
    cur.execute("""
        SELECT COUNT(*) as count 
        FROM (
            SELECT * FROM papers 
            ORDER BY created_at DESC 
            LIMIT 100
        ) AS recent 
        WHERE abstract IS NULL OR abstract = ''
    """)
    result = cur.fetchone()
    empty_count = result['count']
    
    print(f"Recent 100 papers:")
    print(f"  - With empty/null abstracts: {empty_count}")
    print(f"  - With abstracts: {100 - empty_count}")
    
    if empty_count == 0:
        print("\n✓ All recent papers have abstracts! The filter is working.")
    else:
        print(f"\n⚠ {empty_count} recent papers are missing abstracts")
