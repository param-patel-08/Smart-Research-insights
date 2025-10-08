# Query Refinement Quick Reference

## Problem: Not Getting Relevant Papers

### Step 1: Identify What's Wrong

Run check to see current papers:
```powershell
python check_papers.py
```

Questions to ask:
- Too many papers?
- Papers from wrong institutions?
- Papers outside your research area?
- Papers in wrong language?
- Low-quality papers (few citations)?

### Step 2: Find the Right Filters

#### Filter by Research Topic/Concept

**Find OpenAlex Concept IDs:**
1. Go to: https://openalex.org/concepts
2. Search for your topic (e.g., "artificial intelligence", "climate change")
3. Click on the concept
4. Copy ID from URL: `https://openalex.org/C154945302` → use `C154945302`

**Common Research Concepts:**
- `C41008148` - Computer Science
- `C71924100` - Medicine
- `C15744967` - Psychology
- `C162324750` - Economics
- `C127313418` - Physics
- `C86803240` - Biology
- `C17744445` - Political science
- `C127413603` - Engineering
- `C33923547` - Mathematics
- `C144024400` - Sociology

**Add to config/settings.py:**
```python
QUERY_PARAMS = {
    'concepts': ['C41008148', 'C71924100'],  # Computer Science + Medicine
}
```

**Then modify src/sri/ingest_openalex.py around line 58:**
```python
filters = [
    f'institutions.id:{institution_filter}',
    date_filter,
]

# Add concept filter
if QUERY_PARAMS.get('concepts'):
    concept_ids = '|'.join(QUERY_PARAMS['concepts'])
    filters.append(f'concepts.id:{concept_ids}')

params = {
    'filter': ','.join(filters),  # Join all filters with comma
    ...
}
```

---

#### Filter by Citation Count

**Add to config/settings.py:**
```python
QUERY_PARAMS = {
    'min_citations': 10,  # Only papers with 10+ citations
}
```

**Then modify src/sri/ingest_openalex.py:**
```python
# Add after concept filter
if QUERY_PARAMS.get('min_citations'):
    min_cites = QUERY_PARAMS['min_citations']
    filters.append(f'cited_by_count:>{min_cites}')
```

---

#### Filter by Specific Journals

**Find OpenAlex Source (Journal) IDs:**
1. Go to: https://openalex.org/sources
2. Search for journal (e.g., "Nature", "Science")
3. Copy ID from URL: `https://openalex.org/S2764455859` → use `S2764455859`

**Top Journals:**
- `S2764455859` - Nature
- `S4210194219` - Science
- `S2481280884` - The Lancet
- `S201505140` - Cell
- `S2731076878` - PLOS ONE
- `S2742750505` - Proceedings of the National Academy of Sciences (PNAS)

**Add to config/settings.py:**
```python
QUERY_PARAMS = {
    'journals': ['S2764455859', 'S4210194219'],  # Nature + Science
}
```

**Then modify src/sri/ingest_openalex.py:**
```python
if QUERY_PARAMS.get('journals'):
    journal_ids = '|'.join(QUERY_PARAMS['journals'])
    filters.append(f'primary_location.source.id:{journal_ids}')
```

---

#### Filter by Open Access

**Add to config/settings.py:**
```python
QUERY_PARAMS = {
    'open_access_only': True,
}
```

**Then modify src/sri/ingest_openalex.py:**
```python
if QUERY_PARAMS.get('open_access_only'):
    filters.append('is_oa:true')
```

---

#### Filter by Language

**Add to config/settings.py:**
```python
QUERY_PARAMS = {
    'languages': ['en'],  # English only
}
```

**Then modify src/sri/ingest_openalex.py:**
```python
if QUERY_PARAMS.get('languages'):
    lang_codes = '|'.join(QUERY_PARAMS['languages'])
    filters.append(f'language:{lang_codes}')
```

**Common language codes:**
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `zh` - Chinese
- `ja` - Japanese

---

#### Filter by Country

**Add to config/settings.py:**
```python
QUERY_PARAMS = {
    'countries': ['GB', 'US'],  # UK and US only
}
```

**Then modify src/sri/ingest_openalex.py:**
```python
if QUERY_PARAMS.get('countries'):
    country_codes = '|'.join(QUERY_PARAMS['countries'])
    filters.append(f'authorships.institutions.country_code:{country_codes}')
```

