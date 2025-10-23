# Text Preprocessing (Step 2)

This document explains how the preprocessing stage prepares collected papers for topic modeling and downstream analysis: involved files, classes and methods, inputs/outputs, parameters, and how it plugs into the full pipeline.

---

## Overview

- Goal: Convert raw OpenAlex paper records into clean, tokenized text suitable for BERTopic and analytics.
- Inputs: CSV produced in Step 1 (data collection), typically `data/raw/papers_raw.csv`.
- Outputs:
  - Cleaned and filtered DataFrame (in memory)
  - `data/processed/metadata.csv` with key fields (including the `theme` tag from collection)
  - `data/processed/documents.txt` containing one preprocessed document per line
  - Optionally `data/processed/papers_processed.csv` when using the preprocessor's own saver
- Key features:
  - Robust cleaning: lowercasing, URL/email stripping, punctuation and digit removal
  - Optional NLTK-based tokenization and lemmatization (with safe fallback)
  - Abstract-length filter to drop thin or noisy content
  - Optional keyword extraction for quick diagnostics

---

## Key Files and Roles

- `src/paper_preprocessor.py`
  - Class: `PaperPreprocessor`
  - Implements text cleaning, tokenization, lemmatization, abstract-length filtering, keyword extraction, and saving helpers.

- `scripts/run_full_analysis.py` (Step 2)
  - Orchestrates the preprocessing step after collection.
  - Writes `metadata.csv` and `documents.txt` for topic modeling.

- `config/settings.py`
  - Provides `MIN_ABSTRACT_LENGTH`, paths for `RAW_PAPERS_CSV`, `METADATA_CSV`, etc.

---

## Class: PaperPreprocessor

Constructor:
- `__init__(min_abstract_length: int = 50)`
  - Controls the minimum length for `abstract_clean` to keep a paper.
  - Initializes stopwords and WordNet lemmatizer when NLTK is available. Falls back gracefully if not.

Internal setup:
- `_setup_nltk()`
  - Downloads required NLTK resources (`stopwords`, `punkt`, `wordnet`, `omw-1.4`) when available.
  - Builds a stopword set (English + custom domain-generic terms such as "study", "algorithm", etc.).
  - If NLTK is missing or fails, logs a warning and uses a basic fallback (no lemmatization; simple token split).

Public API:
- `clean_text(text: str) -> str`
  - Lowercases; removes URLs, emails, non-letters; collapses whitespace.
  - Designed to be safe on missing/invalid inputs.

- `tokenize_and_lemmatize(text: str) -> List[str]`
  - If NLTK is available: `word_tokenize` -> remove stopwords/short tokens -> lemmatize.
  - Fallback: simple whitespace split and filter short tokens/punctuation.

- `preprocess_abstracts(df: pd.DataFrame) -> pd.DataFrame`
  - Copies input DataFrame and creates:
    - `abstract_clean`: cleaned abstract
    - Filters rows where `len(abstract_clean) >= min_abstract_length`
    - `tokens`: tokenized (and lemmatized when possible) tokens
    - `processed_text`: tokens joined with spaces (for BERTopic)
  - Drops rows with empty `tokens`.
  - Returns the processed DataFrame.

- `extract_keywords(df: pd.DataFrame, top_n: int = 20) -> Dict[str, List[str]]`
  - Aggregates `processed_text` per university and applies TF-IDF to extract salient 1–2 gram keywords.
  - Helpful for diagnostics or dashboard insights.

- `get_processing_stats(df: pd.DataFrame) -> Dict`
  - Returns summary stats: counts, averages, date range, etc.

- `save_processed_data(df: pd.DataFrame, filepath: str) -> None`
  - Serializes processed DataFrame to CSV, converting list fields (like `tokens`) to a pipe-separated string for storage.

---

## End-to-End Flow in the Pipeline

Within `scripts/run_full_analysis.py` (Step 2):

1. Load raw collection output:
   - `df = pd.read_csv(RAW_PAPERS_CSV)`
