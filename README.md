# Babcock Research Trends Analysis System

Automated research intelligence system for tracking emerging trends across Australasian universities using BERTopic and OpenAlex API.

## 🎯 Project Overview

**Sponsor:** Babcock (Karen Trezise, Chief Technologist)  
**Project ID:** BAB-AUSNZ-TECH-TIP-0030_01  
**Analysis Period:** October 2023 - October 2025 (24 months)  
**Strategic Themes:** 9 Babcock priority areas

## 📋 Prerequisites

- Python 3.9 or higher
- pip package manager
- Your email address (for OpenAlex API polite pool)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your email:

```
OPENALEX_EMAIL=your.email@university.edu
```

### 3. Data Collection (Step 1)

Collect papers from Australasian universities:

```bash
python src/openalex_collector.py
```

**Expected output:**
- Raw papers saved to `data/raw/collected_papers.csv`
- ~5,000-10,000 papers (after filtering)
- Takes about 30-60 minutes for full collection

**To test with fewer universities first:**

Edit the `main()` function in `openalex_collector.py`:

```python
# Test with just 3 universities
test_universities = dict(list(ALL_UNIVERSITIES.items())[:3])

df = collector.fetch_all_universities(
    universities=test_universities,
    max_per_uni=100  # Limit to 100 papers per university
)
```

### 4. Preprocessing (Step 2)

Clean and filter papers for analysis:

```bash
python src/preprocessor.py
```

**Expected output:**
- Filtered papers in `data/processed/paper_metadata.csv`
- Documents ready for BERTopic in `data/processed/documents.txt`
- ~3,000-7,000 papers after filtering by Babcock themes

### 5. Next Steps (Coming Soon)

- Topic modeling with BERTopic
- Theme mapping
- Trend analysis
- Dashboard

## 📁 Project Structure

```
babcock-research-trends/
├── config/
│   ├── themes.py              # Babcock's 9 strategic themes
│   └── settings.py            # Configuration settings
├── data/
│   ├── raw/                   # Raw collected papers
│   ├── processed/             # Preprocessed data
│   └── exports/               # Generated reports
├── src/
│   ├── openalex_collector.py # OpenAlex data collection
│   └── preprocessor.py        # Data preprocessing
├── .env                       # Your configuration (create this)
├── .env.example               # Configuration template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔑 Key Features

### Data Collection via OpenAlex
- Fetches papers from 24 Australasian universities
- Date range: Last 24 months (rolling window)
- Includes title, abstract, authors, citations, etc.
- Automatic deduplication

### Intelligent Filtering
- Filters by 9 Babcock strategic themes:
  1. Defense & Security
  2. Autonomous Systems
  3. Cybersecurity
  4. Energy & Sustainability
  5. Advanced Manufacturing
  6. AI & Machine Learning
  7. Marine & Naval
  8. Space & Aerospace
  9. Digital Transformation

### Preprocessing Pipeline
- Cleans and normalizes text
- Combines title + abstract (weighted)
- Calculates relevance scores per theme
- Removes low-quality papers
- Prepares data for BERTopic

## 🎓 Universities Tracked

### Australia (17 universities)
- Group of Eight: Melbourne, Sydney, UNSW, ANU, Monash, UQ, Adelaide, UWA
- Others: QUT, UTS, RMIT, Curtin, Macquarie, Deakin, Griffith, Newcastle, Wollongong

### New Zealand (7 universities)
- Auckland, Otago, Canterbury, Victoria Wellington, Massey, Waikato, AUT

## ⚙️ Configuration

Edit `config/settings.py` to customize:

- Date range for analysis
- University list
- BERTopic parameters
- Filtering thresholds
- File paths

Edit `config/themes.py` to customize:

- Theme keywords
- Strategic priorities
- Theme descriptions

## 📊 Expected Data Volume

Based on 24-month collection:

- **Raw papers collected:** 50,000-100,000
- **After deduplication:** 40,000-80,000
- **After Babcock filtering:** 5,000-10,000
- **After preprocessing:** 3,000-7,000

## 🐛 Troubleshooting

### "Rate limited by OpenAlex"
- Add your email to `.env` file
- Reduce `per_page` parameter
- Add longer `time.sleep()` delays

### "Too few papers collected"
- Check date range in `config/settings.py`
- Verify university IDs are correct
- Lower `MIN_RELEVANCE_SCORE` threshold

### "Out of memory"
- Process universities in batches
- Reduce `max_per_uni` parameter
- Use a machine with more RAM

## 📝 Notes

- First run takes 30-60 minutes for data collection
- OpenAlex API is free but requests you use email for polite pool
- Data is public and no ethics approval needed
- Papers are deduplicated automatically

## 🔄 Quarterly Updates

For production use, run the collection quarterly:
- End of January (Q1)
- End of April (Q2)
- End of July (Q3)
- End of October (Q4)

## 📧 Contact

**Project Sponsor:** Karen Trezise (karen.trezise@babcock.com.au)

## 📄 License

Academic research project - All rights reserved.