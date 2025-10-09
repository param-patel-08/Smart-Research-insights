#   Quick Start Guide - Babcock Research Trends

##   What You Have Now

All code is complete! Here's what's built:

### Core Modules (Ready to Run)

-   **OpenAlex Data Collector** - Fetches papers from 24 universities
-   **Preprocessor** - Cleans and filters papers
-   **BERTopic Analyzer** - Discovers research topics
-   **Theme Mapper** - Maps topics to 9 Babcock themes
-   **Trend Analyzer** - Identifies growth patterns

### Scripts

-   **run_full_analysis.py** - One command runs everything!
-   **exploration/view_results.py** - Quick text summary of results
-   **tests/test_setup.py** - Verify installation

### Configuration

-   **config/themes.py** - 9 Babcock strategic themes defined
-   **config/settings.py** - All settings configured
-   **requirements.txt** - All dependencies listed

---

##   3-Step Setup (5 Minutes)

### Step 1: Install Packages

```powershell
# Activate virtual environment (if created)
.\venv\Scripts\Activate

# Install all packages
pip install -r requirements.txt
```

**Wait for installation** (5-10 minutes). You'll see:

```
Collecting bertopic...
Downloading...
Installing collected packages...
Successfully installed bertopic-0.16.0 ...
```

---

### Step 2: Create .env File

Create a `.env` file with your OpenAlex polite pool email:

```
OPENALEX_EMAIL=your.email@domain.com
```

---

### Step 3: Test Setup

```powershell
python tests/test_setup.py
```

**You should see:**

```
================================================================================
  ALL TESTS PASSED! System is ready to use.
================================================================================
```

If you see errors, check:

-   Packages not installed   Run Step 1 again
-   .env file missing   Check your project folder
-   Python version   Need Python 3.9+

---

##   Running the Analysis

### Option A: Full Automatic Pipeline (Recommended!)

```powershell
python run_full_analysis.py
```

**You'll be asked to choose scope:**

```
Options:
  1. Quick test (3 universities, 100 papers each) - 5 minutes
  2. Medium test (10 universities, 500 papers each) - 15 minutes
  3. Full collection (all 24 universities, no limit) - 30-60 minutes

Enter your choice (1/2/3) [default: 1]:
```

**Recommendation:**

- First time: Choose **1** (quick test) to verify everything works
- Then run: Choose **3** (full collection) for real results

**What happens:**

1.   Collects papers from OpenAlex
2.   Filters by Babcock themes
3.   Runs BERTopic (discovers ~60 topics)
4.   Maps topics to 9 themes
5.   Calculates growth trends
6.   Saves all results

**Total time:**

- Quick test: ~5 minutes
- Full analysis: ~60 minutes

---

### Option B: Step-by-Step (Manual Control)

```powershell
# Step 1: Collect data
python src/openalex_collector.py

# Step 2: Preprocess
python src/preprocessor.py

# Step 3: Topic modeling
python src/topic_analyzer.py

# Step 4: Theme mapping
python src/theme_mapper.py

# Step 5: Trend analysis
python src/trend_analyzer.py
```

---

##   Viewing Results

### Quick Text Summary

```powershell
python view_results.py
```

**Shows:**

-   Papers analyzed
-   Strategic priorities
-   Emerging topics
-    Top universities
-   Growth trends

---

##   Where Are My Results?

After analysis completes, check these folders:

data/
    raw/
        collected_papers.csv         All papers collected
    processed/
        paper_metadata.csv           Filtered papers
        papers_processed.csv         Papers + topic assignments
        documents.txt                Text for BERTopic
        topics_over_time.csv         Quarterly trends
        topic_mapping.json           Topics   Themes mapping
        trend_analysis.json          Strategic insights

models/
    bertopic_model.pkl              Trained BERTopic model

data/processed/
    embeddings.npy                   Cached embeddings (fast re-runs!)

logs/
    full_analysis_YYYYMMDD.log      Detailed logs

##   What You'll Get

### Quantitative Results

- **Papers analyzed:** ~5,000-10,000 (depending on scope)
- **Topics discovered:** ~60-80
- **Themes covered:** All 9 Babcock themes
- **Universities:** 24 (Australia + New Zealand)
- **Time period:** Last 24 months (Oct 2023 - Oct 2025)

### Strategic Insights

-   Growth rate per theme (quarter-over-quarter)
-   Emerging topics (>50% growth)
-   Declining topics
-   Top universities per theme
-   Cross-theme topics
-   Strategic priority scores

### Deliverables for Babcock

-   Interactive dashboard (coming soon!)
-   Quarterly trend analysis
-   University partnership recommendations
-   CONOPS document
-   Development strategy

---

##   Common Issues & Solutions

### "ModuleNotFoundError: No module named 'bertopic'"

**Solution:** Install packages

```powershell
pip install bertopic sentence-transformers umap-learn hdbscan
```

### "FileNotFoundError: .env"

**Solution:** Create .env file

```powershell
"OPENALEX_EMAIL=sdv6266@autuni.ac.nz" | Out-File -FilePath .env -Encoding utf8
```

### "OpenAlex rate limit"

**Solution:** Your email is in polite pool - just wait 10 seconds and retry

### "Out of memory"

**Solution:** Choose scope 1 (quick test) or close other programs

### BERTopic is slow

**Solution:** This is normal! It's doing ML inference. Takes 60-90 seconds.

### Analysis interrupted

**Solution:** Just run again - it won't duplicate data!

---

##    Time Expectations

| Task            | Quick Test | Full Analysis  |
| --------------- | ---------- | -------------- |
| Data collection | 3 min      | 30-45 min      |
| Preprocessing   | 30 sec     | 2 min          |
| BERTopic        | 60 sec     | 90 sec         |
| Theme mapping   | 10 sec     | 15 sec         |
| Trend analysis  | 5 sec      | 10 sec         |
| **TOTAL**       | **~5 min** | **~35-50 min** |

---

##   Your Action Plan

### Today (5 minutes):

1.   Install packages
2.   Run `tests/test_setup.py`
3.   Run quick test: `python run_full_analysis.py` (choose option 1)
4.   View results: `python view_results.py`

### Tonight (if time):

1.   Run full analysis: `python run_full_analysis.py` (choose option 3)
2.   Let it run while you do other things (~1 hour)

### Tomorrow:

1.   View full results
2.   Start writing your project report
3.   Build dashboard (next step!)

---

##   Ready to Start?

```powershell
# Run this now!
python tests/test_setup.py
```

If all tests pass, you're ready to go:

```powershell
python run_full_analysis.py
```

**That's it!** The system will guide you through the rest.  

---

##   Questions?

- Check logs: `logs/full_analysis_*.log`
- Review output files in `data/processed/`
- Re-run `tests/test_setup.py` to diagnose issues

**You've got everything you need - just run it!**  
