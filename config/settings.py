"""
Configuration settings for OpenAlex API ingestion
"""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAlex API Configuration
OPENALEX_EMAIL = os.getenv('OPENALEX_EMAIL', 'your-email@example.com')

# Date range for initial ingestion
ANALYSIS_START_DATE = os.getenv('ANALYSIS_START_DATE', '2019-01-01')
ANALYSIS_END_DATE = os.getenv('ANALYSIS_END_DATE', '2024-12-31')

# ==============================================================================
# UNIVERSITY/INSTITUTION CONFIGURATION
# ==============================================================================
# This is where you define which institutions' papers to fetch from OpenAlex
# 
# To find OpenAlex institution IDs:
# 1. Go to https://openalex.org/
# 2. Search for your institution
# 3. Copy the ID from the URL (e.g., https://openalex.org/I4210131357)
# 4. Add it to the dictionary below
#
# Format: 'Short Name': 'OpenAlex ID'
# ==============================================================================

ALL_UNIVERSITIES = {
    # Add more institutions here:
    # 'MIT': 'I136199984',
    # 'Stanford': 'I97018004',
    # 'Oxford': 'I4210141937',
}

# ==============================================================================
# QUERY REFINEMENT PARAMETERS - BABCOCK PROJECT
# ==============================================================================
# Project Focus: Defense, Aerospace, Nuclear, Energy, Advanced Data Analytics
# 
# Use KEYWORD SEARCH to filter papers by searching titles and abstracts.
# This is more effective than concept IDs for getting exactly what you need.
#
# Available OpenAlex filters:
# - title_and_abstract.search: Search keywords in title AND abstract
# - institutions.id: Filter by institution
# - from_publication_date / to_publication_date: Date range
# - cited_by_count: Minimum citation count (>N format)
# - is_oa: Open access papers only
# - primary_location.source.id: Filter by journal/venue
#
# Documentation: https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/filter-entity-lists
# ==============================================================================

# Additional query parameters (customize as needed)
QUERY_PARAMS = {
    # ========== KEYWORD SEARCH (Most Important!) ==========
    # Search for specific keywords in paper titles AND abstracts
    # Use this to get ONLY relevant papers for your research areas
    # 
    # OpenAlex search syntax:
    # - Use | for OR: 'defense|aerospace|nuclear'
    # - Searches both title AND abstract automatically
    # - Case-insensitive matching
    #
    # For Babcock Project (Defense, Aerospace, Nuclear, Energy, Data Analytics):
    # Current: Fetches ~143 papers from 2024, ~400-600 from 2019-2024
    'search_keywords': 'naval',
    
    # To make more specific (fewer papers):
    # 'search_keywords': 'nuclear energy|renewable energy|defense technology|aerospace engineering',
    
    # To make broader (more papers):
    # 'search_keywords': 'defense|aerospace|nuclear|energy|sustainability|renewable|solar|wind|machine learning|artificial intelligence|deep learning|data science|data analytics|big data|cybersecurity|information security|climate|environment',
    
    # Minimum citation count (filter out low-quality papers)
    'min_citations': None,  # Disabled for testing
    
    # Open access only? (True/False)
    'open_access_only': False,  # Include all papers
    
    # Specific journals/venues (high-quality engineering journals)
    # Add journal IDs here if you want to filter by specific publications
    'journals': [],
    
    # Country codes (ISO 2-letter codes: 'US', 'GB', etc.)
    # Leave empty to include all countries
    'countries': [],
    
    # Language (ISO 2-letter codes: 'en', 'es', etc.)
    'languages': ['en'],  # All languages for now
}

# ==============================================================================
# FIELDS TO RETRIEVE FROM OPENALEX
# ==============================================================================
# Specify which fields to retrieve from the OpenAlex API
# Full list: https://docs.openalex.org/api-entities/works/work-object
# ==============================================================================

OPENALEX_SELECT_FIELDS = [
    'id',
    'title',
    'abstract_inverted_index',
    'publication_date',
    'publication_year',
    'authorships',
    'primary_location',
    'doi',
    'cited_by_count',
    'concepts',  # Research topics/concepts
    'is_open_access',
    'language',
]
