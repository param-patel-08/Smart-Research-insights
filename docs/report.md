# Smarter Research Insights: Codebase Overview

This document summarises the repository structure, data flow, and design decisions behind the Smarter Research Insights proof of concept. It is written to help you and any external AI tooling quickly grasp how the code functions without generating a full narrative report.

---

## Chapter 1. Problem Context and Objectives

### 1.1 Motivation
Babcock International monitors nine strategic technology pillars (for example AI, defence security, marine systems, energy sustainability). The company needs an automated way to trace academic publications from Australian and New Zealand universities across those priorities. Manual curation does not scale, so the project delivers a pipeline that
- collects OpenAlex publications for a configurable university set and date range,
- maps unstructured research outputs onto Babcock's strategic taxonomy, and
- exposes insights through reproducible datasets and a Streamlit dashboard.

### 1.2 Core Requirements
- Harvest scholarly works programmatically, handling rate limits and institution lookups.
- Clean and embed text so that unsupervised topic models can discover latent research areas.
- Quantify temporal trends (growth, recency, volume) and highlight emerging topics.
- Ship the results as both machine-readable assets (CSV, JSON, Pickle) and interactive visualisations.
- Keep configuration externalised so analysts can retune the system without editing core modules.

### 1.3 Current Scope
The proof of concept focuses on peer-reviewed publications between January 2020 and December 2024 for the major universities listed in `config/settings.py`. The taxonomy originates from `config/themes.py` and comprises nine themes with 40+ sub-themes.

---

## Chapter 2. Technical Foundations

### 2.1 Topic Modelling Stack
- **SentenceTransformer embeddings** (all-MiniLM-L6-v2) capture semantic meaning of cleaned abstracts.
- **UMAP** reduces embedding dimensionality to prepare for density clustering.
- **HDBSCAN** groups papers into topics without predefining cluster counts.
- **BERTopic** orchestrates the above, generates keyword representations, and provides `topics_over_time` outputs.

### 2.2 Analytics Concepts
- **Entity resolution** matches raw institution strings to OpenAlex IDs.
- **ETL pipeline** stages (extract, transform, load) are chained inside `run_full_analysis.py`.
- **Temporal aggregation** (monthly or quarterly) powers trend analytics.
- **Explainable mapping** via TF-IDF similarity aligns discovered topics with curated keywords.

### 2.3 Supporting Libraries
Key dependencies include `requests`, `pandas`, `numpy`, `bertopic`, `sentence-transformers`, `umap-learn`, `hdbscan`, `plotly`, and `streamlit`. Requirements are listed in `requirements.txt`.

---

## Chapter 3. Architecture Overview

### 3.1 Layered Design
1. **Data acquisition layer**
	- `src/openalex_collector.py`: generic OpenAlex client (pagination, retries, institution resolution helper).
	- `src/theme_based_collector.py`: issues theme-filtered queries using keyword lists.
2. **Processing and modelling layer**
	- `src/paper_preprocessor.py`: text cleaning and metadata preparation.
	- `src/topic_analyzer.py`: BERTopic configuration, training, persistence.
	- `src/theme_mapper.py`: TF-IDF cosine similarity between topic keywords and strategic keyword sets.
	- `src/trend_analyzer.py`: temporal trend metrics, growth, emerging topic detection.
	- `src/emerging_topics_detector.py`: optional LLM-assisted labelling for emerging clusters.
3. **Persistence layer**
	- `data/raw`: raw OpenAlex exports per run.
	- `data/processed`: cleaned documents, metadata, embeddings, topic assignments, trend summaries.
	- `models/`: stored BERTopic model.
4. **Presentation layer**
	- `dashboard/`: Streamlit application with modular tabs and Plotly charts.
	- `view_results.py`: console summary of pipeline outputs.

### 3.2 Data Flow
1. **Configuration**: Set environment variables (OpenAlex email), universities, date range, thresholds in `config/settings.py`. Define themes and keywords in `config/themes.py`.
2. **Collection**: `ThemeBasedCollector.fetch_all_themes` loops through universities and themes, calls OpenAlex, and writes `data/raw/papers_raw.csv` after deduplication.
3. **Preprocessing**: `PaperPreprocessor.preprocess_abstracts` cleans abstracts, filters short texts, and saves processed documents plus metadata to `data/processed`.
4. **Topic modelling**: `BabcockTopicAnalyzer.fit_transform` trains BERTopic, assigns topic IDs/probabilities, stores `models/bertopic_model.pkl`, `data/processed/papers_processed.csv`, and `data/processed/topics_over_time.csv`.
5. **Theme mapping**: `ThemeMapper.create_theme_mapping` calculates cosine similarity scores and writes `data/processed/topic_mapping.json`.
6. **Trend analysis**: `TrendAnalyzer.analyze_theme_trends` and `TrendAnalyzer.identify_emerging_topics` produce `data/processed/trend_analysis.json`.
7. **Visualisation**: `dashboard/app.py` uses `dashboard/utils/data_loader.py` to load processed artifacts, renders plots from `dashboard/utils/visualizations.py`, and applies styling from `dashboard/theme.css`.

