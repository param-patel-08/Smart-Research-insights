##   License
Academic research project - All rights reserved.

---

Automated research intelligence system for tracking emerging trends across Australasian universities using BERTopic and OpenAlex API.

##   Troubleshooting

##   Quarterly Updates
babcock-research-trends/
    config/
        themes.py              # Babcock's 9 strategic themes
        settings.py            # Configuration settings
    data/
        raw/                   # Raw collected papers
        processed/             # Preprocessed data
        exports/               # Generated reports
    tests/
        test_setup.py          # Environment validation script
        test_focused.py        # Targeted pipeline checks
    src/
        openalex_collector.py  # OpenAlex data collection
        paper_preprocessor.py  # Data preprocessing
        preprocessor.py        # Legacy/simple preprocessor example
        topic_analyzer.py      # BERTopic topic modeling
        theme_mapper.py        # Map topics to Babcock themes
        trend_analyzer.py      # Trend analysis
    dashboard/
        app.py                 # Streamlit dashboard
    run_full_analysis.py      # Full pipeline runner
    view_results.py           # Text summary explorer
    .env                       # Your configuration (create this)
    .env.example               # Configuration template
    requirements.txt           # Python dependencies
    README.md                  # This file

Follow these steps on Windows (PowerShell):

```powershell
# 1) Optional: create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Create .env with your OpenAlex polite pool email
"OPENALEX_EMAIL=your.email@domain.com" | Out-File -FilePath .env -Encoding utf8
```

## Testing your setup

Basic environment checks:

```powershell
python tests/test_setup.py
```

Focused quick check (config, modules, API):

```powershell
python tests/test_focused.py
```
Both scripts will print PASS/FAIL and next steps.

## Run the analysis

```powershell
python run_full_analysis.py
# Choose: 1 (quick), 2 (medium), or 3 (full)
- **Option B: step-by-step (manual control)**

```powershell
# 1) Collect papers from OpenAlex
python src/openalex_collector.py

# 2) Preprocess papers (cleans text and writes metadata/documents)
python src/paper_preprocessor.py

# 3) Topic modeling (BERTopic)
python src/topic_analyzer.py

# 4) Map topics to Babcock themes
python src/theme_mapper.py

# 5) Trend analysis and strategic priorities
python src/trend_analyzer.py
```

## View results

- Quick text summary:

```powershell
python view_results.py
```

- Interactive dashboard:

```powershell
streamlit run dashboard/app.py
```

## Outputs (key files)

- Raw papers: `data/raw/papers_raw.csv`
- Processed metadata: `data/processed/metadata.csv`
- Papers with topics: `data/processed/papers_processed.csv`
- Topics over time: `data/processed/topics_over_time.csv`
- Topic-theme mapping: `data/processed/topic_mapping.json`
- Trend analysis results: `data/processed/trend_analysis.json`
- BERTopic model: `models/bertopic_model.pkl`
- Logs: `logs/full_analysis_*.log`

All file paths are configurable in `config/settings.py`.

## Troubleshooting

- Missing packages: run `pip install -r requirements.txt`.
- `.env` missing: create it with your email (see Setup).
- OpenAlex rate limits: wait and retry; email must be set for polite pool.
- Memory/time: start with quick mode (choice 1) in `run_full_analysis.py`.
- Few or no results: verify university IDs and dates in `config/settings.py`.

For a more detailed walkthrough, see `Quick_start.md`.