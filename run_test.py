"""Quick test ingestion"""
from src.sri.ingest_openalex import run_test_ingestion

print("\n" + "="*60)
print("RUNNING TEST INGESTION")
print("Fetching 50 papers from January 2024...")
print("="*60 + "\n")

result = run_test_ingestion()

print("\n" + "="*60)
print("TEST INGESTION RESULT")
print("="*60)
print(f"Status: {result['status']}")
print(f"Papers Added: {result.get('papers_added', 0)}")
print(f"Papers Fetched: {result.get('papers_fetched', 0)}")
print("="*60)