`run_full_analysis.py` orchestrates all stages with banners, logging, and selectable run scope (quick, medium, full).

### 3.3 Module Interactions
- `run_full_analysis.py` imports configuration, instantiates collectors, preprocessors, and analyzers sequentially, and terminates early if any stage fails.
- `ThemeMapper` feeds its JSON output to `TrendAnalyzer`, which in turn supplies data for dashboard trend and emerging topic views.
- `dashboard/components/filters.py` captures user selections that downstream visualisation functions consume.
- `dashboard/tabs/*` modules are thin wrappers that call chart builders with the filtered dataset.

---

## Chapter 4. Implementation and Methodology

### 4.1 Data Collection (`src/theme_based_collector.py`)
- Builds OpenAlex query strings combining university IDs, publication dates, and theme keywords.
- Handles pagination and rate limiting by attaching the configured email to each request.
- Uses `OpenAlexCollector.resolve_institution` to validate IDs, search for alternatives, and cache results.
- Supports quick (3 universities), medium (10), and full (43) modes controlled by `run_full_analysis.py`.

### 4.2 Text Processing (`src/paper_preprocessor.py`)
- Removes HTML tags, lowercases text, collapses whitespace, and optionally strips accents.
- Drops abstracts shorter than `MIN_ABSTRACT_LENGTH` (configurable).
- Emits `documents.txt` (one cleaned abstract per line) and `metadata.csv` retaining title, authors, university, citations, date, and the original theme label.

### 4.3 Topic Modelling (`src/topic_analyzer.py`)
- Constructs a BERTopic instance with UMAP and HDBSCAN tuned for academic corpora.
- Supports loading/saving embeddings via `embeddings_path` to speed up reruns.
- Provides helper methods: `create_bertopic_model`, `fit_transform`, `get_topics_over_time`, `save_model`.
- After training, appends topic IDs and probabilities to metadata and writes `papers_processed.csv`.

### 4.4 Theme Mapping (`src/theme_mapper.py`)
- Initialises with global and per-theme similarity thresholds.
- For each topic, obtains top keywords from BERTopic, computes TF-IDF cosine similarity, and determines the best matching theme.
- Produces a mapping dict containing selected theme, similarity scores for all themes, sub-theme matches (using hierarchical keywords), and flags for cross-theme topics.
- Persists results to `topic_mapping.json` for downstream analytics and dashboard use.

### 4.5 Trend Analytics (`src/trend_analyzer.py`)
- Ensures a `theme` column exists (taken from mapping if not present).
- Groups by theme and quarter, computing publication counts, average growth, top contributing topics, and leading universities.
- `identify_emerging_topics` blends recency, growth, and volume into an emergingness score.
- `calculate_strategic_priority` derives relative strength across themes based on growth and volume metrics.
- Saves aggregated results to `trend_analysis.json`.

### 4.6 Emerging Topic Labelling (`src/emerging_topics_detector.py`)
- Reloads the saved BERTopic model to analyse emerging clusters in detail.
- Computes component scores (recency, growth, volume) and an overall emergingness value.
- If `OPENAI_API_KEY` is present, generates natural-language labels via the OpenAI API; otherwise outputs keyword-based summaries.
- Designed for batch runs or targeted analyses separate from the main pipeline.

### 4.7 Visualisations (`dashboard/utils/visualizations.py`)
- Defines reusable Plotly/Plotly Express chart builders:
  - `create_sunburst_chart`: Theme > sub-theme > topic hierarchy.
  - `create_sankey_flow`: Flow from themes to sub-themes to universities.
  - `create_trend_timeline`: Area plot of papers per theme over time.
  - `create_growth_heatmap`: Quarter-by-sub-theme intensity chart.
  - `create_impact_bubble_chart`: Growth rate vs citations vs volume for sub-themes.
  - `create_university_radar`: Radar comparison across selected universities.
- Functions expect filtered DataFrames provided by dashboard components.

### 4.8 Dashboard Structure (`dashboard/app.py`)
- Configures Streamlit page settings and loads external CSS from `dashboard/theme.css`.
- Uses `render_filters` to present a popover filter with date range, themes, sub-themes, and universities.
- Defines five tabs (Overview, Theme Analysis, Universities, Trends, Emerging Topics) that call the visualisation functions.
- Styling tweaks in `theme.css` include custom dark theme colours, popover adjustments, and calendar overrides (achieved by high-specificity CSS selectors).

