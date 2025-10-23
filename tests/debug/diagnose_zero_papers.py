"""
Diagnose why AI_Machine_Learning and Energy_Sustainability are getting 0 papers
"""
import requests
from config.settings import OPENALEX_EMAIL, ALL_UNIVERSITIES, ANALYSIS_START_DATE, ANALYSIS_END_DATE
from config.themes import BABCOCK_THEMES

def test_theme_query(theme_name, keywords):
    """Test a theme's query to see if it returns any papers"""
    
    # Build university filter
    institution_filter = "|".join([
        f"https://openalex.org/{uni_id}" 
        for uni_id in ALL_UNIVERSITIES.values()
    ])
    
    # Use first 10 keywords only (to avoid query being too long)
    keyword_list = keywords[:10] if isinstance(keywords, list) else [kw.strip() for kw in keywords.split(',')][:10]
    query = " OR ".join(keyword_list)
    
    # Build OpenAlex API URL
    url = "https://api.openalex.org/works"
    params = {
        "filter": f"authorships.institutions.id:{institution_filter},from_publication_date:{ANALYSIS_START_DATE},to_publication_date:{ANALYSIS_END_DATE}",
        "search": query,  # Try using 'search' parameter instead of filter
        "per_page": 25,
        "mailto": OPENALEX_EMAIL
    }
    
    print(f"\n{'='*80}")
    print(f"Testing: {theme_name}")
    print(f"{'='*80}")
    print(f"Keywords (first 10): {', '.join(keyword_list)}")
    print(f"Universities: {len(ALL_UNIVERSITIES)}")
    print(f"Date range: {ANALYSIS_START_DATE} to {ANALYSIS_END_DATE}")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        count = data['meta']['count']
        print(f"\n✓ SUCCESS: Found {count} papers")
        
        if count > 0:
            print(f"\nFirst 3 paper titles:")
            for i, work in enumerate(data['results'][:3], 1):
                print(f"  {i}. {work['title']}")
        
        return count
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return 0

def main():
    print("DIAGNOSING ZERO PAPER THEMES")
    print("="*80)
    
    # Test AI_Machine_Learning
    aiml_keywords = BABCOCK_THEMES['AI_Machine_Learning']['keywords']
    aiml_count = test_theme_query('AI_Machine_Learning', aiml_keywords)
    
    # Test Energy_Sustainability
    energy_keywords = BABCOCK_THEMES['Energy_Sustainability']['keywords']
    energy_count = test_theme_query('Energy_Sustainability', energy_keywords)
    
    # Test a working theme for comparison (Defense_Security)
    defense_keywords = BABCOCK_THEMES['Defense_Security']['keywords']
    defense_count = test_theme_query('Defense_Security (for comparison)', defense_keywords)
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"AI_Machine_Learning: {aiml_count} papers")
    print(f"Energy_Sustainability: {energy_count} papers")
    print(f"Defense_Security: {defense_count} papers")
    
    if aiml_count == 0:
        print("\n⚠ AI_Machine_Learning query returns 0 papers!")
        print("Possible causes:")
        print("  - Keywords might be too specific/technical")
        print("  - Query might be too long (92 keywords)")
        print("  - OpenAlex might have issues with multi-word terms")
    
    if energy_count == 0:
        print("\n⚠ Energy_Sustainability query returns 0 papers!")
        print("Possible causes:")
        print("  - Keywords might be too specific/technical")
        print("  - Query might be too long (52 keywords)")

if __name__ == "__main__":
    main()