**Common country codes:**
- `US` - United States
- `GB` - United Kingdom
- `CA` - Canada
- `AU` - Australia
- `DE` - Germany
- `FR` - France
- `CN` - China
- `JP` - Japan
- `IN` - India

---

### Step 3: Complete Example

**Goal**: Get only Computer Science papers from top journals with 10+ citations in English

**1. Edit config/settings.py:**
```python
QUERY_PARAMS = {
    'concepts': ['C41008148'],  # Computer Science
    'min_citations': 10,
    'journals': ['S2764455859', 'S4210194219'],  # Nature + Science
    'open_access_only': False,
    'languages': ['en'],
    'countries': [],  # Empty = all countries
}
```

**2. Edit src/sri/ingest_openalex.py in fetch_papers() method:**

Replace line 58 onwards with:

```python
# Build filter list
filters = [
    f'institutions.id:{institution_filter}',
    date_filter,
]

# Add concept filter
if QUERY_PARAMS.get('concepts'):
    concept_ids = '|'.join(QUERY_PARAMS['concepts'])
    filters.append(f'concepts.id:{concept_ids}')

# Add citation filter
if QUERY_PARAMS.get('min_citations'):
    min_cites = QUERY_PARAMS['min_citations']
    filters.append(f'cited_by_count:>{min_cites}')

# Add journal filter
if QUERY_PARAMS.get('journals'):
    journal_ids = '|'.join(QUERY_PARAMS['journals'])
    filters.append(f'primary_location.source.id:{journal_ids}')

# Add open access filter
if QUERY_PARAMS.get('open_access_only'):
    filters.append('is_oa:true')

# Add language filter
if QUERY_PARAMS.get('languages'):
    lang_codes = '|'.join(QUERY_PARAMS['languages'])
    filters.append(f'language:{lang_codes}')

# Add country filter
if QUERY_PARAMS.get('countries'):
    country_codes = '|'.join(QUERY_PARAMS['countries'])
    filters.append(f'authorships.institutions.country_code:{country_codes}')

params = {
    'filter': ','.join(filters),  # Join all filters with comma
    'per-page': per_page,
    'cursor': '*',
    'mailto': self.email,
    'select': 'id,title,abstract_inverted_index,publication_date,publication_year,authorships,primary_location,doi,cited_by_count,concepts,is_open_access,language'
}
```

**3. Run ingestion:**
```powershell
python -m src.sri.ingest_openalex
```

**4. Check results:**
```powershell
python check_papers.py
```

---

### Step 4: Test with Small Sample

Before running full ingestion, test with small sample:

**Edit src/sri/ingest_openalex.py, find run_test_ingestion() function (around line 380):**

```python
def run_test_ingestion():
    """Test ingestion with small sample"""
    ingester = OpenAlexIngester()
    
    papers = ingester.fetch_papers(
        institutions=list(ALL_UNIVERSITIES.values()),
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),  # Just January 2024
        max_papers=50  # Only 50 papers
    )
    
    print(f"Fetched {len(papers)} papers")
    
    # Print samples
    for i, paper in enumerate(papers[:5], 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   Year: {paper['year']}, Citations: {paper['citations']}")
```

**Run test:**
```powershell
python -c "from src.sri.ingest_openalex import run_test_ingestion; run_test_ingestion()"
```

---

### Troubleshooting

**No papers returned:**
- Filters too restrictive - try removing some
- Check institution IDs are correct
- Verify date range has papers

**Too many irrelevant papers:**
- Add concept filters
- Increase min_citations
- Add journal filters
- Narrow date range

**Papers missing abstracts:**
- Some papers don't have abstracts in OpenAlex
- Can't filter by this directly

---

### OpenAlex Filter Documentation

Full docs: https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/filter-entity-lists

**Filter Syntax:**
- `field:value` - Single value
- `field:value1|value2` - OR (either value)
- `field:>value` - Greater than
- `field:<value` - Less than
- `field1:value1,field2:value2` - AND (both conditions)

**Available Filters:**
- `institutions.id`
- `concepts.id`
- `primary_location.source.id`
- `cited_by_count`
- `is_oa`
- `language`
- `from_publication_date`
- `to_publication_date`
- `authorships.institutions.country_code`
- Many more...

---

**Last Updated**: October 8, 2025