---

## Chapter 5. Data Products and Outputs

### 5.1 Generated Files
- `data/raw/papers_raw.csv`: Raw OpenAlex exports filtered by theme and university.
- `data/processed/metadata.csv`: Cleaned metadata aligned with processed documents.
- `data/processed/documents.txt`: Preprocessed abstracts, one per line.
- `data/processed/embeddings.npy`: Optional cached sentence embeddings.
- `data/processed/papers_processed.csv`: Metadata plus topic IDs and probabilities.
- `data/processed/topics_over_time.csv`: BERTopic temporal output used for trend charts.
- `data/processed/topic_mapping.json`: Theme/sub-theme assignments and similarity scores.
- `data/processed/trend_analysis.json`: Quarterly counts, growth metrics, emerging topic listings.
- `models/bertopic_model.pkl`: Persisted BERTopic model for reuse.
- `data/exports/dashboard_data.json` (optional): Pre-packaged dashboard dataset.

### 5.2 Insight Examples
- Topic discovery typically yields 50 to 60 coherent clusters across AI, defence, energy, manufacturing, marine, aerospace, digital transformation, and cybersecurity.
- Trend analysis flags surging areas like zero-trust cybersecurity or energy storage research.
- Emergingness scores combine recency, growth, and volume to prioritise analyst attention.
- Dashboard views allow slicing results by university, theme, sub-theme, and timeline for actionable intelligence.

---

## Chapter 6. Limitations and Mitigations

- **Source coverage**: Only OpenAlex publications are included. Extend by adding arXiv, Dimensions, patents, or national grant feeds.
- **Keyword drift**: Theme keywords require periodic review. Consider automated keyword expansion with word embeddings.
- **LLM dependency**: Emerging topic labelling needs an OpenAI key; provide cached labels and keyword summaries as fallback.
- **Sampling bias**: Smaller institutions outside the curated list may be missed. Expand university coverage or scrape additional sources.
- **Model variability**: BERTopic involves stochastic components. Store UMAP embeddings, set random seeds, or persist model states for reproducibility.

---

## Chapter 7. Future Enhancements

1. Integrate patents, grants, and news feeds to contextualise academic output.
2. Add active learning so analysts can correct theme assignments and retrain incrementally.
3. Visualise collaboration networks (co-authorship, co-institution graphs) to surface partnership opportunities.
4. Implement scheduled pipelines and alerting when emergingness thresholds are exceeded.
5. Containerise the system, orchestrate with Airflow or Prefect, and integrate with enterprise authentication for production deployment.

---

## Appendix A. File and Module Reference

| Path | Purpose |
|------|---------|
| `run_full_analysis.py` | Orchestrates end-to-end pipeline with logging, timing, and mode selection. |
| `src/openalex_collector.py` | Base OpenAlex client with pagination, retry, and institution resolution helpers. |
| `src/theme_based_collector.py` | Theme-aware extension that issues keyword-filtered queries per strategic theme. |
| `src/paper_preprocessor.py` | Cleans abstracts, enforces minimum length, writes documents and metadata. |
| `src/topic_analyzer.py` | Configures and trains BERTopic, saves model, generates temporal outputs. |
| `src/theme_mapper.py` | Maps topic keywords to themes/sub-themes using TF-IDF cosine similarity. |
| `src/trend_analyzer.py` | Computes quarterly trends, growth, emerging topics, and priority scores. |
| `src/emerging_topics_detector.py` | Optional emerging topic labeller with recency/growth/volume scoring and LLM support. |
| `dashboard/app.py` | Streamlit entry point wiring filters, tabs, data loading, and CSS. |
| `dashboard/components/filters.py` | Popover filter UI for date range, themes, sub-themes, and universities. |
| `dashboard/utils/data_loader.py` | Loads processed datasets for dashboard consumption. |
| `dashboard/utils/visualizations.py` | Plotly chart builders reused across dashboard tabs. |
| `dashboard/theme.css` | Global dark theme styling, popover and calendar overrides. |
| `config/settings.py` | Central configuration: dates, universities, thresholds, file paths. |
| `config/themes.py` | Strategic themes, sub-themes, keyword lists, helper utilities. |
| `tests/test_setup.py` | Validates environment and configuration prerequisites. |
| `tests/test_focused.py` | Runs targeted pipeline checks (imports, data availability). |

This overview provides enough context for AI tools or engineers to navigate the repository, adjust configurations, or extend the analytics capabilities.
