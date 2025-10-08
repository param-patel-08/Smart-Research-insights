# Project Reset - API & Database Focus

**Date**: October 8, 2025  
**Purpose**: Stripped down project to focus ONLY on OpenAlex API and Database (no ML/Dashboard)

---

## ✅ What Was Done

### 1. Removed All ML/Dashboard Components
**Deleted:**
- ❌ `dashboard/` - Entire Streamlit dashboard
- ❌ `artifacts/` - BERTopic model files
- ❌ `models/` - Model storage
- ❌ `logs/` - Training logs
- ❌ `data/` - CSV files
- ❌ `src/sri/train_topics.py` - BERTopic training script
- ❌ `src/sri/assign_new_topics.py` - Topic assignment
- ❌ `run_training.py` - Training launcher
- ❌ All test/utility scripts

**Kept:**
- ✅ `src/sri/ingest_openalex.py` - OpenAlex API client
- ✅ `db/` - Database connection and models
- ✅ `config/` - Query configuration

### 2. Simplified Database Schema
**Removed tables:**
- ❌ `topics` - BERTopic topics
- ❌ `paper_topics` - Paper-topic assignments
- ❌ `embeddings` - Cached embeddings
- ❌ `models` - Model metadata

**Kept tables:**
- ✅ `papers` - Core paper metadata (with new fields)
- ✅ `ingestion_state` - Track ingestion progress
- ✅ `ingestion_logs` - Audit logs

**New fields in papers table:**
- `concepts` (JSONB) - OpenAlex research concepts
- `primary_field` (VARCHAR) - Main research area
- `language` (VARCHAR) - Paper language
- `is_open_access` (BOOLEAN) - Open access flag

### 3. Created New Configuration System
**File**: `config/settings.py`

Contains:
- `ALL_UNIVERSITIES` - Institution IDs to query
- `QUERY_PARAMS` - Filter parameters (concepts, citations, journals, etc.)
- `OPENALEX_SELECT_FIELDS` - Fields to retrieve from API

### 4. Created Documentation
- ✅ `README.md` - Complete setup and usage guide
- ✅ `QUERY_REFINEMENT.md` - Step-by-step query refinement guide
- ✅ `.env.example` - Template for environment variables

### 5. Minimal Dependencies
Removed 20+ packages, kept only:
- `psycopg2-binary` - PostgreSQL driver
- `python-dotenv` - Environment variables
- `requests` - HTTP client
- `tqdm` - Progress bars
- `python-dateutil` - Date utilities

---

## 📁 Final Structure

```
Smart-Research-insights/
├── .env                          # Your config (not in git)
├── .env.example                  # Template
├── .gitignore
├── requirements.txt              # Minimal dependencies
├── README.md                     # Main documentation
├── QUERY_REFINEMENT.md          # Query tuning guide
├── THIS_SUMMARY.md              # This file
│
├── setup_database.py             # Initialize Neon DB
├── check_papers.py               # Check database status
│
├── config/
│   ├── __init__.py
│   └── settings.py               # ⭐ CONFIGURE HERE
│
├── db/
│   ├── connection.py             # DB connection pool
│   ├── models/
│   │   └── models.py            # Paper, IngestionLog, IngestionState
│   └── init/
│       └── 01_papers_schema.sql # Database schema
│
└── src/
    └── sri/
        ├── __init__.py
        └── ingest_openalex.py    # OpenAlex API client
```

---

## 🚀 Quick Start

### 1. Setup
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install minimal dependencies
pip install -r requirements.txt
```

### 2. Configure
Edit `.env`:
```properties
NEON_DB_STRING=postgresql://...
OPENALEX_EMAIL=your-email@example.com
ANALYSIS_START_DATE=2019-01-01
ANALYSIS_END_DATE=2024-12-31
```

Edit `config/settings.py`:
```python
ALL_UNIVERSITIES = {
    'Babcock': 'I4210131357',
    # Add more institutions
}

