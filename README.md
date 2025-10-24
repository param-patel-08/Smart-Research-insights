# Smarter Research Insights##   License

Academic research project - All rights reserved.

AI-Powered Research Intelligence Dashboard for tracking emerging trends across Australasian universities using BERTopic and OpenAlex API.

---

## Overview

Automated research intelligence system for tracking emerging trends across Australasian universities using BERTopic and OpenAlex API.

This system automatically collects, analyzes, and visualizes research publications from 43+ Australian and New Zealand universities, mapping them to Babcock International's 9 strategic technology themes.

##   Troubleshooting

## Project Structure

```
Smart-Research-insights/
├── .env                           # Environment variables (create from .env.example)
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── README.md                      # Main documentation (this file)
├── requirements.txt               # Python dependencies
│
├── scripts/                       # ⭐ User-facing executables
│   ├── launch_dashboard.py        # Start Streamlit dashboard
│   ├── run_full_analysis.py       # Run full pipeline
│   ├── view_results.py            # View analysis results
│   └── reprocess_existing_data.py # Reprocess without re-collecting
│
├── config/                        # Configuration
│   ├── __init__.py
│   ├── settings.py                # Settings and constants (universities, dates)
│   └── themes.py                  # Babcock's 9 strategic themes
│
├── src/                           # Core pipeline modules
│   ├── __init__.py
│   ├── theme_based_collector.py   # Collect papers from OpenAlex (theme-filtered)
│   ├── paper_preprocessor.py      # Text cleaning and preprocessing
│   ├── topic_analyzer.py          # BERTopic topic modeling
│   ├── theme_mapper.py            # Topic-to-theme mapping
│   ├── trend_analyzer.py          # Trend analysis and metrics
│   └── emerging_topics_detector.py # Detect emerging topics
│
├── dashboard/                     # Streamlit dashboard
│   ├── __init__.py
│   ├── app.py                     # Main dashboard application
│   ├── theme.css                  # Custom dark theme styling
│   ├── components/                # Reusable UI components
│   │   ├── __init__.py
│   │   └── filters.py             # Filter panel
│   ├── tabs/                      # Dashboard tabs
│   │   ├── __init__.py
│   │   ├── overview_tab.py        # System overview
│   │   ├── trends_tab.py          # Trend analysis
│   │   ├── emerging_topics_tab.py # Emerging topics
│   │   ├── theme_analysis_tab.py  # Theme analysis
│   │   ├── universities_tab.py    # University metrics
│   │   └── data_quality_tab.py    # Data quality metrics
│   └── utils/                     # Dashboard utilities
│       ├── __init__.py
│       ├── data_loader.py         # Data loading functions
│       ├── visualizations.py      # Plotly chart builders
│       ├── insights.py            # Insight generation
│       └── styling.py             # Style utilities
│
├── tests/                         # Test suite
│   ├── test_setup.py              # Environment validation
│   ├── test_focused.py            # Focused pipeline tests
│   └── debug/                     # Debug & one-time scripts
│       ├── test_*.py              # Test scripts
│       ├── debug_*.py             # Debug utilities
│       ├── diagnose_*.py          # Diagnostic scripts
│       ├── analyze_relevance.py   # Relevance analysis
│       ├── check_unis.py          # University check
│       └── fix_imports.py         # Import fixer
│
├── data/                          # Data storage
│   ├── raw/                       # Raw collected papers
│   ├── processed/                 # Processed data & analysis
│   └── topic_labels_cache.json    # Cached topic labels
│
├── docs/                          # Documentation
│   ├── Quick_start.md             # Quick start guide
│   ├── report.md                  # Technical report
│   ├── ORGANIZATION_FINAL.md      # File organization decisions
│   └── *.md                       # Various documentation files
│
├── logs/                          # Log files
└── models/                        # Trained models
    └── bertopic_model.pkl         # Saved BERTopic model
```

## Quick Start

│

├── run_full_analysis.py       # MAIN PIPELINE ORCHESTRATOR## Run the analysis

├── launch_dashboard.py        # Dashboard launcher

├── view_results.py            # CLI results viewer```powershell

├── requirements.txt           # Python dependenciespython run_full_analysis.py

├── .env.example               # Environment variables template# Choose: 1 (quick), 2 (medium), or 3 (full)

└── README.md                  # This file- **Option B: step-by-step (manual control)**

```

```powershell

## Quick Start# 1) Collect papers from OpenAlex

### 1. Setup Environment

```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
Copy-Item .env.example .env
# Edit .env and add your OpenAlex email
```

## View results

### 2. Run Analysis Pipeline

```powershell
# Full pipeline with interactive mode selection
python scripts/run_full_analysis.py

# Options:
# 1. Quick test (3 universities, ~1000-1500 papers) - 8-10 minutes
# 2. Medium test (10 universities, ~4000-6000 papers) - 20-25 minutes
# 3. Full collection (43 universities, ~15000-25000 papers) - 60-120 minutes
```

