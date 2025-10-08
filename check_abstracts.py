"""Check for papers with empty abstracts"""
from db.connection import get_db_cursor

with get_db_cursor() as cur:
    # Count papers with null or empty abstracts
    cur.execute("""
        SELECT COUNT(*) as count 
        FROM papers 
        WHERE abstract IS NULL OR abstract = ''
    """)
    result = cur.fetchone()
    empty_count = result['count']
    
    # Total papers
    cur.execute("SELECT COUNT(*) as count FROM papers")
    total = cur.fetchone()['count']
    
    print(f"Total papers: {total}")
    print(f"Papers with empty/null abstracts: {empty_count}")
    print(f"Papers with abstracts: {total - empty_count}")
    print(f"Percentage with abstracts: {((total - empty_count) / total * 100):.2f}%")
