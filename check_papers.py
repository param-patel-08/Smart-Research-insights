"""
Check papers in database - quick status utility
"""
from db.connection import get_db_cursor
from db.models.models import Paper, IngestionLog

print("="*60)
print("DATABASE STATUS - PAPERS ONLY")
print("="*60)
print()

try:
    # Count papers
    count = Paper.count()
    print(f"📄 Total Papers: {count}")
    print()
    
    if count > 0:
        # Get sample papers
        print("Recent Papers (sample):")
        print("-" * 60)
        papers = Paper.get_all(limit=5)
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper['title'][:80]}...")
            print(f"   OpenAlex ID: {paper['openalex_id']}")
            print(f"   Year: {paper['year']} | DOI: {paper.get('doi', 'N/A')}")
            print(f"   University: {paper.get('university', 'N/A')}")
            print(f"   Journal: {paper.get('journal', 'N/A')}")
            if paper.get('abstract'):
                print(f"   Abstract: {paper['abstract'][:100]}...")
        
        print()
        print("-" * 60)
        
        # Stats by year
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT year, COUNT(*) as count 
                FROM papers 
                GROUP BY year 
                ORDER BY year DESC 
                LIMIT 10
            """)
            years = cur.fetchall()
            
            print("\nPapers by Year:")
            for row in years:
                print(f"  {row['year']}: {row['count']} papers")
        
        print()
        
        # Stats by university
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT university, COUNT(*) as count 
                FROM papers 
                WHERE university IS NOT NULL
                GROUP BY university 
                ORDER BY count DESC 
                LIMIT 10
            """)
            unis = cur.fetchall()
            
            print("Papers by University (Top 10):")
            for row in unis:
                print(f"  {row['university']}: {row['count']} papers")
    
    print()
    
    # Ingestion logs
    logs = IngestionLog.get_recent(limit=5)
    if logs:
        print("\nRecent Ingestion Logs:")
        print("-" * 60)
        for log in logs:
            print(f"  {log['ingestion_date']}: +{log['papers_added']} papers ({log['status']})")
    
    print()
    print("="*60)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
