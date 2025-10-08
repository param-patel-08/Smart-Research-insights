"""
Test database connection and configuration
"""
from db.connection import test_connection
import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("DATABASE CONNECTION TEST")
print("="*60)
print()

# Check environment variables
print("1. Checking environment variables...")
neon_string = os.getenv('NEON_DB_STRING')
email = os.getenv('OPENALEX_EMAIL')
start_date = os.getenv('ANALYSIS_START_DATE')
end_date = os.getenv('ANALYSIS_END_DATE')

if neon_string:
    print("   ✓ NEON_DB_STRING found")
    # Show partial string for security
    parts = neon_string.split('@')
    if len(parts) > 1:
        print(f"   Host: {parts[1].split('/')[0]}")
else:
    print("   ✗ NEON_DB_STRING not found in .env")
    print("   Add: NEON_DB_STRING=postgresql://user:pass@host/database")

if email:
    print(f"   ✓ OPENALEX_EMAIL: {email}")
else:
    print("   ✗ OPENALEX_EMAIL not found")

if start_date and end_date:
    print(f"   ✓ Date range: {start_date} to {end_date}")
else:
    print("   ✗ Date range not configured")

print()

# Test connection
print("2. Testing database connection...")
if test_connection():
    print()
    print("="*60)
    print("✓ ALL CHECKS PASSED")
    print("="*60)
    print()
    print("Next steps:")
    print("1. Configure query parameters: config/settings.py")
    print("2. Initialize database: python setup_database.py")
    print("3. Run ingestion: python -m src.sri.ingest_openalex")
else:
    print()
    print("="*60)
    print("✗ CONNECTION FAILED")
    print("="*60)
    print()
    print("Troubleshooting:")
    print("1. Check NEON_DB_STRING in .env")
    print("2. Verify Neon project is running")
    print("3. Check firewall/network settings")
