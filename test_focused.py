"""
Focused test script for configuration, custom modules, and OpenAlex API
"""

import sys
import os

def test_config():
    """Test configuration files"""
    print("\n" + "="*80)
    print("TESTING CONFIGURATION")
    print("="*80)
    
    try:
        from config.themes import BABCOCK_THEMES
        from config.settings import (
            OPENALEX_EMAIL, 
            ALL_UNIVERSITIES,
            ANALYSIS_START_DATE,
            ANALYSIS_END_DATE
        )
        
        print(f"✓ Themes loaded: {len(BABCOCK_THEMES)} themes")
        print(f"✓ Universities configured: {len(ALL_UNIVERSITIES)}")
        print(f"✓ Date range: {ANALYSIS_START_DATE.date()} to {ANALYSIS_END_DATE.date()}")
        print(f"✓ OpenAlex email: {OPENALEX_EMAIL}")
        
        if OPENALEX_EMAIL == "your.email@example.com":
            print("\n⚠️  WARNING: Please update OPENALEX_EMAIL in .env file!")
            print("   Create .env file with: OPENALEX_EMAIL=your.email@university.edu")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_modules():
    """Test if custom modules can be imported"""
    print("\n" + "="*80)
    print("TESTING CUSTOM MODULES")
    print("="*80)
    
    try:
        from src.openalex_collector import OpenAlexCollector
        print("✓ openalex_collector.py")
        
        from src.paper_preprocessor import PaperPreprocessor
        print("✓ paper_preprocessor.py")
        
        from config.themes import BABCOCK_THEMES
        print("✓ themes.py")
        
        from config.settings import ALL_UNIVERSITIES
        print("✓ settings.py")
        
        return True
        
    except Exception as e:
        print(f"✗ Module import failed: {e}")
        return False

def test_openalex_connection():
    """Test connection to OpenAlex API"""
    print("\n" + "="*80)
    print("TESTING OPENALEX API CONNECTION")
    print("="*80)
    
    try:
        import requests
        from config.settings import OPENALEX_EMAIL
        
        # Test API connection
        url = "https://api.openalex.org/works"
        params = {
            'filter': 'institutions.id:I145311948',  # University of Melbourne
            'per-page': 1,
            'mailto': OPENALEX_EMAIL
        }
        
        # Add headers for better API compatibility
        headers = {
            'User-Agent': 'Babcock-Research-Trends/1.0 (mailto:' + OPENALEX_EMAIL + ')'
        }
        
        print("Testing API connection...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('meta', {}).get('count', 0)
            print(f"✓ OpenAlex API connection successful!")
            print(f"✓ Test query returned {count:,} total papers")
            return True
        else:
            print(f"✗ API returned status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ API connection failed: {e}")
        return False

def main():
    """Run focused tests"""
    print("\n" + "="*80)
    print("BABCOCK RESEARCH TRENDS - FOCUSED SYSTEM TEST")
    print("="*80)
    
    results = []
    
    # Run tests
    results.append(("Configuration", test_config()))
    results.append(("Custom Modules", test_modules()))
    results.append(("OpenAlex API", test_openalex_connection()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED! System is ready to use.")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("✗ SOME TESTS FAILED. Please fix the issues above.")
        print("="*80)

if __name__ == "__main__":
    main()