2. Instantiate preprocessor with configured minimum length:
   - `preprocessor = PaperPreprocessor(min_abstract_length=MIN_ABSTRACT_LENGTH)`
3. Run preprocessing:
   - `df = preprocessor.preprocess_abstracts(df)`
4. Build modeling inputs:
   - `documents = df['processed_text'].tolist()`
   - `metadata = df[['title', 'university', 'date', 'authors', 'journal', 'citations', 'theme']].copy()`
5. Persist outputs:
   - `metadata.to_csv(METADATA_CSV, index=False)`
   - Write `documents.txt` (one document per line)

Downstream (Step 3): topic modeling consumes `documents.txt` and `metadata.csv` and writes `topics_over_time.csv` and the saved BERTopic model.

---

## Inputs and Outputs

Inputs:
- `data/raw/papers_raw.csv` – produced by the collection step

Primary Outputs (by pipeline Step 2):
- `data/processed/metadata.csv` – columns:
  - `title, university, date, authors, journal, citations, theme`
- `data/processed/documents.txt` – preprocessed text per line

Optional Output (using `save_processed_data`):
- `data/processed/papers_processed.csv` – full processed DataFrame including `abstract_clean`, `tokens`, and `processed_text`

---

## Example Usage

Standalone usage:
```python
import pandas as pd
from src.paper_preprocessor import PaperPreprocessor

df = pd.read_csv('data/raw/papers_raw.csv')
pp = PaperPreprocessor(min_abstract_length=50)

processed = pp.preprocess_abstracts(df)
keywords_by_uni = pp.extract_keywords(processed, top_n=20)
stats = pp.get_processing_stats(processed)

pp.save_processed_data(processed, 'data/processed/papers_processed.csv')
```

Pipeline (already wired):
```powershell
python scripts/run_full_analysis.py
```

---

## Performance and Considerations

- NLTK dependency is optional: the implementation falls back gracefully if unavailable.
- Filtering is conservative—consider adjusting `MIN_ABSTRACT_LENGTH` for your corpus.
- Keyword extraction uses TF-IDF over concatenated texts per university; tweak `max_features`, `min_df`, `max_df`, and `ngram_range` for different behavior.

---

## Troubleshooting

- Empty `processed_text` lines
  - Ensure non-empty abstracts and adequate `MIN_ABSTRACT_LENGTH`.
- NLTK download warnings
  - The preprocessor will continue in fallback mode; install NLTK datasets if you prefer lemmatization.
- Mismatch with Step 3
  - Verify `documents.txt` and `metadata.csv` are in sync and generated from the same filtered DataFrame.

---

## Extending/Customizing

- Add domain-specific stopwords to `_setup_nltk`.
- Expand the cleaning rules in `clean_text` for your text sources.
- Replace tokenization/lemmatization with spaCy or a custom pipeline if needed.
- Store additional fields in `metadata.csv` as required by your downstream analytics.

---

## Flow diagram (Preprocessing)

```mermaid
flowchart TD
  subgraph Inputs
    R[CSV: data/raw/papers_raw.csv]
    Cfg[config.settings\nMIN_ABSTRACT_LENGTH, paths]
  end

  A[Load CSV]
  B[PaperPreprocessor.__init__\n(min_abstract_length)]
  C[preprocess_abstracts(df)]
  C1[clean_text]
  C2[tokenize_and_lemmatize\n(NLTK if available,\nfallback otherwise)]
  C3[build processed_text\n(join tokens)]
  D[Filter: length >= min,\nnon-empty tokens]
  E[Build metadata\n(title, university, date, authors, journal, citations, theme)]
  F[documents = processed_text\n(one per line)]
  M[Write metadata.csv\n(data/processed/metadata.csv)]
  T[Write documents.txt\n(data/processed/documents.txt)]
  N[Optional: extract_keywords\n(TF-IDF per university)]

  R --> A --> C
  Cfg --> B
  B --> C
  C --> C1 --> C2 --> C3 --> D
  D --> E --> M
  D --> F --> T
  D --> N

  classDef inp fill:#eef,stroke:#88a,stroke-width:1px;
  class R,Cfg inp;
```