QUERY_PARAMS = {
    'concepts': [],  # Add concept IDs to filter
    'min_citations': None,
    'open_access_only': False,
    'languages': ['en'],
}
```

### 3. Initialize Database
```powershell
python setup_database.py
```

### 4. Run Ingestion
```powershell
# Test with small sample first
python -c "from src.sri.ingest_openalex import run_test_ingestion; run_test_ingestion()"

# Full ingestion
python -m src.sri.ingest_openalex
```

### 5. Check Results
```powershell
python check_papers.py
```

---

## 🔧 Refining Queries

### The Main Problem
**Issue**: Not fetching relevant papers

**Solution**: Add filters to `config/settings.py` and modify `src/sri/ingest_openalex.py`

### Quick Examples

**Filter by research topic:**
```python
# In config/settings.py
QUERY_PARAMS = {
    'concepts': ['C41008148'],  # Computer Science
}

# In src/sri/ingest_openalex.py (line 58+)
if QUERY_PARAMS.get('concepts'):
    concept_ids = '|'.join(QUERY_PARAMS['concepts'])
    filters.append(f'concepts.id:{concept_ids}')
```

**Filter by citation count:**
```python
# In config/settings.py
QUERY_PARAMS = {
    'min_citations': 10,
}

# In src/sri/ingest_openalex.py
if QUERY_PARAMS.get('min_citations'):
    filters.append(f'cited_by_count:>{QUERY_PARAMS["min_citations"]}')
```

**See `QUERY_REFINEMENT.md` for complete guide.**

---

## 📊 Database API

### Query Papers
```python
from db.models.models import Paper

# Count
count = Paper.count()

# Get all with pagination
papers = Paper.get_all(limit=100, offset=0)

# Search with filters
papers = Paper.search(
    keyword='machine learning',
    university='Babcock',
    year_from=2020,
    year_to=2024,
    min_citations=10,
    limit=100
)

# Get by ID
paper = Paper.get_by_openalex_id('W2741809807')
```

### Bulk Insert
```python
from db.models.models import Paper

papers_list = [
    {
        'openalex_id': 'W123',
        'title': 'Example Paper',
        'publication_date': date(2024, 1, 1),
        'year': 2024,
        # ... other fields
    },
    # ... more papers
]

count = Paper.bulk_insert(papers_list)
print(f"Inserted {count} papers")
```

---

## 🤝 Division of Work

| You (API + DB) | Partner (ML + UI) |
|----------------|-------------------|
| ✅ Fetch papers from OpenAlex | BERTopic training |
| ✅ Filter/refine queries | Topic modeling |
| ✅ Store in Neon database | Topic assignment |
| ✅ Maintain schema | Dashboard UI |
| ✅ Provide clean data | Visualizations |

---

## 📖 Key Documentation

### Internal Docs
1. **README.md** - Complete setup guide
2. **QUERY_REFINEMENT.md** - How to tune queries
3. **config/settings.py** - Inline comments for all parameters

### External Docs
- OpenAlex API: https://docs.openalex.org/
- OpenAlex Filtering: https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/filter-entity-lists
- Neon Docs: https://neon.tech/docs

---

## 🎯 Next Steps

### Immediate
1. ✅ Review configuration in `config/settings.py`
2. ✅ Add your Neon connection string to `.env`
3. ✅ Run `python setup_database.py`
4. ✅ Test ingestion with small sample
5. ✅ Check results with `python check_papers.py`

### Query Refinement
1. Identify which papers are irrelevant
2. Find appropriate filters (concepts, journals, citations)
3. Add filters to `config/settings.py`
4. Implement filter logic in `src/sri/ingest_openalex.py`
5. Test and iterate

### Ongoing
- Run incremental ingestion daily/weekly
- Monitor paper quality
- Adjust filters as needed
- Provide database access to partner for ML work

---

## ⚠️ Important Notes

### For You
- Database schema has NO topic/ML tables
- Your partner will add those separately
- Focus on getting RELEVANT papers only
- Quality over quantity

### For Your Partner
- Papers table has all metadata ready
- No embeddings/topics pre-computed
- Schema can be extended (add new tables)
- Don't modify papers table structure

---

**Status**: ✅ Ready for API + Database work  
**Database**: Empty (run setup_database.py)  
**Next Action**: Configure and run initial ingestion  
