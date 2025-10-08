# Smart Research Insights - API & Database Module# 🔬 Smart Research Insights



**Focus**: OpenAlex API integration and PostgreSQL database management for research paper ingestion.Automated research intelligence system for tracking emerging trends across Australasian universities using BERTopic, OpenAlex API, and PostgreSQL.



This module handles fetching research papers from OpenAlex API and storing them in a Neon PostgreSQL database. The ML/topic modeling and dashboard components are handled separately.## ✨ Features



---- 📊 **Real-time Data Ingestion** - Fetch papers from OpenAlex API with incremental updates

- 🤖 **BERTopic Analysis** - Automatic topic discovery and classification using ML

## 🎯 Purpose- 💾 **PostgreSQL Database** - Neon cloud database for scalable storage

- 📈 **Interactive Dashboard** - Streamlit-based visualization with real-time metrics

- ✅ Fetch relevant research papers from OpenAlex API- 🔄 **Incremental Updates** - Fetch new papers and assign topics without full retraining

- ✅ Store paper metadata in PostgreSQL (Neon cloud)

- ✅ Query refinement and filtering## 📋 Prerequisites

- ✅ Incremental updates and state tracking

- ❌ Topic modeling (handled by partner)- Python 3.11 or higher

- ❌ Dashboard/UI (handled by partner)- Neon PostgreSQL account (free tier available at [neon.tech](https://neon.tech))

- OpenAlex API email (for polite pool rate limits)

---

## 🚀 Quick Start

## 📁 Project Structure

### 1. Clone & Install

```

Smart-Research-insights/```bash

├── .env                          # Environment variables (DB connection, API keys)# Clone the repository

├── .env.example                  # Template for .envgit clone https://github.com/param-patel-08/Smart-Research-insights.git

├── requirements.txt              # Python dependenciescd Smart-Research-insights

├── setup_database.py            # Initialize database schema

├── check_papers.py              # Check database status# Create virtual environment

│python -m venv .venv

├── config/

│   ├── __init__.py# Activate virtual environment

│   └── settings.py              # ⭐ QUERY PARAMETERS - Configure here!# Windows:

│.\.venv\Scripts\activate

├── db/# Mac/Linux:

│   ├── connection.py            # Database connection managementsource .venv/bin/activate

│   ├── models/

│   │   └── models.py           # Database models (Paper, IngestionLog, etc.)# Install dependencies

│   └── init/pip install -r requirements.txt

│       └── 01_papers_schema.sql # Database schema```

│

└── src/### 2. Configure Environment

    └── sri/

        ├── __init__.pyCreate a `.env` file (copy from `.env.example`):

        └── ingest_openalex.py   # OpenAlex API client

``````bash

# Neon PostgreSQL Connection

---NEON_DB_STRING=postgresql://user:password@host.neon.tech/dbname?sslmode=require



## 🚀 Quick Start# OpenAlex API

OPENALEX_EMAIL=your.email@example.com

### 1. Prerequisites

# Analysis Settings

- Python 3.10+ANALYSIS_START_DATE=2019-01-01

- Neon PostgreSQL account (free tier works)ANALYSIS_END_DATE=2024-12-31

- OpenAlex API email (for rate limiting)```



### 2. Installation### 3. Setup Database



```powershell```bash

# Create virtual environment# Initialize database schema

python -m venv .venvpython setup_neon_clean.py

.\.venv\Scripts\Activate.ps1```



# Install dependencies### 4. Ingest Data & Train Model

pip install -r requirements.txt

``````bash

# Test ingestion (5 papers)

### 3. Configurationpython -m src.sri.ingest_openalex --mode test --max-papers 5



Create `.env` file:# Full ingestion (all papers since 2019)

python -m src.sri.ingest_openalex --mode initial

```properties

# Neon PostgreSQL Database# Train BERTopic model

NEON_DB_STRING=postgresql://user:password@host/database?sslmode=requirepython run_training.py

```

# OpenAlex API Configuration

OPENALEX_EMAIL=your-email@example.com### 5. Launch Dashboard



# Date range for initial ingestion```bash

ANALYSIS_START_DATE=2019-01-01streamlit run dashboard/app.py

ANALYSIS_END_DATE=2024-12-31```

```

Visit `http://localhost:8501` to view the dashboard.

### 4. Initialize Database

## 📖 Usage

```powershell

python setup_database.py### Incremental Updates

```

```bash

This creates:# Fetch new papers since last update

- `papers` table - Core paper metadatapython -m src.sri.ingest_openalex --mode incremental

- `ingestion_state` table - Tracks ingestion progress

- `ingestion_logs` table - Audit logs# Assign topics to new papers (fast)

python -m src.sri.assign_new_topics

### 5. Run Initial Ingestion```



```powershell### Dashboard Features

python -m src.sri.ingest_openalex

```- **🔄 Fetch Latest** - Incremental paper ingestion

- **♻️ Retrain** - Full model retraining with all papers

Or programmatically:- **🔄 Refresh Data** - Clear cache and reload from database

- **📊 Filters** - Theme, university, date range, confidence

```python- **📈 Visualizations** - Topic trends, growth rates, citations

from src.sri.ingest_openalex import run_initial_ingestion

## 🗂️ Project Structure

result = run_initial_ingestion()

print(f"Fetched {result['papers_added']} papers")```

```Smart-Research-insights/

├── dashboard/          # Streamlit dashboard

### 6. Check Status│   └── app.py

├── src/sri/           # Core modules

```powershell│   ├── ingest_openalex.py    # Data ingestion

python check_papers.py│   ├── train_topics.py       # BERTopic training

```│   └── assign_new_topics.py  # Incremental assignment

├── db/                # Database models & connection

---│   ├── connection.py

│   ├── models/

## 🔧 Query Refinement│   └── init/

├── config/            # Configuration

**The main issue you're facing**: Not fetching relevant papers.│   ├── settings.py

│   └── themes.py

### Current Query Structure├── artifacts/         # Saved models

├── data/             # CSV fallback data

Located in `src/sri/ingest_openalex.py`, line 58:└── check_db.py       # Database verification script

```

```python

params = {## 🔧 Utilities

    'filter': f'institutions.id:{institution_filter},{date_filter}',

    'per-page': 200,### Check Database Status

    'select': 'id,title,abstract_inverted_index,...'

}```bash

```python check_db.py

```

### How to Refine Queries

Shows:

Edit `config/settings.py`:- Papers count

- Topics count  

#### 1. **Add/Remove Institutions**- Assignments count

- Active model version

```python

ALL_UNIVERSITIES = {## 🐛 Troubleshooting

    'Babcock': 'I4210131357',

    'MIT': 'I136199984',          # Add more### Database Connection Issues

    'Stanford': 'I97018004',       # Add more

}```bash

```# Test connection

python -c "from db.connection import test_connection; test_connection()"

**Finding Institution IDs:**

1. Go to https://openalex.org/# Check database status

2. Search for institutionpython check_db.py

3. Copy ID from URL: `https://openalex.org/I4210131357` → use `I4210131357````



#### 2. **Filter by Research Topics/Concepts**### Cache Issues



```pythonIf dashboard shows old data:

QUERY_PARAMS = {1. Click "🔄 Refresh Data" button

    'concepts': [2. Or restart: `streamlit run dashboard/app.py`

        'C41008148',  # Computer Science

        'C71924100',  # Medicine### Model Loading Errors

        'C15744967',  # Psychology

    ],```bash

}# Retrain model

```python run_training.py



**Finding Concept IDs:**# Check if model exists

- Browse: https://openalex.org/conceptsdir artifacts\bertopic_model*  # Windows

- Search for your topic, copy the concept IDls artifacts/bertopic_model*   # Mac/Linux

```

Then modify `ingest_openalex.py` to use these filters.

## 📊 Database Schema

#### 3. **Filter by Citation Count**

- **papers** - Publication metadata (16K+ papers)

```python- **topics** - BERTopic discovered topics

QUERY_PARAMS = {- **paper_topics** - Assignment relationships

    'min_citations': 10,  # Only papers with 10+ citations- **embeddings** - Cached sentence embeddings

}- **models** - Model version tracking

```- **ingestion_state** - Incremental update state

- **ingestion_logs** - Audit trail

#### 4. **Open Access Only**

## 🤝 Contributing

```python

QUERY_PARAMS = {This is an academic research project. For questions or contributions:

    'open_access_only': True,  # Only free papers1. Fork the repository

}2. Create a feature branch

```3. Submit a pull request



#### 5. **Filter by Specific Journals**## 📄 License



```pythonAcademic research project - All rights reserved.

QUERY_PARAMS = {

    'journals': [## 🙏 Acknowledgments

        'S2764455859',  # Nature

        'S4210194219',  # Science- **OpenAlex** - Open access to scholarly metadata

    ],- **Neon** - Serverless PostgreSQL database

}- **BERTopic** - Topic modeling framework

```- **Sentence Transformers** - Document embeddings



**Finding Journal IDs:**---

- Search journal at https://openalex.org/sources

- Copy source ID from URL**Built with ❤️ for research intelligence**


#### 6. **Filter by Country**

```python
QUERY_PARAMS = {
    'countries': ['GB', 'US'],  # UK and US only
}
```

#### 7. **Language Filter**

```python
QUERY_PARAMS = {
    'languages': ['en'],  # English only (default)
}
```

### Advanced Query Refinement

To implement these filters, modify `src/sri/ingest_openalex.py`:

```python
def fetch_papers(self, institutions, start_date, end_date, ...):
    # Build filter string
    filters = [
        f'institutions.id:{institution_filter}',
        date_filter,
    ]
    
    # Add concept filter
    if QUERY_PARAMS.get('concepts'):
        concept_filter = '|'.join(QUERY_PARAMS['concepts'])
        filters.append(f'concepts.id:{concept_filter}')
    
    # Add citation filter
    if QUERY_PARAMS.get('min_citations'):
        filters.append(f'cited_by_count:>{QUERY_PARAMS["min_citations"]}')
    
    # Add open access filter
    if QUERY_PARAMS.get('open_access_only'):
        filters.append('is_oa:true')
    
    params = {
        'filter': ','.join(filters),
        'per-page': per_page,
        ...
    }
```

---

## 📊 Database Schema

### Papers Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `openalex_id` | VARCHAR | OpenAlex work ID (unique) |
| `title` | TEXT | Paper title |
| `abstract` | TEXT | Abstract text |
| `publication_date` | DATE | Publication date |
| `year` | INTEGER | Publication year |
| `authors` | JSONB | Array of author names/info |
| `journal` | VARCHAR | Journal/venue name |
| `doi` | VARCHAR | Digital Object Identifier |
| `url` | TEXT | OpenAlex URL |
| `citations` | INTEGER | Citation count |
| `university` | VARCHAR | Primary institution |
| `institution_id` | VARCHAR | OpenAlex institution ID |
| `concepts` | JSONB | Research concepts with scores |
| `primary_field` | VARCHAR | Main research field |
| `language` | VARCHAR | Paper language |
| `is_open_access` | BOOLEAN | Open access flag |
| `last_synced` | TIMESTAMP | Last sync timestamp |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

---

## 🔍 Querying the Database

### Using Models

```python
from db.models.models import Paper

# Get all papers
papers = Paper.get_all(limit=100)

# Search papers
papers = Paper.search(
    keyword='machine learning',
    university='Babcock',
    year_from=2020,
    year_to=2024,
    min_citations=10
)

# Count papers
count = Paper.count()

# Get by OpenAlex ID
paper = Paper.get_by_openalex_id('W2741809807')
```

### Direct SQL Queries

```python
from db.connection import get_db_cursor

with get_db_cursor() as cur:
    cur.execute("""
        SELECT title, year, citations 
        FROM papers 
        WHERE year >= 2020 
        ORDER BY citations DESC 
        LIMIT 10
    """)
    results = cur.fetchall()
    
    for row in results:
        print(f"{row['title']} ({row['year']}) - {row['citations']} citations")
```

---

## 🔄 Incremental Updates

After initial ingestion, run incremental updates:

```python
from src.sri.ingest_openalex import run_incremental_ingestion

result = run_incremental_ingestion()
print(f"Added {result['papers_added']} new papers")
```

This fetches only papers published since last ingestion.

---

## 🐛 Troubleshooting

### Empty Database After Running

Check:
1. `.env` has correct `NEON_DB_STRING`
2. `config/settings.py` has valid institution IDs
3. Date range in `.env` is reasonable (not too far in past/future)

```powershell
python check_papers.py
```

### API Rate Limiting

OpenAlex allows ~100,000 requests/day for polite API users. Always:
- Set `OPENALEX_EMAIL` in `.env`
- Don't remove `mailto` parameter from API calls

### No Papers Match Filters

Your filters might be too restrictive. Try:
1. Remove concept filters temporarily
2. Expand date range
3. Lower citation minimum
4. Check institution IDs are correct

### Database Connection Errors

Verify Neon connection string:
```powershell
python -c "from db.connection import test_connection; test_connection()"
```

---

## 📖 OpenAlex API Documentation

- **Main Docs**: https://docs.openalex.org/
- **Filtering**: https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/filter-entity-lists
- **Search Institutions**: https://openalex.org/institutions
- **Search Concepts**: https://openalex.org/concepts
- **Search Journals**: https://openalex.org/sources

---

## 🤝 Division of Work

**Your Responsibility (API + Database):**
- ✅ Fetch papers from OpenAlex
- ✅ Filter and refine queries
- ✅ Store papers in database
- ✅ Maintain database schema
- ✅ Provide clean data to partner

**Partner's Responsibility (ML + Dashboard):**
- ❌ BERTopic training
- ❌ Topic assignment
- ❌ Streamlit dashboard
- ❌ Visualizations

---

## 📝 Example Workflow

```python
# 1. Initialize database (one time)
from setup_database import init_database
init_database()

# 2. Configure query in config/settings.py
# Edit ALL_UNIVERSITIES, QUERY_PARAMS, etc.

# 3. Run initial ingestion
from src.sri.ingest_openalex import run_initial_ingestion
result = run_initial_ingestion()

# 4. Check results
from db.models.models import Paper
print(f"Total papers: {Paper.count()}")

# 5. Query papers
papers = Paper.search(
    keyword='artificial intelligence',
    year_from=2020,
    min_citations=5
)

# 6. Run incremental updates daily/weekly
from src.sri.ingest_openalex import run_incremental_ingestion
run_incremental_ingestion()
```

---

## 🔑 Key Files to Edit

1. **`config/settings.py`** - Query parameters, institutions, filters
2. **`src/sri/ingest_openalex.py`** - API client, filter logic
3. **`.env`** - Database connection, API email
4. **`db/models/models.py`** - Database queries, search methods

---

## 📦 Dependencies

```
psycopg2-binary==2.9.9    # PostgreSQL driver
python-dotenv==1.0.0       # Environment variables
requests==2.31.0           # HTTP client
tqdm==4.66.1              # Progress bars
```

---

## 📧 Support

For OpenAlex API issues: https://groups.google.com/g/openalex-users
For Neon database issues: https://neon.tech/docs

---

**Last Updated**: October 8, 2025
**Focus**: API + Database only (no ML/Dashboard)