### 3. View Results

```powershell
# Text-based summary
python scripts/view_results.py

# Interactive dashboard
python scripts/launch_dashboard.py
# or
streamlit run dashboard/app.py
```

## Key Output Files

- Raw papers: `data/raw/papers_raw.csv`
- Processed metadata: `data/processed/metadata.csv`
- Papers with topics: `data/processed/papers_processed.csv`
- Topics over time: `data/processed/topics_over_time.csv`
- Topic-theme mapping: `data/processed/topic_mapping.json`
- Trend analysis results: `data/processed/trend_analysis.json`
- BERTopic model: `models/bertopic_model.pkl`
- Logs: `logs/full_analysis_*.log`




## Main ExecutablesAll file paths are configurable in `config/settings.py`.



### `run_full_analysis.py`## Troubleshooting

Main pipeline orchestrator that runs the complete analysis workflow:

1. Data collection from OpenAlex- Missing packages: run `pip install -r requirements.txt`.

2. Text preprocessing and cleaning- `.env` missing: create it with your email (see Setup).

3. BERTopic topic modeling- OpenAlex rate limits: wait and retry; email must be set for polite pool.

4. Theme mapping- Memory/time: start with quick mode (choice 1) in `run_full_analysis.py`.

5. Trend analysis- Few or no results: verify university IDs and dates in `config/settings.py`.



### `launch_dashboard.py`For a more detailed walkthrough, see `Quick_start.md`.
Launches the Streamlit dashboard for interactive exploration.

### `view_results.py`
Command-line results viewer for quick summaries.

## Pipeline Stages

### Stage 1: Data Collection
- Fetches papers from OpenAlex API filtered by themes
- Deduplicates and validates institution IDs
- Outputs: `data/raw/papers_raw.csv`

### Stage 2: Preprocessing
- Cleans abstracts, removes stopwords
- Tokenizes and lemmatizes text
- Outputs: `data/processed/metadata.csv`, `documents.txt`

### Stage 3: Topic Modeling
- Trains BERTopic with UMAP + HDBSCAN
- Assigns topics to papers
- Outputs: `models/bertopic_model.pkl`, `papers_processed.csv`

### Stage 4: Theme Mapping
- Maps discovered topics to Babcock themes
- Calculates similarity scores
- Outputs: `data/processed/topic_mapping.json`

### Stage 5: Trend Analysis
- Computes growth metrics and emerging topics
- Generates strategic priority scores
- Outputs: `data/processed/trend_analysis.json`

## Configuration

### Key Settings (`config/settings.py`)
- `OPENALEX_EMAIL`: Your email for OpenAlex polite pool
- `ANALYSIS_START_DATE`: Start date for analysis
- `ANALYSIS_END_DATE`: End date for analysis
- `ALL_UNIVERSITIES`: Dictionary of universities and OpenAlex IDs
- File paths and analysis parameters

### Strategic Themes (`config/themes.py`)
- 9 parent themes with hierarchical sub-themes
- Keyword dictionaries for theme detection
- Priority levels and descriptions

## Testing

```powershell
# Environment validation
python tests/test_setup.py

# Pipeline checks
python tests/test_focused.py
```

## Data Outputs

### Processed Datasets
- `papers_raw.csv`: Raw collected papers
- `papers_processed.csv`: Papers with topic assignments
- `metadata.csv`: Cleaned metadata
- `topic_mapping.json`: Topic-theme mappings
- `trend_analysis.json`: Trend metrics and insights

### Models
- `bertopic_model.pkl`: Trained BERTopic model (reusable)

## Technology Stack

- **Data Collection**: OpenAlex API, requests
- **Text Processing**: NLTK, scikit-learn
- **Topic Modeling**: BERTopic, sentence-transformers, UMAP, HDBSCAN
- **Visualization**: Plotly, Plotly Express
- **Dashboard**: Streamlit
- **Data Handling**: pandas, numpy

## Troubleshooting

### Common Issues

**OpenAlex rate limits**
- Ensure `OPENALEX_EMAIL` is set in `.env`
- Use quick mode for testing

**Missing dependencies**
```powershell
pip install -r requirements.txt
```

**Memory issues**
- Start with quick mode (option 1)
- Reduce `MAX_PAPERS_PER_UNIVERSITY` in settings

**No results**
- Verify university IDs in `config/settings.py`
- Check date range settings
- Review logs in `logs/` directory

## Documentation

See `docs/` folder for detailed documentation:
- `report.md`: Comprehensive technical report
- `Quick_start.md`: Detailed quick start guide
- Feature-specific documentation files

## License

Academic research project - All rights reserved.

## Contact

For questions or issues, please refer to the project documentation or contact the development team.
