# Quick Start - Updated Commands

## 🚀 Running the Project

All user-facing scripts are now in the `scripts/` folder.

### Full Analysis Pipeline

```powershell
python scripts/run_full_analysis.py
```

Choose your mode:
- **1** - Quick test (3 universities, ~1000-1500 papers, 8-10 min)
- **2** - Medium test (10 universities, ~4000-6000 papers, 20-25 min)
- **3** - Full collection (43 universities, ~15000-25000 papers, 60-120 min)

### Launch Dashboard

```powershell
python scripts/launch_dashboard.py
```

Opens interactive Streamlit dashboard at `http://localhost:8501`

### View Results (CLI)

```powershell
python scripts/view_results.py
```

Text-based summary of analysis results in the terminal.

### Reprocess Existing Data

```powershell
python scripts/reprocess_existing_data.py
```

Reruns pipeline steps 2-5 without re-collecting data from OpenAlex.

---

## 📁 Project Structure Overview

```
Smart-Research-insights/
│
├── scripts/           ⭐ Run these files
│   ├── run_full_analysis.py
│   ├── launch_dashboard.py
│   ├── view_results.py
│   └── reprocess_existing_data.py
│
├── config/            Configuration
│   ├── settings.py    (universities, dates, paths)
│   └── themes.py      (Babcock's 9 themes)
│
├── src/               Core pipeline (don't run directly)
│   ├── theme_based_collector.py
│   ├── paper_preprocessor.py
│   ├── topic_analyzer.py
│   ├── theme_mapper.py
│   ├── trend_analyzer.py
│   └── emerging_topics_detector.py
│
├── dashboard/         Streamlit UI
│   ├── app.py
│   ├── components/
│   ├── tabs/
│   └── utils/
│
├── tests/             Testing
│   ├── test_setup.py
│   └── test_focused.py
│
├── data/              Data storage
│   ├── raw/
│   └── processed/
│
└── docs/              Documentation
```

---

## 🧪 Testing

```powershell
# Environment validation
python tests/test_setup.py

# Quick focused tests
python tests/test_focused.py
```

---

## 📊 Key Output Files

After running the analysis:

| File | Location | Description |
|------|----------|-------------|
| Raw papers | `data/raw/papers_raw.csv` | Collected papers from OpenAlex |
| Processed papers | `data/processed/papers_processed.csv` | Papers with topics assigned |
| Metadata | `data/processed/metadata.csv` | Paper metadata |
| Topics over time | `data/processed/topics_over_time.csv` | Temporal topic evolution |
| Topic mapping | `data/processed/topic_mapping.json` | Topics mapped to themes |
| Trend analysis | `data/processed/trend_analysis.json` | Strategic trend insights |
| BERTopic model | `models/bertopic_model.pkl` | Trained topic model |
| Logs | `logs/full_analysis_*.log` | Execution logs |

---

## 🔧 Configuration

Edit `.env` file:

```env
OPENALEX_EMAIL=your.email@domain.com
```

Edit `config/settings.py` to change:
- Universities
- Date range
- Analysis parameters

Edit `config/themes.py` to modify:
- Babcock's 9 strategic themes
- Keywords for each theme

---

## 💡 Common Workflows

### First Time Setup

```powershell
# 1. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
Copy-Item .env.example .env
# Edit .env with your email

# 4. Test setup
python tests/test_setup.py

# 5. Run quick test
python scripts/run_full_analysis.py
# Choose option 1 (quick test)
```

### Regular Usage

```powershell
# Activate environment
.\.venv\Scripts\Activate

# Run full analysis
python scripts/run_full_analysis.py

# View dashboard
python scripts/launch_dashboard.py
```

### Reprocessing Only

```powershell
# If you already have data in data/raw/ and want to rerun analysis
python scripts/reprocess_existing_data.py
```

---

## 📝 What Changed?

### October 2025 Cleanup

**Removed:**
- ❌ `dashboard/app_old_backup.py` (duplicate)
- ❌ `dashboard/app_reference.py` (duplicate)
- ❌ `src/openalex_collector.py` (unused, superseded by theme_based_collector)

**Organized:**
- ✅ All executables moved to `scripts/` folder
- ✅ Documentation consolidated in `docs/`
- ✅ Single collector: `theme_based_collector.py`
- ✅ Single dashboard: `app.py`

**Command Changes:**

| Old | New |
|-----|-----|
| `python run_full_analysis.py` | `python scripts/run_full_analysis.py` |
| `python launch_dashboard.py` | `python scripts/launch_dashboard.py` |
| `python view_results.py` | `python scripts/view_results.py` |
| `python reprocess_existing_data.py` | `python scripts/reprocess_existing_data.py` |

---

## 🆘 Troubleshooting

### Import Errors

```powershell
# Regenerate __init__.py files
python tests/debug/fix_imports.py
```

### API Issues

Check your `.env` file has the correct email for OpenAlex polite pool.

### Dashboard Won't Start

```powershell
# Try direct streamlit command
streamlit run dashboard/app.py
```

### No Data

Run the full analysis first:
```powershell
python scripts/run_full_analysis.py
```

---

## 📚 More Documentation

- `docs/Quick_start.md` - Original quick start guide
- `docs/CLEANUP_OCT_2025.md` - Detailed cleanup notes
- `docs/ORGANIZATION_FINAL.md` - File organization rationale
- `README.md` - Comprehensive project documentation

---

*Last updated: October 23, 2025*
